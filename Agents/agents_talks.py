# top of file
from datetime import datetime, timezone

def utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

import requests
import json
import re
from typing import Any, Dict, List, Optional

def normalize_tags(tags_in):
    fixes = {
        "deep learning": "deep-learning",
        "llms": "large-language-models",
        "datascience": "data-science",
        "datcloud": "datacloud",
        "ml ops": "mlops",
    }
    out = []
    for t in tags_in or []:
        t = (t or "").strip().lower().replace(" ", "-")
        t = fixes.get(t, t)
        if t and t not in out:
            out.append(t)
        if len(out) == 3:
            break
    while len(out) < 3:
        out.append("topic")
    return out[:3]



OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:3b"   


# --------------------------
# Low-level LLM helpers
# --------------------------
def _post_ollama(prompt: str, model: str = MODEL_NAME, stream: bool = False, options: Optional[dict] = None) -> str:
    payload = {"model": model, "prompt": prompt, "stream": stream}
    if options:
        payload["options"] = options
    r = requests.post(OLLAMA_URL, json=payload, timeout=180)
    r.raise_for_status()
    data = r.json()
    return data.get("response", "")

FENCE_RE = re.compile(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", re.IGNORECASE)
CURLY_RE = re.compile(r"\{[\s\S]*\}")

def _try_parse_json(text: str) -> Optional[dict]:
    text = text.strip()

    # Case 1: Plain JSON
    try:
        return json.loads(text)
    except Exception:
        pass

    # Case 2: JSON fenced code block
    m = FENCE_RE.search(text)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass

    # Case 3: Largest {...} block
    m = CURLY_RE.search(text)
    if m:
        candidate = m.group(0)
        try:
            return json.loads(candidate)
        except Exception:
            pass

    return None

def call_llm_json(prompt: str, required_keys: List[str], max_retries: int = 3) -> dict:
    """
    Calls the LLM and *forces* a JSON object containing the required keys.
    Retries with a progressively stricter instruction if parsing fails.
    """
    base_instruction = (
        "Return ONLY valid minified JSON (no prose, no markdown). "
        "Do not add explanations. Ensure all required keys are present."
    )
    extra_guard = "\nIf you cannot comply, return an empty JSON object {}."

    last_err = None
    for i in range(max_retries):
        composed = f"{prompt}\n\n{base_instruction}{extra_guard if i>0 else ''}"
        raw = _post_ollama(composed)
        obj = _try_parse_json(raw)
        if isinstance(obj, dict) and all(k in obj for k in required_keys):
            return obj
        last_err = raw

    # Final fallback to keep pipeline moving
    return {}

# --------------------------
# Agents
# --------------------------
def planner_agent(title: str, content: str) -> dict:
    """
    Returns:
    {
      "thought": str,
      "message": str,
      "data": {
        "tags": [str, str, str],
        "summary": str,
        "issues": []
      }
    }
    """
    prompt = f"""
You are the Planner. Analyze the blog and produce planning JSON.

Title: {title}
Content: {content}

Requirements:
- "thought": one sentence capturing the plan for the blog.
- "message": a crisp 1-2 sentence description of the topic.
- "data.tags": exactly 3 topical, specific tags (lowercase).
- "data.summary": ≤25 words, single sentence.
- "data.issues": empty list.

Schema:
{{
  "thought": "string",
  "message": "string",
  "data": {{
    "tags": ["tag-1","tag-2","tag-3"],
    "summary": "string (<=25 words)",
    "issues": []
  }}
}}
"""
    obj = call_llm_json(prompt, required_keys=["thought", "message", "data"])
    data = obj.get("data", {}) if isinstance(obj, dict) else {}
    tags = data.get("tags") if isinstance(data, dict) else None
    if not (isinstance(tags, list) and len(tags) == 3):
        data["tags"] = (tags or [])[:3]
        while len(data["tags"]) < 3:
            data["tags"].append("placeholder-tag")
    data.setdefault("issues", [])

    data["tags"] = normalize_tags(data.get("tags", []))

    obj["data"] = data
    return obj


def reviewer_agent(planner_json: dict) -> dict:
    """
    Returns:
    {
      "thought": str,
      "message": str,
      "data": {
        "tags": [str, str, str],
        "summary": str,
        "issues": []
      }
    }

    (Reviewer provides its own concise message/summary & may tweak tags;
     keep 'issues' as [] for parity with your example.)
    """
    prompt = f"""
You are the Reviewer. Here is the planner JSON:
{json.dumps(planner_json, ensure_ascii=False)}

Provide a brief review JSON with this schema:
{{
  "thought": "one sentence reviewer perspective",
  "message": "1-2 sentence refined explanation",
  "data": {{
    "tags": ["tag-1","tag-2","tag-3"],   // can be the same or slightly revised
    "summary": "≤25 words reviewer summary",
    "issues": []
  }}
}}
"""
    obj = call_llm_json(prompt, required_keys=["thought", "message", "data"])
    data = obj.get("data", {}) if isinstance(obj, dict) else {}
    data.setdefault("issues", [])
    tags = data.get("tags", [])
    if not isinstance(tags, list):
        tags = []
    tags = tags[:3]
    while len(tags) < 3:
        tags.append("placeholder-tag")
    data["tags"] = normalize_tags(tags)      
    obj["data"] = data
    return obj


def cap_25w(text: str) -> str:
    words = str(text or "").split()
    return " ".join(words[:25])

def finalizer_agent(title: str, content: str, planner_json: dict, reviewer_json: dict) -> dict:
    """
    Produces both the 'Finalized Output' and the 'Publish Package' structure.
    """
    # Choose tags (prefer reviewer's, else planner's) and normalize
    rv_tags = normalize_tags((reviewer_json.get("data", {}) or {}).get("tags", []))
    pl_tags = normalize_tags((planner_json.get("data", {}) or {}).get("tags", []))
    tags = rv_tags if rv_tags else pl_tags

    # Ask LLM for a concise final message & summary (using the chosen tags)
    prompt = f"""
You are the Finalizer. Given the blog and prior agents, craft the final message & summary.

Title: {title}
Content: {content}

Planner JSON: {json.dumps(planner_json, ensure_ascii=False)}
Reviewer JSON: {json.dumps(reviewer_json, ensure_ascii=False)}

Use EXACTLY these tags (keep order): {tags}

Return JSON:
{{
  "thought": "one sentence explaining the final synthesis",
  "message": "1-2 sentences, clear and neutral",
  "data": {{
    "tags": {json.dumps(tags)},
    "summary": "≤25 words single sentence",
    "issues": []
  }}
}}
"""
    finalized = call_llm_json(prompt, required_keys=["thought", "message", "data"])

    # Harden + normalize
    finalized.setdefault("data", {})
    finalized["data"].setdefault("tags", tags)
    finalized["data"].setdefault("issues", [])
    finalized["data"]["tags"] = normalize_tags(finalized["data"].get("tags", tags))
    finalized["data"]["summary"] = cap_25w(finalized["data"].get("summary", ""))

    # Build publish package (NO email field; timestamp from Python)
    publish = {
        "title": title,
        "content": content.strip(),
        "agents": [
            {"role": "Planner", "content": planner_json.get("message", "")},
            {"role": "Reviewer", "content": reviewer_json.get("message", "")},
        ],
        "final": {
            "tags": finalized["data"]["tags"],
            "summary": finalized["data"]["summary"],
            "issues": finalized["data"]["issues"],
        },
        "submissionDate": utc_iso(),
    }

    return {"finalized": finalized, "publish": publish}


# --------------------------
# Pretty printers
# --------------------------
def print_section(title: str):
    print(f"\n--- {title} ---")

def pretty(obj: Any) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)

