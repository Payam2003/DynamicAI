import uuid
from app.config import settings
import json
from ollama import chat

SESSIONS = {}

UI_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "step_id": {"type": "string"},
        "reply": {"type": "string"},
        "ui_components": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "component": {"type": "string", "enum": ["button_group", "checklist", "slider"]}, # adesso aggiungo checklist e slider
                    "label": {"type": "string"},
                    "options": {
                        "type": "array",
                        "items": {"type": "string"},
                    }, # aggiungo anche più items, non per forza 3
                    "min_value": {"type": "integer"},
                    "max_value": {"type": "integer"},
                },
                "required": ["component", "label"],
                "additionalProperties": False,
            },
            "minItems": 1,
            "maxItems": 3, # limito a 3 componenti massimo per ora
        },
    },
    "required": ["step_id", "reply", "ui_components"],
    "additionalProperties": False,
}


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

# image_path è una lista ora per gestire poi più file nel caso
def call_ollama_json(prompt: str, model: str = None, image_path: list[str] = None):
    model = model or settings.OLLAMA_MODEL
    image_path = image_path or []

    print("=== OLLAMA CALL START ===")
    print("Using model:", model)
    print("Image paths:", image_path)

    message = {
        "role": "user",
        "content": prompt,
    }

    if image_path:
        message["images"] = image_path

    response = chat(
        model=model,
        messages=[message],
        think=False,
        stream=False,
        format=UI_RESPONSE_SCHEMA,
    )

    print("=== OLLAMA RESPONSE RECEIVED ===")

    text = response.message.content.strip()

    print("=== OLLAMA TEXT ===")
    print(text)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        print("JSON PARSE ERROR:", repr(e))
        print("RAW TEXT THAT FAILED:")
        print(text)

        return {
            "step_id": "fallback_step",
            "reply": "Il modello ha prodotto una risposta non valida. Uso un fallback sicuro.",
            "ui_components": [
                {
                    "component": "button_group",
                    "label": "Scegli come continuare",
                    "options": [
                        "Riprova analisi",
                        "Usa diagnosi guidata",
                        "Torna indietro",
                    ],
                }
            ],
        }

    # normalizzazione minima dello schema
    if isinstance(data.get("step_id"), int):
        data["step_id"] = f"step_{data['step_id']}"

    dynamic_components = {"button_group", "checklist", "slider"}
    normalized_components = []

    for component in data.get("ui_components", []):
        # se il modello restituisce una stringa semplice
        if isinstance(component, str):
            safe_component = component if component in dynamic_components else "button_group"
            normalized_components.append({
                "component": safe_component,
                "label": "Seleziona un'opzione",
                "options": ["Opzione 1", "Opzione 2", "Opzione 3"] if safe_component != "slider" else [],
                "min_value": 0 if safe_component == "slider" else None,
                "max_value": 10 if safe_component == "slider" else None,
            })
            continue

        # se restituisce un dict
        if isinstance(component, dict):
            detected_component = None

            if component.get("component") in dynamic_components:
                detected_component = component["component"]
            elif component.get("type") in dynamic_components:
                detected_component = component["type"]
            elif component.get("component_type") in dynamic_components:
                detected_component = component["component_type"]
            elif component.get("name") in dynamic_components:
                detected_component = component["name"]

            if detected_component is None:
                detected_component = "button_group"

            normalized = {
                "component": detected_component,
                "label": component.get("label", "Seleziona un'opzione"),
            }

            if detected_component in {"button_group", "checklist"}:
                raw_options = component.get("options", [])
                normalized_options = []

                for option in raw_options:
                    if isinstance(option, str):
                        normalized_options.append(option)
                    elif isinstance(option, dict):
                        if "text" in option:
                            normalized_options.append(option["text"])
                        elif "label" in option:
                            normalized_options.append(option["label"])
                        elif "value" in option:
                            normalized_options.append(str(option["value"]))

                if not normalized_options:
                    normalized_options = ["Opzione 1", "Opzione 2", "Opzione 3"]

                normalized["options"] = normalized_options

            if detected_component == "slider":
                normalized["min_value"] = component.get("min_value", 0)
                normalized["max_value"] = component.get("max_value", 10)

            normalized_components.append(normalized)

    if not normalized_components:
        normalized_components = [
            {
                "component": "button_group",
                "label": "Scegli come continuare",
                "options": [
                    "Identifica il problema",
                    "Verifica il danno visibile",
                    "Inizia diagnosi guidata",
                ],
            }
        ]

    data["ui_components"] = normalized_components
    return data

