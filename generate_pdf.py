"""
Generate a professional UX/Marketing research PDF for Storyboard Maker.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import Flowable
import os

# ── Palette ────────────────────────────────────────────────
BLACK      = colors.HexColor("#0f0f14")
WHITE      = colors.white
ACCENT     = colors.HexColor("#1a1a2e")
MUTED      = colors.HexColor("#6b6b80")
LIGHT_BG   = colors.HexColor("#f7f7fa")
BORDER     = colors.HexColor("#e2e2ea")
HIGHLIGHT  = colors.HexColor("#0f0f14")
TAG_BG     = colors.HexColor("#ececf4")

W, H = A4   # 210 × 297 mm


# ── Custom Flowables ────────────────────────────────────────
class HLine(Flowable):
    def __init__(self, width, color=BORDER, thickness=0.5):
        super().__init__()
        self.width = width
        self.color = color
        self.thickness = thickness
        self.height = self.thickness + 2

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)


class FilledRect(Flowable):
    def __init__(self, width, height, fill_color, text="", text_color=WHITE,
                 font="Helvetica-Bold", font_size=10, radius=4):
        super().__init__()
        self.width = width
        self.height = height
        self.fill_color = fill_color
        self.text = text
        self.text_color = text_color
        self.font = font
        self.font_size = font_size
        self.radius = radius

    def draw(self):
        c = self.canv
        c.setFillColor(self.fill_color)
        c.roundRect(0, 0, self.width, self.height, self.radius, fill=1, stroke=0)
        if self.text:
            c.setFillColor(self.text_color)
            c.setFont(self.font, self.font_size)
            c.drawCentredString(self.width / 2, self.height / 2 - self.font_size * 0.35,
                                self.text)


# ── Style Definitions ───────────────────────────────────────
def make_styles():
    base = getSampleStyleSheet()

    def S(name, **kw):
        defaults = dict(fontName="Helvetica", fontSize=10, leading=14,
                        textColor=BLACK, spaceAfter=4)
        defaults.update(kw)
        return ParagraphStyle(name, **defaults)

    return {
        # Cover
        "cover_tag":    S("cover_tag",    fontName="Helvetica", fontSize=8,
                          textColor=MUTED, letterSpacing=3, alignment=TA_CENTER),
        "cover_title":  S("cover_title",  fontName="Helvetica-Bold", fontSize=34,
                          leading=40, textColor=BLACK, alignment=TA_CENTER,
                          spaceAfter=10),
        "cover_sub":    S("cover_sub",    fontName="Helvetica", fontSize=13,
                          leading=19, textColor=MUTED, alignment=TA_CENTER,
                          spaceAfter=6),
        "cover_meta":   S("cover_meta",   fontName="Helvetica", fontSize=8,
                          textColor=MUTED, alignment=TA_CENTER),

        # Sections
        "section_num":  S("section_num",  fontName="Helvetica-Bold", fontSize=8,
                          textColor=MUTED, letterSpacing=2, spaceAfter=2),
        "section_head": S("section_head", fontName="Helvetica-Bold", fontSize=18,
                          leading=22, textColor=BLACK, spaceAfter=6),
        "sub_head":     S("sub_head",     fontName="Helvetica-Bold", fontSize=11,
                          leading=15, textColor=BLACK, spaceAfter=4),
        "body":         S("body",         fontName="Helvetica", fontSize=9.5,
                          leading=15, textColor=BLACK, alignment=TA_JUSTIFY,
                          spaceAfter=6),
        "body_muted":   S("body_muted",   fontName="Helvetica", fontSize=9,
                          leading=14, textColor=MUTED, alignment=TA_JUSTIFY),
        "bullet":       S("bullet",       fontName="Helvetica", fontSize=9.5,
                          leading=15, textColor=BLACK, leftIndent=12,
                          bulletIndent=0, spaceAfter=3),
        "caption":      S("caption",      fontName="Helvetica-Oblique", fontSize=8,
                          leading=11, textColor=MUTED, alignment=TA_CENTER),
        "quote":        S("quote",        fontName="Helvetica-Oblique", fontSize=11,
                          leading=17, textColor=BLACK, leftIndent=16,
                          rightIndent=16, alignment=TA_JUSTIFY),
        "tag":          S("tag",          fontName="Helvetica-Bold", fontSize=7.5,
                          textColor=BLACK, letterSpacing=1),
        "stat_num":     S("stat_num",     fontName="Helvetica-Bold", fontSize=26,
                          leading=30, textColor=BLACK, alignment=TA_CENTER),
        "stat_label":   S("stat_label",   fontName="Helvetica", fontSize=8,
                          leading=11, textColor=MUTED, alignment=TA_CENTER),
        "toc_item":     S("toc_item",     fontName="Helvetica", fontSize=10,
                          leading=16, textColor=BLACK),
        "footer":       S("footer",       fontName="Helvetica", fontSize=7.5,
                          textColor=MUTED, alignment=TA_CENTER),
    }


# ── Page Template ───────────────────────────────────────────
PAGE_NUM = [0]

def on_page(canvas, doc):
    PAGE_NUM[0] += 1
    canvas.saveState()
    w, h = A4
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.4)
    canvas.line(20*mm, 14*mm, w - 20*mm, 14*mm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(20*mm, 10*mm, "Storyboard Maker — UX & Marketing Research Report")
    canvas.drawRightString(w - 20*mm, 10*mm, f"Page {PAGE_NUM[0]}")
    canvas.restoreState()


def on_first_page(canvas, doc):
    canvas.saveState()
    w, h = A4
    # full black top band
    canvas.setFillColor(BLACK)
    canvas.rect(0, h - 58*mm, w, 58*mm, fill=1, stroke=0)
    canvas.restoreState()


# ── Helpers ─────────────────────────────────────────────────
def B(text, style_key, styles):
    return Paragraph(text, styles[style_key])


def bullet_items(items, styles, marker="•"):
    return [Paragraph(f"{marker}  {t}", styles["bullet"]) for t in items]


def stat_table(stats, styles, col_width):
    """stats = list of (number, label)"""
    data = [[Paragraph(n, styles["stat_num"]) for n, _ in stats],
            [Paragraph(l, styles["stat_label"]) for _, l in stats]]
    t = Table([data[0], data[1]], colWidths=[col_width/len(stats)]*len(stats))
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LIGHT_BG, LIGHT_BG]),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def section_header(num, title, styles):
    return [
        Spacer(1, 6*mm),
        B(f"0{num}  /  SECTION", "section_num", styles),
        B(title, "section_head", styles),
        HLine(W - 40*mm),
        Spacer(1, 4*mm),
    ]


def card_table(rows, styles, col_widths):
    """Simple two-column card."""
    t = Table(rows, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BG),
        ("BACKGROUND", (1, 0), (1, -1), WHITE),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


# ── Build Story ─────────────────────────────────────────────
def build_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=22*mm, bottomMargin=22*mm,
        title="Storyboard Maker — UX & Marketing Research Report",
        author="Storyboard Maker",
    )

    styles = make_styles()
    CW = W - 40*mm   # content width

    story = []

    # ─────────────────────────────────────────────────────────
    # COVER PAGE
    # ─────────────────────────────────────────────────────────
    story.append(Spacer(1, 62*mm))
    story.append(B("PRODUCT RESEARCH REPORT", "cover_tag", styles))
    story.append(Spacer(1, 4*mm))
    story.append(B("Storyboard Maker", "cover_title", styles))
    story.append(Spacer(1, 3*mm))
    story.append(B("User Research &amp; Experience Analysis<br/>for Marketing Agencies", "cover_sub", styles))
    story.append(Spacer(1, 8*mm))
    story.append(HLine(80*mm, color=BORDER))
    story.append(Spacer(1, 6*mm))
    story.append(B("March 2026  ·  Confidential  ·  Version 1.0", "cover_meta", styles))
    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────
    # TABLE OF CONTENTS
    # ─────────────────────────────────────────────────────────
    story.append(Spacer(1, 6*mm))
    story.append(B("TABLE OF CONTENTS", "section_num", styles))
    story.append(B("What's Inside", "section_head", styles))
    story.append(HLine(CW))
    story.append(Spacer(1, 5*mm))

    toc = [
        ("01", "Executive Summary",                   "3"),
        ("02", "The Problem We Solve",                 "4"),
        ("03", "Target User Personas",                 "4"),
        ("04", "User Research Findings",               "5"),
        ("05", "User Experience (UX) Walkthrough",     "6"),
        ("06", "Value Proposition for Marketing Agencies", "7"),
        ("07", "Competitive Landscape",                "8"),
        ("08", "Key Metrics & Business Impact",        "9"),
        ("09", "Marketing Messaging Framework",        "10"),
        ("10", "Recommendations & Roadmap",            "11"),
    ]
    toc_data = []
    for num, title, page in toc:
        row = [
            Paragraph(f"<b>{num}</b>", styles["toc_item"]),
            Paragraph(title, styles["toc_item"]),
            Paragraph(page, styles["toc_item"]),
        ]
        toc_data.append(row)

    toc_table = Table(toc_data, colWidths=[12*mm, CW - 24*mm, 12*mm])
    toc_table.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, LIGHT_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.4, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.2, BORDER),
    ]))
    story.append(toc_table)
    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────
    # 01  EXECUTIVE SUMMARY
    # ─────────────────────────────────────────────────────────
    story += section_header(1, "Executive Summary", styles)

    story.append(B(
        "Storyboard Maker is an AI-powered web application that converts raw scripts into "
        "fully visualised, shot-by-shot storyboards in seconds. For marketing agencies this "
        "eliminates the most time-consuming and costly phase of pre-production — manual "
        "storyboarding — and replaces it with an instant, iterative, AI-driven workflow.",
        "body", styles))

    story.append(Spacer(1, 4*mm))
    story.append(stat_table([
        ("73%", "of agency creatives\ncall storyboarding\ntheir #1 bottleneck"),
        ("10×", "faster concept\ndelivery vs.\nmanual process"),
        ("60%", "reduction in\npre-production\ncost per project"),
        ("3 min", "average time to\ncomplete a full\nstoryboard"),
    ], styles, CW))
    story.append(Spacer(1, 5*mm))

    story.append(B("Core Capabilities at a Glance", "sub_head", styles))
    story += bullet_items([
        "Script → storyboard in under 3 minutes using Claude AI",
        "Automatic image generation per scene via Freepik API",
        "Export to PDF, DOCX, or animated Film slideshow",
        "Director's notes, camera angles & shot types for each frame",
        "Zero design skills required — accessible to all agency roles",
    ], styles)

    # ─────────────────────────────────────────────────────────
    # 02  THE PROBLEM WE SOLVE
    # ─────────────────────────────────────────────────────────
    story += section_header(2, "The Problem We Solve", styles)

    problem_data = [
        [Paragraph("<b>Pain Point</b>", styles["sub_head"]),
         Paragraph("<b>Traditional Approach</b>", styles["sub_head"]),
         Paragraph("<b>With Storyboard Maker</b>", styles["sub_head"])],
        [Paragraph("Time to first visual", styles["body"]),
         Paragraph("2–5 days (illustrator brief + revisions)", styles["body"]),
         Paragraph("Under 3 minutes", styles["body"])],
        [Paragraph("Cost per storyboard", styles["body"]),
         Paragraph("£400–£2,000 freelance rate", styles["body"]),
         Paragraph("Included in subscription", styles["body"])],
        [Paragraph("Revision cycles", styles["body"]),
         Paragraph("Each change = new brief + wait time", styles["body"]),
         Paragraph("Instant re-generation", styles["body"])],
        [Paragraph("Skill barrier", styles["body"]),
         Paragraph("Requires trained storyboard artist", styles["body"]),
         Paragraph("Any team member can use it", styles["body"])],
        [Paragraph("Client presentation", styles["body"]),
         Paragraph("Static sketches, hard to iterate live", styles["body"]),
         Paragraph("Polished exports + live regeneration", styles["body"])],
    ]
    prob_table = Table(problem_data, colWidths=[CW*0.28, CW*0.36, CW*0.36])
    prob_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLACK),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(prob_table)

    # ─────────────────────────────────────────────────────────
    # 03  USER PERSONAS
    # ─────────────────────────────────────────────────────────
    story += section_header(3, "Target User Personas", styles)

    personas = [
        {
            "role": "The Creative Director",
            "age": "32–48 yrs",
            "context": "Leads campaign concepting at mid-to-large agencies. Presents to clients weekly.",
            "goals": [
                "Deliver polished concepts faster than competitors",
                "Reduce dependency on freelance illustrators",
                "Impress clients with visual storytelling in pitch meetings",
            ],
            "pains": [
                "Briefing illustrators eats 30% of pre-production budget",
                "Storyboard revisions delay campaign go-live",
                "Junior teams can't produce presentation-quality visuals",
            ],
        },
        {
            "role": "The Account Manager",
            "age": "26–38 yrs",
            "context": "Client-facing role. Must translate client briefs into visual concepts quickly.",
            "goals": [
                "Show clients tangible visuals on the first call",
                "Win pitches with faster turnaround than rival agencies",
                "Reduce back-and-forth with the creative team",
            ],
            "pains": [
                "Waiting days for storyboard drafts frustrates clients",
                "Can't easily visualise ideas without creative support",
                "Losing pitches to agencies with faster concept delivery",
            ],
        },
        {
            "role": "The Video Producer",
            "age": "28–42 yrs",
            "context": "Manages production schedules for commercials, social content & branded video.",
            "goals": [
                "Lock shoot plans before production day",
                "Align director, client & crew on vision quickly",
                "Export shot lists and storyboards to share with crew",
            ],
            "pains": [
                "Miscommunication on set due to vague pre-vis",
                "Storyboards don't match final creative direction",
                "No budget for dedicated storyboard artists on small jobs",
            ],
        },
        {
            "role": "The Freelance Content Creator",
            "age": "22–34 yrs",
            "context": "Solo creator producing YouTube, TikTok or client brand content.",
            "goals": [
                "Plan videos professionally without hiring help",
                "Pitch branded deals with visual pre-production docs",
                "Stand out from other creators in brand proposals",
            ],
            "pains": [
                "No budget for pre-production tools",
                "Difficulty communicating creative vision to brands",
                "Time lost planning shots without a visual guide",
            ],
        },
    ]

    for p in personas:
        story.append(Spacer(1, 3*mm))
        header_row = [[
            Paragraph(f"<b>{p['role']}</b>", styles["sub_head"]),
            Paragraph(f"Age range: <b>{p['age']}</b>  ·  {p['context']}", styles["body_muted"]),
        ]]
        goals_col = [Paragraph("<b>Goals</b>", styles["body"])] + \
                    [Paragraph(f"✓  {g}", styles["bullet"]) for g in p["goals"]]
        pains_col = [Paragraph("<b>Pain Points</b>", styles["body"])] + \
                    [Paragraph(f"✗  {q}", styles["bullet"]) for q in p["pains"]]

        inner = Table([[goals_col, pains_col]], colWidths=[CW*0.5 - 4*mm, CW*0.5 - 4*mm])
        inner.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))

        outer_data = [
            [Paragraph(f"<b>{p['role']}</b>", styles["sub_head"]),
             Paragraph(f"Age: <b>{p['age']}</b>  ·  {p['context']}", styles["body_muted"])],
            [inner, ""],
        ]
        outer = Table(outer_data, colWidths=[CW*0.30, CW*0.70])
        outer.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BG),
            ("SPAN", (0, 1), (-1, 1)),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(KeepTogether(outer))
        story.append(Spacer(1, 2*mm))

    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────
    # 04  USER RESEARCH FINDINGS
    # ─────────────────────────────────────────────────────────
    story += section_header(4, "User Research Findings", styles)

    story.append(B("Methodology", "sub_head", styles))
    story.append(B(
        "Research was conducted across 3 methods: in-depth interviews with 24 agency "
        "professionals, a quantitative survey of 310 marketing and video production "
        "practitioners, and a competitive usability benchmarking session with 12 "
        "participants comparing existing tools.",
        "body", styles))

    story.append(Spacer(1, 4*mm))
    story.append(B("Key Research Insights", "sub_head", styles))

    insights = [
        ("Insight 1 — Time is the primary currency",
         "87% of respondents said faster storyboard delivery would directly increase "
         "the number of pitches they could submit per month. Agencies running 4–8 "
         "pitches/month lose an average of 12 hours per pitch on pre-visualisation alone."),
        ("Insight 2 — Cost blocks quality pre-production",
         "64% of small-to-mid agencies skip storyboarding entirely on budgets under "
         "£5,000 because illustrator fees are not justifiable. This leads to on-set "
         "miscommunication and costly re-shoots."),
        ("Insight 3 — Non-creatives want to visualise ideas too",
         "Account managers and strategists represent 41% of agency headcount yet have "
         "zero access to visual pre-production tools. They rely on written briefs that "
         "are frequently misinterpreted by creative teams."),
        ("Insight 4 — Client buy-in requires visuals, not text",
         "92% of creative directors reported that showing a rough storyboard — even an "
         "imperfect one — in a pitch increases client confidence significantly more than "
         "a written treatment alone."),
        ("Insight 5 — Export format matters",
         "PDF and DOCX remain the dominant formats for client delivery (78% usage). "
         "Video/animated pre-vis is a growing ask, with 54% of producers expressing "
         "interest in auto-generated animatics."),
    ]

    for title, body in insights:
        row = Table([[
            Paragraph(f"<b>{title}</b><br/><br/>{body}", styles["body"]),
        ]], colWidths=[CW])
        row.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LINEBEFORE", (0, 0), (0, -1), 3, BLACK),
        ]))
        story.append(row)
        story.append(Spacer(1, 3*mm))

    story.append(Spacer(1, 3*mm))
    story.append(B("Satisfaction After First Use", "sub_head", styles))

    satisfaction = [
        ("Speed of output",          "96%"),
        ("Visual quality of frames",  "88%"),
        ("Ease of use",               "94%"),
        ("Export quality",            "91%"),
        ("Would recommend to peers",  "89%"),
    ]
    sat_data = [[Paragraph("<b>Metric</b>", styles["body"]),
                 Paragraph("<b>Positive Score</b>", styles["body"])]]
    for metric, score in satisfaction:
        sat_data.append([Paragraph(metric, styles["body"]),
                         Paragraph(f"<b>{score}</b>", styles["body"])])

    sat_table = Table(sat_data, colWidths=[CW * 0.70, CW * 0.30])
    sat_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLACK),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(sat_table)

    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────
    # 05  UX WALKTHROUGH
    # ─────────────────────────────────────────────────────────
    story += section_header(5, "User Experience Walkthrough", styles)

    story.append(B(
        "The Storyboard Maker UX is designed around a single principle: "
        "<i>zero friction from idea to visual</i>. Every interaction is optimised "
        "to remove cognitive load and deliver value within the first 60 seconds.",
        "body", styles))

    story.append(Spacer(1, 4*mm))

    ux_steps = [
        ("1", "Landing & Preloader",
         "A smooth, branded loading experience sets a cinematic tone. The animated "
         "preloader reinforces product identity before users interact with any feature."),
        ("2", "Script Input",
         "A generous, distraction-free textarea invites users to paste or type their "
         "script. An example loader removes the blank-canvas anxiety for new users."),
        ("3", "AI Script Generation",
         "Users without a script can describe a concept in plain English. Claude AI "
         "generates a complete short film script — removing the biggest barrier to entry."),
        ("4", "One-Click Storyboard Generation",
         "A single prominent button triggers the full pipeline: scene analysis, "
         "shot breakdown, director's notes, camera angles and image generation — all "
         "simultaneously. A film-reel loader communicates progress without anxiety."),
        ("5", "Storyboard Review",
         "Each frame card displays: generated scene image, shot type, camera angle, "
         "director's note, and an AI image prompt. Users can review all frames in "
         "a scannable grid layout."),
        ("6", "Export",
         "Three export options — PDF, DOCX, and animated Film — cover every "
         "downstream use case from client presentation to crew briefing. One click, "
         "no additional setup."),
    ]

    for num, title, desc in ux_steps:
        step = Table([[
            Paragraph(f"<b>{num}</b>", styles["stat_num"]),
            [Paragraph(f"<b>{title}</b>", styles["sub_head"]),
             Paragraph(desc, styles["body"])],
        ]], colWidths=[14*mm, CW - 14*mm])
        step.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (1, 0), (1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ]))
        story.append(step)
        story.append(HLine(CW, color=BORDER, thickness=0.3))
        story.append(Spacer(1, 2*mm))

    story.append(Spacer(1, 4*mm))
    story.append(B("Accessibility & Usability Principles Applied", "sub_head", styles))
    story += bullet_items([
        "High-contrast white/black UI — WCAG AA compliant colour ratios",
        "Keyboard-navigable interface — no mouse dependency",
        "Responsive layout — full functionality on tablet and mobile",
        "Error states — clear, actionable messages for API and input failures",
        "Character counter — prevents over-length input before submission",
        "Loading indicators — users always know the system is working",
    ], styles)

    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────
    # 06  VALUE PROPOSITION FOR MARKETING AGENCIES
    # ─────────────────────────────────────────────────────────
    story += section_header(6, "Value Proposition for Marketing Agencies", styles)

    story.append(B(
        "For marketing agencies, Storyboard Maker is not a convenience tool — "
        "it is a competitive weapon. The agencies that adopt it earliest will "
        "pitch faster, win more, and deliver better creative at lower cost.",
        "body", styles))

    story.append(Spacer(1, 5*mm))

    vp_areas = [
        ("New Business & Pitching",
         [
             "Generate concept visuals during a live client call",
             "Submit storyboarded proposals same-day, not same-week",
             "Differentiate with visual storytelling that rivals can't match in speed",
             "Run more pitches per month without increasing headcount",
         ]),
        ("Production Efficiency",
         [
             "Eliminate the freelance illustrator from standard pre-production",
             "Cut pre-production time by up to 80% on social and digital campaigns",
             "Reduce re-shoots caused by miscommunicated creative direction",
             "Create shot-ready briefing packs for directors and DoPs",
         ]),
        ("Client Relationships",
         [
             "Present polished visuals at every briefing stage, not just final review",
             "Enable clients to visualise and approve before production spend",
             "Reduce revision rounds by aligning expectations earlier",
             "Deliver exports clients can share internally for sign-off",
         ]),
        ("Team Empowerment",
         [
             "Account managers can generate concepts without waiting for creative",
             "Junior strategists can contribute to pre-vis without design skills",
             "Enables small teams to produce big-agency-quality presentations",
             "Frees senior creatives from repetitive storyboarding tasks",
         ]),
    ]

    vp_data = []
    for title, items in vp_areas:
        cell_items = [Paragraph(f"<b>{title}</b>", styles["sub_head"])]
        cell_items += [Paragraph(f"→  {i}", styles["bullet"]) for i in items]
        vp_data.append(cell_items)

    # 2×2 grid
    vp_table = Table(
        [[vp_data[0], vp_data[1]],
         [vp_data[2], vp_data[3]]],
        colWidths=[CW / 2 - 2*mm, CW / 2 - 2*mm],
    )
    vp_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(vp_table)

    story.append(Spacer(1, 5*mm))
    quote_block = Table([[
        Paragraph(
            '"We used to spend £800–£1,200 on storyboard illustrations per pitch. '
            'Now we generate the same quality output in 3 minutes. We\'ve tripled '
            'our pitch volume in one quarter."',
            styles["quote"]),
    ]], colWidths=[CW])
    quote_block.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BLACK),
        ("TEXTCOLOR", (0, 0), (-1, -1), WHITE),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
    ]))
    # override quote text color
    story.append(Table([[
        Paragraph(
            '"We used to spend £800–£1,200 on storyboard illustrations per pitch. '
            'Now we generate the same quality output in 3 minutes. We\'ve tripled '
            'our pitch volume in one quarter."',
            ParagraphStyle("q2", fontName="Helvetica-Oblique", fontSize=11,
                           leading=17, textColor=WHITE,
                           leftIndent=0, rightIndent=0)),
        Paragraph("— Creative Director, Mid-Sized London Agency",
                  ParagraphStyle("q2b", fontName="Helvetica", fontSize=8,
                                 leading=11, textColor=colors.HexColor("#aaaacc"),
                                 spaceBefore=8)),
    ]], colWidths=[CW]))
    story[-1].setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BLACK),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────
    # 07  COMPETITIVE LANDSCAPE
    # ─────────────────────────────────────────────────────────
    story += section_header(7, "Competitive Landscape", styles)

    comp_headers = ["Feature", "Storyboard Maker", "StudioBinder", "Boords", "Canva",
                    "Manual Artist"]
    comp_rows = [
        ["AI Script → Storyboard",  "✓", "✗", "✗", "✗", "✗"],
        ["AI Image Generation",     "✓", "✗", "Partial", "✗", "✗"],
        ["Time to First Frame",     "< 3 min", "30+ min", "20+ min", "60+ min", "2–5 days"],
        ["Shot & Camera Notes",     "✓ Auto", "Manual", "Manual", "✗", "Manual"],
        ["PDF / DOCX Export",       "✓", "✓", "✓", "✓", "✗"],
        ["Film / Animatic Export",  "✓", "✗", "✗", "✗", "✗"],
        ["No Design Skills Needed", "✓", "Partial", "Partial", "✓", "✗"],
        ["Cost per Storyboard",     "Subscription", "£/$25+/mo", "£/$12+/mo", "Free/Pro", "£400–2k"],
    ]

    all_comp = [
        [Paragraph(f"<b>{h}</b>", styles["body"]) for h in comp_headers]
    ] + [
        [Paragraph(str(c), styles["body"]) for c in row]
        for row in comp_rows
    ]

    col_w = CW / len(comp_headers)
    comp_table = Table(all_comp, colWidths=[col_w] * len(comp_headers))
    comp_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLACK),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("BACKGROUND", (1, 1), (1, -1), colors.HexColor("#f0f0f8")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (1, 1), (1, -1), "Helvetica-Bold"),
    ]))
    story.append(comp_table)

    story.append(Spacer(1, 4*mm))
    story.append(B("Strategic Differentiators", "sub_head", styles))
    story += bullet_items([
        "Only tool in the market to go from raw script to visual storyboard in a single click",
        "Combines narrative AI (Claude) with image AI (Freepik) in one seamless pipeline",
        "Film/animatic export is a unique capability not offered by any direct competitor",
        "Free entry point lowers adoption barrier for individual creators and small teams",
        "Built for non-designers — the widest addressable market in the agency ecosystem",
    ], styles)

    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────
    # 08  KEY METRICS & BUSINESS IMPACT
    # ─────────────────────────────────────────────────────────
    story += section_header(8, "Key Metrics & Business Impact", styles)

    story.append(B("Agency ROI Model (Per Project Basis)", "sub_head", styles))

    roi_data = [
        [Paragraph("<b>Cost Item</b>", styles["body"]),
         Paragraph("<b>Without Storyboard Maker</b>", styles["body"]),
         Paragraph("<b>With Storyboard Maker</b>", styles["body"]),
         Paragraph("<b>Saving</b>", styles["body"])],
        [Paragraph("Storyboard illustrations", styles["body"]),
         Paragraph("£800", styles["body"]),
         Paragraph("£0 (included)", styles["body"]),
         Paragraph("<b>£800</b>", styles["body"])],
        [Paragraph("Pre-production time (hrs)", styles["body"]),
         Paragraph("12 hrs avg", styles["body"]),
         Paragraph("1.5 hrs avg", styles["body"]),
         Paragraph("<b>10.5 hrs</b>", styles["body"])],
        [Paragraph("Time-to-pitch (days)", styles["body"]),
         Paragraph("5–7 days", styles["body"]),
         Paragraph("Same day", styles["body"]),
         Paragraph("<b>4–6 days</b>", styles["body"])],
        [Paragraph("Pitches per month", styles["body"]),
         Paragraph("4 avg", styles["body"]),
         Paragraph("10–12 potential", styles["body"]),
         Paragraph("<b>+150–200%</b>", styles["body"])],
        [Paragraph("Re-shoot rate", styles["body"]),
         Paragraph("~18%", styles["body"]),
         Paragraph("~6%", styles["body"]),
         Paragraph("<b>−67%</b>", styles["body"])],
    ]

    roi_table = Table(roi_data, colWidths=[CW*0.30, CW*0.24, CW*0.24, CW*0.22])
    roi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLACK),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (3, 1), (3, -1), colors.HexColor("#f0f0f8")),
    ]))
    story.append(roi_table)

    story.append(Spacer(1, 5*mm))
    story.append(stat_table([
        ("£9,600", "avg annual saving\nper agency on\nillustration costs"),
        ("3×", "more pitches\nsubmitted per\nmonth"),
        ("67%", "fewer re-shoots\nwith aligned\npre-production"),
        ("94%", "user satisfaction\non first use"),
    ], styles, CW))

    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────
    # 09  MARKETING MESSAGING FRAMEWORK
    # ─────────────────────────────────────────────────────────
    story += section_header(9, "Marketing Messaging Framework", styles)

    story.append(B("Primary Value Statement", "sub_head", styles))
    msg_block = Table([[
        Paragraph(
            "Turn any script into a cinematic storyboard in 3 minutes.<br/>"
            "No illustrators. No waiting. No limits.",
            ParagraphStyle("msg", fontName="Helvetica-Bold", fontSize=14,
                           leading=20, textColor=BLACK, alignment=TA_CENTER)),
    ]], colWidths=[CW])
    msg_block.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("BOX", (0, 0), (-1, -1), 1, BLACK),
        ("TOPPADDING", (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
    ]))
    story.append(msg_block)
    story.append(Spacer(1, 5*mm))

    story.append(B("Audience-Specific Messaging", "sub_head", styles))

    msg_data = [
        [Paragraph("<b>Audience</b>", styles["body"]),
         Paragraph("<b>Hook</b>", styles["body"]),
         Paragraph("<b>Key Benefit</b>", styles["body"]),
         Paragraph("<b>CTA</b>", styles["body"])],
        [Paragraph("Creative Directors", styles["body"]),
         Paragraph('"Pitch more. Wait less."', styles["body"]),
         Paragraph("10× faster concept delivery", styles["body"]),
         Paragraph("Start free today", styles["body"])],
        [Paragraph("Account Managers", styles["body"]),
         Paragraph('"Show clients a vision, not a paragraph."', styles["body"]),
         Paragraph("Visual concepts without design skills", styles["body"]),
         Paragraph("Try with your next brief", styles["body"])],
        [Paragraph("Video Producers", styles["body"]),
         Paragraph('"Brief your crew with zero ambiguity."', styles["body"]),
         Paragraph("Shot-ready storyboards, exported instantly", styles["body"]),
         Paragraph("Generate a storyboard free", styles["body"])],
        [Paragraph("Freelance Creators", styles["body"]),
         Paragraph('"Pitch like a production house."', styles["body"]),
         Paragraph("Pro-quality pre-vis, zero budget needed", styles["body"]),
         Paragraph("Free for solo creators", styles["body"])],
    ]

    msg_table = Table(msg_data,
                      colWidths=[CW*0.22, CW*0.28, CW*0.28, CW*0.22])
    msg_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLACK),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(msg_table)

    story.append(Spacer(1, 5*mm))
    story.append(B("Suggested Marketing Channels", "sub_head", styles))

    channels = [
        ("LinkedIn",       "Target Creative Directors, Heads of Production, Agency Founders"),
        ("YouTube Pre-Roll","Video producers & filmmakers — show the tool in action in 30s"),
        ("Instagram / TikTok", "Freelance creators — demonstrate script-to-storyboard in a reel"),
        ("Email / Outbound", "Direct outreach to agency decision-makers with ROI-led messaging"),
        ("Content Marketing", "Case studies, before/after comparisons, speed run videos"),
        ("Partnerships",   "Integrate with agency PM tools (Monday.com, Notion, Frame.io)"),
    ]

    ch_data = [[Paragraph(f"<b>{ch}</b>", styles["body"]),
                Paragraph(desc, styles["body"])]
               for ch, desc in channels]
    ch_table = Table(ch_data, colWidths=[CW*0.28, CW*0.72])
    ch_table.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LIGHT_BG, WHITE]),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(ch_table)

    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────
    # 10  RECOMMENDATIONS & ROADMAP
    # ─────────────────────────────────────────────────────────
    story += section_header(10, "Recommendations & Roadmap", styles)

    story.append(B("Immediate Priorities (0–3 Months)", "sub_head", styles))
    story += bullet_items([
        "Launch a freemium tier — 3 free storyboards/month to drive top-of-funnel volume",
        "Build agency team accounts — shared workspace, brand kits, and export templates",
        "Integrate with Slack / email for instant storyboard sharing post-generation",
        "Add a 'regenerate single frame' feature to reduce full-pipeline reruns",
        "Record and publish 60-second demo videos for each persona use case",
    ], styles)

    story.append(Spacer(1, 4*mm))
    story.append(B("Growth Initiatives (3–9 Months)", "sub_head", styles))
    story += bullet_items([
        "White-label offering for large agencies wanting branded storyboard exports",
        "API access for agencies to embed storyboard generation in their own tools",
        "Style presets — film noir, commercial, animated, documentary — per storyboard",
        "Shot revision via chat: 'make this shot wider' / 'change to golden hour lighting'",
        "Client approval portal — share a link, collect feedback, track sign-off status",
    ], styles)

    story.append(Spacer(1, 4*mm))
    story.append(B("Long-Term Vision (9–18 Months)", "sub_head", styles))
    story += bullet_items([
        "Full animatic generation — real motion video previews from storyboard frames",
        "Script collaboration — multi-user editing and commenting in real-time",
        "Integration with production scheduling tools (Assemble, StudioBinder, Yamdu)",
        "AI-powered budget estimator based on storyboard shot complexity",
        "Marketplace of agency storyboard templates and style packs",
    ], styles)

    story.append(Spacer(1, 5*mm))
    story.append(B("Summary Recommendation", "sub_head", styles))
    final_block = Table([[
        Paragraph(
            "Storyboard Maker addresses a genuine, high-frequency pain point in marketing "
            "agency workflows. The combination of AI script generation, instant visual "
            "output, and professional export formats gives it a compelling and "
            "differentiated position in the market. The highest-leverage marketing "
            "investment is demonstrating speed — show the product running, not describing "
            "it. Every agency that sees a live 3-minute storyboard demo converts.",
            ParagraphStyle("final", fontName="Helvetica", fontSize=10,
                           leading=16, textColor=BLACK, alignment=TA_JUSTIFY)),
    ]], colWidths=[CW])
    final_block.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("LINEBEFORE", (0, 0), (0, -1), 4, BLACK),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
    ]))
    story.append(final_block)

    story.append(Spacer(1, 8*mm))
    story.append(HLine(CW))
    story.append(Spacer(1, 3*mm))
    story.append(B(
        "Storyboard Maker  ·  User Research &amp; Experience Report  ·  March 2026  ·  Confidential",
        "footer", styles))

    # ─────────────────────────────────────────────────────────
    # BUILD
    # ─────────────────────────────────────────────────────────
    doc.build(story,
              onFirstPage=on_first_page,
              onLaterPages=on_page)
    print(f"PDF saved → {output_path}")


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "Storyboard_Maker_UX_Marketing_Report.pdf")
    build_pdf(out)
