"""Builds files/Kobalt_Capability_Statement.pdf (one page, Letter).
Everything shown is drawn from the site's own project write-ups; the license / bonding / insurance
lines come from data/capability.json so nothing is invented. Re-run after editing that file."""
import json
from pathlib import Path
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

ROOT = Path(__file__).resolve().parent.parent
cfg = json.loads((ROOT / "data/capability.json").read_text())
COBALT, AMBER, CHAR, CONC, MUTE = HexColor("#1B3F73"), HexColor("#E8A33D"), HexColor("#21252B"), HexColor("#ECE9E2"), HexColor("#5B6472")
W, H = letter
M = 36

def style(size=9, lead=None, color=CHAR, bold=False):
    return ParagraphStyle("s", fontName="Helvetica-Bold" if bold else "Helvetica", fontSize=size, leading=lead or size * 1.33, textColor=color)

def para(c, html, x, y_top, width, st):
    p = Paragraph(html, st); _, h = p.wrap(width, 1000); p.drawOn(c, x, y_top - h); return y_top - h

def heading(c, text, x, y, width):
    y -= 0
    c.setFont("Helvetica-Bold", 10.5); c.setFillColor(COBALT); c.drawString(x, y, text.upper())
    c.setStrokeColor(AMBER); c.setLineWidth(2); c.line(x, y - 4, x + width, y - 4)
    return y - 20

out = ROOT / "files" / "Kobalt_Capability_Statement.pdf"
c = canvas.Canvas(str(out), pagesize=letter)
c.setTitle("Kobalt Construction Capability Statement"); c.setAuthor("Kobalt Construction Inc."); c.setSubject("Capability statement")

# ---- header band ----
c.setFillColor(COBALT); c.rect(0, H - 100, W, 100, fill=1, stroke=0)
logo_path = ROOT / "images/logo-hd.png"; lw, lh_ = Image.open(logo_path).size
lw_pt = 150; lh_pt = lw_pt * lh_ / lw
c.setFillColor(white); c.roundRect(M, H - 100 + (100 - lh_pt - 16) / 2, lw_pt + 16, lh_pt + 16, 6, fill=1, stroke=0)
c.drawImage(str(logo_path), M + 8, H - 100 + (100 - lh_pt - 16) / 2 + 8, width=lw_pt, height=lh_pt, mask="auto")
c.setFillColor(white); c.setFont("Helvetica-Bold", 23); c.drawString(M + lw_pt + 40, H - 50, "CAPABILITY STATEMENT")
c.setFillColor(AMBER); c.setFont("Helvetica-Bold", 11); c.drawString(M + lw_pt + 40, H - 70, "CONSTRUCTION  \u2022  SITEWORK SPECIALIST")
c.setFillColor(HexColor("#C9D6EA")); c.setFont("Helvetica", 9.5); c.drawString(M + lw_pt + 40, H - 86, "Tobyhanna, Pennsylvania")

# ---- contact strip ----
c.setFillColor(CONC); c.rect(0, H - 128, W, 28, fill=1, stroke=0)
c.setFillColor(CHAR); c.setFont("Helvetica-Bold", 8.5)
c.drawCentredString(W / 2, H - 118, "216 PA-196, Tobyhanna, PA 18466    |    570.895.4613    |    info@kobaltconstruction.com    |    kobaltconstruction.com")

# ---- left column ----
LX, LW = M, 332
y = H - 158
y = heading(c, "Company Overview", LX, y, LW)
y = para(c, f"Kobalt Construction is a Tobyhanna, Pennsylvania contractor serving commercial, public, and residential clients across the Poconos, Scranton, the Wyoming Valley, Hazleton, and the Lehigh Valley. With {cfg.get('years','15+')} years in business, our crews handle site work, concrete, and paving, and we manage projects from permitting through final walkthrough.", LX, y, LW, style(10, 14)) - 22
y = heading(c, "Core Capabilities", LX, y, LW)
caps = [("Site Work &amp; Excavation", "Demolition, clearing, earthwork, stormwater and erosion control, utilities, and retaining walls."),
        ("Concrete", "Foundations, slabs, curbing, sidewalks, and decorative concrete."),
        ("Paving", "Milling and repaving, new asphalt, curbing, and striping for lots, roads, and trails."),
        ("General Contracting", "Full project management from permitting through final walkthrough, with one point of contact."),
        ("Design &amp; Consultation", "Pre-construction planning, budgeting, and feasibility.")]
