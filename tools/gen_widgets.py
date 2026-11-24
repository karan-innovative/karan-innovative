#!/usr/bin/env python3
"""Regenerate the profile README widgets from live GitHub contribution data.

Writes a dark set to assets/ and a light set to assets/light/. The README picks
between them with <picture media="(prefers-color-scheme: dark)">.
"""
import json, os, sys, datetime, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICONS = json.load(open(os.path.join(ROOT, "tools", "icons.json")))
LOGIN = os.environ.get("PROFILE_LOGIN", "karan-innovative")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

QUERY = """
query($login:String!){
  user(login:$login){
    contributionsCollection{
      contributionCalendar{ totalContributions weeks{ contributionDays{ date contributionCount } } }
      restrictedContributionsCount
    }
  }
}"""


def fetch():
    if not TOKEN:
        sys.exit("GITHUB_TOKEN is not set")
    body = json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=body,
        headers={"Authorization": "bearer " + TOKEN,
                 "Content-Type": "application/json",
                 "User-Agent": "profile-widget-generator"})
    with urllib.request.urlopen(req, timeout=45) as r:
        payload = json.load(r)
    if "errors" in payload:
        sys.exit("GraphQL error: %s" % payload["errors"])
    return payload["data"]["user"]["contributionsCollection"]


CAL = fetch()

# Safety net: these widgets are only meaningful if the token can see private
# contributions. A token that cannot returns a near-empty calendar, which would
# otherwise be committed over good data.
_total = CAL["contributionCalendar"]["totalContributions"]
if _total < 50:
    sys.exit("refusing to write: calendar returned only %d contributions. The token "
             "probably cannot see private contributions -- add a GH_PAT secret with "
             "read:user scope." % _total)

W = 880
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"

THEMES = {
    "dark": dict(
        dir="", INK0="#0B1020", INK1="#161F3A", CARD0="#121A2E", CARD1="#1A2440",
        STROKE="#27324D", TXT="#EAF0FB", MUT="#93A6C4", DIM="#6C809F",
        A1="#6366F1", A2="#22D3EE", A3="#A855F7",
        SHEEN="#FFFFFF", SHEEN_OP="0.07", DOT="#8FA6CC", DOT_OP="0.10",
        SHADOW="#000000", SHADOW_OP="0.45", SHADOW_DY="6", SHADOW_SD="10",
        ORB_A="0.55", ORB_B="0.45", CHIP="#FFFFFF", CHIP_OP="0.045",
        TILE_OP="0.16", PILL_OP="0.06", AREA0="0.42", AREA1="0.16",
        GRID_OP="0.55", GLOW_SD="5", LINE_W="2.6",
    ),
    "light": dict(
        dir="light", INK0="#F7FAFF", INK1="#DEE9FC", CARD0="#FFFFFF", CARD1="#F5F9FE",
        STROKE="#D5DFEF", TXT="#0D1626", MUT="#4D5F7A", DIM="#6B7C96",
        A1="#4F46E5", A2="#0C87AC", A3="#9333EA",
        SHEEN="#1B2A41", SHEEN_OP="0.022", DOT="#2A4066", DOT_OP="0.07",
        SHADOW="#1B2A41", SHADOW_OP="0.13", SHADOW_DY="4", SHADOW_SD="8",
        ORB_A="0.34", ORB_B="0.30", CHIP="#1B2A41", CHIP_OP="0.035",
        TILE_OP="0.14", PILL_OP="0.05", AREA0="0.30", AREA1="0.11",
        GRID_OP="0.9", GLOW_SD="2.5", LINE_W="2.8",
    ),
}

T = THEMES["dark"]
INK0 = INK1 = CARD0 = CARD1 = STROKE = TXT = MUT = DIM = A1 = A2 = A3 = ""
DEFS = ""
A = os.path.join(ROOT, "assets")


