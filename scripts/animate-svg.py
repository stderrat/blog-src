#!/usr/bin/env python3
"""
animate-svg.py - turn an Inkscape SVG into an animated diagram for the
{{< animated-svg >}} shortcode (YAUB theme).

The choreography lives in a small YAML file next to the SVG source:

    source: prerequisites-objects.svg          # relative to this YAML file
    output: ../prerequisites-objects-animated.svg
    standalone: ../prerequisites-objects-animated-standalone.svg   # optional
    stages:                                    # optional: blocks fade/slide in
                                               # (omit -> blocks always visible)
      - at: 0.3                                # seconds after start
        ids: [rect4, text4, text5]             # Inkscape element IDs
    dots:                                      # optional: dots flowing along arrows
      - along: path36                          # follow this path's "d"
        at: 4.6                                # first appearance (s)
        dur: 2.4                               # one trip (s), loops
        color: "#0F766E"
        below: rect36                          # draw underneath this element

"output" is for the shortcode: no <style> inside, timing comes from the theme
CSS/JS (starts on scroll-in, reduced-motion aware).
"standalone" (optional) embeds its own CSS + SMIL timing, so it animates on
its own when used via image:: / <img>, on GitHub, in slides, etc.

Usage:  python3 scripts/animate-svg.py path/to/diagram.anim.yaml [...]
Requires PyYAML (pip install pyyaml).
"""
import os
import re
import sys

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required: pip install pyyaml")

STANDALONE_CSS = """
@keyframes asvg-reveal { from { opacity:0; translate:0 8px } to { opacity:1; translate:0 0 } }
@keyframes asvg-fade { from { opacity:0 } to { opacity:1 } }
.rv { animation: asvg-reveal .45s cubic-bezier(.2,.8,.3,1.1) both; animation-delay: var(--d,0s); }
.flow-dot { visibility: visible; animation: asvg-fade .3s both; animation-delay: var(--d,0s); }
@media (prefers-reduced-motion: reduce) { .rv { animation: none } .flow-dot { display: none } }
"""


def tag_span(svg, el_id):
    """Return (start, end) of the start tag carrying id="el_id"."""
    m = re.search(r'<[A-Za-z][^<>]*?\bid="%s"[^<>]*?>' % re.escape(el_id), svg)
    if not m:
        raise KeyError(el_id)
    return m.start(), m.end()


def set_attrs(tag, cls=None, delay=None):
    if cls:
        if re.search(r'\sclass="', tag):
            tag = re.sub(r'(\sclass=")([^"]*)"', lambda m: '%s%s %s"' % (m.group(1), m.group(2), cls) if cls not in m.group(2).split() else m.group(0), tag, count=1)
        else:
            tag = re.sub(r'^(<[A-Za-z:]+)', r'\1 class="%s"' % cls, tag, count=1)
    if delay is not None:
        d = '--d:%.2fs' % delay
        if re.search(r'\sstyle="', tag):
            tag = re.sub(r'(\sstyle=")([^"]*)"', lambda m: '%s%s;%s"' % (m.group(1), re.sub(r'--d:[^;"]*;?', '', m.group(2)).rstrip(';'), d) if m.group(2) else '%s%s"' % (m.group(1), d), tag, count=1)
        else:
            tag = re.sub(r'^(<[A-Za-z:]+)', r'\1 style="%s"' % d, tag, count=1)
    return tag


def path_d(svg, el_id):
    s, e = tag_span(svg, el_id)
    m = re.search(r'\sd="([^"]+)"', svg[s:e])
    if not m:
        raise KeyError('%s has no d attribute' % el_id)
    return m.group(1)


def build(cfg, base, standalone):
    svg = open(os.path.join(base, cfg['source']), encoding='utf-8').read()
    svg = re.sub(r'<style id="asvg-style">.*?</style>\s*', '', svg, flags=re.S)

    seen = set()
    for stage in cfg.get('stages', []):
        for el_id in stage['ids']:
            if el_id in seen:
                sys.exit('ID used in more than one stage: %s' % el_id)
            seen.add(el_id)
            try:
                s, e = tag_span(svg, el_id)
            except KeyError:
                sys.exit('ID not found in SVG: %s' % el_id)
            svg = svg[:s] + set_attrs(svg[s:e], 'rv', float(stage['at'])) + svg[e:]

    for dot in cfg.get('dots', []):
        try:
            d = path_d(svg, dot['along'])
        except KeyError as err:
            sys.exit('Dot path problem: %s' % err)
        at, dur = float(dot.get('at', 0)), float(dot.get('dur', 2))
        begin = '%.2fs' % at if standalone else 'indefinite'
        circle = ('<circle class="flow-dot" style="--d:%.2fs" visibility="hidden" r="%s" fill="%s" '
                  'stroke="#FFFFFF" stroke-width="1.5"><animateMotion path="%s" begin="%s" '
                  'data-begin="%.2f" dur="%.2fs" repeatCount="indefinite" calcMode="linear"/></circle>\n  '
                  % (at, dot.get('radius', 4.5), dot.get('color', '#0F766E'), d, begin, at, dur))
        if dot.get('below'):
            try:
                s, _ = tag_span(svg, dot['below'])
            except KeyError:
                sys.exit('"below" ID not found in SVG: %s' % dot['below'])
            svg = svg[:s] + circle + svg[s:]
        else:
            svg = svg.replace('</svg>', circle + '</svg>', 1)

    if standalone:
        style = '<style id="asvg-style">%s</style>\n' % STANDALONE_CSS
        if '</defs>' in svg:
            svg = svg.replace('</defs>', '</defs>\n' + style, 1)
        else:
            svg = re.sub(r'(<svg\b[^>]*>)', r'\1\n' + style, svg, count=1)

    total = len(re.findall(r'<(?:rect|text|path|circle|ellipse|line|polyline|polygon|g|use|image)\b', svg))
    return svg, len(seen), total


def main(paths):
    if not paths:
        sys.exit(__doc__)
    for p in paths:
        base = os.path.dirname(os.path.abspath(p))
        cfg = yaml.safe_load(open(p, encoding='utf-8'))
        for key, standalone in (('output', False), ('standalone', True)):
            if not cfg.get(key):
                continue
            svg, animated, total = build(cfg, base, standalone)
            out = os.path.normpath(os.path.join(base, cfg[key]))
            open(out, 'w', encoding='utf-8').write(svg)
            print('%s -> %s (%d animated elements, %s)' % (p, out, animated, 'standalone' if standalone else 'shortcode'))


if __name__ == '__main__':
    main(sys.argv[1:])
