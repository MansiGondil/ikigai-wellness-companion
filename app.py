from pathlib import Path

import logging

import streamlit as st
from backend import (
    wellness_chat, reset_attack_memory, get_setting,
    is_crisis_text, normalize_quotes, CRISIS_REPLY,
)

# Friendly fallbacks: users never see raw errors
CONNECTION_TROUBLE = "I'm having trouble connecting right now. Please try again in a minute."
LIMIT_NOTE = "That's the limit for this session. Thanks for spending time here."


def _max_messages():
    """Soft cap on user messages per browser session (setting MAX_MESSAGES, default 25)."""
    try:
        return max(1, int(get_setting("MAX_MESSAGES", 25)))
    except (TypeError, ValueError):
        return 25


MAX_MESSAGES = _max_messages()

# ================================
# 🌿 Page Configuration
# ================================
st.set_page_config(
    page_title="Ikigai",
    page_icon=str(Path(__file__).parent / "assets" / "favicon.png"),  # custom blue blossom
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ================================
# 🎨 Custom CSS
# ================================
st.markdown("""
<style>
/* Jost (wordmark, buttons, labels, captions), Lora (body + chat, incl. italic tagline).
   Lora body and Jost headings are also set in config.toml */
@import url('https://fonts.googleapis.com/css2?family=Jost:wght@400;500;600&family=Lora:ital,wght@0,400;0,500;1,400&display=swap');

html, body, .stApp {
    padding: 0 !important;
    margin: 0 !important;
}

/* Soft sky gradient with a very subtle linen/paper texture on top (inline SVG noise, ~5% opacity) */
.stApp {
    background-image:
        url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='240' height='240'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85 0.35' numOctaves='3' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 0.24  0 0 0 0 0.36  0 0 0 0 0.47  0 0 0 1 0'/></filter><rect width='100%25' height='100%25' filter='url(%23n)' opacity='0.05'/></svg>"),
        linear-gradient(180deg, #BFE0FA 0%, #DCEBF3 100%) !important;
    background-attachment: fixed !important;
}
/* Let the sky show through Streamlit's own page layers */
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background: transparent !important;
}

/* No sidebar: hide the expand arrow */
[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapseButton"],
section[data-testid="stSidebar"] {
    display: none !important;
}

/* One centered column */
.block-container {
    max-width: 820px !important;
    padding-top: 1rem !important;
    padding-bottom: 1rem !important;
}

/* Reduce spacing after divider */
hr {
    margin-top: 0.5rem !important;
    margin-bottom: 0.5rem !important;
}

/* ---------- Header ---------- */
.ik-header {
    text-align: center;
    padding: 2.5rem 0 2rem 0;
}
.ik-wordmark {
    display: inline-block;   /* shrink-wraps the letters, so the butterfly can be placed against them */
    position: relative;
    font-family: 'Jost', sans-serif;
    font-weight: 600;
    font-size: 3.2rem;
    text-transform: uppercase;
    letter-spacing: 0.4em;
    padding-left: 0.4em;  /* balances the trailing letter-spacing so it stays centered */
    line-height: 1.1;
    color: #24384D;
}
.ik-tagline {
    font-family: 'Lora', Georgia, serif;
    font-style: italic;
    font-size: 1.15rem;
    color: #4A6683;
    margin-top: 0.6rem;
}
.ik-subcaption {
    font-family: 'Jost', sans-serif;
    font-size: 0.85rem;
    color: #7790A8;
    margin-top: 0.35rem;
}

/* Quiet affirmation line */
.ik-affirmation {
    text-align: center;
    font-family: 'Lora', Georgia, serif;
    font-style: italic;
    font-size: 0.95rem;
    color: #3F5B77;
    margin: 1.75rem 0 2.25rem 0;
}

/* ---------- Mode cards (display only; the slider in the centre is the control) ---------- */
.ik-card {
    background: rgba(255, 255, 255, 0.72);
    -webkit-backdrop-filter: blur(6px);
    backdrop-filter: blur(6px);
    border: 1px solid #C5D9E8;
    border-radius: 16px;
    padding: clamp(22px, 7cqw, 28px);
    box-sizing: border-box;
    height: 100%;
    overflow: hidden;            /* safety net; the rules below keep the content from ever needing it */
    display: flex;
    flex-direction: column;
    transition: background 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
}
.ik-card.selected {
    background: #FFFFFF;
    border-color: #9DBFD8;
    box-shadow: 0 6px 20px rgba(36, 56, 77, 0.12);
}
/* Font sizes grow with the card width (cqw = 1% of the card's width) */
.ik-card-title {
    font-family: 'Jost', sans-serif;
    font-weight: 600;
    font-size: clamp(1.2rem, 7.2cqw, 1.6rem);
    letter-spacing: 0.06em;
    color: #24384D;
}
.ik-card-tagline {
    font-family: 'Lora', Georgia, serif;
    font-style: italic;
    font-size: clamp(0.95rem, 5.2cqw, 1.18rem);
    color: #4A6683;
    margin-top: 0.35rem;
}
.ik-card-body {
    font-family: 'Lora', Georgia, serif;
    font-size: clamp(0.88rem, 4.6cqw, 1.06rem);
    line-height: 1.6;
    color: #3F5B77;
    margin-top: 0.75rem;
}
.ik-card-label {
    font-family: 'Jost', sans-serif;
    font-variant-caps: all-small-caps;
    font-size: clamp(0.92rem, 4.8cqw, 1.08rem);
    letter-spacing: 0.12em;
    color: #7790A8;
    margin-top: 1rem;
}
.ik-card-line {
    font-family: 'Lora', Georgia, serif;
    font-size: clamp(0.86rem, 4.4cqw, 1.02rem);
    line-height: 1.5;
    color: #3F5B77;
}
.ik-card-try {
    font-family: 'Jost', sans-serif;
    font-size: clamp(0.84rem, 4.2cqw, 0.98rem);
    color: #3F5B77;
    margin-top: 1rem;
}
.ik-card-try em {
    font-family: 'Lora', Georgia, serif;
    color: #24384D;
}
.ik-card-small {
    font-family: 'Jost', sans-serif;
    font-size: clamp(0.8rem, 4cqw, 0.92rem);
    letter-spacing: 0.04em;
    color: #7790A8;
    margin-top: auto;            /* sits at the bottom of the card */
    padding-top: 1rem;
}

/* ---------- Layout sizes shared by the side cards and the centre panel ---------- */
:root {
    --center-w: min(760px, calc(100vw - 2 * 270px));
    --gap: calc((100vw - var(--center-w)) / 2);                 /* page edge to panel, each side */
    --card-w: clamp(210px, calc(var(--gap) - 5vw), 420px);
    --card-x: calc((var(--gap) - var(--card-w)) / 2);          /* same space before and after the card */
}
/* Reserve the scrollbar space on both sides, so the panel stays exactly centred under the cards */
[data-testid="stMain"] {
    scrollbar-gutter: stable both-edges;
}
.st-key-center_panel {
    max-width: 760px;
    margin: 0 auto;
}

/* Side cards, fixed to the screen: Support below the top-left tree, Reflect above the bottom-right tree */
.st-key-side_left,
.st-key-side_right {
    position: fixed;
    width: var(--card-w);
    z-index: 2;
    container-type: size;        /* lets the card's text react to the card's own height and width */
}
.st-key-side_left  { container-name: support; }
.st-key-side_right { container-name: reflect; }
.st-key-side_left  { left: var(--card-x);  top: 37vh; bottom: 4vh; }
.st-key-side_right { right: var(--card-x); top: 9vh;  bottom: 37vh; }
/* The card fills its fixed box */
.st-key-side_left [data-testid="stElementContainer"],
.st-key-side_right [data-testid="stElementContainer"],
.st-key-side_left [data-testid="stMarkdown"],
.st-key-side_right [data-testid="stMarkdown"],
.st-key-side_left [data-testid="stMarkdown"] > div,
.st-key-side_right [data-testid="stMarkdown"] > div,
.st-key-side_left [data-testid="stMarkdownContainer"],
.st-key-side_right [data-testid="stMarkdownContainer"] {
    height: 100%;
    margin: 0 !important;
}
@media (min-width: 1200px) {
    .st-key-center_panel { max-width: var(--center-w); }
}

/* One-line mode caption: only shown when the side cards are hidden */
.ik-mode-caption {
    display: none;
    text-align: center;
    font-family: 'Jost', sans-serif;
    font-size: 0.85rem;
    color: #7790A8;
    margin-top: -0.25rem;
}

/* Under 1200px: no side cards, caption under the slider instead */
@media (max-width: 1199px) {
    .st-key-side_left,
    .st-key-side_right {
        display: none !important;
    }
    .ik-mode-caption { display: block; }
}

/* ---------- Empty chat line ---------- */
.ik-empty-chat {
    text-align: center;
    font-family: 'Lora', Georgia, serif;
    font-style: italic;
    font-size: 1rem;
    color: #4A6683;
    margin: 0.5rem 0 1rem 0;
}

/* ---------- Message box that stands out ---------- */
[data-testid="stTextAreaRootElement"] {
    overflow: hidden;   /* keeps the inner textarea inside the rounded corners */
    background: #FFFFFF !important;
    border: 1.5px solid #7FA6CC !important;
    border-radius: 14px !important;
    box-shadow: 0 4px 14px rgba(36, 56, 77, 0.10) !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
[data-testid="stTextAreaRootElement"]:focus-within {
    border-color: #5B8DB8 !important;
    box-shadow: 0 4px 14px rgba(36, 56, 77, 0.10), 0 0 0 3px rgba(91, 141, 184, 0.25) !important;
}
[data-testid="stTextArea"] textarea {
    background: transparent !important;
    border-radius: 14px !important;
    color: #24384D !important;
    min-height: 110px !important;
}
[data-testid="stTextArea"] textarea::placeholder {
    color: #56708A !important;
    opacity: 1 !important;
}

/* ---------- Butterfly resting on the last "I" of the wordmark ---------- */
/* Sized in em, so it scales with the wordmark. The last letter ends 0.4em before the right edge
   (the trailing letter-spacing), so the butterfly is centred just right of that letter's top. */
.ik-butterfly {
    position: absolute;
    right: -0.11em;
    top: -0.56em;
    width: 1em;
    height: 0.8125em;           /* keeps the 64 x 52 drawing in proportion */
    transform: rotate(12deg);
    pointer-events: none;
    z-index: 2;
}
.ik-butterfly .bf-wing-l,
.ik-butterfly .bf-wing-r {
    transform-origin: 32px 30px;
}
.ik-butterfly .bf-antennae {
    transform-origin: 32px 17px;
}
@media (prefers-reduced-motion: no-preference) {
    .ik-butterfly .bf-wing-l,
    .ik-butterfly .bf-wing-r {
        animation: bf-flap 4.5s ease-in-out infinite;
    }
    .ik-butterfly .bf-antennae {
        animation: bf-sway 3.2s ease-in-out infinite alternate;
    }
    @keyframes bf-flap {
        0%, 62%, 100% { transform: scaleX(1); }
        74%           { transform: scaleX(0.32); }
        86%           { transform: scaleX(1); }
    }
    @keyframes bf-sway {
        from { transform: rotate(-5deg); }
        to   { transform: rotate(5deg); }
    }
}

/* Powder-blue heart in the footer */
.ik-heart {
    width: 1em;
    height: 1em;
    vertical-align: -0.14em;
}

/* ---------- Typography ---------- */
h1, h2, h3, h4 {
    color: #24384D !important;
}
/* Buttons, widget labels, captions and expander titles in Jost */
button p,
[data-testid="stWidgetLabel"] p,
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p,
[data-testid="stExpander"] summary p,
[data-testid="stSliderTickBar"],
[data-testid="stSliderThumbValue"] {
    font-family: 'Jost', sans-serif !important;
}
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p {
    color: #7790A8 !important;
}

/* ---------- Buttons ---------- */
button[data-testid="stBaseButton-primary"],
button[data-testid="stBaseButton-secondary"] {
    color: #1F4E79 !important;
    border-radius: 10px !important;
    padding: 0.3rem 1rem !important;
    min-height: 2.2rem !important;
}
button[data-testid="stBaseButton-primary"] p,
button[data-testid="stBaseButton-secondary"] p {
    font-size: 0.9rem !important;
    color: #1F4E79 !important;
}
button[data-testid="stBaseButton-primary"] {
    background-color: #BFD8EA !important;
    border: 1px solid #9DBFD8 !important;
}
button[data-testid="stBaseButton-primary"]:hover {
    background-color: #AECBE0 !important;
    border-color: #9DBFD8 !important;
}
button[data-testid="stBaseButton-secondary"] {
    background-color: #FFFFFF !important;
    border: 1px solid #C5D9E8 !important;
}
button[data-testid="stBaseButton-secondary"]:hover {
    background-color: #F4F8FB !important;
    border-color: #9DBFD8 !important;
}

/* ---------- Support / Reflect pill slider ---------- */
[data-testid="stSlider"] {
    max-width: 320px;
    margin: 0 auto;
}
/* Streamlit 1.66 slider structure: [role=group] > div > (track bar, thumb, tick bar) */
/* Track bar as a soft pale-blue pill (replaces the thin gradient line) */
[data-testid="stSlider"] [role="group"] > div > div:first-child {
    background: #BFD8EA !important;
    height: 12px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    border-radius: 999px !important;
}
/* White rounded thumb, big enough to drag or tap on a phone */
[data-testid="stSlider"] [role="group"] > div > div:nth-child(2) {
    background-color: #FFFFFF !important;
    border: 1px solid #9DBFD8 !important;
    width: 28px !important;
    height: 28px !important;
    box-shadow: 0 1px 3px rgba(36, 56, 77, 0.18) !important;
}
/* The words "Support" / "Reflect" are shown as static text beside the slider,
   so hide the slider's own value bubble and tick labels */
[data-testid="stSliderThumbValue"],
[data-testid="stSliderTickBar"] {
    display: none !important;
}
.ik-mode-word {
    font-family: 'Jost', sans-serif;
    font-size: 1rem;
    color: #7790A8;
    font-weight: 400;
    padding-top: 0.4rem;
}
.ik-mode-word.left  { text-align: right; }
.ik-mode-word.right { text-align: left; }
.ik-mode-word.selected {
    color: #24384D;
    font-weight: 600;
}

/* Send and New conversation: identical size, font, corners and alignment */
.st-key-button_row {
    align-items: center;
}
.st-key-button_row button {
    width: 168px !important;
    height: 44px !important;
    min-height: 44px !important;
    padding: 0 1rem !important;
    border-radius: 10px !important;
}
.st-key-button_row button p {
    font-family: 'Jost', sans-serif !important;
    font-size: 15px !important;
    white-space: nowrap;
}
/* Very narrow phones: both buttons shrink equally so they still share one row */
@media (max-width: 420px) {
    .st-key-button_row button { width: calc((100vw - 6rem) / 2) !important; padding: 0 0.4rem !important; }
}

/* ---------- Chat ---------- */
.chat-container {
    display: flex;
    flex-direction: column;
    background-color: transparent;
    padding: 0;
    max-height: 480px;
    overflow-y: auto;
    border-radius: 12px;
    margin-top: 0 !important;
}

/* User bubble */
.chat-bubble-user {
    align-self: flex-end;
    background-color: #CFE2F0;
    padding: 14px 18px;
    border-radius: 18px;
    margin: 6px 0;
    max-width: 80%;
    font-family: 'Lora', Georgia, serif;
    font-size: 16px;
    line-height: 1.6;
    color: #3F5B77;
}

/* Bot bubble */
.chat-bubble-bot {
    align-self: flex-start;
    background-color: #FFFFFF;
    border: 1px solid #C5D9E8;
    padding: 14px 18px;
    border-radius: 18px;
    margin: 6px 0;
    max-width: 80%;
    font-family: 'Lora', Georgia, serif;
    font-size: 16px;
    line-height: 1.6;
    color: #3F5B77;
}

/* Links inside bubbles */
.chat-bubble-user a,
.chat-bubble-bot a {
    color: #1F4E79;
    text-decoration: underline;
}

/* Remove extra spacing around Markdown blocks */
div[data-testid="stMarkdownContainer"] {
    margin-top: 0 !important;
    margin-bottom: 0.5rem !important;
}

/* Reduce spacing around text inputs */
div[data-testid="stVerticalBlock"] > div {
    gap: 0.5rem !important;
}

/* Footer: the "Built with" line closes the white panel */
.ik-footer-small {
    text-align: center;
    font-family: 'Jost', sans-serif;
    font-size: 12px;
    color: #7790A8;
    margin-bottom: 0;
}
/* Disclaimer: outside the panel, on the sky, the very last thing on the page.
   It never gets wider than the space between the two corner tree drawings. */
.ik-disclaimer {
    text-align: center;
    font-family: 'Jost', sans-serif;
    font-size: 13px;
    line-height: 1.5;
    color: #3F5B77;
    max-width: min(760px, calc(100vw - 2 * min(26vw, 34vh * 1.2) - 24px));
    margin: 20px auto 28px auto !important;   /* beats Streamlit's own paragraph margins */
}
@media (min-width: 1200px) {
    .ik-disclaimer { max-width: min(var(--center-w), calc(100vw - 2 * min(26vw, 34vh * 1.2) - 24px)); }
}
/* Phones: too narrow to fit between the trees, so it keeps the panel width and ends above the
   bottom-right tree drawing instead (the drawing is 26vw wide, so 26vw * 5/6 tall) */
@media (max-width: 640px) {
    .ik-disclaimer {
        max-width: 100%;
        margin-bottom: calc(26vw * 5 / 6 + 16px) !important;
    }
}

</style>
""", unsafe_allow_html=True)


# ================================
# Background scene: blossom trees, falling petals, centre panel
# (the trees are drawn from scratch by tools/make_blossoms.py; no third-party images)
# ================================
import base64
import random
from functools import lru_cache

ASSETS = Path(__file__).parent / "assets"


@st.cache_data
def _encode_svg(filename, modified_ns):
    """Base64-encodes one SVG. modified_ns is part of the cache key, so a regenerated file is picked up."""
    encoded = base64.b64encode((ASSETS / filename).read_bytes()).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def blossom_data_uri(filename):
    """Data URI for one generated SVG (cached until the file changes)."""
    return _encode_svg(filename, (ASSETS / filename).stat().st_mtime_ns)


@lru_cache(maxsize=1)
def falling_petals_html(count=18):
    """Petals with their own size, colour, start position, speed and sway, set as CSS variables."""
    rnd = random.Random(7)
    spans = []
    for i in range(count):
        size = rnd.uniform(8, 18)
        colour = "#F7C6D4" if i % 2 == 0 else "#FFFFFF"
        duration = rnd.uniform(14, 28)
        spans.append(
            f"<span style='--x:{(i + rnd.uniform(0.1, 0.9)) / count * 100:.1f}%;"
            f"--y:{rnd.uniform(8, 88):.0f}vh;--w:{size:.1f}px;--h:{size * 0.68:.1f}px;--c:{colour};"
            f"--d:{duration:.1f}s;--delay:-{rnd.uniform(0, duration):.1f}s;--sway:{rnd.uniform(18, 46):.0f}px;"
            f"--r:{rnd.uniform(0, 180):.0f}deg'></span>"
        )
    return f'<div class="ik-petals" aria-hidden="true">{"".join(spans)}</div>'


# The tree CSS carries base64 data, so it goes through st.html (a style-only block,
# no Markdown parsing) instead of st.markdown, which would re-parse it on every rerun
st.html(f"""
<style>
/* Two calm blossom trees, each inside a 26vw x 34vh corner zone, behind everything, clicks pass through */
.stApp::before,
.stApp::after {{
    content: "";
    position: fixed;
    width: 26vw;
    height: 34vh;
    background-repeat: no-repeat;
    background-size: contain;
    opacity: 0.75;
    pointer-events: none;
    z-index: 0;
}}
.stApp::before {{
    left: 0;
    top: 0;
    background-image: url("{blossom_data_uri('blossom_top_left.svg')}");
    background-position: left top;
}}
.stApp::after {{
    right: 0;
    bottom: 0;
    background-image: url("{blossom_data_uri('blossom_bottom_right.svg')}");
    background-position: right bottom;
}}
</style>
""")


# Side-card fallbacks: when a card's box is too short for its text, step through these stages in
# order (first smaller text, then drop "Good for", then "Try saying", then "I won't", then tighter text).
CARD_STAGES = [
    ".ik-card-body { font-size: clamp(0.84rem, 4.2cqw, 0.96rem); line-height: 1.5; margin-top: 0.55rem; }"
    ".ik-card-line { font-size: clamp(0.82rem, 4cqw, 0.94rem); line-height: 1.42; }"
    ".ik-card-label, .ik-card-try { margin-top: 0.7rem; } .ik-card-small { padding-top: 0.7rem; }",
    ".ik-sec-goodfor { display: none; }",
    ".ik-card-try { display: none; }",
    ".ik-sec-wont { display: none; }",
    ".ik-card { padding: 18px; } .ik-card-title { font-size: 1.1rem; } .ik-card-tagline { font-size: 0.9rem; }"
    ".ik-card-body { font-size: 0.8rem; line-height: 1.42; } .ik-card-line { font-size: 0.78rem; line-height: 1.36; }",
]
# Measured in headless Chrome: the card height each stage needs (+10px margin), per card and width band.
# A stage switches on when the card box is shorter than its number; None = never needed.
CARD_THRESHOLDS = {
    "support": [(0, 239, [626, 556, 465, None, None]),
                (240, 299, [520, 476, 386, None, None]),
                (300, None, [553, 497, 394, None, None])],
    "reflect": [(0, 239, [728, 626, 535, 481, 390]),
                (240, 299, [619, 564, 474, 419, None]),
                (300, None, [646, 581, 479, 442, None])],
}


def card_fallback_css():
    rules = []
    for name, bands in CARD_THRESHOLDS.items():
        for low, high, thresholds in bands:
            width = (f" and (min-width: {low}px)" if low else "") + (f" and (max-width: {high}px)" if high else "")
            for stage, limit in enumerate(thresholds):
                if limit:
                    rules.append(f"@container {name} (max-height: {limit - 1}px){width} {{ {CARD_STAGES[stage]} }}")
    return "\n".join(rules)


st.html(f"<style>\n{card_fallback_css()}\n</style>")

st.markdown(f"""
<style>

/* Wide page; everything sits above the trees */
.block-container {{
    position: relative;
    z-index: 1;
    max-width: 100% !important;
    padding: 1rem 1.5rem 2rem 1.5rem !important;
    margin-top: 2.5rem;
}}

/* Frosted panel behind the centre column only (a separate layer, so the blur never traps the petals) */
.st-key-center_panel {{
    position: relative;
    z-index: 0;
    padding: 1.25rem 2.25rem 1.75rem 2.25rem;
}}
.st-key-center_panel::before {{
    content: "";
    position: absolute;
    inset: 0;
    background: rgba(255, 255, 255, 0.62);
    -webkit-backdrop-filter: blur(6px);
    backdrop-filter: blur(6px);
    border-radius: 24px;
    box-shadow: 0 4px 24px rgba(36, 56, 77, 0.06);
    z-index: -1;
}}
@media (max-width: 640px) {{
    .block-container {{ padding: 0.75rem 0.75rem 1.5rem 0.75rem !important; margin-top: 2.5rem; }}
    .st-key-center_panel {{ padding: 1rem 1rem 1.25rem 1rem; }}
}}
/* Let the trees show through the (otherwise opaque) header bar */
[data-testid="stHeader"] {{
    background: transparent !important;
}}

/* Falling petals: above the trees, below the text, never clickable */
.ik-petals {{
    position: fixed;
    inset: 0;
    overflow: hidden;
    pointer-events: none;
    z-index: -1;
}}
.ik-petals span {{
    position: absolute;
    left: var(--x);
    top: var(--y);
    width: var(--w);
    height: var(--h);
    background: var(--c);
    border-radius: 50%;
    opacity: 0.8;
    transform: rotate(var(--r));
    box-shadow: 0 0 1px rgba(232, 138, 166, 0.35);
}}
/* Reduced motion: just a few still petals */
.ik-petals span:nth-child(n+7) {{ display: none; }}

@media (prefers-reduced-motion: no-preference) {{
    .ik-petals span,
    .ik-petals span:nth-child(n+7) {{
        display: block;
        top: 0;
        animation: ik-fall var(--d) ease-in-out var(--delay) infinite;
    }}
    @keyframes ik-fall {{
        0%   {{ transform: translate3d(0, -8vh, 0) rotate(var(--r)); }}
        25%  {{ transform: translate3d(var(--sway), 22vh, 0) rotate(calc(var(--r) + 90deg)); }}
        50%  {{ transform: translate3d(calc(var(--sway) * -0.6), 50vh, 0) rotate(calc(var(--r) + 180deg)); }}
        75%  {{ transform: translate3d(calc(var(--sway) * 0.8), 80vh, 0) rotate(calc(var(--r) + 270deg)); }}
        100% {{ transform: translate3d(0, 112vh, 0) rotate(calc(var(--r) + 360deg)); }}
    }}
}}
</style>
{falling_petals_html()}
""", unsafe_allow_html=True)


# Cute butterfly that rests on the last "I" of the wordmark (original drawing; wings fold gently, antennae sway)
BUTTERFLY_SVG = (
    "<svg class='ik-butterfly' viewBox='0 0 64 52' aria-hidden='true'>"
    "<defs><linearGradient id='bfWing' x1='0' y1='0' x2='1' y2='1'>"
    "<stop offset='0' stop-color='#B0E0E6'/><stop offset='1' stop-color='#A9C8E6'/></linearGradient></defs>"
    # Left wings (upper + lower) with pink inner patches and white spots
    "<g class='bf-wing-l'>"
    "<path d='M31 27C24 11 9 4 4.5 13.5C1.5 21 12 30 31 29Z' fill='url(#bfWing)' stroke='#8CB4D6' stroke-width='0.8'/>"
    "<path d='M31 30C22 31 10.5 36 13 43.5C15.5 50 26 45 31 33Z' fill='url(#bfWing)' stroke='#8CB4D6' stroke-width='0.8'/>"
    "<ellipse cx='18' cy='18' rx='6' ry='4.4' transform='rotate(-22 18 18)' fill='#F7C6D4' opacity='0.85'/>"
    "<ellipse cx='21' cy='38.5' rx='3.8' ry='3' fill='#F7C6D4' opacity='0.85'/>"
    "<circle cx='9.5' cy='14' r='1.9' fill='#FFFFFF'/><circle cx='13.5' cy='9.8' r='1.2' fill='#FFFFFF'/>"
    "<circle cx='16.5' cy='42.5' r='1.3' fill='#FFFFFF'/></g>"
    # Right wings (mirror image)
    "<g class='bf-wing-r'>"
    "<path d='M33 27C40 11 55 4 59.5 13.5C62.5 21 52 30 33 29Z' fill='url(#bfWing)' stroke='#8CB4D6' stroke-width='0.8'/>"
    "<path d='M33 30C42 31 53.5 36 51 43.5C48.5 50 38 45 33 33Z' fill='url(#bfWing)' stroke='#8CB4D6' stroke-width='0.8'/>"
    "<ellipse cx='46' cy='18' rx='6' ry='4.4' transform='rotate(22 46 18)' fill='#F7C6D4' opacity='0.85'/>"
    "<ellipse cx='43' cy='38.5' rx='3.8' ry='3' fill='#F7C6D4' opacity='0.85'/>"
    "<circle cx='54.5' cy='14' r='1.9' fill='#FFFFFF'/><circle cx='50.5' cy='9.8' r='1.2' fill='#FFFFFF'/>"
    "<circle cx='47.5' cy='42.5' r='1.3' fill='#FFFFFF'/></g>"
    # Curly antennae with little dot tips
    "<g class='bf-antennae' fill='none' stroke='#5A7A99' stroke-width='1' stroke-linecap='round'>"
    "<path d='M30.6 17C29 11.5 25.5 8.5 23.6 9.6C22.4 10.4 23.3 12.1 24.6 11.3'/>"
    "<path d='M33.4 17C35 11.5 38.5 8.5 40.4 9.6C41.6 10.4 40.7 12.1 39.4 11.3'/>"
    "<circle cx='24.6' cy='11.3' r='1.2' fill='#5A7A99' stroke='none'/>"
    "<circle cx='39.4' cy='11.3' r='1.2' fill='#5A7A99' stroke='none'/></g>"
    # Small round body and head with dot eyes and blushing cheeks
    "<ellipse cx='32' cy='33' rx='3.3' ry='9' fill='#5A7A99'/>"
    "<circle cx='32' cy='21.5' r='5' fill='#5A7A99'/>"
    "<circle cx='30.2' cy='21' r='0.95' fill='#FFFFFF'/><circle cx='33.8' cy='21' r='0.95' fill='#FFFFFF'/>"
    "<ellipse cx='29.1' cy='23.4' rx='1.2' ry='0.7' fill='#F7C6D4'/>"
    "<ellipse cx='34.9' cy='23.4' rx='1.2' ry='0.7' fill='#F7C6D4'/>"
    "</svg>"
)


# ================================
# 💬 Session State
# ================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "last_intent" not in st.session_state:
    st.session_state.last_intent = None

# User messages sent in this browser session; "New conversation" does not reset it
if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0

# Flag to clear the input textbox safely (set before widget creation)
if "clear_input" not in st.session_state:
    st.session_state.clear_input = False


# ================================
# 🔀 Support / Reflect mode text
# ================================
MODE_CARDS = {
    "Support": {
        "tagline": "Let's make today a little lighter.",
        "body": "Warm words, gentle coping ideas, and a steady presence for when everything feels like a lot.",
        # (section label, lines, CSS class used to hide it on short screens)
        "sections": [
            ("What you'll get", ["A kind first response", "One or two small things to try",
                                 "A calming idea, only if it helps"], "ik-sec-main"),
            ("Good for", ["A rough day", "Racing thoughts", "Feeling stretched thin"], "ik-sec-goodfor"),
        ],
        "try": "I had a rough day.",
        "small": "Comfort · Calm · Coping ideas",
    },
    "Reflect": {
        "tagline": "Hear your own voice again.",
        "body": "No advice, no pressure. Just a quiet space and one good question to help you find what matters to you.",
        "sections": [
            ("How it works", ["1. Say what's on your mind", "2. I reflect back what I hear",
                              "3. You decide what's true for you"], "ik-sec-main"),
            ("Good for", ["A big decision", "Mixed feelings", "Thinking out loud"], "ik-sec-goodfor"),
            ("I won't", ["decide for you, hand you a to-do list, or steer you anywhere."], "ik-sec-wont"),
        ],
        "try": "I can't decide what to do.",
        "small": "Listen · Pause · Reflect",
    },
}


def mode_card_html(mode_name, selected):
    """One display-only side card. The highlighted card is the selected mode."""
    card = MODE_CARDS[mode_name]
    sections = "".join(
        f'<div class="ik-sec {css_class}"><div class="ik-card-label">{label}</div>'
        + "".join(f'<div class="ik-card-line">{line}</div>' for line in lines)
        + "</div>"
        for label, lines, css_class in card["sections"]
    )
    return (
        f'<div class="ik-card{" selected" if selected else ""}">'
        f'<div class="ik-card-title">{mode_name}</div>'
        f'<div class="ik-card-tagline">{card["tagline"]}</div>'
        f'<div class="ik-card-body">{card["body"]}</div>'
        f"{sections}"
        f'<div class="ik-card-try">Try saying: <em>"{card["try"]}"</em></div>'
        f'<div class="ik-card-small">{card["small"]}</div>'
        "</div>"
    )


# One-line caption shown under the slider when the side cards are hidden (under 1200px)
MODE_CAPTIONS = {
    "Support": "Comfort and coping ideas",
    "Reflect": "I listen and ask questions, no advice",
}


# ================================
# Helper: Turn a chat message into safe HTML for a bubble
# ================================
import html
import re

MARKDOWN_LINK = re.compile(r'\[([^\]]+)\]\((https?://[^\s)]+)\)')
PLAIN_URL = re.compile(r'https?://[^\s<>"\'\]\)]+')
BOLD = re.compile(r'\*\*(.+?)\*\*')


def render_message_html(text):
    """
    Markdown links [text](url) become clickable text, plain URLs become links,
    **bold** becomes bold and line breaks are kept. Everything else is escaped,
    so a message can never inject its own HTML into the page.
    """
    links = []

    def keep_link(href, label):
        links.append(
            f'<a href="{html.escape(href, quote=True)}" target="_blank" rel="noopener">{label}</a>'
        )
        return f"\x00{len(links) - 1}\x00"  # placeholder, swapped back in at the end

    # 1. Markdown links first, so their URL is not turned into a second link
    text = MARKDOWN_LINK.sub(lambda m: keep_link(m.group(2), html.escape(m.group(1))), text)

    # 2. Remaining plain URLs (trailing punctuation stays outside the link)
    def plain(m):
        url = m.group(0).rstrip(".,;:!?")
        return keep_link(url, html.escape(url)) + m.group(0)[len(url):]
    text = PLAIN_URL.sub(plain, text)

    # 3. Escape everything else, then bold and line breaks
    text = html.escape(text)
    text = BOLD.sub(r"<strong>\1</strong>", text)
    text = text.replace("\n", "<br>")

    # 4. Put the links back
    return re.sub(r"\x00(\d+)\x00", lambda m: links[int(m.group(1))], text)


# ================================
# 🪧 Side cards (display only; fixed to the screen on wide screens, hidden under 1200px)
# Rendered before the panel, so the disclaimer stays the very last thing on the page. The slider below
# stores its value in st.session_state, so we already know the selected mode here.
# ================================
current_mode = st.session_state.get("help_mode", "Support")
for key, mode_name in (("side_left", "Support"), ("side_right", "Reflect")):
    with st.container(key=key):
        st.markdown(mode_card_html(mode_name, current_mode == mode_name), unsafe_allow_html=True)


# ================================
# 🧭 Centre column: everything else, on the frosted panel
# ================================
with st.container(key="center_panel"):

    # ---------- Header ----------
    st.markdown(
        '<div class="ik-header">'
        f'<div class="ik-wordmark">Ikigai{BUTTERFLY_SVG}</div>'
        '<div class="ik-tagline">Your mind. Your meaning. Your way.</div>'
        '<div class="ik-subcaption">Your mental wellness companion powered by AI</div>'
        '</div>',
        unsafe_allow_html=True
    )

    # ---------- Mode slider: "Support" | slider | "Reflect"; wrap=False keeps it on one line on phones ----------
    left, middle, right = st.columns([1, 3, 1], vertical_alignment="center", wrap=False)

    with middle:
        # Passed to wellness_chat as mode="support" or mode="reflect"
        help_mode = st.select_slider(
            "How would you like me to help?",
            options=["Support", "Reflect"],
            value="Support",
            key="help_mode",
            label_visibility="collapsed",
        )

    # Static words on both sides; the selected one is bold navy, the other muted blue
    # (filled in after the slider so we know which one is selected)
    for column, word, side in ((left, "Support", "left"), (right, "Reflect", "right")):
        selected = " selected" if help_mode == word else ""
        column.markdown(f'<div class="ik-mode-word {side}{selected}">{word}</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="ik-mode-caption">{MODE_CAPTIONS[help_mode]}</div>', unsafe_allow_html=True)

    # ---------- Affirmation ----------
    st.markdown(
        '<div class="ik-affirmation">'
        "Today's affirmation: You are allowed to pause, breathe, and take things one step at a time."
        "</div>",
        unsafe_allow_html=True,
    )

    # ---------- Chat ----------
    if st.session_state.messages:
        chat_html = '<div class="chat-container">'

        for msg, role in st.session_state.messages:
            bubble_class = "chat-bubble-user" if role == "user" else "chat-bubble-bot"
            chat_html += f'<div class="{bubble_class}">{render_message_html(msg)}</div>'

        chat_html += '</div>'

        st.markdown(chat_html, unsafe_allow_html=True)

    else:
        st.markdown('<p class="ik-empty-chat">Start anywhere. I\'m listening.</p>', unsafe_allow_html=True)

    # ---------- User input (with the butterfly resting on the box) ----------
    # If requested, clear the input value before creating the widget
    if st.session_state.get("clear_input", False):
        st.session_state["input_box"] = ""
        st.session_state["clear_input"] = False

    user_input = st.text_area(
        "Your message",
        placeholder="What's on your mind today?",
        height=110,
        key="input_box",
        label_visibility="collapsed"
    )

    # Soft per-session cap: after MAX_MESSAGES, a kind note and Send is disabled
    limit_reached = st.session_state.user_message_count >= MAX_MESSAGES
    if limit_reached:
        st.markdown(f'<p class="ik-empty-chat">{LIMIT_NOTE}</p>', unsafe_allow_html=True)

    # Button row: Send on the left, "New conversation" on the right, both 168 x 44 px
    with st.container(key="button_row", horizontal=True, horizontal_alignment="distribute",
                      vertical_alignment="center", wrap=False):
        send_button = st.button("Send", type="primary", key="send_button", width=168, disabled=limit_reached)
        if st.button("New conversation", key="new_conversation", width=168):
            st.session_state.messages = []
            st.session_state.chat_history = []
            st.session_state.last_intent = None
            reset_attack_memory()  # Reset security tracking
            st.rerun()

    # ---------- Handle Send ----------
    if send_button and user_input.strip() and not limit_reached:

        # Add user message to UI chat
        st.session_state.messages.append((user_input, "user"))
        st.session_state.user_message_count += 1

        # Get bot response WITH CONVERSATION HISTORY (no survey data)
        with st.spinner("Responding with care..."):
            try:
                intent, reply, crisis, updated_history = wellness_chat(
                    user_input,
                    st.session_state.chat_history,
                    survey_data=None,
                    mode=help_mode.lower()
                )
            except Exception as error:
                # Rate limit, bad key, timeout...: log only the error type (never the message, which
                # could include part of a key), and show a gentle reply instead of a stack trace
                logging.getLogger("ikigai").warning("wellness_chat failed: %s", type(error).__name__)
                updated_history = st.session_state.chat_history     # keep the history unchanged
                if is_crisis_text(normalize_quotes(user_input.lower())):
                    # Crisis support never depends on the model being reachable
                    intent, reply, crisis = "crisis", CRISIS_REPLY, True
                else:
                    intent, reply, crisis = "unavailable", CONNECTION_TROUBLE, False

        # Update the LangChain chat history
        st.session_state.chat_history = updated_history

        # Add bot reply to UI chat
        st.session_state.messages.append((reply, "bot"))

        # Remember the intent for the "Under the hood" panel
        st.session_state.last_intent = intent

        # Request a clear of the input box on the next run (safe: before widget creation)
        st.session_state.clear_input = True

        if crisis:
            st.error(
                "💛 Your message shows signs of severe distress. "
                "Please reach out to someone you trust or contact a hotline immediately."
            )

        st.rerun()

    # ---------- Under the hood ----------
    with st.expander("Under the hood", expanded=False):
        st.caption(f"Messages in conversation: {len(st.session_state.messages)}")
        st.caption(f"Detected intent: {st.session_state.last_intent or '—'}")
        st.caption(f"Current mode: {help_mode.lower()}")

    # ---------- Footer ----------
    st.markdown("---")
    # "Built with" is the last line inside the white panel
    st.markdown(
        "<p class='ik-footer-small'>"
        "Built with "
        "<svg class='ik-heart' viewBox='0 0 24 24' role='img' aria-label='love'>"
        "<path d='M12 20.5s-7.4-4.5-9.5-9.1C1 8.2 3.1 4.5 6.8 4.5c2 0 3.5 1.1 5.2 3 1.7-1.9 3.2-3 5.2-3 3.7 0 5.8 3.7 4.3 6.9-2.1 4.6-9.5 9.1-9.5 9.1z' "
        "fill='#B0E0E6' stroke='#8CBFD6' stroke-width='1.4' stroke-linejoin='round'/></svg>"
        " using Streamlit, LangChain, LangGraph and an OpenAI-compatible LLM API."
        "</p>",
        unsafe_allow_html=True
    )


# ================================
# Disclaimer: outside the panel, the very last element on the page
# ================================
st.markdown(
    "<p class='ik-disclaimer'>"
    "Ikigai is not a therapist or a substitute for professional care. It is for adults. "
    "If you are in crisis, call or text 988 (US)."
    "</p>",
    unsafe_allow_html=True
)