def build_defs():
    return f"""
<linearGradient id="ink" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="{INK0}"/><stop offset="1" stop-color="{INK1}"/>
</linearGradient>
<linearGradient id="card" x1="0" y1="0" x2="0.4" y2="1">
  <stop offset="0" stop-color="{CARD1}"/><stop offset="1" stop-color="{CARD0}"/>
</linearGradient>
<linearGradient id="acc" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="{A1}"/><stop offset="0.55" stop-color="{A2}"/><stop offset="1" stop-color="{A3}"/>
</linearGradient>
<linearGradient id="sheen" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="{T['SHEEN']}" stop-opacity="{T['SHEEN_OP']}"/>
  <stop offset="1" stop-color="{T['SHEEN']}" stop-opacity="0"/>
</linearGradient>
<radialGradient id="orbA"><stop offset="0" stop-color="{A1}" stop-opacity="{T['ORB_A']}"/><stop offset="1" stop-color="{A1}" stop-opacity="0"/></radialGradient>
<radialGradient id="orbB"><stop offset="0" stop-color="{A2}" stop-opacity="{T['ORB_B']}"/><stop offset="1" stop-color="{A2}" stop-opacity="0"/></radialGradient>
<filter id="shadow" x="-30%" y="-30%" width="160%" height="190%">
  <feDropShadow dx="0" dy="{T['SHADOW_DY']}" stdDeviation="{T['SHADOW_SD']}" flood-color="{T['SHADOW']}" flood-opacity="{T['SHADOW_OP']}"/>
</filter>
<filter id="glow" x="-60%" y="-60%" width="220%" height="220%">
  <feGaussianBlur stdDeviation="{T['GLOW_SD']}" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>
<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">
  <circle cx="1.4" cy="1.4" r="1.4" fill="{T['DOT']}" fill-opacity="{T['DOT_OP']}"/>
</pattern>
"""


def apply_theme(name):
    global T, INK0, INK1, CARD0, CARD1, STROKE, TXT, MUT, DIM, A1, A2, A3, DEFS, A
    T = THEMES[name]
    INK0, INK1 = T["INK0"], T["INK1"]
    CARD0, CARD1 = T["CARD0"], T["CARD1"]
    STROKE, TXT, MUT, DIM = T["STROKE"], T["TXT"], T["MUT"], T["DIM"]
    A1, A2, A3 = T["A1"], T["A2"], T["A3"]
    DEFS = build_defs()
    A = os.path.join(ROOT, "assets", T["dir"]) if T["dir"] else os.path.join(ROOT, "assets")
    os.makedirs(A, exist_ok=True)


def tw(s, size, weight=600):
    k = 0.60 if weight >= 600 else 0.555
    narrow = sum(1 for c in s if c in "iIl.,:;'|!jft()[]/ ")
    return size * (k * len(s) - 0.22 * narrow)


def svg(w, h, body, defs=None):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" fill="none" font-family="{FONT}">\n'
            f'<defs>{DEFS if defs is None else defs}</defs>\n{body}\n</svg>\n')


def write(name, s):
    open(os.path.join(A, name), "w").write(s)
    print("    %-20s %6d bytes" % (name, len(s)))


def icon(key, x, y, size, color="#FFFFFF", op="1"):
    sc = size / 24.0
    return (f'<g transform="translate({x:.1f},{y:.1f}) scale({sc:.4f})" fill="{color}" fill-opacity="{op}">'
            f'<path d="{ICONS[key]}"/></g>')


