"""Build the optional one-page demo attachment with ReportLab (included in Odoo)."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def build_pdf(destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(destination), pagesize=A4)
    pdf.setTitle("Kitchen Measurement - Bahodir Furniture Client")
    pdf.setAuthor("Furniture Manufacturing Demo")
    pdf.setFillColor(colors.HexColor("#254A40"))
    pdf.rect(0, 722, A4[0], 120, fill=1, stroke=0)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawString(48, 780, "KITCHEN MEASUREMENT")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(48, 753, "Furniture manufacturing demo | Reference 001")
    pdf.setFillColor(colors.HexColor("#222222"))
    for y, label, value in (
        (680, "Customer", "Bahodir Furniture Client"),
        (632, "Product", "Custom Kitchen Furniture"),
        (584, "Production address", "Sho'rchi, Shaldiroq MFY"),
    ):
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(48, y, label.upper())
        pdf.setFont("Helvetica", 13)
        pdf.drawString(48, y - 21, value)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(48, 509, "Illustrative plan - dimensions in millimetres")
    pdf.setStrokeColor(colors.HexColor("#254A40"))
    pdf.setFillColor(colors.HexColor("#EDF3F0"))
    pdf.rect(85, 327, 420, 120, fill=1)
    for x in (155, 225, 295, 365, 435):
        pdf.line(x, 327, x, 447)
    pdf.setFillColor(colors.HexColor("#222222"))
    pdf.setFont("Helvetica", 11)
    pdf.drawCentredString(295, 462, "3000")
    pdf.drawString(511, 381, "600")
    pdf.drawCentredString(295, 307, "Six base cabinet bays")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(48, 252, "Worktop height: 900 mm")
    pdf.drawString(48, 231, "Finish: light oak / white")
    pdf.setStrokeColor(colors.HexColor("#D9E1DC"))
    pdf.line(48, 175, 547, 175)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(48, 153, "DEMO FILE - NOT AN APPROVED PRODUCTION DRAWING")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(48, 134, "Example dimensions only. Confirm site measurements before manufacture.")
    pdf.drawString(48, 51, "kitchen_measurement.pdf")
    pdf.drawRightString(547, 51, "1 / 1")
    pdf.showPage()
    pdf.save()


if __name__ == "__main__":
    import sys

    build_pdf(sys.argv[1])
