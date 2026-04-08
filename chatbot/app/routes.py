# contiene gli endpoint HTTP per la chat, upload, e altre funzionalità

from fastapi import APIRouter, File, HTTPException, UploadFile
from typing import List

from app.schemas import ChatbotResponse, ErrorResponse, NextStepRequest
from app.services import (
    create_session,
    get_session,
    store_bot_turn,
    store_user_turn,
    call_openai_for_initial_analysis,
    call_openai_for_next_step,
)
from app.utils import is_allowed_file, save_upload_file

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.post(
    "/chatbot/upload",
    response_model=ChatbotResponse,
    responses={400: {"model": ErrorResponse}},
)
async def upload_files(files: List[UploadFile] = File(...)):
    print(">>> upload_files route reached")
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    saved_files = []

    try:
        for file in files:
            if not is_allowed_file(file.filename or ""):
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type: {file.filename}",
                )

            file_info = await save_upload_file(file)
            saved_files.append(file_info)

        session_id = create_session(saved_files)

        response_data = call_openai_for_initial_analysis(saved_files)

        store_bot_turn(
            session_id=session_id,
            reply=response_data["reply"],
            ui_components=response_data["ui_components"],
            step_id=response_data["step_id"],
        )

        return ChatbotResponse(
            session_id=session_id,
            step_id=response_data["step_id"],
            reply=response_data["reply"],
            ui_components=response_data["ui_components"],
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        print("UPLOAD ERROR:", repr(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/chatbot/next-step",
    response_model=ChatbotResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def next_step(request: NextStepRequest):
    session = get_session(request.session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    try:
        store_user_turn(
            session_id=request.session_id,
            action_type=request.action_type,
            payload=request.payload,
            step_id=request.step_id,
        )

        response_data = call_openai_for_next_step(
            session_id=request.session_id,
            step_id=request.step_id,
            action_type=request.action_type,
            payload=request.payload,
        )

        store_bot_turn(
            session_id=request.session_id,
            reply=response_data["reply"],
            ui_components=response_data["ui_components"],
            step_id=response_data["step_id"],
        )

        return ChatbotResponse(
            session_id=request.session_id,
            step_id=response_data["step_id"],
            reply=response_data["reply"],
            ui_components=response_data["ui_components"],
        )

    except Exception as e:
        print("UPLOAD ERROR:", repr(e))
        raise HTTPException(status_code=500, detail=str(e))