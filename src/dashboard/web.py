"""
Web Dashboard: View scripts in browser + download PDF.
Run with: python -m src.dashboard.web
"""
import io
import sys
sys.path.insert(0, ".")

from flask import Flask, render_template_string, send_file
from src.utils.database import init_db
from src.scripts.manager import ScriptManager
from src.affiliate.tracker import AffiliateTracker

app = Flask(__name__)
init_db()
sm = ScriptManager()
af = AffiliateTracker()

# ═══════════════════════════════════════════════════
#  STYLE CONFIG
# ═══════════════════════════════════════════════════
STYLE_MAP = {
    1: ("Problem-Solution", "#DC3232"),
    2: ("Storytelling", "#3282DC"),
    3: ("Edukasi", "#28A046"),
    4: ("Review Jujur", "#C88200"),
    5: ("POV / Trending", "#9632C8"),
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TikTok Script Dashboard</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f0f0f; color: #e8e8e8; }
  .header { background: linear-gradient(135deg, #1a1a2e, #16213e); padding: 30px 40px; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #fe2c55; }
  .header h1 { font-size: 24px; color: #fff; }
  .header h1 span { color: #fe2c55; }
  .btn-download { background: #fe2c55; color: #fff; border: none; padding: 12px 28px; border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; text-decoration: none; transition: all 0.2s; }
  .btn-download:hover { background: #e8274d; transform: translateY(-1px); box-shadow: 0 4px 15px rgba(254,44,85,0.4); }

  .product-bar { background: #1a1a1a; padding: 20px 40px; display: flex; gap: 30px; flex-wrap: wrap; border-bottom: 1px solid #2a2a2a; }
  .product-bar .item { display: flex; flex-direction: column; }
  .product-bar .label { font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 1px; }
  .product-bar .value { font-size: 16px; font-weight: 600; color: #fff; margin-top: 2px; }
  .product-bar .value.price { color: #25f4ee; }
  .product-bar .value.commission { color: #fe2c55; }

  .container { max-width: 900px; margin: 30px auto; padding: 0 20px; }
  .script-card { background: #1a1a1a; border-radius: 12px; margin-bottom: 24px; overflow: hidden; border: 1px solid #2a2a2a; transition: border-color 0.2s; }
  .script-card:hover { border-color: #444; }
  .script-badge { display: inline-block; padding: 4px 14px; color: #fff; font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; border-radius: 0 0 8px 0; }
  .script-header { padding: 20px 24px 12px; }
  .script-header h2 { font-size: 18px; color: #fff; margin-top: 10px; }
  .hook-box { margin: 0 24px; padding: 14px 18px; border-radius: 8px; font-size: 15px; font-style: italic; border-left: 3px solid; }
  .script-content { padding: 20px 24px; font-size: 13px; line-height: 1.8; white-space: pre-wrap; color: #ccc; }
  .script-content .action { color: #888; font-style: italic; font-size: 12px; }
  .cta-box { margin: 0 24px 20px; padding: 12px 18px; border-radius: 8px; color: #fff; font-weight: 600; font-size: 14px; text-align: center; }
  .tags { padding: 0 24px 16px; font-size: 12px; color: #666; }
  .notes { padding: 0 24px 20px; font-size: 12px; color: #555; font-style: italic; }

  .footer { text-align: center; padding: 40px; color: #444; font-size: 12px; }

  @media (max-width: 600px) {
    .header { padding: 20px; flex-direction: column; gap: 15px; }
    .product-bar { padding: 15px 20px; }
    .script-header, .script-content, .cta-box, .tags, .notes { padding-left: 16px; padding-right: 16px; }
    .hook-box { margin: 0 16px; }
  }
</style>
</head>
<body>

<div class="header">
  <h1><span>TikTok</span> Script Dashboard</h1>
  <a href="/download-pdf" class="btn-download">Download PDF</a>
</div>

{% if product %}
<div class="product-bar">
  <div class="item"><span class="label">Produk</span><span class="value">{{ product.name }}</span></div>
  <div class="item"><span class="label">Harga</span><span class="value price">Rp{{ "{:,.0f}".format(product.price) }}</span></div>
  <div class="item"><span class="label">Komisi</span><span class="value commission">{{ product.commission_rate }}% (Rp{{ "{:,.0f}".format(product.price * product.commission_rate / 100) }}/sale)</span></div>
  <div class="item"><span class="label">Total Script</span><span class="value">{{ scripts|length }}</span></div>
</div>
{% endif %}

<div class="container">
  {% for s in scripts %}
  {% set style = styles.get(loop.index, ("Script", "#666")) %}
  <div class="script-card">
    <div class="script-header">
      <span class="script-badge" style="background:{{ style[1] }}">{{ style[0] }}</span>
      <h2>Script #{{ loop.index }}: {{ s.title }}</h2>
    </div>

    <div class="hook-box" style="background:{{ style[1] }}15; border-color:{{ style[1] }}">
      "{{ s.hook }}"
    </div>

    <div class="script-content">
      {%- for line in s.content.strip().split('\n') %}
        {%- if line.strip().startswith('[ACTION:') %}
<span class="action">{{ line.strip() }}</span>
        {%- else %}
{{ line }}
        {%- endif %}
      {%- endfor %}
    </div>

    <div class="cta-box" style="background:{{ style[1] }}">{{ s.cta }}</div>

    <div class="tags">{{ s.tags.split(',')|map('trim')|map('regex_replace', '^', '#')|join(' ') if s.tags else '' }}</div>
    {% if s.notes %}<div class="notes">{{ s.notes }}</div>{% endif %}
  </div>
  {% endfor %}
</div>

<div class="footer">TikTok Script Tracking System</div>
</body>
</html>
"""


def _hashtag(val, pattern, repl):
    """Jinja helper."""
    import re
    return re.sub(pattern, repl, val)


app.jinja_env.filters["regex_replace"] = _hashtag
app.jinja_env.filters["trim"] = str.strip


class DotDict(dict):
    __getattr__ = dict.__getitem__


@app.route("/")
def index():
    scripts_raw = sm.list_scripts()
    scripts_raw.sort(key=lambda s: s["id"])
    scripts_list = [DotDict(s) for s in scripts_raw]

    product = None
    if scripts_list and scripts_list[0].get("product_id"):
        p = af.get_product(scripts_list[0]["product_id"])
        if p:
            product = DotDict(p)

    return render_template_string(HTML_TEMPLATE, scripts=scripts_list, product=product, styles=STYLE_MAP)


@app.route("/download-pdf")
def download_pdf():
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm, mm
    from reportlab.lib.colors import HexColor, white
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER

    scripts_raw = sm.list_scripts()
    scripts_raw.sort(key=lambda s: s["id"])

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=1.5*cm, bottomMargin=1.5*cm, leftMargin=2*cm, rightMargin=2*cm)
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle('CoverTitle', parent=styles['Title'], fontSize=32, spaceAfter=6, textColor=HexColor('#1a1a1a'), alignment=TA_CENTER))
    styles.add(ParagraphStyle('CoverSub', parent=styles['Normal'], fontSize=14, textColor=HexColor('#666666'), alignment=TA_CENTER, spaceAfter=20))
    styles.add(ParagraphStyle('ScriptTitle', parent=styles['Heading1'], fontSize=18, textColor=HexColor('#1a1a1a'), spaceAfter=8, spaceBefore=4))
    styles.add(ParagraphStyle('HookText', parent=styles['Normal'], fontSize=12, textColor=HexColor('#333333'), fontName='Helvetica-BoldOblique', leftIndent=10, spaceAfter=10, spaceBefore=4, borderPadding=6))
    styles.add(ParagraphStyle('ScriptBody', parent=styles['Normal'], fontSize=10, textColor=HexColor('#222222'), leading=14, spaceAfter=3))
    styles.add(ParagraphStyle('ActionLine', parent=styles['Normal'], fontSize=9, textColor=HexColor('#888888'), fontName='Helvetica-Oblique', leftIndent=15, spaceAfter=2, leading=12))
    styles.add(ParagraphStyle('CTAText', parent=styles['Normal'], fontSize=11, textColor=white, fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=8))
    styles.add(ParagraphStyle('TagStyle', parent=styles['Normal'], fontSize=8, textColor=HexColor('#999999'), fontName='Helvetica-Oblique', spaceAfter=4))
    styles.add(ParagraphStyle('NoteStyle', parent=styles['Normal'], fontSize=8, textColor=HexColor('#777777'), fontName='Helvetica-Oblique'))
    styles.add(ParagraphStyle('Badge', parent=styles['Normal'], fontSize=9, textColor=white, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle('SectionLabel', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold', textColor=HexColor('#333333'), spaceAfter=4, spaceBefore=8))

    story = []

    # Cover
    story.append(Spacer(1, 4*cm))
    story.append(Paragraph('VITASMA KIDS', styles['CoverTitle']))
    story.append(Paragraph('TikTok Affiliate Script Collection', styles['CoverSub']))
    story.append(Spacer(1, 1*cm))

    info_data = [
        ['Produk', 'Vitasma Kids - Madu Herbal Anak'],
        ['Harga', 'Rp95.000 (Flash Sale -21%)'],
        ['Komisi', 'Rp10.450 / sale (11%)'],
        ['Repurchase', '3.500+ buyers'],
        ['Scripts', f'{len(scripts_raw)} script'],
    ]
    t = Table(info_data, colWidths=[3.5*cm, 10*cm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#F5F5F5')),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#DDDDDD')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
    ]))
    story.append(t)

    # Scripts
    for i, script in enumerate(scripts_raw, 1):
        story.append(PageBreak())
        label, hex_color = STYLE_MAP.get(i, ("Script", "#666666"))
        color = HexColor(hex_color)

        badge = Table([[Paragraph(f'&nbsp; {label.upper()} &nbsp;', styles['Badge'])]], colWidths=[5.5*cm])
        badge.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), color), ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]))
        story.append(badge)
        story.append(Spacer(1, 4*mm))
        story.append(Paragraph(f'Script #{i}: {script["title"]}', styles['ScriptTitle']))

        # Hook
        story.append(Paragraph('HOOK:', styles['SectionLabel']))
        hook_t = Table([[Paragraph(f'&quot;{script["hook"]}&quot;', styles['HookText'])]], colWidths=[16*cm])
        hook_t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), HexColor('#FFF8F0')), ('LINEBEFOREDECOR', (0, 0), (0, -1), 3, color), ('TOPPADDING', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, -1), 8), ('LEFTPADDING', (0, 0), (-1, -1), 12)]))
        story.append(hook_t)
        story.append(Spacer(1, 4*mm))

        # Content
        story.append(Paragraph('SCRIPT:', styles['SectionLabel']))
        for line in script['content'].strip().split('\n'):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 2*mm))
                continue
            safe = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            if line.startswith('[ACTION:'):
                story.append(Paragraph(safe, styles['ActionLine']))
            else:
                story.append(Paragraph(safe, styles['ScriptBody']))
        story.append(Spacer(1, 4*mm))

        # CTA
        cta_t = Table([[Paragraph(f'CTA: {script["cta"]}', styles['CTAText'])]], colWidths=[16*cm])
        cta_t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), color), ('TOPPADDING', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, -1), 8)]))
        story.append(cta_t)
        story.append(Spacer(1, 3*mm))

        tags = ' '.join([f'#{t.strip()}' for t in script['tags'].split(',')])
        story.append(Paragraph(f'Tags: {tags}', styles['TagStyle']))
        if script.get('notes'):
            story.append(Paragraph(f'Notes: {script["notes"]}', styles['NoteStyle']))

    doc.build(story)
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name='Vitasma_Kids_Scripts.pdf', mimetype='application/pdf')


if __name__ == "__main__":
    print("\n  TikTok Script Dashboard")
    print("  Open: http://localhost:5001\n")
    app.run(host="0.0.0.0", port=5001, debug=False)
