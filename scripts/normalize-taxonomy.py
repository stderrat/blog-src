#!/usr/bin/env python3
"""
normalize-taxonomy.py - consolidate categories in the front matter of all
content files according to taxonomy-map.yaml.

- Works on YAML front matter (--- ... ---) in .adoc and .md files.
- Uses ruamel.yaml in round-trip mode, so comments, key order and quoting
  of the front matter are preserved.
- A category that is mapped away is added as a tag (if not present yet),
  so the tag pages keep working.
- Default is a dry run that prints a unified diff. Nothing is written
  unless --apply is given.

Requirements:
    pip install ruamel.yaml

Usage:
    ./normalize-taxonomy.py --content ../content                # dry run, shows diff
    ./normalize-taxonomy.py --content ../content --apply        # write changes
    ./normalize-taxonomy.py --content ../content --report       # category usage before/after
"""
import argparse
import collections
import difflib
import io
import pathlib
import re
import sys

try:
    from ruamel.yaml import YAML
    from ruamel.yaml.scalarstring import DoubleQuotedScalarString as DQ
except ImportError:
    sys.exit("ruamel.yaml is missing: pip install ruamel.yaml")

FM_DELIM = "---"


def split_front_matter(text):
    """Return (front_matter, body) or (None, text) if no YAML front matter.

    Accepts the common variants ``---\\n`` and ``--- \\n`` (trailing spaces
    on the opening/closing delimiter), which many AsciiDoc posts use.
    """
    open_m = re.match(r"^---[ \t]*\n", text)
    if not open_m:
        return None, text
    close_m = re.search(r"\n---[ \t]*\n", text[open_m.end() :])
    if not close_m:
        return None, text
    # Include the newline that precedes the closing delimiter in fm (ruamel-friendly).
    fm_end = open_m.end() + close_m.start() + 1
    fm = text[open_m.end() : fm_end]
    body = text[open_m.end() + close_m.end() :]
    return fm, body


def ci_lookup(mapping, value):
    """Case-insensitive lookup; returns (found, target)."""
    for k, v in mapping.items():
        if k.lower() == str(value).lower():
            return True, v
    return False, None


def dedupe(seq):
    seen, out = set(), []
    for item in seq:
        key = str(item).lower()
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def set_seq(data, key, values):
    """Replace the content of a list in the front matter, keeping its style.

    String items are double-quoted so multi-word values (e.g. Secret Management)
    stay valid inside flow-style ``[a, b]`` lists.
    """
    quoted = [DQ(str(v)) if isinstance(v, str) else v for v in values]
    current = data.get(key)
    if isinstance(current, list):
        del current[:]
        current.extend(quoted)
    else:
        data[key] = quoted


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--content", required=True, help="path to the Hugo content directory")
    ap.add_argument("--map", default=str(pathlib.Path(__file__).with_name("taxonomy-map.yaml")))
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    ap.add_argument("--report", action="store_true", help="print category usage before/after")
    args = ap.parse_args()

    yaml = YAML()  # round-trip
    yaml.preserve_quotes = True
    yaml.width = 4096
    yaml.indent(mapping=2, sequence=4, offset=2)  # keeps "  - item" style
    mapping = YAML(typ="safe").load(pathlib.Path(args.map).read_text())["map"]

    before, after = collections.Counter(), collections.Counter()
    changed, skipped = 0, []

    for path in sorted(pathlib.Path(args.content).rglob("*")):
        if path.suffix not in (".adoc", ".md") or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        fm, body = split_front_matter(text)
        if fm is None:
            if text.startswith("+++"):
                skipped.append(f"{path} (TOML front matter)")
            continue
        data = yaml.load(fm)
        if not data or "categories" not in data:
            continue

        cats = data.get("categories") or []
        if isinstance(cats, str):
            cats = [cats]
        tags = list(data.get("tags") or [])
        new_cats = []
        for c in cats:
            before[c] += 1
            found, target = ci_lookup(mapping, c)
            if not found:
                new_cats.append(c)
                continue
            tags.append(c)                 # keep the old value as tag
            if target:
                new_cats.append(target)
        new_cats = dedupe(new_cats)
        tags = dedupe(tags)
        for c in new_cats:
            after[c] += 1

        if [str(c) for c in new_cats] == [str(c) for c in cats] and \
           [str(t) for t in tags] == [str(t) for t in (data.get("tags") or [])]:
            continue

        # modify the existing sequences in place, so ruamel keeps their
        # style (flow "[a, b]" or block "- a") and any comments
        set_seq(data, "categories", new_cats)
        set_seq(data, "tags", tags)

        buf = io.StringIO()
        yaml.dump(data, buf)
        new_text = f"{FM_DELIM}\n{buf.getvalue()}{FM_DELIM}\n{body}"
        changed += 1
        if args.apply:
            path.write_text(new_text, encoding="utf-8")
        else:
            sys.stdout.writelines(difflib.unified_diff(
                text.splitlines(keepends=True), new_text.splitlines(keepends=True),
                fromfile=str(path), tofile=str(path), n=1))

    print(f"\n{'Changed' if args.apply else 'Would change'}: {changed} file(s)", file=sys.stderr)
    for s in skipped:
        print(f"Skipped: {s}", file=sys.stderr)
    if args.report:
        print("\nCategories before:", file=sys.stderr)
        for k, v in before.most_common():
            print(f"  {v:3d}  {k}", file=sys.stderr)
        print("\nCategories after:", file=sys.stderr)
        for k, v in after.most_common():
            print(f"  {v:3d}  {k}", file=sys.stderr)


if __name__ == "__main__":
    main()
