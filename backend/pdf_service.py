"""Reusable PDF generation service using xhtml2pdf (pisa).
Templates are simple HTML strings compatible with xhtml2pdf's limited CSS subset.
"""
import io
from xhtml2pdf import pisa


def html_to_pdf_bytes(html: str) -> bytes:
    buf = io.BytesIO()
    result = pisa.CreatePDF(src=html, dest=buf, encoding="utf-8")
    if result.err:
        raise RuntimeError(f"PDF generation failed: {result.err}")
    return buf.getvalue()


DEV_BRAND = "Developed by Zeeshan Computers Sheikh Fazal · 0343-0819382"


def _safe(v):
    if v is None:
        return "—"
    return str(v)


def voucher_pdf(v: dict) -> bytes:
    """A4 LANDSCAPE with 3 copies in one page separated by cut lines."""
    school = v["school"]
    stu = v["student"]
    inv = v["invoice"]
    labels = v.get("copy_labels") or ["Copy 1 — Student Copy", "Copy 2 — Parent Copy", "Copy 3 — Bank Copy"]

    def copy_block(label):
        return f"""
        <table class="cp"><tr>
          <td class="hdr">
            <b style="font-size:12pt">{_safe(school.get('name'))}</b><br/>
            <span style="font-size:8pt">{_safe(school.get('address'))} · {_safe(school.get('phone'))}</span>
          </td>
          <td class="hdr" align="right">
            <b style="font-size:11pt">FEE VOUCHER</b><br/>
            <span style="font-size:8pt">{label}</span><br/>
            <span style="font-size:8pt">Voucher #: {_safe(v.get('voucher_no'))} · Issued: {_safe(v.get('issue_date'))}</span>
          </td>
        </tr></table>
        <table class="info"><tr>
          <td>Student: <b>{_safe(stu.get('name'))}</b></td>
          <td>Student ID: <b>{_safe(stu.get('student_id') or stu.get('admission_number'))}</b></td>
          <td>Class: {_safe(stu.get('class_name'))} {_safe(stu.get('section_name'))}</td>
          <td>Roll #: {_safe(stu.get('roll_number'))}</td>
        </tr><tr>
          <td>Father: {_safe(stu.get('father_name'))}</td>
          <td>Fee for: {_safe(inv.get('month') or inv.get('title'))}</td>
          <td>Due date: <b>{_safe(inv.get('due_date'))}</b></td>
          <td>Status: {_safe(inv.get('status'))}</td>
        </tr></table>
        <table class="amt">
          <tr><th>Description</th><th align="right">Amount (PKR)</th></tr>
          <tr><td>{_safe(inv.get('title'))}</td><td align="right">{inv.get('amount', 0):,.0f}</td></tr>
          {"<tr><td>Already paid</td><td align='right'>-" + f"{inv.get('paid_amount', 0):,.0f}" + "</td></tr>" if inv.get('paid_amount') else ""}
          {"<tr><td>Previous balance</td><td align='right'>" + f"{v.get('previous_balance', 0):,.0f}" + "</td></tr>" if v.get('previous_balance') else ""}
          <tr class="tot"><td><b>Total Payable</b></td><td align="right"><b>PKR {v.get('total_payable', 0):,.0f}</b></td></tr>
        </table>
        <div class="pay">Payment: {_safe(school.get('bank_instructions') or 'Pay at school office before due date.')}</div>
        """

    css = """
      @page { size: A4 landscape; margin: 8mm; }
      body { font-family: Helvetica, Arial, sans-serif; font-size: 8.5pt; color: #111; }
      .copy { border: 1.5px dashed #333; padding: 6px 10px; margin-bottom: 6px; }
      .cp { width:100%; border:none; margin-bottom:4px; }
      .cp td.hdr { border-bottom: 1px solid #666; padding-bottom:3px; }
      table.info { width:100%; border-collapse:collapse; margin:4px 0; font-size:8pt;}
      table.info td { padding:2px 4px; }
      table.amt { width:100%; border-collapse:collapse; margin-top:2px; font-size:8pt;}
      table.amt th, table.amt td { border: 1px solid #999; padding:3px 5px; }
      table.amt th { background:#eef; }
      table.amt tr.tot td { background:#f2f2f2; }
      .pay { font-size:7pt; margin-top:3px; white-space:pre-wrap; }
      .brand { text-align:center; font-size:7pt; color:#777; margin-top:2px; }
    """
    html = f"""<html><head><style>{css}</style></head><body>
      <div class="copy">{copy_block(labels[0])}<div class="brand">{DEV_BRAND}</div></div>
      <div class="copy">{copy_block(labels[1])}<div class="brand">{DEV_BRAND}</div></div>
      <div class="copy">{copy_block(labels[2])}<div class="brand">{DEV_BRAND}</div></div>
    </body></html>"""
    return html_to_pdf_bytes(html)


