"""Read-only: count how often each NMS.py function-hook byte pattern matches in the installed NMS.exe.

Parses the repo's copy of NMS.py's types.py with ast (no import of pymhf or nmspy), pulls every
function_hook / static_function_hook / Pattern string, and counts matches in the exe bytes.
Nothing is written to the game folder; the exe is only opened for reading.
"""

import ast
import json
import re
import sys
import time
from pathlib import Path

TYPES = Path(r"F:\Game Development\Modding\No Mans Sky\nms-settlement-mod\scratch\nmspy_types.py")
EXE = Path(r"X:\SteamLibrary\steamapps\common\No Man's Sky\Binaries\NMS.exe")
OUT = Path(__file__).with_name("pattern-scan.json")

HOOK_NAMES = {"function_hook", "static_function_hook"}


def compile_pattern(text: str) -> re.Pattern:
    parts = []
    for tok in text.split():
        parts.append(b"." if tok in ("?", "??") else re.escape(bytes([int(tok, 16)])))
    return re.compile(b"".join(parts), re.DOTALL)


def collect(tree: ast.AST):
    found = []

    def visit(node, owner):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                visit(child, owner + [child.name])
            elif isinstance(child, ast.FunctionDef):
                for dec in child.decorator_list:
                    if isinstance(dec, ast.Call):
                        fn = dec.func
                        name = fn.id if isinstance(fn, ast.Name) else getattr(fn, "attr", "")
                        if name in HOOK_NAMES and dec.args and isinstance(dec.args[0], ast.Constant):
                            found.append((".".join(owner + [child.name]), dec.args[0].value))
                visit(child, owner)
            elif isinstance(child, ast.AnnAssign):
                # Annotated[..., Pattern("...")] globals
                for sub in ast.walk(child):
                    if (
                        isinstance(sub, ast.Call)
                        and isinstance(sub.func, ast.Name)
                        and sub.func.id == "Pattern"
                        and sub.args
                        and isinstance(sub.args[0], ast.Constant)
                    ):
                        target = child.target.id if isinstance(child.target, ast.Name) else "?"
                        found.append((".".join(owner + [target]) + " (global)", sub.args[0].value))
            else:
                visit(child, owner)

    visit(tree, [])
    return found


def main():
    tree = ast.parse(TYPES.read_text(encoding="utf-8"))
    entries = collect(tree)
    data = EXE.read_bytes()
    print(f"{len(entries)} patterns, exe {len(data)} bytes", file=sys.stderr)
    results = []
    started = time.time()
    for name, pat in entries:
        rx = compile_pattern(pat)
        hits = [m.start() for m in rx.finditer(data)]
        results.append({"name": name, "matches": len(hits), "first_file_offset": hits[0] if hits else None})
    OUT.write_text(json.dumps(results, indent=1), encoding="utf-8")
    total = len(results)
    one = sum(1 for r in results if r["matches"] == 1)
    zero = [r["name"] for r in results if r["matches"] == 0]
    many = [(r["name"], r["matches"]) for r in results if r["matches"] > 1]
    print(f"total {total}, exactly one match {one}, none {len(zero)}, several {len(many)}, {time.time() - started:.0f}s")
    print("NONE:", *zero, sep="\n  ")
    print("SEVERAL:", *many, sep="\n  ")


if __name__ == "__main__":
    main()
