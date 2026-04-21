from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services import (
    create_workflow_session,
    get_workflow_session,
    update_workflow_session,
    generate_workflow_ui,
    refine_workflow_ui,
)
from app.schemas import WorkflowRefineRequest

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
        session_id = create_workflow_session([file_info])
        response_data = await generate_workflow_ui([file_info])
        response_data["session_id"] = session_id
        update_workflow_session(session_id=session_id, current_ui=response_data, feedback_state={})
        return response_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflow-ui/refine")
async def refine_workflow_ui_route(request: WorkflowRefineRequest):
    session = get_workflow_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    try:
        file_infos = session.get("files", [])

        response_data = await refine_workflow_ui(
            file_infos=file_infos,
            current_ui=request.current_ui,
            feedback_state=request.feedback_state,
        )

        response_data["session_id"] = request.session_id

        update_workflow_session(
            session_id=request.session_id,
            current_ui=response_data,
            feedback_state=request.feedback_state,
        )

        return response_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))