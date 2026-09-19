"""Parse source as data. Never import or execute the inspected project."""
from __future__ import annotations

import ast
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import sys


VERSION = "source-ast-v2"
SUFFIXES = {".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".html"}


def sha(data):
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode("utf-8")).hexdigest()


def empty(language):
    return {"language": language, "symbols": [], "imports": [], "calls": [], "entries": [], "limitations": []}


def python_source(raw):
    tree = ast.parse(raw)
    result = empty("python")

    class Visitor(ast.NodeVisitor):
        scope = []

        def definition(self, node, kind):
            name = ".".join([*self.scope, node.name])
            result["symbols"].append({"name": name, "kind": kind, "line": node.lineno,
                                      "end_line": node.end_lineno, "sha256": sha(ast.dump(node, include_attributes=False))})
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    result["calls"].append({"target": ast.unparse(base), "caller": name, "line": base.lineno, "kind": "inherits"})
            self.scope.append(node.name)
            self.generic_visit(node)
            self.scope.pop()

        def visit_FunctionDef(self, node): self.definition(node, "function")
        def visit_AsyncFunctionDef(self, node): self.definition(node, "async_function")
        def visit_ClassDef(self, node): self.definition(node, "class")

        def visit_Import(self, node):
            for alias in node.names:
                result["imports"].append({"module": alias.name, "name": "", "alias": alias.asname or alias.name,
                                          "line": node.lineno, "scope": ".".join(self.scope), "level": 0})

        def visit_ImportFrom(self, node):
            for alias in node.names:
                result["imports"].append({"module": node.module or "", "name": alias.name, "alias": alias.asname or alias.name,
                                          "line": node.lineno, "scope": ".".join(self.scope), "level": node.level})

        def visit_Call(self, node):
            target = ast.unparse(node.func)
            result["calls"].append({"target": target[:180], "caller": ".".join(self.scope) or "<module>", "line": node.lineno, "kind": "call"})
            if target in {"__import__", "importlib.import_module"}:
                literal = node.args[0].value if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str) else None
                if literal:
                    result["imports"].append({"module": literal, "name": "", "alias": "", "line": node.lineno, "scope": ".".join(self.scope), "level": 0, "dynamic": True})
                else:
                    result["limitations"].append({"line": node.lineno, "reason": "nonliteral_dynamic_import"})
            self.generic_visit(node)

        def visit_If(self, node):
            test = node.test
            if isinstance(test, ast.Compare) and len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq):
                pair = [test.left, test.comparators[0]]
                if any(isinstance(n, ast.Name) and n.id == "__name__" for n in pair) and any(isinstance(n, ast.Constant) and n.value == "__main__" for n in pair):
                    result["entries"].append({"kind": "python_main_guard", "line": node.lineno, "symbol": "__main__"})
            self.generic_visit(node)

    Visitor().visit(tree)
    return result


def js_parser(suffix):
    try:
        from tree_sitter import Language, Parser
    except ImportError:
        local = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "lib/project-map-source"
        if local.is_dir() and str(local) not in sys.path:
            sys.path.insert(0, str(local))
        from tree_sitter import Language, Parser
    if suffix in {".ts", ".tsx"}:
        import tree_sitter_typescript as grammar
        language = grammar.language_tsx() if suffix == ".tsx" else grammar.language_typescript()
    else:
        import tree_sitter_javascript as grammar
        language = grammar.language()
    return Parser(Language(language))


