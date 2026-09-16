from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import unittest
from urllib.error import HTTPError
from urllib.parse import urljoin, urlsplit
from urllib.request import ProxyHandler, Request, build_opener

SCRIPTS = Path(__file__).resolve().parents[1] / "maintain-project-map/scripts"
sys.path.insert(0, str(SCRIPTS))
from serve_map import start_reader, stop_reader, reader_status, receipt_path, SCHEMA
from project_map import init_project


def fetch(url, headers=None, method="GET"):
    req = Request(url, headers=headers or {}, method=method)
    with build_opener(ProxyHandler({})).open(req, timeout=3) as response:
        return response.status, response.read(), dict(response.headers)


class PreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.entry = self.root / "views/index.html"
        self.entry.parent.mkdir()
        self.entry.write_text("<h1>中文地图</h1>", encoding="utf-8")

    def tearDown(self):
        stop_reader(self.entry)
        self.temp.cleanup()

    def test_local_link_serves_entry_and_relative_diagrams(self):
        (self.entry.parent / "architecture.html").write_text("<p>模块</p>", encoding="utf-8")
        (self.entry.parent / "architecture.native.html").write_text("<p>原版模块</p>", encoding="utf-8")
        (self.entry.parent / "workflow.native.html").write_text("<p>原版流程</p>", encoding="utf-8")
        state = start_reader(self.entry)
        self.assertEqual(urlsplit(state["url"]).hostname, "localhost")
        status, body, headers = fetch(state["url"])
        self.assertEqual(status, 200)
        self.assertEqual(body.decode(), "<h1>中文地图</h1>")
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(fetch(urljoin(state["url"], "architecture.html"))[1].decode(), "<p>模块</p>")
        self.assertEqual(fetch(urljoin(state["url"], "architecture.native.html"))[1].decode(), "<p>原版模块</p>")
        self.assertEqual(fetch(urljoin(state["url"], "workflow.native.html"))[1].decode(), "<p>原版流程</p>")
        self.assertNotIn("Access-Control-Allow-Origin", headers)

    def test_repeat_generation_reuses_service_and_reads_new_bytes(self):
        first = start_reader(self.entry)
        self.entry.write_text("<h1>更新后的地图</h1>", encoding="utf-8")
        second = start_reader(self.entry)
        self.assertTrue(second["reused"])
        self.assertEqual((first["pid"], first["url"]), (second["pid"], second["url"]))
        self.assertEqual(fetch(second["url"])[1].decode(), "<h1>更新后的地图</h1>")

    def test_unlisted_files_traversal_host_and_origin_are_denied(self):
        (self.entry.parent / "private.txt").write_text("not served")
        url = start_reader(self.entry)["url"]
        origin = urlsplit(url)
        blocked = [urljoin(url, "private.txt"), url + "../private.txt", url + "%2e%2e%2fprivate.txt",
                   urljoin(url, receipt_path(self.entry).name), f"{origin.scheme}://{origin.netloc}/"]
        for address in blocked:
            with self.assertRaises(HTTPError) as error:
                fetch(address)
            self.assertEqual(error.exception.code, 404)
        for headers in ({"Host": "foreign.invalid"}, {"Origin": "https://foreign.invalid"}):
            with self.assertRaises(HTTPError) as error:
                fetch(url, headers)
            self.assertEqual(error.exception.code, 403)
        with self.assertRaises(HTTPError) as error:
            fetch(url, method="POST")
        self.assertEqual(error.exception.code, 405)

    def test_stop_is_explicit_and_service_is_reopenable(self):
        first = start_reader(self.entry)
        self.assertEqual(reader_status(self.entry)["status"], "running")
        self.assertTrue(stop_reader(self.entry)["changed"])
        self.assertEqual(reader_status(self.entry)["status"], "stopped")
        self.assertFalse(stop_reader(self.entry)["changed"])
        second = start_reader(self.entry)
        self.assertFalse(second["reused"])
        self.assertNotEqual(second["url"], first["url"])

    def test_foreign_receipt_preserved_and_stale_own_receipt_recovered(self):
        receipt = receipt_path(self.entry)
        receipt.write_text('"user data"', encoding="utf-8")
        with self.assertRaises(ValueError):
            start_reader(self.entry)
        self.assertEqual(receipt.read_text(), '"user data"')
        receipt.write_text(json.dumps({"schema": SCHEMA, "entry": str(self.entry.resolve()),
                                      "port": 0, "token": "0" * 32, "pid": os.getpid()}))
        self.assertEqual(start_reader(self.entry)["status"], "running")

    def test_two_processes_start_one_service(self):
        command = [sys.executable, "-B", str(SCRIPTS / "serve_map.py"), "start", str(self.entry)]
        children = [subprocess.Popen(command, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(2)]
        results = []
        for child in children:
            out, err = child.communicate(timeout=15)
            self.assertEqual(child.returncode, 0, err.decode("utf-8"))
            results.append(json.loads(out))
        self.assertEqual(results[0]["pid"], results[1]["pid"])
        self.assertEqual(results[0]["url"], results[1]["url"])

    def test_render_cli_defaults_http_and_export_only_stays_offline(self):
        project = self.root / "project"
        init_project(project, "阅读样例", kind="skill")
        command = [sys.executable, "-B", str(SCRIPTS / "render_map.py"), str(project),
                   "--no-diagrams", "--output", str(self.entry)]
        result = subprocess.run(command, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8"))
        payload = json.loads(result.stdout)
        self.assertEqual(payload["preview"]["status"], "running")
        self.assertEqual(fetch(payload["url"])[0], 200)
        stop_reader(self.entry)
        result = subprocess.run(command + ["--export-only"], creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8"))
        self.assertNotIn("preview", json.loads(result.stdout))
        self.assertEqual(reader_status(self.entry)["status"], "stopped")


if __name__ == "__main__":
    unittest.main()
