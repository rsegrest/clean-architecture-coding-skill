#!/usr/bin/env python3
"""Check Clean Architecture dependency direction in TS/JS and Python sources.

Usage:
  check_boundaries.py <src-dir> [--layers domain=domain,entities usecases=application ...]
                      [--strict] [--quiet]

A file's layer is the first path segment (relative to <src-dir>) matching a layer
alias. Imports from an inner layer to an outer layer are violations. Inner layers
(domain, usecases) importing known frameworks/I-O libraries are violations too.
Direct I/O globals (fetch, localStorage, os.environ, ...) in inner layers are
warnings (errors with --strict).

Exit code: 0 = clean, 1 = violations, 2 = usage error.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

RANK = {"domain": 0, "usecases": 1, "adapters": 2, "ui": 3}
DEFAULT_LAYERS = {
    "domain": ["domain", "entities", "core"],
    "usecases": ["application", "usecases", "use_cases", "useCases", "use-cases", "services_app"],
    "adapters": ["adapters", "adapter", "infrastructure", "infrastructures", "repositories",
                 "presenters", "gateways", "data"],
    "ui": ["ui", "presentation", "components", "pages", "app_ui", "web", "mobile",
           "entrypoints", "api", "cli", "views", "routes", "hooks", "di"],
}
TS_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}
PY_EXT = {".py"}
SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", "__pycache__", ".venv",
             "venv", "coverage", ".turbo"}

FRAMEWORKS_TS = {"react", "react-dom", "react-native", "next", "axios", "recoil", "zustand",
                 "redux", "@reduxjs/toolkit", "@tanstack/react-query", "swr",
                 "styled-components", "@emotion/react", "vue", "svelte", "@angular/core",
                 "express", "prisma", "@prisma/client", "mongoose", "pg", "firebase"}
FRAMEWORKS_PY = {"sqlalchemy", "django", "fastapi", "flask", "pydantic", "requests", "httpx",
                 "aiohttp", "boto3", "starlette", "psycopg", "psycopg2", "pymongo", "redis",
                 "celery", "typer", "click"}
IO_TS = re.compile(r"\b(fetch\s*\(|localStorage|sessionStorage|window\.|document\.|"
                   r"process\.env|import\.meta\.env)")
IO_PY = re.compile(r"\b(os\.environ|os\.getenv|open\s*\(|print\s*\()")

TS_IMPORT = re.compile(
    r"""(?:import\s+(?:type\s+)?(?:[\w*{}\s,$]+\s+from\s+)?|export\s+[\w*{}\s,$]*\s+from\s+|"""
    r"""require\s*\(\s*|import\s*\(\s*)['"]([^'"]+)['"]""")
PY_IMPORT = re.compile(r"^\s*(?:from\s+(\.*[\w.]*)\s+import|import\s+([\w.]+))", re.M)


def build_alias_map(specs: list[str] | None) -> dict[str, str]:
    layers = DEFAULT_LAYERS
    if specs:
        layers = {}
        for spec in specs:
            key, _, vals = spec.partition("=")
            if key not in RANK or not vals:
                sys.exit(f"bad --layers spec {spec!r}; keys: {', '.join(RANK)}")
            layers[key] = vals.split(",")
    return {alias: layer for layer, aliases in layers.items() for alias in aliases}


def layer_of(parts, aliases):
    for p in parts:
        if p in aliases:
            return aliases[p]
    return None


def strip_comments_ts(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"(^|[^:])//.*", r"\1", text)


def ts_target_parts(spec, file, root):
    if spec.startswith("."):
        target = (file.parent / spec).resolve()
        try:
            return target.relative_to(root).parts, False
        except ValueError:
            return None, False
    for prefix in ("@/", "~/", "src/", "#/"):
        if spec.startswith(prefix):
            return tuple(spec[len(prefix):].split("/")), False
    if spec.startswith("@") and "/" in spec:
        scope = spec[1:].split("/")[0]
        return (scope, *spec.split("/")[1:]), True  # e.g. @domain/x; also packages
    return None, True


def py_target_parts(mod, file, root, local_pkgs):
    if mod.startswith("."):
        dots = len(mod) - len(mod.lstrip("."))
        base = file.parent
        for _ in range(dots - 1):
            base = base.parent
        rest = [p for p in mod.lstrip(".").split(".") if p]
        try:
            return (*base.resolve().relative_to(root).parts, *rest)
        except ValueError:
            return None
    parts = mod.split(".")
    if parts[0] in local_pkgs:
        return tuple(parts)
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src")
    ap.add_argument("--layers", nargs="+")
    ap.add_argument("--strict", action="store_true", help="treat I/O warnings as errors")
    ap.add_argument("--quiet", action="store_true", help="hide warnings")
    args = ap.parse_args()

    root = Path(args.src).resolve()
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2
    aliases = build_alias_map(args.layers)
    local_pkgs = {p.name for p in root.iterdir() if p.is_dir() or p.suffix == ".py"}
    local_pkgs = {n.removesuffix(".py") for n in local_pkgs} | {root.name}

    errors, warnings, scanned, layered = [], [], 0, 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            f = Path(dirpath) / name
            ext = f.suffix
            if ext not in TS_EXT | PY_EXT or name.endswith(".d.ts"):
                continue
            rel = f.relative_to(root)
            if re.search(r"(\.test\.|\.spec\.|^test_|_test\.py$)", name) or "tests" in rel.parts \
                    or "__tests__" in rel.parts:
                continue
            scanned += 1
            src_layer = layer_of(rel.parts[:-1], aliases)
            if src_layer is None:
                continue
            layered += 1
            text = f.read_text(errors="ignore")
            is_py = ext in PY_EXT
            inner = RANK[src_layer] <= RANK["usecases"]

            if is_py:
                imports = [(m.group(1) or m.group(2)) for m in PY_IMPORT.finditer(text)]
            else:
                imports = TS_IMPORT.findall(strip_comments_ts(text))

            for spec in imports:
                if is_py:
                    tparts = py_target_parts(spec, f, root, local_pkgs)
                    pkg = spec.split(".")[0]
                    external = tparts is None
                else:
                    tparts, external = ts_target_parts(spec, f, root)
                    pkg = "/".join(spec.split("/")[:2]) if spec.startswith("@") else spec.split("/")[0]
                if tparts:
                    tlayer = layer_of(tparts[:-1] if not external else tparts[:1], aliases) \
                        or layer_of(tparts, aliases)
                    if tlayer and RANK[tlayer] > RANK[src_layer]:
                        errors.append(f"{rel}: {src_layer} -> {tlayer}  ({spec})")
                        continue
                if inner and external and pkg in (FRAMEWORKS_PY if is_py else FRAMEWORKS_TS):
                    errors.append(f"{rel}: {src_layer} imports framework/I-O lib '{pkg}'")

            if inner:
                io = IO_PY if is_py else IO_TS
                for lineno, line in enumerate(text.splitlines(), 1):
                    m = io.search(line)
                    if m and not line.lstrip().startswith(("#", "//", "*")):
                        warnings.append(f"{rel}:{lineno}: {src_layer} uses I/O '{m.group(1).strip()}'")

    if args.strict:
        errors += warnings
        warnings = []
    for e in errors:
        print(f"ERROR   {e}")
    if not args.quiet:
        for w in warnings:
            print(f"WARN    {w}")
    print(f"\nscanned {scanned} files ({layered} in recognized layers): "
          f"{len(errors)} error(s), {len(warnings)} warning(s)")
    if layered == 0:
        print("no files matched any layer folder; pass --layers to map your folder names")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
