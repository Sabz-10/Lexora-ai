from exceptions import DocumentParseError
from pypdf.errors import PyPdfError
from docx.opc.exceptions import PackageNotFoundError
from zipfile import BadZipFile
from lxml.etree import XMLSyntaxError
from docx.text.paragraph import Paragraph
from docx.table import Table
from file_validator import validate_file
from config import MAX_PDF_PAGES
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader
from docx import Document

from config import (
    MAX_FILE_SIZE,
    MAX_DOCUMENT_CHARACTERS,
    SUPPORTED_EXTENSIONS,
)

from document_models import DocumentBlock, ParsedDocument


def extract_pdf(content: bytes):
    reader = PdfReader(BytesIO(content))

    if reader.is_encrypted:
        raise ValueError(
            "Password-protected PDF is not supported."
        )

    # Check page count before extracting text
    if len(reader.pages) > MAX_PDF_PAGES:
        raise ValueError("PDF exceeds the page limit.")

    for number, page in enumerate(reader.pages, start=1):
        yield "page", number, page.extract_text() or ""

def extract_docx(content: bytes):
    document = Document(BytesIO(content))

    paragraph_number = 0
    row_number = 0

    for item in document.iter_inner_content():

        if isinstance(item, Paragraph):
            paragraph_number += 1

            yield (
                "paragraph",
                paragraph_number,
                item.text,
            )

        elif isinstance(item, Table):

            for row in item.rows:
                row_number += 1

                text = " | ".join(
                    cell.text for cell in row.cells
                )

                yield "table_row", row_number, text


def extract_txt(content: bytes):
    text = content.decode("utf-8-sig")

    for number, line in enumerate(text.splitlines(), start=1):
        yield "line", number, line


def _extract_document(
    filename: str,
    content: bytes
) -> ParsedDocument:

    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError("Unsupported file format.")

    if not content:
        raise ValueError("Uploaded file is empty.")

    if len(content) > MAX_FILE_SIZE:
        raise ValueError("File exceeds the upload size limit.")

    validate_file(extension, content)

    extractors = {
        ".pdf": extract_pdf,
        ".docx": extract_docx,
        ".txt": extract_txt,
    }

    blocks = []
    warnings = []
    offset = 0

    for source_type, number, raw_text in extractors[extension](content):

        text = raw_text.strip()

        if not text:
            if source_type == "page":
                warnings.append(
                    f"Page {number} has no extractable text."
                )
            continue

        start = offset + (1 if blocks else 0)
        end = start + len(text)

        if end > MAX_DOCUMENT_CHARACTERS:
            raise ValueError("Document exceeds the character limit.")

        blocks.append(
            DocumentBlock(
                block_id=len(blocks) + 1,
                text=text,
                source_type=source_type,
                source_number=number,
                start_offset=start,
                end_offset=end,
            )
        )

        offset = end

    if not blocks:
        raise ValueError(
            "No readable text found. OCR may be required."
        )

    return ParsedDocument(
        filename=Path(filename).name,
        file_type=extension,
        blocks=blocks,
        total_characters=offset,
        warnings=warnings,
    )
def extract_document(
    filename: str,
    content: bytes
) -> ParsedDocument:

    try:
        return _extract_document(filename, content)

    except PyPdfError as error:
        raise DocumentParseError(
            "The PDF is corrupted or cannot be read."
        ) from error

    except (
        PackageNotFoundError,
        BadZipFile,
        XMLSyntaxError,
        KeyError,
    ) as error:
        raise DocumentParseError(
            "The document structure is invalid or corrupted."
        ) from error
