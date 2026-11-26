import os
from dotenv import load_dotenv

load_dotenv()


# Application information
APP_NAME = "Lexora AI"
APP_VERSION = "1.1.0"


# Document upload limits
MAX_FILE_SIZE_MB = int(
    os.getenv("MAX_FILE_SIZE_MB", "25")
)

MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024

MAX_DOCUMENT_CHARACTERS = int(
    os.getenv("MAX_DOCUMENT_CHARACTERS", "1000000")
)


# Supported document formats
SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt",
}


# Analysis settings
SINGLE_PASS_MAX_TOKENS = 20000

CHUNK_TARGET_TOKENS = 8000

CHUNK_OVERLAP_TOKENS = 400

MAX_CONCURRENT_REQUESTS = 2

MAX_RETRIES = 2

# Document resource protection
MAX_PDF_PAGES = 500

MAX_DOCX_UNCOMPRESSED_SIZE = 100 * 1024 * 1024

MAX_DOCX_ENTRIES = 5000


# Risk classification
ALLOWED_CLAUSE_RISKS = {
    "green",
    "yellow",
    "red",
}


# Legal disclaimer
DISCLAIMER = (
    "This is general information, not legal advice."
)