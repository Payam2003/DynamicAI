import uuid
import json
import base64
import httpx

from app.config import settings

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
                    "component": {
                        "type": "string",
                        "enum": ["button_group", "checklist", "slider"],
                    },
                    "label": {"type": "string"},
                    "options": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "min_value": {"type": "integer"},
                    "max_value": {"type": "integer"},
                    "step": {"type": "integer"},
                },
                "required": ["component", "label"],
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
        "stato_analisi": {
            "problemi_sospetti": None,
            "sintomi_osservati": [],
            "gravità_stimata": None,
            "concentrazione_attuale": None,
        },
    }
    return session_id


def get_session(session_id: str):
    return SESSIONS.get(session_id)


def store_bot_turn(session_id: str, reply: str, ui_components: list, step_id: str):
    session = SESSIONS[session_id]
    session["history"].append(
        {
            "role": "assistant",
            "reply": reply,
            "ui_components": ui_components,
            "step_id": step_id,
        }
    )
    session["last_ui_components"] = ui_components
    session["last_step_id"] = step_id


def store_user_turn(session_id: str, action_type: str, payload: dict, step_id: str):
    session = SESSIONS[session_id]
    session["history"].append(
        {
            "role": "user",
            "action_type": action_type,
            "payload": payload,
            "step_id": step_id,
        }
    )


def file_to_data_url(path: str, content_type: str) -> str:
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{content_type};base64,{encoded}"


def build_openrouter_content(prompt: str, file_infos: list[dict]) -> list[dict]:
    content = [{"type": "text", "text": prompt}]

    for f in file_infos:
        content_type = f.get("content_type") or ""
        path = f.get("path")

        if not path:
            continue

        if content_type.startswith("image/"):
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": file_to_data_url(path, content_type),
                    },
                }
            )

        elif content_type == "text/plain":
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as txt_file:
                    txt = txt_file.read(12000)
                content.append(
                    {
                        "type": "text",
                        "text": f"\n\nContenuto del file {f.get('original_name', 'file.txt')}:\n{txt}",
                    }
                )
            except Exception:
                pass

        elif content_type == "application/pdf":
            content.append(
                {
                    "type": "text",
                    "text": (
                        f"\n\nL'utente ha caricato anche un PDF chiamato "
                        f"{f.get('original_name', 'document.pdf')}. "
                        "Se non puoi leggerlo nativamente, ragiona solo sul contesto disponibile "
                        "e fai domande diagnostiche prudenti."
                    ),
                }
            )

    return content


def strip_markdown_fences(text: str) -> str:
    text = text.strip()

    if text.startswith("```json"):
        text = text[len("```json"):].strip()

    elif text.startswith("```"):
        text = text[len("```"):].strip()

    if text.endswith("```"):
        text = text[:-3].strip()

    return text


def recover_action_payload_format(parsed: dict) -> dict | None:
    action_type = parsed.get("action_type")
    payload = parsed.get("payload")

    if not action_type:
        return None

    if action_type == "checklist":
        options = []
        if isinstance(payload, list):
            options = [str(item) for item in payload if str(item).strip()]
        elif isinstance(payload, dict):
            raw_options = payload.get("options", [])
            if isinstance(raw_options, list):
                options = [str(item) for item in raw_options if str(item).strip()]

        if options:
            return {
                "step_id": "recovered_checklist_step",
                "reply": "Seleziona tutte le informazioni rilevanti per continuare la diagnosi.",
                "ui_components": [
                    {
                        "component": "checklist",
                        "label": "Indica i dettagli utili",
                        "options": options,
                    }
                ],
            }

    if action_type == "button_group":
        options = []
        if isinstance(payload, list):
            options = [str(item) for item in payload if str(item).strip()]
        elif isinstance(payload, dict):
            raw_options = payload.get("options", [])
            if isinstance(raw_options, list):
                options = [str(item) for item in raw_options if str(item).strip()]

        if options:
            return {
                "step_id": "recovered_button_step",
                "reply": "Scegli l'opzione più adatta per proseguire.",
                "ui_components": [
                    {
                        "component": "button_group",
                        "label": "Seleziona un'opzione",
                        "options": options,
                    }
                ],
            }

    if action_type == "slider":
        min_value = 0
        max_value = 10
        step = 1
        label = "Indica il livello"

        if isinstance(payload, dict):
            min_value = payload.get("min_value", 0)
            max_value = payload.get("max_value", 10)
            step = payload.get("step", 1)
            label = payload.get("label", label)

        return {
            "step_id": "recovered_slider_step",
            "reply": "Indica il livello per continuare la diagnosi.",
            "ui_components": [
                {
                    "component": "slider",
                    "label": label,
                    "min_value": min_value,
                    "max_value": max_value,
                    "step": step,
                }
            ],
        }

    return None


