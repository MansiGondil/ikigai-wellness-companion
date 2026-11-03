"""
Generates the two calm cherry-blossom branches used as page backgrounds:

    assets/blossom_top_left.svg      hangs in from the top-left corner, curving down and right
    assets/blossom_bottom_right.svg  rises from the bottom-right corner, curving up and left

Simple on purpose: a few smooth branches in one flat bark colour and, per tree, exactly
26 blossoms (15 white, 11 pale pink), 10 buds and 10 leaves. No blur, no filters, no
gradients. Standard library only, seeded so the output is the same every time.

Run from the project folder:  python tools/make_blossoms.py
"""

import math
import random
from pathlib import Path

WIDTH, HEIGHT = 600, 500           # SVG canvas (user units); shown inside a 26vw x 34vh corner zone
MARGIN = 16                        # keep everything fully inside the canvas
N_WHITE, N_PINK, N_BUDS, N_LEAVES = 15, 11, 10, 10
N_BLOSSOMS = N_WHITE + N_PINK
SIZE = 1.2                         # 20% larger than before: blossoms ~12-19px on screen
OUT_DIR = Path(__file__).resolve().parent.parent / "assets"

BARK = "#7A6468"
PETAL = "M0 0C-5 -2 -7.5 -8 -5 -11.6C-3.6 -13.4 -1.4 -13 0 -11C1.4 -13 3.6 -13.4 5 -11.6C7.5 -8 5 -2 0 0Z"
PETAL_RADIUS = 12.5                # how far a petal reaches from the centre at scale 1


def flower(symbol_id, fill, centre, edge=None):
    stroke = f" stroke='{edge}' stroke-width='0.5'" if edge else ""
    petals = "".join(f"<path d='{PETAL}' fill='{fill}'{stroke} transform='rotate({a})'/>" for a in (0, 72, 144, 216, 288))
    return f"<g id='{symbol_id}'>{petals}<circle r='2.2' fill='{centre}'/></g>"


DEFS = (
    "<defs>"
    + flower("w", "#FFFFFF", "#F2B5C6", edge="#E8D3DC")     # white, very thin edge so it shows on the sky
    + flower("p", "#F7C6D4", "#E88AA6")                      # pale pink
    + "<g id='b'><ellipse cy='-3.5' rx='2.6' ry='4.2' fill='#E89AB0'/></g>"                      # bud
    + "<g id='l'><path d='M0 0C4 -4 4.4 -11 0 -16C-4.4 -11 -4 -4 0 0Z' fill='#A8CFA0'/></g>"    # leaf
    + "</defs>"
)


def cubic_point(p0, p1, p2, p3, t):
    u = 1 - t
    return (u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
            u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1])


def inside(x, y, pad=MARGIN):
    return pad < x < WIDTH - pad and pad < y < HEIGHT - pad


def grow_branches(rnd):
    """Grows one hanging branch from the top-left corner (3 forks = 4 levels).
    Returns the bark strokes plus candidate spots for flowers, buds and leaves."""
    strokes, tip_spots, branch_spots = [], [], []

    def grow(start, angle, length, width, depth):
        angle += 0.18 * math.cos(angle) * min(depth, 1)          # hanging branches droop gently
        end = (start[0] + math.cos(angle) * length, start[1] + math.sin(angle) * length)
        end = (min(max(end[0], MARGIN), WIDTH - MARGIN), min(max(end[1], MARGIN), HEIGHT - MARGIN))
        bend1, bend2 = rnd.uniform(-0.35, 0.35), rnd.uniform(-0.35, 0.35)
        c1 = (start[0] + math.cos(angle + bend1) * length * 0.35, start[1] + math.sin(angle + bend1) * length * 0.35)
        c2 = (start[0] + math.cos(angle + bend2) * length * 0.7, start[1] + math.sin(angle + bend2) * length * 0.7)

        # Gentle taper: two halves, the second a little thinner
        end_width = max(width * 0.55, 1.0)
        mid = cubic_point(start, c1, c2, end, 0.5)
        q1, q3 = cubic_point(start, c1, c2, end, 0.25), cubic_point(start, c1, c2, end, 0.75)
        strokes.append((f"M{start[0]:.0f} {start[1]:.0f}Q{q1[0]:.0f} {q1[1]:.0f} {mid[0]:.0f} {mid[1]:.0f}", width * 0.88))
        strokes.append((f"M{mid[0]:.0f} {mid[1]:.0f}Q{q3[0]:.0f} {q3[1]:.0f} {end[0]:.0f} {end[1]:.0f}", (width + end_width) / 2 * 0.8))

        # Spots along younger branches (for single flowers, buds and leaves)
        if depth >= 1:
            for t in (0.35, 0.6, 0.85):
                branch_spots.append((*cubic_point(start, c1, c2, end, t), math.degrees(angle)))

        if depth == 3:
            tip_spots.append((*end, math.degrees(angle)))
            return

        children = 3 if depth == 0 else rnd.choice((2, 2, 2, 3))
        for i in range(children):
            if i == 0:
                origin, spread = end, rnd.uniform(-0.2, 0.25)
            else:
                origin = cubic_point(start, c1, c2, end, rnd.uniform(0.45, 0.85))
                spread = (1 if i % 2 else -1) * rnd.uniform(0.55, 0.95)
            grow(origin, angle + spread, length * rnd.uniform(0.6, 0.75), end_width * (1 if i == 0 else 0.85), depth + 1)

    grow((-10, 34), math.radians(rnd.uniform(18, 26)), 210, 6, 0)
    return strokes, tip_spots, branch_spots


