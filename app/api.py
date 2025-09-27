import os
import io
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from app.processor import process_resume

router = APIRouter()

@router.post("/format-profile")
async def format_profile(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()

        # Get OpenAI key from environment variable
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return JSONResponse(
                status_code=500,
                content={"error": "OPENAI_API_KEY is not set in server environment."},
            )

        pdf_bytes, trainer_name = process_resume(file_bytes, openai_key)

        # Return as downloadable PDF
        headers = {
            "Content-Disposition": f'attachment; filename="{trainer_name}.pdf"'
        }
        return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers=headers)

    except Exception as e:
        # Log the error in server logs
        print(f"Error in /format-profile: {e}")

        return JSONResponse(
            status_code=500,
            content={"error": f"Internal server error: {str(e)}"},
        )