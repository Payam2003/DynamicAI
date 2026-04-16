import json
import base64
import httpx

from app.config import settings


WORKFLOW_UI_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "summary": {"type": "string"},
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "components": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "component": {
                                    "type": "string",
                                    "enum": [
                                        "checkbox_group",
                                        "radio_group",
                                        "button_group",
                                        "slider",
                                        "select",
                                        "textarea",
                                        "alert",
                                        "info_card",
                                    ],
                                },
                                "label": {"type": "string"},
                                "options": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "min_value": {"type": "integer"},
                                "max_value": {"type": "integer"},
                                "step": {"type": "integer"},
                                "text": {"type": "string"},
                                "placeholder": {"type": "string"},
                                "status": {"type": "string"},
                                "title_text": {"type": "string"},
                                "description_text": {"type": "string"},
                            },
                            "required": ["component"],
                            "additionalProperties": True,
                        },
                    },
                },
                "required": ["id", "title", "description", "components"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["title", "summary", "sections"],
    "additionalProperties": False,
}


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
                        "Se non riesci a leggerlo nativamente, usa solo il contesto disponibile "
                        "e genera comunque un'interfaccia coerente orientata al task."
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


def normalize_workflow_ui_response(data: dict) -> dict:
    allowed_components = {
        "checkbox_group",
        "radio_group",
        "button_group",
        "slider",
        "select",
        "textarea",
        "alert",
        "info_card",
    }

    if not isinstance(data, dict):
        return {
            "title": "Interfaccia dinamica di fallback",
            "summary": "La risposta del modello non era un oggetto JSON valido.",
            "sections": [
                {
                    "id": "section_1",
                    "title": "Sezione di fallback",
                    "description": "Generata perché il modello ha restituito una struttura non valida.",
                    "components": [
                        {
                            "component": "info_card",
                            "label": "Struttura non valida",
                            "text": "Il modello non ha restituito un oggetto JSON valido.",
                        }
                    ],
                }
            ],
        }

    if not data.get("title"):
        data["title"] = "Interfaccia dinamica generata"

    if not data.get("summary"):
        data["summary"] = "Interfaccia orientata al task generata a partire dall'input caricato."

    sections = data.get("sections", [])
    normalized_sections = []

    for section_index, section in enumerate(sections):
        if not isinstance(section, dict):
            continue

        normalized_section = {
            "id": section.get("id", f"section_{section_index + 1}"),
            "title": section.get("title", f"Sezione {section_index + 1}"),
            "description": section.get("description", "Sezione generata automaticamente."),
            "components": [],
        }

        for component in section.get("components", []):
            if not isinstance(component, dict):
                continue

            component_type = component.get("component")
            if component_type not in allowed_components:
                continue

            normalized_component = {"component": component_type}

            if "label" in component:
                normalized_component["label"] = component["label"]

            if component_type in {
                "checkbox_group",
                "radio_group",
                "button_group",
                "select",
            }:
                raw_options = component.get("options", [])

                if isinstance(raw_options, str):
                    raw_options = [opt.strip() for opt in raw_options.split(",") if opt.strip()]
                elif not isinstance(raw_options, list):
                    raw_options = []

                normalized_component["options"] = [
                    str(opt) for opt in raw_options if str(opt).strip()
                ]

                if not normalized_component["options"]:
                    normalized_component["options"] = [
                        "Opzione A",
                        "Opzione B",
                        "Opzione C",
                    ]

            if component_type == "slider":
                try:
                    normalized_component["min_value"] = int(component.get("min_value", 0))
                except Exception:
                    normalized_component["min_value"] = 0

                try:
                    normalized_component["max_value"] = int(component.get("max_value", 10))
                except Exception:
                    normalized_component["max_value"] = 10

                try:
                    normalized_component["step"] = int(component.get("step", 1))
                except Exception:
                    normalized_component["step"] = 1

                if "label" not in normalized_component:
                    normalized_component["label"] = "Seleziona un valore"

            if component_type == "textarea":
                normalized_component["placeholder"] = component.get(
                    "placeholder",
                    "Scrivi qui le tue note",
                )
                if "label" not in normalized_component:
                    normalized_component["label"] = "Note"

            if component_type == "alert":
                normalized_component["status"] = component.get("status", "info")
                normalized_component["title_text"] = component.get(
                    "title_text",
                    component.get("label", "Avviso"),
                )
                normalized_component["description_text"] = component.get(
                    "description_text",
                    component.get("text", ""),
                )

            if component_type == "info_card":
                normalized_component["label"] = component.get("label", "Informazione")
                normalized_component["text"] = component.get(
                    "text",
                    "Nessuna informazione aggiuntiva disponibile.",
                )

            normalized_section["components"].append(normalized_component)

        if not normalized_section["components"]:
            normalized_section["components"] = [
                {
                    "component": "info_card",
                    "label": "Sezione di fallback",
                    "text": "Il modello ha generato una sezione vuota, quindi è stato inserito un blocco di fallback.",
                }
            ]

        normalized_sections.append(normalized_section)

    if not normalized_sections:
        normalized_sections = [
            {
                "id": "section_1",
                "title": "Sezione generata",
                "description": "Sezione di fallback generata dal backend.",
                "components": [
                    {
                        "component": "info_card",
                        "label": "Interfaccia di fallback",
                        "text": "La risposta del modello era incompleta. È stata generata una sezione di fallback.",
                    }
                ],
            }
        ]

    data["sections"] = normalized_sections
    return data


