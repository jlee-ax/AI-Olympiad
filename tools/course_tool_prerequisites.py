"""Trace registered Python tools in a student's routed notebooks without executing them."""
import ast
from dataclasses import dataclass
from fnmatch import fnmatchcase
import json
import re
import sys


@dataclass(frozen=True)
class Symbol:
    path: str


@dataclass(frozen=True)
class Dependency:
    topic: str
    api: str
    cell: str


@dataclass(frozen=True)
class Function:
    node: ast.AST
    cell: str


def values(items):
    return set().union(*items)


def dependencies(items):
    return {v for v in items if isinstance(v, Dependency)}


def matches(path, module):
    return path == module or path.startswith(module + ".")


class Reader:
    """Each full notebook and its compulsory route start with a fresh name table."""

    def __init__(self, rules, tiers):
        self.rules = rules
        self.tiers = tiers
        self.findings = set()
        self.cell = None
        self.line = 1
        self.active = set()
        self.returns = set()

    def note(self, topic, api, kind, origin=None):
        self.findings.add((self.cell, topic, api, kind, self.tiers[self.cell],
                           self.line, origin or self.cell))

    def dynamic(self, name):
        for rule in self.rules:
            if not rule["available"]:
                self.note(rule["topic"], name, "unresolved")

    def rule_use(self, api):
        result = set()
        for rule in self.rules:
            if not any(matches(api, mod) for mod in rule["modules"]):
                continue
            if any(fnmatchcase(api, pattern) for pattern in rule["data_only"]):
                self.note(rule["topic"], api, "data_only")
            elif rule["available"]:
                self.note(rule["topic"], api, "scheduled")
            else:
                result.add(Dependency(rule["topic"], api, self.cell))
        return result

    def mark(self, result):
        for dep in dependencies(result):
            self.note(dep.topic, dep.api, "use", dep.cell)

    def expr(self, node, env):
        if node is None:
            return set()
        if isinstance(node, ast.Name):
            return env.get(node.id, set())
        if isinstance(node, ast.Attribute):
            return {Symbol(v.path + "." + node.attr) if isinstance(v, Symbol) else v
                    for v in self.expr(node.value, env)}
        if isinstance(node, ast.NamedExpr):
            result = self.expr(node.value, env)
            self.bind(node.target, result, env)
            return result
        if not isinstance(node, ast.Call):
            return values(self.expr(child, env) for child in ast.iter_child_nodes(node))
        targets = self.expr(node.func, env)
        positional = [self.expr(arg, env) for arg in node.args]
        keywords = {arg.arg: self.expr(arg.value, env) for arg in node.keywords}
        args = values([*positional, *keywords.values()])
        result = dependencies(targets | args)
        if isinstance(node.func, ast.Name) and node.func.id not in env:
            if node.func.id in {"__import__", "getattr", "eval", "exec"}:
                targets = {Symbol("builtins." + node.func.id)}
        for target in targets:
            if isinstance(target, Function):
                result.update(self.call_function(target, positional, keywords, env))
            elif isinstance(target, Symbol):
                if target.path in {"builtins.__import__", "importlib.import_module"}:
                    if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                        result.add(Symbol(node.args[0].value))
                    else:
                        self.dynamic(target.path)
                elif target.path == "builtins.getattr" and len(node.args) >= 2:
                    name = node.args[1]
                    modules = [v for v in positional[0] if isinstance(v, Symbol)]
                    if isinstance(name, ast.Constant) and isinstance(name.value, str):
                        result.update(Symbol(v.path + "." + name.value) for v in modules)
                    elif modules:
                        self.dynamic("getattr with a computed name")
                elif target.path in {"builtins.eval", "builtins.exec"}:
                    self.dynamic(target.path)
                else:
                    result.update(self.rule_use(target.path))
        self.mark(result)
        return result

    def call_function(self, fun, positional, keywords, caller):
        node = fun.node
        if fun in self.active:
            return dependencies(values([*positional, *keywords.values()]))
        local = caller.copy()
        params = [arg.arg for arg in node.args.posonlyargs + node.args.args]
        for name in params + [arg.arg for arg in node.args.kwonlyargs]:
            local[name] = set()
        for name, value in zip(params, positional):
            local[name] = value
        local.update({k: v for k, v in keywords.items() if k is not None})
        if node.args.vararg:
            local[node.args.vararg.arg] = values(positional[len(params):])
        if node.args.kwarg:
            local[node.args.kwarg.arg] = values(keywords.values())
        self.active.add(fun)
        previous = self.returns
        self.returns = set()
        # Attribute the dependency to the learner cell that invokes this helper.
        for statement in node.body:
            self.statement(statement, local, in_call=True)
        result = self.returns
        self.returns = previous
        self.active.remove(fun)
        return result

    @staticmethod
    def bind(target, result, env):
        if isinstance(target, ast.Name):
            env[target.id] = result
        elif isinstance(target, (ast.Tuple, ast.List)):
            for item in target.elts:
                Reader.bind(item, result, env)
        elif isinstance(target, (ast.Attribute, ast.Subscript)):
            base = target.value
            while isinstance(base, (ast.Attribute, ast.Subscript)):
                base = base.value
            if isinstance(base, ast.Name):
                env[base.id] = env.get(base.id, set()) | dependencies(result)

    def statement(self, node, env, in_call=False):
        if not in_call:
            self.line = node.lineno
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                if alias.name == "*":
                    self.dynamic("wildcard import from " + str(node.module))
                    continue
                if isinstance(node, ast.Import):
                    name = alias.asname or alias.name.split(".")[0]
                    path = alias.name if alias.asname else name
                else:
                    name = alias.asname or alias.name
                    path = ".".join(filter(None, (node.module, alias.name)))
                env[name] = {Symbol(path)}
            return
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            env[node.name] = {Function(node, self.cell)}
            for default in [*node.args.defaults, *node.args.kw_defaults, *node.decorator_list]:
                self.mark(self.expr(default, env))
            return
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            result = self.expr(node.value, env)
            self.mark(result)
            for target in node.targets if isinstance(node, ast.Assign) else [node.target]:
                if isinstance(node, ast.AugAssign):
                    result |= self.expr(target, env)
                self.bind(target, result, env)
            return
        if isinstance(node, ast.Return):
            result = self.expr(node.value, env)
            self.mark(result)
            self.returns.update(result)
            return
        if isinstance(node, ast.If):
            self.mark(self.expr(node.test, env))
            branches = []
            for statements in [node.body, node.orelse]:
                branch = env.copy()
                for statement in statements:
                    self.statement(statement, branch, in_call)
                branches.append(branch)
            for name in branches[0].keys() | branches[1].keys():
                env[name] = branches[0].get(name, set()) | branches[1].get(name, set())
            return
        if isinstance(node, (ast.For, ast.AsyncFor)):
            self.bind(node.target, self.expr(node.iter, env), env)
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.stmt):
                self.statement(child, env, in_call)
            else:
                self.mark(self.expr(child, env))

    def scan(self, entries):
        env = {}
        for self.cell, source in entries:
            try:
                tree = ast.parse(source)
            except (SyntaxError, ValueError) as error:
                self.line = getattr(error, "lineno", None) or 1
                self.dynamic("unparsed notebook cell")
                continue
            for statement in tree.body:
                self.statement(statement, env)

    def prose(self, ref, source):
        self.cell = ref
        for number, line in enumerate(source.splitlines(), 1):
            self.line = number
            # A documentation URL is not an instruction to use its API.
            visible = re.sub(r"https?://[^\s)>]+", "", line)
            for rule in self.rules:
                if rule["available"]:
                    continue
                for name in rule["mentions"]:
                    if re.search(r"(?<![A-Za-z_0-9])" + re.escape(name) + r"(?![A-Za-z_0-9])", visible):
                        self.note(rule["topic"], name, "mention")