def normalize_response_data(data: dict) -> dict:
    if isinstance(data.get("step_id"), int):
        data["step_id"] = f"step_{data['step_id']}"

    dynamic_components = {"button_group", "checklist", "slider"}
    normalized_components = []

    for component in data.get("ui_components", []):
        if isinstance(component, str):
            safe_component = component if component in dynamic_components else "button_group"
            normalized_components.append(
                {
                    "component": safe_component,
                    "label": "Seleziona un'opzione",
                    "options": ["Riprova analisi", "Continua diagnosi", "Torna indietro"]
                    if safe_component != "slider"
                    else [],
                    "min_value": 0 if safe_component == "slider" else None,
                    "max_value": 10 if safe_component == "slider" else None,
                    "step": 1 if safe_component == "slider" else None,
                }
            )
            continue

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
                raw_options = (
                    component.get("options")
                    or component.get("items")
                    or component.get("option_strings")
                    or []
                )

                normalized_options = []

                if isinstance(raw_options, str):
                    split_options = [opt.strip() for opt in raw_options.split(",") if opt.strip()]
                    normalized_options.extend(split_options)

                elif isinstance(raw_options, list):
                    for option in raw_options:
                        if isinstance(option, str):
                            normalized_options.append(option)
                        elif isinstance(option, dict):
                            if "text" in option:
                                normalized_options.append(str(option["text"]))
                            elif "label" in option:
                                normalized_options.append(str(option["label"]))
                            elif "value" in option:
                                normalized_options.append(str(option["value"]))

                if not normalized_options:
                    normalized_options = [
                        "Riprova analisi",
                        "Descrivi meglio il problema",
                        "Torna indietro",
                    ]

                normalized["options"] = normalized_options

            if detected_component == "slider":
                normalized["min_value"] = component.get("min_value", 0)
                normalized["max_value"] = component.get("max_value", 10)
                normalized["step"] = component.get("step", 1)

            normalized_components.append(normalized)

    if not normalized_components:
        normalized_components = [
            {
                "component": "button_group",
                "label": "Scegli come continuare",
                "options": [
                    "Riprova analisi",
                    "Usa diagnosi guidata",
                    "Torna indietro",
                ],
            }
        ]

    data["ui_components"] = normalized_components

    if not data.get("step_id"):
        data["step_id"] = "fallback_step"

    if not data.get("reply"):
        data["reply"] = "Procediamo con il prossimo passaggio della diagnosi."

    return data


async def call_openrouter_json(prompt: str, file_infos: list[dict] | None = None):
    if not settings.OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY non configurata.")

    content = build_openrouter_content(prompt, file_infos or [])

    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [
            {
                "role": "user",
                "content": content,
            }
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "dynamic_ui_response",
                "strict": True,
                "schema": UI_RESPONSE_SCHEMA,
            },
        },
    }

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "DynamicAI",
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(
            settings.OPENROUTER_URL,
            headers=headers,
            json=payload,
        )

    if response.status_code == 429:
        raise RuntimeError(
            "Il modello gratuito è temporaneamente occupato. Riprova tra poco oppure cambia modello."
        )

    if response.status_code >= 400:
        raise RuntimeError(f"OpenRouter error {response.status_code}: {response.text}")

    data = response.json()

    try:
        text = data["choices"][0]["message"]["content"].strip()
        print("RAW MODEL CONTENT:")
        print(text)

        text = strip_markdown_fences(text)
        parsed = json.loads(text)

        print("PARSED MODEL JSON:")
        print(parsed)

        if "action_type" in parsed and "payload" in parsed:
            recovered = recover_action_payload_format(parsed)
            if recovered is not None:
                print("RECOVERED FROM action_type/payload FORMAT:")
                print(recovered)
                return normalize_response_data(recovered)

        return normalize_response_data(parsed)

    except Exception as e:
        print("PARSING ERROR:", str(e))
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


