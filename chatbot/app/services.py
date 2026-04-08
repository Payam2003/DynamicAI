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
                    "component": {"type": "string", "enum": ["button_group"]},
                    "label": {"type": "string"},
                    "options": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 3,
                        "maxItems": 3,
                    },
                },
                "required": ["component", "label", "options"],
                "additionalProperties": False,
            },
            "minItems": 1,
            "maxItems": 1,
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

def call_ollama_json(prompt: str, model: str = None, image_path: str = None):
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

    data = json.loads(text)

    # normalizzazione minima dello schema
    if isinstance(data.get("step_id"), int):
        data["step_id"] = f"step_{data['step_id']}"

    normalized_components = []

    for component in data.get("ui_components", []):
        # se il modello restituisce una stringa semplice
        if isinstance(component, str):
            normalized_components.append({
                "component": component,
                "label": "Seleziona un'opzione",
                "options": ["Opzione 1", "Opzione 2", "Opzione 3"],
            })
            continue

        # se restituisce un dict
        if isinstance(component, dict):
            # normalizza il nome del tipo componente
            if "type" in component and "component" not in component:
                component["component"] = component.pop("type")

            if "name" in component and "component" not in component:
                component["component"] = component.pop("name")

            if "component_type" in component and "component" not in component:
                component["component"] = component.pop("component_type")

            # label di fallback
            if "label" not in component:
                component["label"] = "Seleziona un'opzione"

            # normalizza options
            raw_options = component.get("options", [])

            normalized_options = []
            for option in raw_options:
                # caso semplice: già stringa
                if isinstance(option, str):
                    normalized_options.append(option)
                # caso oggetto tipo {"text": "...", "value": "..."}
                elif isinstance(option, dict):
                    if "text" in option:
                        normalized_options.append(option["text"])
                    elif "label" in option:
                        normalized_options.append(option["label"])
                    elif "value" in option:
                        normalized_options.append(str(option["value"]))

            # fallback se non ci sono opzioni valide
            if not normalized_options:
                normalized_options = ["Opzione 1", "Opzione 2", "Opzione 3"]

            component["options"] = normalized_options[:3]

            normalized_components.append(component)

            # fallback finale
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
    image_files = [
        f for f in file_infos
        if (f.get("content_type") or "").startswith("image/")
    ]

    if image_files:
        image_path = [f["path"] for f in image_files]

        prompt = """
            Sei un planner di troubleshooting operativo per oggetti fisici reali.

            Analizza l'immagine caricata dall'utente.
            Il tuo compito NON è essere un chatbot generico.
            NON devi proporre azioni come "salva", "annulla", "rivedi".
            Devi proporre il primo step di una GUI dinamica per diagnosticare un possibile problema fisico visibile.

            Le opzioni devono essere realistiche per troubleshooting operativo, ad esempio:
            - identificare il sintomo principale
            - verificare una perdita o un danno visibile
            - iniziare una diagnosi guidata
            - confermare una condizione di sicurezza o osservazione

            Restituisci solo un JSON valido con:
            - step_id
            - reply
            - ui_components

            Regole:
            - tutto in italiano
            - esattamente un componente
            - il componente deve essere "button_group"
            - esattamente 3 opzioni
            - le opzioni devono essere coerenti con ciò che si vede nell'immagine
            - non usare markdown
            """

        return call_ollama_json(prompt, image_path=image_path)

    file_names = ", ".join(f["original_name"] for f in file_infos)

    prompt = f"""
        Sei un planner di troubleshooting operativo.

        L'utente ha caricato questi file: {file_names}.

        Non hai a disposizione un'immagine analizzabile, quindi genera un primo step generico ma utile per iniziare una diagnosi.

        Restituisci solo un JSON valido con:
        - step_id
        - reply
        - ui_components

        Regole:
        - tutto in italiano
        - esattamente un componente
        - il componente deve essere "button_group"
        - esattamente 3 opzioni
        - non usare markdown
            """

    return call_ollama_json(prompt)

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
