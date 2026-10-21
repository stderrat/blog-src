#!/usr/bin/env python3
"""Build a Font Awesome subset (woff2 + slim CSS) for YAUB.

Reads icon names from themes/yaub/fa-icons-used.txt (one fa-* name per line),
extracts codepoints from the full FA CSS, subsets solid/regular/brands fonts,
and writes:
  themes/yaub/static/webfonts/subset/*.woff2
  themes/yaub/static/css/fontawesome-subset.min.css

Originals under webfonts/ and css/fontawesome-all.min.css are never modified.
Rollback: set params.useFontAwesomeSubset = false in config.toml
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "themes" / "yaub" / "static"
CSS_FULL = THEME / "css" / "fontawesome-all.min.css"
ICONS_FILE = ROOT / "themes" / "yaub" / "fa-icons-used.txt"
OUT_DIR = THEME / "webfonts" / "subset"
OUT_CSS = THEME / "css" / "fontawesome-subset.min.css"

# Icon class -> which font family (override heuristics)
BRANDS = {"github", "java", "microsoft", "redhat", "opensuse"}
REGULAR = {"clock", "calendar-alt", "calendar"}  # far uses these in theme


def load_icons() -> list[str]:
    names = []
    for line in ICONS_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name = line.removeprefix("fa-")
        if name in {"fw", "lg", "spin", "brands", "solid", "regular"}:
            continue
        names.append(name)
    return sorted(set(names))


def parse_icon_codepoints(css: str) -> dict[str, str]:
    """Map icon name -> unicode hex (without \\), e.g. search -> f002."""
    # .fa-search:before{content:"\f002"} or multi-selectors
    pat = re.compile(
        r"\.fa-([a-z0-9-]+):before(?:\s*,\s*\.fa-[a-z0-9-]+:before)*"
        r'\{content:"\\([0-9a-fA-F]+)"\}'
    )
    # Also handle groups: .fa-a:before,.fa-b:before{content:"\xxxx"}
    pat_group = re.compile(
        r"((?:\.fa-[a-z0-9-]+:before\s*,\s*)*\.fa-[a-z0-9-]+:before)"
        r'\{content:"\\([0-9a-fA-F]+)"\}'
    )
    mapping: dict[str, str] = {}
    for m in pat_group.finditer(css):
        selectors, code = m.group(1), m.group(2).lower()
        for name in re.findall(r"\.fa-([a-z0-9-]+):before", selectors):
            mapping[name] = code
    return mapping


def subset_font(src: Path, dst: Path, unicodes: set[int]) -> None:
    font = TTFont(src)
    options = Options()
    options.flavor = "woff2"
    options.with_zopfli = False
    options.desubroutinize = True
    options.layout_closure = True
    subsetter = Subsetter(options=options)
    # Keep space + a few ASCII in case of measurement quirks
    unicodes = set(unicodes) | {0x20}
    subsetter.populate(unicodes=unicodes)
    subsetter.subset(font)
    dst.parent.mkdir(parents=True, exist_ok=True)
    font.flavor = "woff2"
    font.save(dst)
    font.close()


def main() -> int:
    if not CSS_FULL.is_file():
        print(f"missing {CSS_FULL}", file=sys.stderr)
        return 1
    css = CSS_FULL.read_text(encoding="utf-8", errors="replace")
    mapping = parse_icon_codepoints(css)
    icons = load_icons()

    missing = [n for n in icons if n not in mapping]
    if missing:
        print("WARNING: icons not found in FA CSS (skipped):", ", ".join(missing))

    solid_u: set[int] = set()
    regular_u: set[int] = set()
    brands_u: set[int] = set()
    used_rules: list[tuple[str, str]] = []

    for name in icons:
        if name not in mapping:
            continue
        code = mapping[name]
        cp = int(code, 16)
        if name in BRANDS:
            brands_u.add(cp)
        elif name in REGULAR:
            # also include in solid — theme mixes fas/far for calendar/clock
            regular_u.add(cp)
            solid_u.add(cp)
        else:
            solid_u.add(cp)
        used_rules.append((name, code))

    # v4-style bare .fa often uses solid glyphs
    print(
        f"subset: {len(used_rules)} icons | "
        f"solid={len(solid_u)} regular={len(regular_u)} brands={len(brands_u)}"
    )

    sources = {
        "fa-solid-900": (THEME / "webfonts" / "fa-solid-900.ttf", solid_u),
        "fa-regular-400": (THEME / "webfonts" / "fa-regular-400.ttf", regular_u),
        "fa-brands-400": (THEME / "webfonts" / "fa-brands-400.ttf", brands_u),
    }
    for key, (src, unicodes) in sources.items():
        if not unicodes:
            print(f"skip empty {key}")
            continue
        if not src.is_file():
            print(f"missing {src}", file=sys.stderr)
            return 1
        dst = OUT_DIR / f"{key}.woff2"
        subset_font(src, dst, unicodes)
        print(f"  {dst.relative_to(ROOT)}  {dst.stat().st_size // 1024}kB")

    # Slim CSS: base + used :before rules + @font-face → subset/
    base = (
        '.fa,.fa-brands,.fa-classic,.fa-regular,.fa-solid,.fab,.far,.fas'
        '{-moz-osx-font-smoothing:grayscale;-webkit-font-smoothing:antialiased;'
        'display:var(--fa-display,inline-block);font-style:normal;font-variant:normal;'
        'line-height:1;text-rendering:auto}'
        '.fa,.fa-classic,.fa-regular,.fa-solid,.far,.fas'
        '{font-family:var(--fa-style-family,"Font Awesome 6 Free");'
        'font-weight:var(--fa-style,900)}'
        '.fa-brands,.fab{font-family:"Font Awesome 6 Brands";font-weight:400}'
        '.fa-solid,.fas{font-weight:900}.fa-regular,.far{font-weight:400}'
        '.fa-fw{text-align:center;width:1.25em}'
        '.fa-lg{font-size:1.25em;line-height:.05em;vertical-align:-.075em}'
        '.fa-spin{-webkit-animation:fa-spin 2s linear infinite;animation:fa-spin 2s linear infinite}'
        '@-webkit-keyframes fa-spin{0%{-webkit-transform:rotate(0);transform:rotate(0)}'
        '100%{-webkit-transform:rotate(360deg);transform:rotate(360deg)}}'
        '@keyframes fa-spin{0%{transform:rotate(0)}100%{transform:rotate(360deg)}}'
    )
    faces = (
        '@font-face{font-family:"Font Awesome 6 Free";font-style:normal;font-weight:900;'
        'font-display:swap;src:url(../webfonts/subset/fa-solid-900.woff2) format("woff2")}'
        '@font-face{font-family:"Font Awesome 6 Free";font-style:normal;font-weight:400;'
        'font-display:swap;src:url(../webfonts/subset/fa-regular-400.woff2) format("woff2")}'
        '@font-face{font-family:"Font Awesome 6 Brands";font-style:normal;font-weight:400;'
        'font-display:swap;src:url(../webfonts/subset/fa-brands-400.woff2) format("woff2")}'
        # FA5 / v4 family names used by some markup
        '@font-face{font-family:"Font Awesome 5 Free";font-style:normal;font-weight:900;'
        'font-display:swap;src:url(../webfonts/subset/fa-solid-900.woff2) format("woff2")}'
        '@font-face{font-family:"Font Awesome 5 Free";font-style:normal;font-weight:400;'
        'font-display:swap;src:url(../webfonts/subset/fa-regular-400.woff2) format("woff2")}'
        '@font-face{font-family:"Font Awesome 5 Brands";font-style:normal;font-weight:400;'
        'font-display:swap;src:url(../webfonts/subset/fa-brands-400.woff2) format("woff2")}'
        '@font-face{font-family:"FontAwesome";font-style:normal;font-weight:900;'
        'font-display:swap;src:url(../webfonts/subset/fa-solid-900.woff2) format("woff2")}'
    )
    rules = "".join(f'.fa-{n}:before{{content:"\\{c}"}}' for n, c in used_rules)
    OUT_CSS.write_text(base + faces + rules + "\n", encoding="utf-8")
    print(f"  {OUT_CSS.relative_to(ROOT)}  {OUT_CSS.stat().st_size // 1024}kB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