def javascript_source(raw, suffix):
    parser = js_parser(suffix)
    tree = parser.parse(raw)
    result = empty("typescript" if suffix in {".ts", ".tsx"} else "javascript")
    text = lambda n: raw[n.start_byte:n.end_byte].decode("utf-8", errors="replace") if n else ""

    def literal(node):
        if node and node.type == "string":
            value = text(node)
            return value[1:-1] if "\\" not in value else None
        return None

    def walk(node, scope=()):
        line = node.start_point.row + 1
        if node.type == "ERROR" or node.is_missing:
            result["limitations"].append({"line": line, "reason": "syntax_error"})
        name_node = node.child_by_field_name("name")
        definition = node.type in {"function_declaration", "generator_function_declaration", "class_declaration", "abstract_class_declaration", "method_definition", "interface_declaration", "type_alias_declaration"}
        if node.type == "variable_declarator":
            value = node.child_by_field_name("value")
            definition = value is not None and value.type in {"arrow_function", "function_expression", "generator_function", "class"}
        if definition and name_node:
            name = text(name_node)
            scope = (*scope, name)
            result["symbols"].append({"name": ".".join(scope), "kind": node.type, "line": line,
                                      "end_line": node.end_point.row + 1, "sha256": sha(raw[node.start_byte:node.end_byte])})
        if node.type in {"import_statement", "export_statement"}:
            module = literal(node.child_by_field_name("source"))
            if module:
                bindings = []
                def imports(n):
                    if n.type in {"import_specifier", "export_specifier"}:
                        name = text(n.child_by_field_name("name"))
                        bindings.append({"name": name, "alias": text(n.child_by_field_name("alias")) or name})
                    elif n.type == "namespace_import":
                        bindings.append({"name": "*", "alias": text(n.named_children[-1])})
                    elif n.type == "import_clause":
                        for child in n.named_children:
                            if child.type == "identifier": bindings.append({"name": "default", "alias": text(child)})
                    for child in n.named_children: imports(child)
                if node.type == "import_statement": imports(node)
                result["imports"].append({"module": module, "line": line, "bindings": bindings, "scope": ".".join(scope), "kind": node.type})
        if node.type == "call_expression":
            target = text(node.child_by_field_name("function"))
            arguments = node.child_by_field_name("arguments")
            if target in {"require", "import"}:
                module = literal(arguments.named_children[0]) if arguments and arguments.named_children else None
                if module:
                    alias = ""
                    if node.parent and node.parent.type == "variable_declarator":
                        alias = text(node.parent.child_by_field_name("name"))
                    result["imports"].append({"module": module, "line": line, "bindings": [{"name": "*", "alias": alias}] if alias else [], "dynamic": target == "import", "scope": ".".join(scope)})
                else:
                    result["limitations"].append({"line": line, "reason": "nonliteral_dynamic_import"})
            result["calls"].append({"target": target[:180], "caller": ".".join(scope) or "<module>", "line": line, "kind": "call"})
        for child in node.named_children:
            walk(child, scope)

    walk(tree.root_node)
    return result


def html_source(raw):
    result = empty("html/javascript")

    class Scripts(HTMLParser):
        active = False

        def handle_starttag(self, tag, attrs):
            if tag != "script": return
            attrs = dict(attrs)
            self.active = not attrs.get("src") and attrs.get("type", "") in {"", "module", "text/javascript", "application/javascript"}
            if attrs.get("src"):
                result["imports"].append({"module": attrs["src"], "line": self.getpos()[0], "bindings": [], "kind": "html_script"})

        def handle_endtag(self, tag):
            if tag == "script": self.active = False

        def handle_data(self, data):
            if not self.active: return
            parsed = javascript_source(data.encode(), ".js")
            for key in ("symbols", "imports", "calls", "entries", "limitations"):
                for item in parsed[key]:
                    item["line"] += self.getpos()[0] - 1
                    if "end_line" in item: item["end_line"] += self.getpos()[0] - 1
                    result[key].append(item)
    Scripts().feed(raw.decode("utf-8-sig"))
    return result


def parse_source(path, raw):
    suffix = Path(path).suffix.lower()
    try:
        if suffix in {".py", ".pyi"}: result = python_source(raw)
        elif suffix == ".html": result = html_source(raw)
        else: result = javascript_source(raw, suffix)
        if Path(path).name == "__main__.py":
            result["entries"].append({"kind": "python_module_entry", "line": 1, "symbol": "__main__"})
        if any(len(result[k]) > 10000 for k in ("symbols", "calls", "imports")):
            raise ValueError("source_structure_limit")
        return result
    except (SyntaxError, UnicodeError, ValueError, RecursionError, ImportError) as exc:
        result = empty(suffix.lstrip("."))
        result["limitations"] = [{"reason": "parser_unavailable" if isinstance(exc, ImportError) else "parse_failed", "detail": str(exc)[:240]}]
        return result


def symbol_fingerprint(path, symbol):
    raw = Path(path).read_bytes()
    parsed = parse_source(path, raw)
    hits = [s for s in parsed["symbols"] if s["name"] == symbol]
    if len(hits) == 1:
        return {"status": "found", **hits[0]}
    return {"status": "unavailable" if parsed["limitations"] else "missing" if not hits else "ambiguous"}
