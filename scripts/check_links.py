#!/usr/bin/env python3
"""Check that relative links in the documentation resolve to tracked files.

Covers README.md, docs/*.md and results/comparison/COMPARISON.md: Markdown
links and images, reference definitions, and HTML href/src attributes.
External URLs and in-page anchors are skipped. A link to a directory passes
if git tracks at least one file under it.

Run from anywhere:  python3 scripts/check_links.py
"""

import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
DOCS = ["README.md", *sorted(str(p.relative_to(ROOT)) for p in (ROOT / "docs").glob("*.md")),
        "results/comparison/COMPARISON.md"]

LINK_PATTERNS = [
    re.compile(r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)"),  # [text](target)
    re.compile(r"^\s*\[[^\]]+\]:\s*<?(\S+?)>?(?:\s|$)", re.MULTILINE),     # [ref]: target
    re.compile(r"\b(?:href|src)\s*=\s*[\"']([^\"']+)[\"']", re.IGNORECASE),  # <img src>, <a href>
]
FENCE = re.compile(r"^(```|~~~).*?^\1", re.MULTILINE | re.DOTALL)
INLINE_CODE = re.compile(r"`[^`\n]*`")

tracked = set(subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, check=True,
                             capture_output=True, text=True).stdout.split("\0")) - {""}
tracked_dirs = {str(p) for f in tracked for p in Path(f).parents}


def is_external(target):
    return target.startswith("#") or re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE)


broken, count = [], 0
for doc in DOCS:
    text = (ROOT / doc).read_text(encoding="utf-8")
    # blank out code, keeping newlines so match offsets give line numbers
    for code in (FENCE, INLINE_CODE):
        text = code.sub(lambda c: re.sub(r"[^\n]", " ", c.group(0)), text)
    for pattern in LINK_PATTERNS:
        for m in pattern.finditer(text):
            target = m.group(1)
            if is_external(target):
                continue
            count += 1
            path = unquote(target.split("#", 1)[0].split("?", 1)[0])
            resolved = (ROOT / doc).parent / path
            try:
                rel = resolved.resolve().relative_to(ROOT).as_posix()
            except ValueError:
                broken.append((doc, target, "points outside the repository"))
                continue
            if rel not in tracked and rel not in tracked_dirs:
                line = text.count("\n", 0, m.start()) + 1
                broken.append((f"{doc}:{line}", target, f"{rel} is not a tracked file"))

for where, target, why in broken:
    print(f"BROKEN  {where}  {target}  ({why})")
print(f"{count} relative links checked in {len(DOCS)} files, {len(broken)} broken")
sys.exit(1 if broken else 0)