def place(seed):
    """Places exactly 26 flowers, 10 buds and 10 leaves without piling them up. None if it can't."""
    rnd = random.Random(seed)
    strokes, tips, along = grow_branches(rnd)
    blossoms, buds, leaves = [], [], []
    taken = []                                   # (x, y, radius) of everything placed so far

    def free(x, y, r, overlap=0.95):
        return inside(x, y, r * 0.8) and all(math.hypot(x - tx, y - ty) >= (r + tr) * overlap for tx, ty, tr in taken)

    # Flowers: 1-3 around each twig tip first (denser at the tips), then single ones along branches
    spots = []
    for x, y, _ in tips:
        spots += [(x + rnd.uniform(-18, 18), y + rnd.uniform(-18, 18)) for _ in range(3)]
    spots += [(x + rnd.uniform(-8, 8), y + rnd.uniform(-8, 8)) for x, y, _ in along]
    for x, y in spots:
        if len(blossoms) == N_BLOSSOMS:
            break
        scale = rnd.uniform(0.8, 1.25) * SIZE
        r = PETAL_RADIUS * scale
        if free(x, y, r):
            blossoms.append([None, x, y, rnd.uniform(0, 72), scale])
            taken.append((x, y, r))
    if len(blossoms) < N_BLOSSOMS:
        return None

    # Exactly 15 white and 11 pink, mixed through the tree
    colours = ["w"] * N_WHITE + ["p"] * N_PINK
    rnd.shuffle(colours)
    for b, c in zip(blossoms, colours):
        b[0] = c

    # Buds near twig tips and along twigs; leaves along branches
    def scatter(points, count, radius, jitter, store):
        rnd.shuffle(points)
        for x, y, angle in points:
            if len(store) == count:
                break
            px, py = x + rnd.uniform(-jitter, jitter), y + rnd.uniform(-jitter, jitter)
            scale = rnd.uniform(0.9, 1.15) * SIZE
            if free(px, py, radius * scale, overlap=0.85):
                store.append((px, py, angle + 90 + rnd.uniform(-45, 45), scale))
                taken.append((px, py, radius * scale))

    scatter(list(tips) + list(along), N_BUDS, 5.5, 16, buds)
    scatter(list(along) + list(tips), N_LEAVES, 9.0, 10, leaves)
    if len(buds) < N_BUDS or len(leaves) < N_LEAVES:
        return None
    return strokes, blossoms, buds, leaves


def use(symbol, x, y, rotate, scale):
    return f"<use href='#{symbol}' transform='translate({x:.0f} {y:.0f}) rotate({rotate:.0f}) scale({scale:.2f})'/>"


def build_svg(seed, flip):
    for attempt in range(200):                   # try seeds until everything fits
        result = place(seed + attempt * 1000)
        if result:
            break
    else:
        raise RuntimeError("could not place all blossoms, buds and leaves")
    strokes, blossoms, buds, leaves = result
    body = (
        f"<g fill='none' stroke='{BARK}' stroke-linecap='round'>"
        + "".join(f"<path d='{d}' stroke-width='{w:.1f}'/>" for d, w in strokes) + "</g>"
        + "".join(use("l", x, y, r, s) for x, y, r, s in leaves)
        + "".join(use("b", x, y, r, s) for x, y, r, s in buds)
        + "".join(use(k, x, y, r, s) for k, x, y, r, s in blossoms)
    )
    if flip:  # turn the hanging branch around so it rises from the bottom-right corner
        body = f"<g transform='rotate(180 {WIDTH / 2} {HEIGHT / 2})'>{body}</g>"
    svg = f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {WIDTH} {HEIGHT}'>{DEFS}{body}</svg>"
    counts = dict(blossoms=len(blossoms), white=sum(b[0] == "w" for b in blossoms),
                  pink=sum(b[0] == "p" for b in blossoms), buds=len(buds), leaves=len(leaves))
    return svg, counts


if __name__ == "__main__":
    OUT_DIR.mkdir(exist_ok=True)
    for name, seed, flip in (("blossom_top_left.svg", 31, False), ("blossom_bottom_right.svg", 58, True)):
        svg, counts = build_svg(seed, flip)
        (OUT_DIR / name).write_text(svg, encoding="utf-8")
        print(f"{name}: {len(svg.encode()) / 1024:.1f} KB  {counts}")
