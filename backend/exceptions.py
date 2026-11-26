class DocumentError(ValueError):
    """Base exception for document processing errors."""


class DocumentParseError(DocumentError):
    """Raised when document content cannot be parsed."""