def header():
    H = 208
    b = f"""
<rect width="{W}" height="{H}" rx="22" fill="url(#ink)"/>
<rect width="{W}" height="{H}" rx="22" fill="url(#dots)"/>
<g opacity="0.95"><ellipse cx="742" cy="30" rx="210" ry="150" fill="url(#orbA)"/>
<ellipse cx="868" cy="178" rx="180" ry="130" fill="url(#orbB)"/></g>
<rect width="{W}" height="{H}" rx="22" fill="url(#sheen)"/>
<rect x="0.6" y="0.6" width="{W-1.2}" height="{H-1.2}" rx="21.4" stroke="{STROKE}"/>
<rect x="44" y="52" width="4" height="104" rx="2" fill="url(#acc)"/>
<text x="68" y="86" font-size="35" font-weight="700" fill="{TXT}" letter-spacing="-0.6">Karan Singh Singare</text>
<text x="69" y="118" font-size="16.5" font-weight="600" fill="{A2}" letter-spacing="0.2">Mobile Platform Engineer</text>
<text x="69" y="148" font-size="13.5" fill="{MUT}">Offline-first sync, native storage and the modules React Native stands on.</text>
<g transform="translate(69,164)">
  <rect width="128" height="26" rx="13" fill="{T['CHIP']}" fill-opacity="{T['PILL_OP']}" stroke="{STROKE}"/>
  <circle cx="16" cy="13" r="3.2" fill="{A2}"/>
  <text x="27" y="17.5" font-size="11.5" font-weight="600" fill="{MUT}" letter-spacing="0.3">Innovapptive</text>
  <rect x="140" width="150" height="26" rx="13" fill="{T['CHIP']}" fill-opacity="{T['PILL_OP']}" stroke="{STROKE}"/>
  <circle cx="156" cy="13" r="3.2" fill="{A3}"/>
  <text x="167" y="17.5" font-size="11.5" font-weight="600" fill="{MUT}" letter-spacing="0.3">Hyderabad, India</text>
</g>"""
    write("header.svg", svg(W, H, b))


def button(name, label, ikey, c0, c1):
    h, pad, iw = 46, 22, 18
    w = int(pad + iw + 10 + tw(label, 14.5, 700) + pad)
    gid = "g_" + name.replace(".svg", "").replace("-", "_")
    d = (f'<linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1">'
         f'<stop offset="0" stop-color="{c0}"/><stop offset="1" stop-color="{c1}"/></linearGradient>'
         '<filter id="bs" x="-40%" y="-40%" width="180%" height="210%">'
         '<feDropShadow dx="0" dy="3" stdDeviation="5" flood-color="#0B1020" flood-opacity="0.35"/></filter>'
         '<linearGradient id="bsheen" x1="0" y1="0" x2="0" y2="1">'
         '<stop offset="0" stop-color="#fff" stop-opacity="0.22"/>'
         '<stop offset="0.55" stop-color="#fff" stop-opacity="0.04"/>'
         '<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>')
    b = f"""
<g filter="url(#bs)"><rect x="1" y="1" width="{w-2}" height="{h-2}" rx="{(h-2)/2}" fill="url(#{gid})"/></g>
<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="{(h-2)/2}" fill="url(#bsheen)"/>
<rect x="1.5" y="1.5" width="{w-3}" height="{h-3}" rx="{(h-3)/2}" stroke="#FFFFFF" stroke-opacity="0.28"/>
{icon(ikey, pad, (h-iw)/2, iw, "#FFFFFF", "0.97")}
<text x="{pad+iw+10}" y="{h/2+5.2}" font-size="14.5" font-weight="700" fill="#FFFFFF" letter-spacing="0.2">{label}</text>"""
    write(name, svg(w, h, b, d))


def stats():
    days = [d for wk in CAL["contributionCalendar"]["weeks"] for d in wk["contributionDays"]]
    total = CAL["contributionCalendar"]["totalContributions"]
    active = sum(1 for d in days if d["contributionCount"] > 0)
    peak = max(d["contributionCount"] for d in days)
    best = cur = 0
    for d in days:
        cur = cur + 1 if d["contributionCount"] > 0 else 0
        best = max(best, cur)
    items = [("{:,}".format(total), "CONTRIBUTIONS", "past 12 months", A2),
             (str(active), "ACTIVE DAYS", "of 365", A1),
             (str(best), "LONGEST STREAK", "consecutive days", A3),
             (str(peak), "BUSIEST DAY", "contributions", A2)]
    gap, n = 16, 4
    cw, H = (W - gap * (n - 1)) / n, 124
    parts = []
    for i, (val, lab, sub, col) in enumerate(items):
        x = i * (cw + gap)
        parts.append(f"""<g transform="translate({x:.1f},0)">
  <g filter="url(#shadow)"><rect width="{cw:.1f}" height="{H}" rx="18" fill="url(#card)"/></g>
  <rect width="{cw:.1f}" height="{H}" rx="18" fill="url(#sheen)"/>
  <rect x="0.6" y="0.6" width="{cw-1.2:.1f}" height="{H-1.2}" rx="17.4" stroke="{STROKE}"/>
  <rect x="22" y="0" width="46" height="3" rx="1.5" fill="{col}"/>
  <circle cx="{cw-26:.1f}" cy="26" r="3.6" fill="{col}" fill-opacity="0.85"/>
  <text x="22" y="62" font-size="33" font-weight="700" fill="{TXT}" letter-spacing="-1.1">{val}</text>
  <text x="22" y="86" font-size="10.5" font-weight="700" fill="{col}" letter-spacing="1.1">{lab}</text>
  <text x="22" y="104" font-size="11" fill="{DIM}">{sub}</text>
</g>""")
    write("stats.svg", svg(W, H, "\n".join(parts)))


