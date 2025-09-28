from fastapi import APIRouter, UploadFile, Form, Query
from fastapi.responses import StreamingResponse, JSONResponse
from app.processor import process_resume
import io, base64

router = APIRouter()

@router.post("/format-profile")
async def format_profile(
    file: UploadFile,
    openai_key: str = Form(...),
    debug: bool = Query(False)
):
    file_bytes = await file.read()
    try:
        pdf_bytes, trainer_name, debug_text_path, debug_html_path = process_resume(file_bytes, openai_key)

        if debug:
            # Return debug files as base64 so you can see in Render
            with open(debug_text_path, "r", encoding="utf-8") as f:
                raw_text = f.read()
            with open(debug_html_path, "r", encoding="utf-8") as f:
                html_preview = f.read()

            return JSONResponse({
                "trainer_name": trainer_name,
                "raw_text": raw_text[:1000],       # preview text
                "html_preview": html_preview[:2000], # preview HTML
                "pdf_base64": base64.b64encode(pdf_bytes).decode()
            })

        # Default: return PDF directly
        return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf",
                                 headers={"Content-Disposition": f"attachment; filename={trainer_name}.pdf"})

    except Exception as e:
        return JSONResponse({"error": f"Internal server error: {e}"}, status_code=500)