async def call_openai_for_initial_analysis(file_infos):
    file_names = ", ".join(f["original_name"] for f in file_infos)

    prompt = f"""
Sei un planner di troubleshooting operativo per oggetti fisici reali.

L'utente ha caricato questi file: {file_names}.

Analizza i contenuti disponibili e genera SOLO il prossimo step di una GUI dinamica per diagnosi guidata.
Non sei un chatbot generico.
Non proporre azioni come "salva", "annulla", "rivedi".

Scegli il componente UI più adatto tra:
- "button_group" per una scelta singola
- "checklist" per selezionare più sintomi o condizioni
- "slider" per indicare gravità, intensità o livello del problema

Restituisci SOLO un JSON con questa struttura esatta:
{{
  "step_id": "string",
  "reply": "string",
  "ui_components": [
    {{
      "component": "button_group" | "checklist" | "slider",
      "label": "string",
      "options": ["string", "string", "string"],
      "min_value": 0,
      "max_value": 10,
      "step": 1
    }}
  ]
}}

Regole obbligatorie:
- genera un solo step
- genera un solo componente in ui_components
- preferisci un button_group per il primo step iniziale della diagnosi
- usa solo button_group, checklist o slider
- se usi button_group o checklist, genera SEMPRE almeno 3 options realistiche, specifiche e in italiano
- non usare placeholder come "Opzione 1", "Opzione 2", "Opzione 3"
- se usi slider, includi min_value, max_value e step
- tutto deve essere in italiano
- non usare markdown
- non usare ```json
- non aggiungere testo fuori dal JSON
- non restituire mai chiavi come action_type o payload
- non dedurre componenti interni specifici se non chiaramente visibili nell'immagine
- usa ipotesi prudenti e progressive
""".strip()

    return await call_openrouter_json(prompt, file_infos=file_infos)


async def call_openai_for_next_step(
    session_id: str,
    step_id: str,
    action_type: str,
    payload: dict,
):
    session = SESSIONS.get(session_id)
    if not session:
        return {
            "step_id": "fallback_step",
            "reply": "Sessione non trovata. Ricarica il file e riprova.",
            "ui_components": [
                {
                    "component": "button_group",
                    "label": "Scegli come continuare",
                    "options": ["Ricomincia"],
                }
            ],
        }

    stato = session.setdefault(
        "stato_analisi",
        {
            "problemi_sospetti": None,
            "sintomi_osservati": [],
            "gravità_stimata": None,
            "concentrazione_attuale": None,
        },
    )

    selected = payload.get("selected_option")
    selected_list = payload.get("selected_options")
    slider_value = payload.get("value")

    if action_type == "button_group_submit" and selected:
        stato["concentrazione_attuale"] = selected

    if action_type == "checklist_submit" and isinstance(selected_list, list):
        stato["sintomi_osservati"] = selected_list
        stato["concentrazione_attuale"] = "raccolta_sintomi"

    if action_type == "slider_submit" and slider_value is not None:
        stato["gravità_stimata"] = slider_value
        stato["concentrazione_attuale"] = "stima_gravità"

    prompt = build_next_step_prompt(
        session=session,
        step_id=step_id,
        action_type=action_type,
        payload=payload,
    )

    return await call_openrouter_json(prompt=prompt, file_infos=session.get("files", []))


def build_next_step_prompt(session: dict, step_id: str, action_type: str, payload: dict) -> str:
    files = session.get("files", [])
    history = session.get("history", [])
    stato_analisi = session.get("stato_analisi", {})

    file_names = ", ".join(f.get("original_name", "file") for f in files)

    history_lines = []
    for turn in history[-6:]:
        if turn["role"] == "assistant":
            history_lines.append(
                f"Assistant step={turn.get('step_id')}: {turn.get('reply')}"
            )
        else:
            history_lines.append(
                f"User action={turn.get('action_type')} payload={json.dumps(turn.get('payload', {}), ensure_ascii=False)}"
            )

    history_text = "\n".join(history_lines) if history_lines else "Nessuna cronologia precedente."

    return f"""
Sei un planner di troubleshooting operativo per attività fisiche complesse.

L'utente NON usa testo libero: interagisce solo tramite componenti GUI dinamici.

File caricati: {file_names}
Step corrente: {step_id}

Ultima azione utente:
- action_type: {action_type}
- payload: {json.dumps(payload, ensure_ascii=False)}

Stato attuale dell'analisi:
{json.dumps(stato_analisi, ensure_ascii=False)}

Cronologia recente:
{history_text}

Genera SOLO il prossimo step della GUI.

Restituisci SOLO un JSON con questa struttura esatta:
{{
  "step_id": "string",
  "reply": "string",
  "ui_components": [
    {{
      "component": "button_group" | "checklist" | "slider",
      "label": "string",
      "options": ["string", "string", "string"],
      "min_value": 0,
      "max_value": 10,
      "step": 1
    }}
  ]
}}

Regole obbligatorie:
- non sei un chatbot generico
- non usare markdown
- non usare ```json
- non aggiungere testo fuori dal JSON
- non ripetere il passo precedente
- un solo step
- un solo componente
- usa solo button_group, checklist o slider
- tutto in italiano
- sii progressivo, prudente e concreto
- se usi button_group o checklist, genera options vere e specifiche
- non usare mai placeholder come "Opzione 1"
- non restituire mai chiavi come action_type o payload
- non restituire un input utente simulato
- restituisci solo il prossimo step renderizzabile dal frontend
""".strip()