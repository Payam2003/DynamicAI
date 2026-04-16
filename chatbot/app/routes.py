from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services import generate_workflow_ui
from app.utils import is_allowed_file, save_upload_file

router = APIRouter()


@router.post("/workflow-ui/generate")
async def generate_workflow_ui_route(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    if not is_allowed_file(file.filename or ""):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.filename}",
        )

    try:
        file_info = await save_upload_file(file)
        response_data = await generate_workflow_ui([file_info])
        return response_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))