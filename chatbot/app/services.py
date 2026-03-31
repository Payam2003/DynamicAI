import uuid
from app.config import settings

SESSIONS = {}

def create_session(file_infos):
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = {
        "files": file_infos,
        "history": [],
        "last_ui_components": [],
        "last_step_id": None,
    }
    return session_id


def get_session(session_id: str):
    return SESSIONS.get(session_id)


def store_bot_turn(session_id: str, reply: str, ui_components: list, step_id: str):
    session = SESSIONS[session_id]
    session["history"].append({
        "role": "assistant",
        "reply": reply,
        "ui_components": ui_components,
        "step_id": step_id,
    })
    session["last_ui_components"] = ui_components
    session["last_step_id"] = step_id


def store_user_turn(session_id: str, action_type: str, payload: dict, step_id: str):
    session = SESSIONS[session_id]
    session["history"].append({
        "role": "user",
        "action_type": action_type,
        "payload": payload,
        "step_id": step_id,
    })


def call_openai_for_initial_analysis(file_infos):
    file_names = ", ".join(f["original_name"] for f in file_infos)

    return {
        "step_id": "step_1",
        "reply": f"Ho ricevuto questo file: {file_names}. Seleziona una delle seguenti opzioni per iniziare l'analisi:",
        "ui_components": [
            {
                "component": "button_group",
                "label": "Seleziona l'azione successiva",
                "options": [
                    "Identifica il problema",
                    "Spiega il problema visibile",
                    "Guidami passo dopo passo",
                ],
            }
        ],
    }


def call_openai_for_next_step(session_id: str, step_id: str, action_type: str, payload: dict):
    selected = payload.get("selected_option", "")

    if step_id == "step_1":
        if selected == "Identifica il problema":
            return {
                "step_id": "step_2_identify",
                "reply": "Ti aiuterò a identificare il problema. Quale di questi descrive meglio il problema visibile?",
                "ui_components": [
                    {
                        "component": "button_group",
                        "label": "Scegli il sintomo più visibile",
                        "options": [
                            "Perdita",
                            "Arrugginito",
                            "Componente allentato",
                            "Crepa o danno visibile",
                        ],
                    }
                ],
            }

        if selected == "Spiega il problema visibile":
            return {
                "step_id": "step_2_explain",
                "reply": "Ti guiderò analizzando il problema. Quale di questi descrive meglio il problema visibile?",
                "ui_components": [
                    {
                        "component": "button_group",
                        "label": "Scegli la condizione",
                        "options": [
                            "Problema minore",
                            "Problema moderato",
                            "Danno visibile grave",
                        ],
                    }
                ],
            }

        if selected == "Guidami passo dopo passo":
            return {
                "step_id": "step_2_guide",
                "reply": "Ti guiderò passo dopo passo. Prima di tutto, confermi che l'oggetto è spento e sicuro da ispezionare?",
                "ui_components": [
                    {
                        "component": "button_group",
                        "label": "Before continuing, confirm the situation",
                        "options": [
                            "L'oggetto è spento",
                            "L'oggetto è sicuro da ispezionare",
                            "Sono pronto per il primo passo",
                        ],
                    }
                ],
            }

    if step_id == "step_2_guide":
        if selected == "L'oggetto è spento":
            return {
                "step_id": "step_3_guide_power",
                "reply": "Bene, adesso analizza l'oggetto",
                "ui_components": [
                    {
                        "component": "button_group",
                        "label": "Cosa noti?",
                        "options": [
                            "Una perdita",
                            "Un pezzo allentato",
                            "Niente di strano",
                        ],
                    }
                ],
            }

        if selected == "L'oggetto è sicuro da ispezionare":
            return {
                "step_id": "step_3_guide_safety",
                "reply": "Bene. Successivamente, controlla se le parti visibili mostrano corrosione o danni fisici.",
                "ui_components": [
                    {
                        "component": "button_group",
                        "label": "Scegli cosa vedi",
                        "options": [
                            "Corrosione",
                            "Crepa",
                            "Nessun danno visibile",
                        ],
                    }
                ],
            }

        if selected == "Sono pronto per il primo passo":
            return {
                "step_id": "step_3_guide_ready",
                "reply": "Step 1: ispeziona la base dell'oggetto per bene e analizza le anomalie",
                "ui_components": [
                    {
                        "component": "button_group",
                        "label": "Scegli il problema",
                        "options": [
                            "Perdita alla base",
                            "Maniglia allentata",
                            "Ruggine vicino all'giunto",
                        ],
                    }
                ],
            }

    return {
        "step_id": "fallback_step",
        "reply": f"Hai selezionato: {selected}. Ho ricevuto il feedback ma il flusso è ancora statico",
        "ui_components": [
            {
                "component": "button_group",
                "label": "Scegli come continuare",
                "options": [
                    "Ricomincia",
                    "Torna indietro",
                ],
            }
        ],
    }
