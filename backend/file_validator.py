from io import BytesIO
from zipfile import ZipFile, BadZipFile

from config import (
    MAX_DOCX_UNCOMPRESSED_SIZE,
    MAX_DOCX_ENTRIES,
)


def validate_pdf(content: bytes):
    if not content.startswith(b"%PDF-"):
        raise ValueError("Invalid PDF file signature.")


def validate_docx(content: bytes):
    try:
        with ZipFile(BytesIO(content)) as archive:

            entries = archive.infolist()

            if len(entries) > MAX_DOCX_ENTRIES:
                raise ValueError(
                    "DOCX contains too many internal files."
                )

            total_size = sum(
                entry.file_size for entry in entries
            )

            if total_size > MAX_DOCX_UNCOMPRESSED_SIZE:
                raise ValueError(
                    "DOCX exceeds decompressed size limit."
                )

            required_files = {
                "[Content_Types].xml",
                "word/document.xml",
            }

            if not required_files.issubset(
                archive.namelist()
            ):
                raise ValueError("Invalid DOCX structure.")

    except BadZipFile as error:
        raise ValueError("Invalid DOCX archive.") from error


def validate_txt(content: bytes):
    try:
        text = content.decode("utf-8-sig")

    except UnicodeDecodeError as error:
        raise ValueError(
            "TXT file must use UTF-8 encoding."
        ) from error

    if "\x00" in text:
        raise ValueError("Invalid text file content.")


def validate_file(extension: str, content: bytes):

    validators = {
        ".pdf": validate_pdf,
        ".docx": validate_docx,
        ".txt": validate_txt,
    }

    validators[extension](content)