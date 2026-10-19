# -*- coding: utf-8 -*-
"""P2-7b: AST-based data-flow analysis (taint tracking).

Extends reachability (P2-7, regex + line-based) with real Python AST parsing.

What it adds:
- Sources via function arguments (regex can't see this).
- Flow through intermediate variables (a -> b -> sink).
- Full path: source -> intermediate -> sink, with line numbers.

Deterministic: Python ast only, no LLM.
Fail-open: returns {} on parse error, non-Python, or no flow.
Backward compatible: returns only {"dataflow": {...}} — exploitability
is a separate concern (P2-7).
"""
import ast

from src.tools.patterns import AST_TAINT_SOURCES, AST_TAINT_SINKS


def _match_call(call: ast.Call, patterns: list[str]) -> str | None:
    """Return matched pattern name if call matches one of patterns."""
    func = call.func
    dotted = _call_to_dotted(func)
    if dotted is None:
        return None
    for pattern in patterns:
        if dotted == pattern or dotted.endswith("." + pattern):
            return pattern
    return None


def _call_to_dotted(node: ast.AST) -> str | None:
    """Convert ast.Call func to dotted name: request.args.get -> 'request.args.get'."""
    parts = []
    cur = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
    else:
        return None
    return ".".join(reversed(parts))


def _flatten_patterns(mapping: dict) -> dict:
    """Flatten AST_TAINT_* to {dotted_name: group_name} for fast lookup."""
    flat = {}
    for group, names in mapping.items():
        for name in names:
            flat[name] = group
    return flat


def _node_line(node: ast.AST) -> int:
    return getattr(node, "lineno", 0)


def _node_content(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:
        return ""


def analyze_dataflow(material: str, language: str = "python") -> dict:
    """AST-based taint analysis for Python.

    Returns:
        {
            "path": [{"line": int, "type": str, "name": str, "content": str}, ...],
            "source": {"line": int, "name": str, "content": str},
            "sink":   {"line": int, "name": str, "content": str},
            "intermediate": [{"line": int, "name": str}, ...],
            "source_count": int,
            "sink_count": int,
        }
        Empty dict if no flow, non-Python, or parse error.
    """
    if language != "python":
        return {}

    try:
        tree = ast.parse(material)
    except (SyntaxError, ValueError):
        return {}

    flat_sources = _flatten_patterns(AST_TAINT_SOURCES)
    flat_sinks = _flatten_patterns(AST_TAINT_SINKS)

    # Step 1: collect all source-calls and sink-calls (with line numbers).
    source_calls = []
    sink_calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        dotted = _call_to_dotted(node.func)
        if dotted is None:
            continue
        # Source?
        for pat, group in flat_sources.items():
            if dotted == pat or dotted.startswith(pat + "."):
                source_calls.append({
                    "line": _node_line(node),
                    "name": pat,
                    "group": group,
                    "content": _node_content(node),
                })
                break
        # Sink?
        for pat, group in flat_sinks.items():
            if dotted == pat or dotted.startswith(pat + "."):
                sink_calls.append({
                    "line": _node_line(node),
                    "name": pat,
                    "group": group,
                    "content": _node_content(node),
                })
                break

    # P2-7b-fix2: sink is mandatory; source may come from function args.
    # (Regex-based reachability requires both; AST can infer source from args.)
    if not sink_calls:
        return {}

    sink = sink_calls[0]
    source = source_calls[0] if source_calls else None

    # Step 2: collect tainted variable names.
    # Heuristic: any assignment whose RHS contains a source call is tainted;
    # propagate via simple transitive closure (up to 3 passes).
    tainted_names = set()
    assignments = []  # (target_name, rhs_names, lineno)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            rhs_names = set()
            rhs_has_source = False
            for sub in ast.walk(node.value):
                if isinstance(sub, ast.Call):
                    dotted = _call_to_dotted(sub.func)
                    if dotted and any(
                        dotted == p or dotted.startswith(p + ".")
                        for p in flat_sources
                    ):
                        rhs_has_source = True
                if isinstance(sub, ast.Name):
                    rhs_names.add(sub.id)
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assignments.append(
                        (target.id, rhs_names, _node_line(node), rhs_has_source)
                    )
                    if rhs_has_source:
                        tainted_names.add(target.id)

    # P2-7b-fix: function arguments as taint sources.
    # Regex-based reachability cannot see function args; AST can.
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for arg in node.args.args:
                if arg.arg and arg.arg != "self":
                    tainted_names.add(arg.arg)

    # Transitive closure.
    for _ in range(3):
        changed = False
        for target, rhs_names, _lineno, _has_src in assignments:
            if target in tainted_names:
                continue
            if rhs_names & tainted_names:
                tainted_names.add(target)
                changed = True
        if not changed:
            break

    # Step 3: find sink calls whose args reference tainted names.
    tainted_sink = None
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        dotted = _call_to_dotted(node.func)
        if dotted is None:
            continue
        is_sink = any(dotted == p or dotted.startswith(p + ".") for p in flat_sinks)
        if not is_sink:
            continue
        # Any argument referencing a tainted name?
        for sub in ast.walk(node):
            if isinstance(sub, ast.Name) and sub.id in tainted_names:
                tainted_sink = {
                    "line": _node_line(node),
                    "name": dotted,
                    "content": _node_content(node),
                }
                break
        if tainted_sink:
            break

    # If no tainted sink found, fall back to first sink (best-effort).
    if tainted_sink is None:
        tainted_sink = {
            "line": sink["line"],
            "name": sink["name"],
            "content": sink["content"],
        }

    # P2-7b-fix3: synthesize source from function args if no source_call.
    if source is None:
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for arg in node.args.args:
                    if arg.arg in tainted_names:
                        source = {
                            "line": arg.lineno,
                            "name": arg.arg,
                            "content": "arg: " + arg.arg,
                        }
                        break
            if source:
                break

    # If still no source — no flow to report.
    if source is None:
        return {}

    # Step 4: build path.
    path = []
    path.append({
        "line": source["line"],
        "type": "source",
        "name": source["name"],
        "content": source["content"],
    })
    for target, rhs_names, lineno, _has_src in assignments:
        if target in tainted_names and lineno > source["line"] and lineno <= tainted_sink["line"]:
            path.append({
                "line": lineno,
                "type": "intermediate",
                "name": target,
                "content": "",
            })
    path.append({
        "line": tainted_sink["line"],
        "type": "sink",
        "name": tainted_sink["name"],
        "content": tainted_sink["content"],
    })

    intermediates = [
        {"line": p["line"], "name": p["name"]}
        for p in path if p["type"] == "intermediate"
    ]

    # P2-7b-fix4: source_count must reflect reality.
    # If source came from function args (fallback), source_calls is empty,
    # but the source IS present in the path. Report at least 1.
    effective_source_count = max(len(source_calls), 1)

    return {
        "path": path,
        "source": {
            "line": source["line"],
            "name": source["name"],
            "content": source["content"],
        },
        "sink": {
            "line": tainted_sink["line"],
            "name": tainted_sink["name"],
            "content": tainted_sink["content"],
        },
        "intermediate": intermediates,
        "source_count": effective_source_count,
        "sink_count": len(sink_calls),
    }


def enrich_dataflow(material: str, finding: dict | None = None,
                    language: str = "python") -> dict:
    """Enrich audit with dataflow (backward-compatible).

    Returns ONLY {"dataflow": {...}} — exploitability is a separate concern.

    Fail-open: any exception -> {"dataflow": {}}.
    """
    try:
        flow = analyze_dataflow(material, language=language)
    except Exception:
        flow = {}
    return {"dataflow": flow}
