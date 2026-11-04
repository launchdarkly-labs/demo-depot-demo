#!/usr/bin/env python3
# Builds docs/setup-slide.pptx: the one-slide Demo Depot setup guide as editable text.
#   uv run --with python-pptx docs/build-setup-slide.py
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

OUT = Path(__file__).with_name("setup-slide.pptx")

BG, PANEL, LINE = RGBColor(0x12, 0x14, 0x1C), RGBColor(0x1A, 0x1D, 0x28), RGBColor(0x2A, 0x2E, 0x3D)
INK, MUTED, CODE_BG = RGBColor(0xF5, 0xF6, 0xFA), RGBColor(0xAA, 0xB0, 0xC4), RGBColor(0x0D, 0x0F, 0x15)
ACCENT, ACCENT2, EYEBROW = RGBColor(0x40, 0x5B, 0xFF), RGBColor(0x7B, 0x42, 0xBC), RGBColor(0x7D, 0x90, 0xFF)
GREEN, COMMENT = RGBColor(0x3D, 0xDC, 0x84), RGBColor(0x6F, 0x77, 0x8F)
SANS, MONO = "Helvetica Neue", "Menlo"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
slide = prs.slides.add_slide(prs.slide_layouts[6])
slide.background.fill.solid()
slide.background.fill.fore_color.rgb = BG


def rect(x, y, w, h, fill, line=None, radius=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE, x, y, w, h)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    if line:
        shape.line.color.rgb = line
        shape.line.width = Pt(0.75)
    else:
        shape.line.fill.background()
    if radius:
        shape.adjustments[0] = radius
    shape.shadow.inherit = False
    return shape


def text(x, y, w, h, runs_per_para, size=11, color=INK, font=SANS, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, spacing=1.15, space_after=4, bullets=False):
    """runs_per_para: list of paragraphs; each paragraph is a list of (text, {overrides}) runs or a str."""
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05)
    tf.margin_top = tf.margin_bottom = Inches(0.03)
    first = True
    for para in runs_per_para:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = align
        p.line_spacing = spacing
        p.space_after = Pt(space_after)
        runs = [(para, {})] if isinstance(para, str) else [(r, {}) if isinstance(r, str) else r for r in para]
        if bullets:
            runs = [("•  ", {"color": MUTED})] + list(runs)
        for t, o in runs:
            r = p.add_run()
            r.text = t
            f = r.font
            f.name = o.get("font", font)
            f.size = Pt(o.get("size", size))
            f.bold = o.get("bold", bold)
            f.color.rgb = o.get("color", color)
    return box


def code(x, y, w, h, lines, size=9.5):
    rect(x, y, w, h, CODE_BG, LINE, radius=0.06)
    paras = []
    for ln in lines:
        if isinstance(ln, str):
            paras.append([(ln, {})])
        else:
            paras.append(ln)
    text(x + Inches(0.08), y + Inches(0.04), w - Inches(0.16), h - Inches(0.08), paras,
         size=size, font=MONO, color=RGBColor(0xE8, 0xEB, 0xF5), spacing=1.1, space_after=1)


# Accent bar, eyebrow, title, subtitle
rect(0, 0, Inches(0.1), prs.slide_height, ACCENT)
L = Inches(0.6)
text(L, Inches(0.35), Inches(6), Inches(0.3), [[("DEMO DEPOT", {"bold": True, "color": EYEBROW})]], size=11)
text(L, Inches(0.6), Inches(12), Inches(0.7), [[("From a repo to the catalog in one tag", {"bold": True})]], size=32)
text(L, Inches(1.25), Inches(12), Inches(0.4),
     ["Install once, let Claude make the repo depot-ready, publish by tagging. Every launch gets its own LaunchDarkly project."],
     size=14, color=MUTED)

# Three columns
TOP, H, GAP = Inches(1.85), Inches(4.85), Inches(0.2)
W = (Inches(13.333) - L - Inches(0.6) - 2 * GAP) / 3
PAD = Inches(0.2)


def column(i, title, when):
    x = L + i * (W + GAP)
    rect(x, TOP, W, H, PANEL, LINE, radius=0.04)
    circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, x + PAD, TOP + PAD, Inches(0.36), Inches(0.36))
    circ.fill.solid(); circ.fill.fore_color.rgb = ACCENT; circ.line.fill.background(); circ.shadow.inherit = False
    tf = circ.text_frame; tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = str(i + 1); r.font.bold = True; r.font.size = Pt(13); r.font.color.rgb = INK; r.font.name = SANS
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    text(x + PAD + Inches(0.45), TOP + PAD - Inches(0.04), W - PAD * 2 - Inches(0.45), Inches(0.45),
         [[(title, {"bold": True})]], size=15, anchor=MSO_ANCHOR.MIDDLE)
    text(x + PAD + Inches(0.45), TOP + PAD + Inches(0.36), W - PAD * 2 - Inches(0.45), Inches(0.3), [when], size=9, color=MUTED)
    return x + PAD, TOP + PAD + Inches(0.72), W - PAD * 2  # content origin and width


