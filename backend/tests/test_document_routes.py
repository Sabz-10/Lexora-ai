
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_extract_txt_success():
    response = client.post(
        "/api/extract",
        files={
            "file": (
                "contract.txt",
                b"Rental Agreement\nMonthly rent: INR 15000",
                "text/plain"
            )
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["total_blocks"] == 2
    assert data["total_characters"] == 40
    assert data["warnings"] == []


def test_extract_unsupported_file():
    response = client.post(
        "/api/extract",
        files={
            "file": (
                "sample.exe",
                b"Sample content",
                "application/octet-stream"
            )
        }
    )

    assert response.status_code == 400


def test_extract_empty_file():
    response = client.post(
        "/api/extract",
        files={
            "file": ("empty.txt", b"", "text/plain")
        }
    )

    assert response.status_code == 400


def test_extract_missing_file():
    response = client.post("/api/extract")

    assert response.status_code == 422


def test_extract_corrupted_pdf():
    response = client.post(
        "/api/extract",
        files={
            "file": (
                "corrupted.pdf",
                b"%PDF-1.7\nInvalid document content",
                "application/pdf"
            )
        }
    )

    assert response.status_code == 422


def test_extract_oversized_file(monkeypatch):
    monkeypatch.setattr(
        "document_routes.MAX_FILE_SIZE", 5
    )

    response = client.post(
        "/api/extract",
        files={
            "file": (
                "large.txt",
                b"123456",
                "text/plain"
            )
        }
    )

    assert response.status_code == 413