def activity():
    weeks = CAL["contributionCalendar"]["weeks"]
    vals = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in weeks]
    firsts = [w["contributionDays"][0]["date"] for w in weeks]
    H, PT, PB, PL, PR = 300, 86, 46, 34, 34
    cw, ch = W - PL - PR, H - PT - PB
    mx = max(vals) or 1
    pts = [(PL + i * cw / (len(vals) - 1), PT + ch - (v / mx) * ch) for i, v in enumerate(vals)]

    def smooth(p):
        d = "M%.2f,%.2f" % p[0]
        for i in range(len(p) - 1):
            x0, y0 = p[i - 1] if i else p[0]
            x1, y1 = p[i]
            x2, y2 = p[i + 1]
            x3, y3 = p[i + 2] if i + 2 < len(p) else p[-1]
            d += "C%.2f,%.2f %.2f,%.2f %.2f,%.2f" % (
                x1 + (x2 - x0) / 6, y1 + (y2 - y0) / 6,
                x2 - (x3 - x1) / 6, y2 - (y3 - y1) / 6, x2, y2)
        return d

    line = smooth(pts)
    area = line + "L%.2f,%.2f L%.2f,%.2f Z" % (pts[-1][0], PT + ch, pts[0][0], PT + ch)
    grid = "".join(f'<line x1="{PL}" y1="{PT+ch*f:.1f}" x2="{PL+cw}" y2="{PT+ch*f:.1f}" '
                   f'stroke="{STROKE}" stroke-opacity="{T["GRID_OP"]}" stroke-dasharray="3 5"/>'
                   for f in (0, .25, .5, .75, 1))
    ticks, seen = [], set()
    for i, ds in enumerate(firsts):
        dt = datetime.date.fromisoformat(ds)
        if dt.day <= 7 and (dt.year, dt.month) not in seen:
            seen.add((dt.year, dt.month))
            x = PL + i * cw / (len(vals) - 1)
            ticks.append(f'<text x="{x:.1f}" y="{PT+ch+26}" font-size="10.5" font-weight="600" '
                         f'fill="{DIM}" text-anchor="middle" letter-spacing="0.6">'
                         f'{dt.strftime("%b").upper()}</text>')
    pi = vals.index(mx)
    px, py = pts[pi]
    d2 = DEFS + f"""
<linearGradient id="areaF" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="{A2}" stop-opacity="{T['AREA0']}"/>
  <stop offset="0.55" stop-color="{A1}" stop-opacity="{T['AREA1']}"/>
  <stop offset="1" stop-color="{A1}" stop-opacity="0"/>
</linearGradient>"""
    b = f"""
<g filter="url(#shadow)"><rect width="{W}" height="{H}" rx="20" fill="url(#card)"/></g>
<rect width="{W}" height="{H}" rx="20" fill="url(#sheen)"/>
<rect x="0.6" y="0.6" width="{W-1.2}" height="{H-1.2}" rx="19.4" stroke="{STROKE}"/>
<text x="34" y="44" font-size="16" font-weight="700" fill="{TXT}" letter-spacing="-0.2">Contribution activity</text>
<text x="34" y="64" font-size="11.5" fill="{DIM}">Weekly totals across public and private repositories, past 12 months</text>
<g transform="translate({W-34},34)">
  <rect x="-116" y="0" width="116" height="26" rx="13" fill="{T['CHIP']}" fill-opacity="{T['PILL_OP']}" stroke="{STROKE}"/>
  <circle cx="-100" cy="13" r="3.4" fill="{A2}"/>
  <text x="-90" y="17.5" font-size="11" font-weight="600" fill="{MUT}">peak {mx}/week</text>
</g>
{grid}
<path d="{area}" fill="url(#areaF)"/>
<path d="{line}" stroke="url(#acc)" stroke-width="{T['LINE_W']}" stroke-linecap="round" filter="url(#glow)"/>
{"".join(ticks)}
<line x1="{px:.1f}" y1="{py:.1f}" x2="{px:.1f}" y2="{PT+ch}" stroke="{A2}" stroke-opacity="0.35" stroke-dasharray="2 4"/>
<circle cx="{px:.1f}" cy="{py:.1f}" r="7" fill="{A2}" fill-opacity="0.22"/>
<circle cx="{px:.1f}" cy="{py:.1f}" r="3.8" fill="{CARD0}" stroke="{A2}" stroke-width="2"/>"""
    write("activity.svg", svg(W, H, b, d2))


