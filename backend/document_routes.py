
from dataclasses import asdict

from fastapi import APIRouter, UploadFile, File, HTTPException
from starlette.concurrency import run_in_threadpool

from config import MAX_FILE_SIZE
from document_parser import extract_document
from exceptions import DocumentParseError


router = APIRouter(
    prefix="/api",
    tags=["Documents"]
)


@router.post("/extract")
async def extract_uploaded_document(
    file: UploadFile = File(...)
):
    try:
        content = await file.read(MAX_FILE_SIZE + 1)

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File exceeds the upload size limit."
            )

        document = await run_in_threadpool(
            extract_document,
            file.filename or "",
            content
        )

        return {
            "success": True,
            "filename": document.filename,
            "file_type": document.file_type,
            "total_characters": document.total_characters,
            "total_blocks": len(document.blocks),
            "full_text": document.full_text,
            "blocks": [
                asdict(block)
                for block in document.blocks
            ],
            "warnings": document.warnings
        }

    except DocumentParseError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error)
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    finally:
        await file.close()