def inspect(packet):
    rules, route = packet["rules"], packet["route"]
    tiers = {ref: unit["tier"] for unit in route["units"] for ref in unit["cells"]}
    provided = {entry["cell"]: entry["alternative"] for entry in route.get("provided_examples", [])}
    reader = Reader(rules, tiers)
    for book, notebook in packet["notebooks"].items():
        code = {}
        for entry in notebook["cells"]:
            ref = book + "/" + entry["id"]
            if ref not in tiers:
                raise ValueError("Student cell is absent from the route: " + ref)
            source = "".join(entry["source"])
            if entry["cell_type"] == "code":
                code[ref] = source
            elif entry["cell_type"] == "markdown":
                reader.prose(ref, source)
        # A full Run All, the planned order, and a student skipping all optional units
        # can expose different bindings. Keep the file's kernel separate from every other book.
        orders = [tuple(code), tuple(ref for ref in tiers if ref in code),
                  tuple(ref for ref, tier in tiers.items() if tier != "conditional" and ref in code)]
        for order in dict.fromkeys(orders):
            reader.scan((ref, code[ref]) for ref in order)

    findings, blocked, review_cells = [], [], set()
    for cell, topic, api, kind, tier, line, origin in sorted(reader.findings):
        if kind == "use":
            if tier == "conditional":
                kind = "conditional"
            elif cell in provided and cell == origin:
                kind = "provided"
                review_cells.update((cell, provided[cell]))
            else:
                kind = "premature"
        item = dict(cell=cell, topic=topic, api=api, kind=kind, tier=tier, line=line, origin=origin)
        findings.append(item)
        if kind == "premature":
            blocked.append(item)
        if tier != "conditional" and kind in {"mention", "unresolved"}:
            review_cells.add(cell)
    return {"findings": findings, "blocked": blocked, "review_cells": sorted(review_cells)}


if __name__ == "__main__":
    print(json.dumps(inspect(json.load(sys.stdin)), ensure_ascii=False))
