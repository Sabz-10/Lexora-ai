import pytest

from document_parser import extract_document


def test_txt_extraction():
    document = extract_document(
        "sample.txt",
        b"Rental Agreement\nMonthly rent: INR 15000"
    )

    assert len(document.blocks) == 2
    assert document.total_characters == 40
    assert document.blocks[0].text == "Rental Agreement"


def test_source_offsets():
    document = extract_document(
        "sample.txt",
        b"First line\nSecond line"
    )

    for block in document.blocks:
        extracted = document.full_text[
            block.start_offset:block.end_offset
        ]

        assert extracted == block.text


def test_empty_file():
    with pytest.raises(ValueError):
        extract_document("empty.txt", b"")


def test_unsupported_format():
    with pytest.raises(ValueError):
        extract_document("sample.exe", b"Sample")


def test_whitespace_only():
    with pytest.raises(ValueError):
        extract_document("sample.txt", b"   \n   ")


def test_file_size_limit(monkeypatch):
    monkeypatch.setattr(
        "document_parser.MAX_FILE_SIZE", 5
    )

    with pytest.raises(ValueError):
        extract_document("sample.txt", b"123456")


def test_character_limit(monkeypatch):
    monkeypatch.setattr(
        "document_parser.MAX_DOCUMENT_CHARACTERS", 5
    )

    with pytest.raises(ValueError):
        extract_document("sample.txt", b"123456")
from io import BytesIO

from docx import Document
from reportlab.pdfgen import canvas


def test_pdf_extraction():
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)

    pdf.drawString(50, 750, "Rental Agreement")
    pdf.showPage()

    pdf.drawString(50, 750, "Monthly rent: INR 15000")
    pdf.save()

    document = extract_document(
        "contract.pdf", buffer.getvalue()
    )

    assert len(document.blocks) == 2
    assert document.blocks[0].source_type == "page"
    assert document.blocks[0].source_number == 1
    assert document.blocks[1].source_number == 2
    assert "Monthly rent: INR 15000" in document.full_text


def test_docx_extraction():
    buffer = BytesIO()
    doc = Document()

    doc.add_paragraph("Employment Agreement")
    doc.add_paragraph("Monthly salary: INR 50000")

    doc.save(buffer)

    document = extract_document(
        "contract.docx", buffer.getvalue()
    )

    assert len(document.blocks) == 2
    assert document.blocks[0].source_type == "paragraph"
    assert document.blocks[1].source_number == 2
    assert "Monthly salary: INR 50000" in document.full_text


def test_docx_table_extraction():
    buffer = BytesIO()
    doc = Document()

    table = doc.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Salary"
    table.cell(0, 1).text = "INR 50000"

    doc.save(buffer)

    document = extract_document(
        "contract.docx", buffer.getvalue()
    )

    assert document.blocks[0].source_type == "table_row"
    assert document.blocks[0].text == "Salary | INR 50000"


def test_pdf_empty_page_warning():
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)

    pdf.drawString(50, 750, "Rental Agreement")
    pdf.showPage()

    pdf.showPage()
    pdf.save()

    document = extract_document(
        "contract.pdf", buffer.getvalue()
    )

    assert len(document.blocks) == 1
    assert len(document.warnings) == 1
    assert "Page 2" in document.warnings[0]
def test_docx_reading_order():
    buffer = BytesIO()
    doc = Document()

    doc.add_paragraph("Payment Terms")

    table = doc.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Rent"
    table.cell(0, 1).text = "INR 15000"

    doc.add_paragraph("Termination Terms")

    doc.save(buffer)

    document = extract_document(
        "contract.docx", buffer.getvalue()
    )

    assert document.full_text == (
        "Payment Terms\n"
        "Rent | INR 15000\n"
        "Termination Terms"
    )

    assert [
        block.source_type for block in document.blocks
    ] == [
        "paragraph",
        "table_row",
        "paragraph",
    ]
def test_fake_pdf():
    with pytest.raises(ValueError, match="signature"):
        extract_document("fake.pdf", b"Not a PDF")


def test_invalid_docx():
    with pytest.raises(ValueError, match="archive"):
        extract_document("fake.docx", b"Not a DOCX")


def test_invalid_txt_encoding():
    with pytest.raises(ValueError, match="UTF-8"):
        extract_document("sample.txt", b"\xff\xfe\xfd")


def test_binary_txt():
    with pytest.raises(ValueError, match="Invalid text"):
        extract_document("sample.txt", b"Hello\x00World")


def test_pdf_page_limit(monkeypatch):
    monkeypatch.setattr(
        "document_parser.MAX_PDF_PAGES", 1
    )

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)

    pdf.drawString(50, 750, "Page One")
    pdf.showPage()

    pdf.drawString(50, 750, "Page Two")
    pdf.save()

    with pytest.raises(ValueError, match="page limit"):
        extract_document(
            "contract.pdf", buffer.getvalue()
        )


def test_docx_decompressed_limit(monkeypatch):
    monkeypatch.setattr(
        "file_validator.MAX_DOCX_UNCOMPRESSED_SIZE", 10
    )

    buffer = BytesIO()
    doc = Document()
    doc.add_paragraph("Sample Contract")
    doc.save(buffer)

    with pytest.raises(ValueError, match="decompressed"):
        extract_document(
            "contract.docx", buffer.getvalue()
        )
from exceptions import DocumentParseError


def test_corrupted_pdf():
    with pytest.raises(DocumentParseError):
        extract_document(
            "corrupted.pdf",
            b"%PDF-1.7\nInvalid document content"
        )


def test_parse_error_inheritance():
    assert issubclass(DocumentParseError, ValueError)