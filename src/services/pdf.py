"""PDF generation service using WeasyPrint."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from src.models import Invoice

TEMPLATE_DIR = Path(__file__).parent.parent.parent / "templates"


def _get_env():
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape
    except ImportError:
        return None
    return Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )


def render_invoice_pdf(invoice: Invoice, output_path: str | None = None) -> bytes:
    """Render an invoice to PDF bytes, optionally writing to output_path."""
    template = _get_env().get_template("invoice.html")

    html_out = template.render(
        invoice=invoice,
        company=invoice.company,
        contact=invoice.contact,
        subtotal=invoice.subtotal,
        tax_total=invoice.tax_total,
        total=invoice.total,
        currency=invoice.currency,
        issue_date=invoice.issue_date or date.today(),
        due_date=invoice.due_date or date.today(),
        number=invoice.number,
        lines=invoice.lines,
    )

    from weasyprint import HTML

    pdf_bytes = HTML(string=html_out).write_pdf()

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

    return pdf_bytes


def render_statement_pdf(contact_name: str, transactions: list, output_path: str | None = None) -> bytes:
    """Render a customer/vendor statement to PDF."""
    template = _get_env().get_template("statement.html")
    html_out = template.render(
        contact_name=contact_name,
        transactions=transactions,
    )

    from weasyprint import HTML

    pdf_bytes = HTML(string=html_out).write_pdf()

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

    return pdf_bytes