async def generate_workflow_ui(file_infos: list[dict]) -> dict:
    file_names = ", ".join(f.get("original_name", "file") for f in file_infos)

    prompt = f"""
Sei un sistema LLM per la progettazione di interfacce dinamiche per task fisici di troubleshooting.

L'utente ha caricato questi file: {file_names}.

Il tuo obiettivo NON è produrre una risposta da chatbot e NON è generare un flusso conversazionale step-by-step.
Devi invece inferire internamente un workflow di task e trasformarlo in una singola interfaccia dinamica composta da più sezioni strutturate.

Il workflow deve rimanere implicito.
Non devi esporlo come conversazione.
Non devi generare un singolo passo successivo.

Genera un'interfaccia orientata al task con:
- un titolo
- un breve sommario
- da 2 a 4 sezioni
- ogni sezione deve contenere uno o più componenti UI scelti dalla libreria consentita

Tipi di componenti consentiti:
- checkbox_group
- radio_group
- button_group
- slider
- select
- textarea
- alert
- info_card

Restituisci SOLO JSON valido con questa struttura:
{{
  "title": "string",
  "summary": "string",
  "sections": [
    {{
      "id": "string",
      "title": "string",
      "description": "string",
      "components": [
        {{
          "component": "checkbox_group | radio_group | button_group | slider | select | textarea | alert | info_card",
          "label": "string",
          "options": ["string", "string"],
          "min_value": 0,
          "max_value": 10,
          "step": 1,
          "placeholder": "string",
          "text": "string",
          "status": "info | warning | error | success",
          "title_text": "string",
          "description_text": "string"
        }}
      ]
    }}
  ]
}}

Regole:
- restituisci solo JSON
- non usare markdown
- non usare ```json
- non restituire messaggi da chat
- non restituire step_id
- non restituire reply
- non restituire ui_components
- genera sezioni che riflettano una sequenza temporale o funzionale implicita del task
- scegli componenti sensati per il troubleshooting fisico
- mantieni l'interfaccia coerente, compatta e interamente in italiano
""".strip()

    content = build_openrouter_content(prompt, file_infos)

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
                "name": "workflow_ui_response",
                "strict": True,
                "schema": WORKFLOW_UI_SCHEMA,
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
            "Il modello gratuito è temporaneamente occupato. Riprova tra poco."
        )

    if response.status_code >= 400:
        raise RuntimeError(f"OpenRouter error {response.status_code}: {response.text}")

    raw = response.json()
    text = raw["choices"][0]["message"]["content"].strip()
    text = strip_markdown_fences(text)

    print("RAW WORKFLOW MODEL CONTENT:")
    print(text)

    try:
        parsed = json.loads(text)
    except Exception:
        return {
            "title": "Interfaccia dinamica di fallback",
            "summary": "La risposta del modello non è stata interpretata correttamente, quindi è stata generata un'interfaccia di fallback.",
            "sections": [
                {
                    "id": "section_1",
                    "title": "Sezione di fallback",
                    "description": "Generata a causa di un output non valido del modello.",
                    "components": [
                        {
                            "component": "info_card",
                            "label": "Errore nell'output del modello",
                            "text": "Il modello ha restituito un formato di risposta non valido.",
                        }
                    ],
                }
            ],
        }

    return normalize_workflow_ui_response(parsed)