def _card_front(school, stu, session, photo_src):
    return f"""
    <table class="card front">
      <tr><td colspan="2" class="hdr">
        <b>{_safe(school.get('name'))}</b><br/>
        <span style="font-size:6.5pt">{_safe(school.get('address'))}</span><br/>
        <b class="tag">STUDENT ID CARD · {_safe(session)}</b>
      </td></tr>
      <tr>
        <td class="ph">{('<img src="' + photo_src + '" width="82" height="100"/>') if photo_src else '<div class="ph-empty">Photo</div>'}</td>
        <td class="info">
          <table>
            <tr><td>Name:</td><td><b>{_safe(stu.get('name'))}</b></td></tr>
            <tr><td>Student ID:</td><td><b>{_safe(stu.get('student_id'))}</b></td></tr>
            <tr><td>Adm #:</td><td>{_safe(stu.get('admission_number'))}</td></tr>
            <tr><td>Class:</td><td>{_safe(stu.get('class_name'))} {_safe(stu.get('section_name'))}</td></tr>
            <tr><td>Roll #:</td><td>{_safe(stu.get('roll_number'))}</td></tr>
            <tr><td>Father:</td><td>{_safe(stu.get('father_name'))}</td></tr>
          </table>
        </td>
      </tr>
      <tr><td colspan="2" class="ftr">{_safe(school.get('phone'))} · {_safe(school.get('email'))}</td></tr>
    </table>
    """


def _card_back(school, back_text):
    return f"""
    <table class="card back">
      <tr><td class="hdr"><b>{_safe(school.get('name'))}</b></td></tr>
      <tr><td class="body">
        <b>Contact</b><br/>
        {_safe(school.get('address'))}<br/>
        Phone: {_safe(school.get('phone'))}<br/>
        Email: {_safe(school.get('email'))}<br/><br/>
        <div style="white-space:pre-wrap">{_safe(back_text or 'If found, please return to the above school address.')}</div>
      </td></tr>
      <tr><td class="brand">{DEV_BRAND}</td></tr>
    </table>
    """


def id_cards_pdf(school, students, session, back_text, photo_urls_by_id=None):
    """One PDF with N students. 4 cards per A4 page (2×2) — fronts first pages, backs following.
    photo_urls_by_id: {student_id: data-uri or absolute url string}
    """
    photo_urls_by_id = photo_urls_by_id or {}
    css = """
      @page { size: A4; margin: 10mm; }
      body { font-family: Helvetica, Arial, sans-serif; color:#111; font-size:8pt; }
      .grid { width:100%; border-collapse:collapse; }
      .grid td { width:50%; padding:5px; vertical-align:top; }
      table.card { width:100%; border: 1.5px solid #065F46; border-collapse:collapse; }
      table.card td { border:none; padding:4px; }
      table.card .hdr { background:#065F46; color:#fff; padding:4px 6px; text-align:center; font-size:8pt; }
      table.card .hdr .tag { display:block; font-size:6.5pt; letter-spacing:1px; margin-top:2px; }
      table.card .ph { width:90px; text-align:center; vertical-align:top; padding:6px;}
      table.card .ph-empty { border:1px dashed #999; width:82px; height:100px; text-align:center; padding-top:38px; color:#999; font-size:7pt;}
      table.card .info { padding:4px; }
      table.card .info table { font-size:7.5pt; width:100%; }
      table.card .info table td { padding:1px 2px; }
      table.card .ftr { background:#f6f6f6; text-align:center; font-size:7pt; padding:3px; }
      table.card .body { padding:8px 10px; font-size:8pt; }
      table.card .brand { text-align:center; color:#777; font-size:6.5pt; padding:3px; }
      .page-break { page-break-before: always; }
      h4 { font-size:9pt; color:#065F46; margin:4px 0; }
    """

    def render_pages(items, title):
        rows = []
        for i in range(0, len(items), 2):
            pair = items[i:i+2]
            cells = "".join(f"<td>{c}</td>" for c in pair)
            if len(pair) == 1:
                cells += "<td></td>"
            rows.append(f"<tr>{cells}</tr>")
        pages = []
        # 4 cards per A4 (2 rows × 2 cols) → 2 tr per page
        for j in range(0, len(rows), 2):
            page = f'<h4>{title}</h4><table class="grid">{"".join(rows[j:j+2])}</table>'
            pages.append(page)
        return "".join(f'<div class="{("page-break" if k>0 else "")}">{p}</div>' for k, p in enumerate(pages))

    fronts = [_card_front(school, s, session, photo_urls_by_id.get(s["id"])) for s in students]
    backs = [_card_back(school, back_text) for _ in students]
    html = f"""<html><head><style>{css}</style></head><body>
      {render_pages(fronts, 'Front side')}
      <div class="page-break">{render_pages(backs, 'Back side')}</div>
    </body></html>"""
    return html_to_pdf_bytes(html)