for name, text in caps:
    y = para(c, f"<b>{name}.</b> {text}", LX, y, LW, style(9.8, 13.2)) - 6.5
y -= 14
y = heading(c, "Selected Projects", LX, y, LW)
projects = [("Wawa, Plains Township", "Clearing, bulk excavation with engineered retaining walls, utilities, and on-site stone recycling."),
            ("AutoZone, Stroudsburg", "Demolition, two underground infiltration basins, earthwork, concrete, and paving, with Highway Occupancy Permit work."),
            ("Carbon County Emergency Training Center, Nesquehoning", "Land clearing, earthwork, and utilities on a 10-acre public safety training site."),
            ("Luzerne County Flood Authority", "Garage expansion sitework: demolition, earthwork, stormwater, a rain garden, and paving."),
            ("Hazleton Area School District", "Parking lot paving completed ahead of the start of the school year."),
            ("Weis Supermarkets, Mt. Pocono", "Phased cold-milling and repaving that kept the store accessible to customers."),
            ("Capouse Avenue Park, Scranton", "Site work for a $1.8 million park revitalization with a new splash pad and playground.")]
for name, text in projects:
    y = para(c, f"<b>{name}.</b> {text}", LX, y, LW, style(9.4, 12.6)) - 6

# ---- right column card (measured first so the card fits its content) ----
import io
RX, RW = 392, W - 392 - M
top = H - 150

def draw_right(cv):
    state = {"y": top - 10}
    def rhead(t, gap=0):
        state["y"] -= gap
        cv.setFont("Helvetica-Bold", 9.6); cv.setFillColor(COBALT); cv.drawString(RX, state["y"], t.upper()); state["y"] -= 14
    def rtext(html, size=9.2):
        state["y"] = para(cv, html, RX, state["y"], RW, style(size, size * 1.38)) - 4
    rhead("At a Glance")
    rtext("<b>Based in:</b> Tobyhanna, PA")
    rtext(f"<b>Years in business:</b> {cfg.get('years','15+')}")
    rtext("<b>Sectors:</b> Commercial, public, and residential")
    rtext("<b>Service area:</b> Poconos, Scranton and Lackawanna County, Wyoming Valley, Hazleton, and the Lehigh Valley")
    rhead("Credentials", 12)
    given = [(k, v) for k, v in (("License", cfg.get("license")), ("Bonding", cfg.get("bonding")), ("Insurance", cfg.get("insurance"))) if v]
    if given:
        for k, v in given: rtext(f"<b>{k}:</b> {v}")
    else:
        rtext("Licensing, bonding, and insurance documentation available on request.")
    for s_ in cfg.get("safety", []): rtext(f"<b>Safety:</b> {s_}")
    rhead("Notable Project Sites", 12)
    rtext("AutoZone (Stroudsburg, Wyoming)<br/>Wawa (Plains Township)<br/>Weis Supermarkets (Mt. Pocono)<br/>Lowe's (Mt. Pocono)")
    rhead("Public-Sector Projects", 12)
    rtext("Hazleton Area School District<br/>Pocono Mountain School District<br/>Carbon County<br/>Luzerne County Flood Authority<br/>Borough of Dallas<br/>Dickson City Borough<br/>Westfall Township")
    return state["y"]

end_y = draw_right(canvas.Canvas(io.BytesIO(), pagesize=letter))
c.setFillColor(CONC); c.roundRect(RX - 12, end_y - 6, RW + 24, (top + 8) - (end_y - 6), 8, fill=1, stroke=0)
draw_right(c)
assert y > 70 and end_y > 70, "content overflows into the footer"

# ---- footer ----
c.setFillColor(COBALT); c.rect(0, 0, W, 54, fill=1, stroke=0)
c.setFillColor(white); c.setFont("Helvetica-Bold", 11); c.drawString(M, 31, "Request a quote or project documentation")
c.setFont("Helvetica", 9.5); c.drawString(M, 16, "570.895.4613   |   info@kobaltconstruction.com   |   kobaltconstruction.com")
c.setFillColor(HexColor("#C9D6EA")); c.setFont("Helvetica", 8); c.drawRightString(W - M, 16, "Updated October 2026")
c.save()
print("wrote", out.relative_to(ROOT), round(out.stat().st_size / 1024), "KB")