def call_openai_for_initial_analysis(file_infos):
    file_names = ", ".join(f["original_name"] for f in file_infos)

    image_files = [
        f for f in file_infos
        if (f.get("content_type") or "").startswith("image/")
    ]

    if image_files:
        image_path = [f["path"] for f in image_files]

        prompt = f"""
        Sei un planner di troubleshooting operativo per oggetti fisici reali.

        L'utente ha caricato questi file: {file_names}.

        Analizza l'immagine e genera il prossimo stato di una GUI dinamica per una diagnosi guidata passo dopo passo.

        Il tuo compito non è essere un chatbot generico.
        Non proporre azioni come "salva", "annulla", "rivedi".
        Devi scegliere il componente UI più adatto in base al tipo di informazione che serve nel passo corrente.

        Puoi usare solo UNO di questi componenti:
        - "button_group" se serve una scelta singola tra alternative
        - "checklist" se l'utente deve selezionare più sintomi o condizioni osservabili
        - "slider" se serve stimare intensità, gravità o livello di danno

        Restituisci solo JSON valido con questa struttura:
        {{
        "step_id": "diag_001",
        "reply": "breve messaggio in italiano",
        "ui_components": [
            {{
            "component": "button_group" oppure "checklist" oppure "slider",
            "label": "breve etichetta in italiano",
            "options": ["..."] se il componente è button_group o checklist,
            "min_value": 0 se il componente è slider,
            "max_value": 10 se il componente è slider
            }}
        ]
        }}

        Regole obbligatorie:
        - genera un solo step
        - genera un solo componente in ui_components
        - usa solo i componenti: button_group, checklist, slider
        - se usi button_group o checklist, options deve essere una lista di stringhe
        - se usi slider, includi min_value e max_value
        - tutto deve essere in italiano
        - non usare markdown
        - non aggiungere testo fuori dal JSON
        """

        return call_ollama_json(prompt, image_path=image_path)

    file_names = ", ".join(f["original_name"] for f in file_infos)

    prompt = f"""
    Sei un planner di troubleshooting operativo per oggetti fisici reali.

    L'utente ha caricato questi file: {file_names}.

    Analizza l'immagine e genera il prossimo stato di una GUI dinamica per una diagnosi guidata passo dopo passo.

    Il tuo compito non è essere un chatbot generico.
    Non proporre azioni come "salva", "annulla", "rivedi".
    Devi scegliere il componente UI più adatto in base al tipo di informazione che serve nel passo corrente.

    Puoi usare solo UNO di questi componenti:
    - "button_group" se serve una scelta singola tra alternative
    - "checklist" se l'utente deve selezionare più sintomi o condizioni osservabili
    - "slider" se serve stimare intensità, gravità o livello di danno

    Restituisci solo JSON valido con questa struttura:
    {{
    "step_id": "diag_001",
    "reply": "breve messaggio in italiano",
    "ui_components": [
        {{
        "component": "button_group" oppure "checklist" oppure "slider",
        "label": "breve etichetta in italiano",
        "options": ["..."] se il componente è button_group o checklist,
        "min_value": 0 se il componente è slider,
        "max_value": 10 se il componente è slider
        }}
    ]
    }}

    Regole obbligatorie:
    - genera un solo step
    - genera un solo componente in ui_components
    - usa solo i componenti: button_group, checklist, slider
    - se usi button_group o checklist, options deve essere una lista di stringhe
    - se usi slider, includi min_value e max_value
    - tutto deve essere in italiano
    - non usare markdown
    - non aggiungere testo fuori dal JSON
    """

    return call_ollama_json(prompt)

def call_openai_for_next_step(session_id: str, step_id: str, action_type: str, payload: dict):
    selected = payload.get("selected_option", "")
    selected_list = payload.get("selected_options", [])
    slider_value = payload.get("value", None)

    if action_type == "checklist_submit":
        return {
            "step_id": f"{step_id}_after_checklist",
            "reply": f"Hai selezionato questi sintomi: {', '.join(selected_list)}. Ora indica la gravità del problema.",
            "ui_components": [
                {
                    "component": "slider",
                    "label": "Quanto è grave il problema osservato?",
                    "min_value": 0,
                    "max_value": 10,
                }
            ],
        }

    if action_type == "slider_submit":
        return {
            "step_id": f"{step_id}_after_slider",
            "reply": f"Hai indicato un livello di gravità pari a {slider_value}. Ora scegli come vuoi proseguire.",
            "ui_components": [
                {
                    "component": "button_group",
                    "label": "Prossima azione",
                    "options": [
                        "Continua diagnosi",
                        "Mostra istruzioni semplici",
                        "Ricomincia",
                    ],
                }
            ],
        }

    if action_type == "button_group_submit":
        if selected == "Guidami passo dopo passo":
            return {
                "step_id": "step_2_checklist",
                "reply": "Seleziona tutti i sintomi che osservi.",
                "ui_components": [
                    {
                        "component": "checklist",
                        "label": "Sintomi osservabili",
                        "options": [
                            "Perdita continua",
                            "Perdita solo quando aperto",
                            "Ruggine visibile",
                            "Base bagnata",
                            "Maniglia allentata",
                        ],
                    }
                ],
            }

    return {
        "step_id": "fallback_step",
        "reply": "Ho ricevuto il tuo feedback. Scegli come continuare.",
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
