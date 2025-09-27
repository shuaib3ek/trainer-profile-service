import io
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from app.processor import process_resume

router = APIRouter()

@router.post("/format-profile")
async def format_profile(
    file: UploadFile = File(...),
    openai_key: str = Form(...)
):
    file_bytes = await file.read()
    pdf_bytes, full_name = process_resume(file_bytes, openai_key)

    # Sanitize filename
    safe_name = full_name.strip().replace(" ", "_") if full_name else file.filename.split(".")[0]
    filename = f"{safe_name}_TrainerProfile.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )