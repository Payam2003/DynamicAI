# Utile per structured outputs, per progettare il formato dei dati che il frontend deve ricevere
# mette i modelli Pydantic di input/output

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel

class WorkflowRefineRequest(BaseModel):
    session_id: str
    current_ui: Dict[str, Any]
    feedback_state: Dict[str, Any]


class UIComponent(BaseModel):
    component: Literal["button_group", "checklist", "slider"]
    label: str
    options: List[str] = []
    min_value: Optional[int] = None
    max_value: Optional[int] = None
    step: Optional[int] = None


class ChatbotResponse(BaseModel):
    session_id: Optional[str] = None
    step_id: str
    reply: str
    ui_components: List[UIComponent] = []

class NextStepRequest(BaseModel):
    session_id: str
    step_id: str
    action_type: str
    payload: Dict[str, Any]

class ErrorResponse(BaseModel):
    detail: str