def stack():
    rows = [[("TypeScript", "typescript", "#3178C6"), ("React Native", "react", "#149ECA"),
             ("Kotlin", "kotlin", "#8A4BE8"), ("Swift", "swift", "#F05138")],
            [("C++", "cplusplus", "#5586B5"), ("SQLite", "sqlite", "#2C9CC4"),
             ("Android", "android", "#2BA55F"), ("iOS", "apple", "#6B7A8F")]]
    PADX, TOP, CH, GAP, RG = 30, 74, 46, 12, 12
    H = TOP + len(rows) * CH + (len(rows) - 1) * RG + 26
    parts = [f"""
<g filter="url(#shadow)"><rect width="{W}" height="{H}" rx="20" fill="url(#card)"/></g>
<rect width="{W}" height="{H}" rx="20" fill="url(#sheen)"/>
<rect x="0.6" y="0.6" width="{W-1.2}" height="{H-1.2}" rx="19.4" stroke="{STROKE}"/>
<text x="34" y="44" font-size="16" font-weight="700" fill="{TXT}" letter-spacing="-0.2">Working with</text>
<text x="34" y="62" font-size="11.5" fill="{DIM}">Day to day, across the JavaScript and native sides</text>"""]
    for r, row in enumerate(rows):
        y = TOP + r * (CH + RG)
        widths = [9 + 28 + 12 + tw(n, 13.5, 600) + 20 for n, _, _ in row]
        x = PADX
        for (name, key, col), w in zip(row, widths):
            parts.append(f"""<g transform="translate({x:.1f},{y})">
  <rect width="{w:.1f}" height="{CH}" rx="14" fill="{T['CHIP']}" fill-opacity="{T['CHIP_OP']}"/>
  <rect x="0.6" y="0.6" width="{w-1.2:.1f}" height="{CH-1.2}" rx="13.4" stroke="{STROKE}"/>
  <rect x="9" y="9" width="28" height="28" rx="9" fill="{col}" fill-opacity="{T['TILE_OP']}"/>
  {icon(key, 15, 15, 16, col, "1")}
  <text x="{9+28+12}" y="{CH/2+5}" font-size="13.5" font-weight="600" fill="{TXT}">{name}</text>
</g>""")
            x += w + GAP
    write("stack.svg", svg(W, H, "\n".join(parts)))


print("regenerating widgets for @%s" % LOGIN)
for _name in ("dark", "light"):
    print("  theme: %s" % _name)
    apply_theme(_name)
    header(); stats(); activity(); stack()

apply_theme("dark")   # buttons are brand-coloured and shared by both themes
button("btn-linkedin.svg", "LinkedIn", "linkedin", "#0A66C2", "#1D8EF0")
button("btn-email.svg", "Email", "gmail", "#C2410C", "#F0652B")
button("btn-github.svg", "GitHub", "github", "#30363D", "#596575")
print("done")