def inline(s):
    return (s, {"font": MONO, "size": 10})


# Column 1
x, y, w = column(0, "Install once", "Per machine, about five minutes")
text(x, y, w, Inches(0.3), [[("Claude Code plugin", {"bold": True}), (" (skill + MCP server)", {})]], size=11, bullets=True)
code(x, y + Inches(0.32), w, Inches(0.62), ["/plugin marketplace add launchdarkly-labs/demo-depot-publish", "/plugin install demo-depot@demo-depot"])
text(x, y + Inches(1.02), w, Inches(0.3), [[("The ", {"bold": True}), inline("ddu"), (" CLI", {"bold": True}), (" (Node 20+, Docker for ", {}), inline("ddu run"), (")", {})]], size=11, bullets=True)
code(x, y + Inches(1.34), w, Inches(0.78), ["npm i -g --allow-remote=root https://github.com/launchdarkly-labs/demo-depot-publish/releases/latest/download/demo-depot-cli.tgz"])
text(x, y + Inches(2.2), w, Inches(0.9),
     [[("Tokens", {"bold": True}), (", in the portal under Settings: save your ", {}), ("LaunchDarkly API token", {"bold": True}),
       (" (launches run as you), create a ", {}), ("Demo Depot API token", {"bold": True}), (", sign the CLI in", {})]], size=11, bullets=True)
code(x, y + Inches(3.05), w, Inches(0.62), [[("ddu auth login", {}), ("   # paste the ddp. token", {"color": COMMENT})], "ddu auth status"])

# Column 2
x, y, w = column(1, "Make the repo depot-ready", "Per demo, in Claude Code, inside the repo")
text(x, y, w, Inches(0.3), ["Ask Claude:"], size=11)
code(x, y + Inches(0.3), w, Inches(0.62), [[("Using the demo-depot skill, make this repo ready for Demo Depot.", {"color": GREEN})]])
text(x, y + Inches(1.0), w, Inches(0.3), ["The skill inventories the code and adds:"], size=11)
text(x, y + Inches(1.3), w, Inches(1.3), [
    [inline("demo.yaml"), (" manifest: container, port, health check, parameters", {})],
    [inline("ld/seed.json"), (": the flags every launch starts with", {})],
    [inline("DEMO.md"), (" talk track, cover image, publish workflow", {})],
], size=11, bullets=True)
text(x, y + Inches(2.55), w, Inches(0.3), ["Then check it yourself:"], size=11)
code(x, y + Inches(2.85), w, Inches(0.62), [
    [("ddu validate .", {}), ("   # the checks the depot runs", {"color": COMMENT})],
    [("ddu run", {}), ("          # local run, depot layout", {"color": COMMENT})],
])

# Column 3
x, y, w = column(2, "Publish and launch", "Repo in launchdarkly-labs or launchdarkly-demos")
code(x, y, w, Inches(0.62), ['git commit -am "Depot-ready" && git push', "git tag v0.1.0 && git push origin v0.1.0"])
text(x, y + Inches(0.72), w, Inches(1.9), [
    ["GitHub Actions builds the arm64 image and uploads the manifest and seed"],
    [("The depot ", {}), ("verifies", {"bold": True}), (" the version by launching it once (2 to 5 minutes), then DMs you on Slack", {})],
    [("Any SE opens the catalog, clicks ", {}), ("Launch", {"bold": True}), (", and gets their own URL and LaunchDarkly project", {})],
], size=11, bullets=True)
text(x, y + Inches(2.6), w, Inches(0.5), [[("New version? Bump the tag: ", {}), inline("v0.1.1"), (". Done for the day? ", {}), ("Tear down", {"bold": True}), (" from My Demos.", {})]], size=11)
text(x, y + Inches(3.1), w, Inches(0.6), [[("Or let Claude do all of it over MCP: ", {}), ('"publish this and launch it when it\'s verified."', {"color": GREEN})]], size=11)

# Footer
fy = Inches(6.95)
slide.shapes.add_connector(1, L, fy - Inches(0.1), Inches(13.333) - Inches(0.6), fy - Inches(0.1)).line.color.rgb = LINE
text(L, fy, Inches(8), Inches(0.3), [[("Portal ", {"bold": True}), ("demodepot.launchdarklydemos.com   ·   ", {"color": MUTED}),
                                      ("Tools and docs ", {"bold": True}), ("github.com/launchdarkly-labs/demo-depot-publish", {"color": MUTED})]], size=10)
text(Inches(8.5), fy, Inches(4.23), Inches(0.3), [[("Example ", {"bold": True}), ("github.com/launchdarkly-labs/demo-depot-demo", {"color": MUTED})]],
     size=10, align=PP_ALIGN.RIGHT)

prs.save(OUT)
print(f"wrote {OUT}")
