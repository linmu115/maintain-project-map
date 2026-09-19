#!/usr/bin/env python3
"""Local, bounded-file HTTP delivery for a generated project-map reader."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from http.client import HTTPException
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from html import escape
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import tempfile
import threading
import time
from urllib.parse import unquote, urlsplit, parse_qs
from urllib.request import Request, ProxyHandler, build_opener

SCHEMA = "project-map-preview/v1"
IDLE_SECONDS = 8 * 60 * 60


def entry_path(entry):
    path = Path(entry).expanduser().resolve()
    if path.suffix.lower() != ".html" or not path.is_file():
        raise ValueError("Preview entry must be an existing generated .html file")
    return path


def receipt_path(entry):
    return entry.with_suffix(".preview.json")


def read_receipt(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def write_receipt(path, value):
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                     prefix=".preview-", delete=False) as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        temporary = Path(f.name)
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def preview_lock(entry):
    path = entry.with_suffix(".preview.lock")
    deadline = time.monotonic() + 6
    while True:
        try:
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise RuntimeError(f"Preview is busy; inspect an abandoned lock before removing it: {path}")
            time.sleep(0.05)
    try:
        os.close(descriptor)
        yield
    finally:
        path.unlink(missing_ok=True)


def request_control(state, action, method="GET"):
    port, token = state.get("port"), state.get("token")
    if type(port) is not int or not 1 <= port <= 65535 or not isinstance(token, str) or not re.fullmatch(r"[a-f0-9]{32}", token):
        return None
    # Receipt fields never choose a remote host or a system process to signal.
    url = f"http://127.0.0.1:{port}/{token}/__{action}"
    try:
        req = Request(url, data=b"" if method == "POST" else None, method=method)
        with build_opener(ProxyHandler({})).open(req, timeout=0.7) as response:
            return json.loads(response.read(8192))
    except (OSError, ValueError, HTTPException):
        return None


def live_state(entry):
    state = read_receipt(receipt_path(entry))
    if state.get("schema") != SCHEMA or state.get("entry") != str(entry):
        return None
    health = request_control(state, "health")
    if not health or any(health.get(k) != state.get(k) for k in ("schema", "token", "entry", "pid")):
        return None
    return state


def public_state(state, reused=False):
    return {"status": "running", "url": state["url"], "entry": state["entry"],
            "pid": state["pid"], "reused": reused, "idle_timeout_hours": IDLE_SECONDS // 3600}


def start_reader(entry):
    entry = entry_path(entry)
    with preview_lock(entry):
        receipt = receipt_path(entry)
        previous = read_receipt(receipt)
        if receipt.exists() and (receipt.is_symlink() or previous.get("schema") != SCHEMA or previous.get("entry") != str(entry)):
            raise ValueError(f"Existing preview receipt is not owned by this entry; preserved: {receipt}")
        existing = live_state(entry)
        if existing and existing.get("history_assets_version", 0) < 2:
            try:
                needs_history = bool(json.loads((entry.parent / "history-assets.json").read_text(encoding="utf-8")).get("files"))
            except (OSError, ValueError, AttributeError):
                needs_history = False
            if needs_history:
                acknowledgement = request_control(existing, "stop", "POST")
                if not acknowledgement or acknowledgement.get("token") != existing["token"]:
                    raise RuntimeError("Existing preview could not upgrade for lazy history assets; HTML remains available")
                deadline = time.monotonic() + 3
                while request_control(existing, "health") is not None and time.monotonic() < deadline:
                    time.sleep(0.05)
                if request_control(existing, "health") is not None:
                    raise RuntimeError("Previous preview has not stopped yet")
                existing = None
        if existing:
            return public_state(existing, reused=True)
        token = secrets.token_hex(16)
        command = [sys.executable, "-B", str(Path(__file__).resolve()), "_run", str(entry), "--token", token]
        options = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL,
                   "stderr": subprocess.DEVNULL, "close_fds": True}
        if os.name == "nt":
            options["creationflags"] = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
        else:
            options["start_new_session"] = True
        child = subprocess.Popen(command, **options)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            state = live_state(entry)
            if state and state.get("token") == token:
                return public_state(state)
            if child.poll() is not None:
                raise RuntimeError(f"Preview exited during startup (code {child.returncode}); HTML export remains available")
            time.sleep(0.05)
        # This handle belongs to the child just created, never to a PID from a receipt.
        child.terminate()
        child.wait(timeout=3)
        raise RuntimeError("Preview startup timed out; HTML export remains available")


def reader_status(entry):
    entry = entry_path(entry)
    state = live_state(entry)
    return public_state(state, reused=True) if state else {"status": "stopped", "entry": str(entry)}


def stop_reader(entry):
    entry = entry_path(entry)
    with preview_lock(entry):
        state = live_state(entry)
        if not state:
            return {"status": "stopped", "entry": str(entry), "changed": False}
        result = request_control(state, "stop", "POST")
        if not result or result.get("token") != state["token"]:
            raise RuntimeError("Preview did not acknowledge stop; no system process was killed")
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            if request_control(state, "health") is None:
                return {"status": "stopped", "entry": str(entry), "changed": True}
            time.sleep(0.05)
        raise RuntimeError("Preview has not stopped yet")


def run_server(entry, token):
    entry = entry_path(entry)
    if not re.fullmatch(r"[a-f0-9]{32}", token):
        raise ValueError("Invalid preview identity")
    stopped = threading.Event()
    allowed = {entry.name, "architecture.html", "workflow.html", "docs.json",
               "architecture.native.html", "workflow.native.html"}
    state = {}
    project_open_lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def send_bytes(self, status, body, content_type="text/plain; charset=utf-8"):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def target(self):
            port = state["port"]
            hosts = {f"localhost:{port}", f"127.0.0.1:{port}"}
            if self.headers.get("Host", "").lower() not in hosts:
                self.send_bytes(403, b"Invalid local host")
                return None
            origin = self.headers.get("Origin")
            if origin and origin not in {"http://" + host for host in hosts}:
                self.send_bytes(403, b"Foreign origin")
                return None
            try:
                path = unquote(urlsplit(self.path).path, errors="strict")
            except (ValueError, UnicodeError):
                self.send_bytes(400, b"Invalid path")
                return None
            prefix = f"/{token}/"
            if not path.startswith(prefix):
                self.send_bytes(404, b"Not found")
                return None
            self.server.last_request = time.monotonic()
            return path[len(prefix):]

        def do_GET(self):
            target = self.target()
            if target is None:
                return
            if target == "__health":
                self.send_bytes(200, json.dumps(state).encode(), "application/json")
                return
            if target == "__project":
                if self.command == "HEAD":
                    self.send_bytes(405, b"Open the project link with GET")
                    return
                try:
                    from system_map import open_project_target
                    values = parse_qs(urlsplit(self.path).query, max_num_fields=8)
                    if set(values) - {"project", "diagram", "record", "node"} or any(len(v) != 1 for v in values.values()):
                        raise ValueError("项目链接参数不明确")
                    with project_open_lock:
                        url = open_project_target(entry, values.get("project", [""])[0],
                                                  **{k: values[k][0] for k in ("diagram", "record", "node") if k in values})
                    self.send_response(302)
                    self.send_header("Location", url)
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                except (OSError, ValueError, RuntimeError) as exc:
                    page = ('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>项目暂不可用</title>'
                            '<style>body{font:16px/1.7 system-ui;max-width:680px;margin:12vh auto;padding:24px;color:#222}</style>'
                            '<h1>暂时无法进入项目</h1><p>' + escape(str(exc)) + '</p>'
                            '<p>系统地图仍保留在原标签页。请修复项目位置或图源后，从原页重新进入。</p></html>')
                    self.send_bytes(409, page.encode("utf-8"), "text/html; charset=utf-8")
                return
            if target == "":
                target = entry.name
            if re.fullmatch(r"history/[a-f0-9]{20}/EVT-[a-f0-9]{20}-\d+\.json", target):
                try:
                    from development_history import read_export_packet
                    packet = read_export_packet(entry.parent, target)
                    self.send_bytes(200, json.dumps(packet, ensure_ascii=False).encode(), "application/json; charset=utf-8")
                except KeyError:
                    self.send_bytes(404, b"Not found")
                except (OSError, ValueError) as exc:
                    self.send_bytes(409, json.dumps({"error": str(exc)}, ensure_ascii=False).encode(), "application/json; charset=utf-8")
                return
            history_asset = False
            if re.fullmatch(r"(?:history/[a-f0-9]{20}/(?:index|EVT-[a-f0-9]{20}-\d+)\.json|archive/[a-f0-9]{20}\.html)", target):
                try:
                    manifest = entry.parent / "history-assets.json"
                    if not manifest.is_symlink():
                        history_asset = target in json.loads(manifest.read_text(encoding="utf-8")).get("files", [])
                except (OSError, ValueError, AttributeError):
                    pass
            if target not in allowed and not history_asset:
                self.send_bytes(404, b"Not found")
                return
            path = entry.parent / target
            if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(entry.parent) or (not history_asset and path.resolve().parent != entry.parent):
                self.send_bytes(404, b"Not found")
                return
            try:
                content = path.read_bytes()
            except OSError:
                self.send_bytes(404, b"Not found")
                return
            kind = "application/json; charset=utf-8" if path.suffix == ".json" else "text/html; charset=utf-8"
            self.send_bytes(200, content, kind)

        do_HEAD = do_GET

        def do_POST(self):
            target = self.target()
            if target is None:
                return
            if target != "__stop":
                self.send_bytes(405, b"Read-only preview")
                return
            self.send_bytes(200, json.dumps({"token": token}).encode(), "application/json")
            stopped.set()

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    server.timeout = 0.3
    server.last_request = time.monotonic()
    port = server.server_address[1]
    state.update(schema=SCHEMA, entry=str(entry), token=token, pid=os.getpid(), port=port, history_assets_version=2,
                 url=f"http://localhost:{port}/{token}/")
    receipt = receipt_path(entry)
    try:
        write_receipt(receipt, state)
        while not stopped.is_set() and time.monotonic() - server.last_request < IDLE_SECONDS:
            server.handle_request()
    finally:
        server.server_close()
        if read_receipt(receipt).get("token") == token:
            receipt.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("start", "status", "stop", "_run"))
    parser.add_argument("entry", help="Generated views/index.html")
    parser.add_argument("--token", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        if args.action == "_run":
            run_server(args.entry, args.token or "")
            return 0
        operation = {"start": start_reader, "status": reader_status, "stop": stop_reader}[args.action]
        print(json.dumps(operation(args.entry), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