# --------------------------
# Main
# --------------------------
if __name__ == "__main__":
    # New topic: Deep Learning LLMs & Data Cloud
    title = "Deep Learning LLMs and the Data Cloud"
    content = (
        "Modern deep learning has enabled large language models (LLMs) that perform reasoning, summarization, and code generation. "
        "Operationalizing LLMs at scale increasingly relies on the data cloud—platforms like Snowflake, BigQuery, and Databricks—"
        "for governed data access, feature pipelines, vector search, and cost-aware orchestration. "
        "Techniques such as retrieval-augmented generation (RAG), fine-tuning, and prompt engineering integrate enterprise data "
        "with foundation models while preserving governance and observability. "
        "MLOps for LLMs covers evaluation, safety, monitoring for drift/toxicity/PII, and pipeline automation to reliably move "
        "from experimentation to production."
    )

    print("Multi-Agent Blog Packaging\n" + "="*60)

    # Planner
    print_section("Planner (JSON)")
    planner_json = planner_agent(title, content)
    print(pretty(planner_json))

    # Reviewer
    print_section("Reviewer (JSON)")
    reviewer_json = reviewer_agent(planner_json)
    print(pretty(reviewer_json))

    # Finalizer + Publish
    print_section("Finalized Output")
    bundle = finalizer_agent(title, content, planner_json, reviewer_json)
    print(pretty(bundle["finalized"]))

    print_section("Publish Package")
    print(pretty(bundle["publish"]))
