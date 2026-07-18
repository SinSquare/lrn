"""LLM client helpers."""

import json

from google import genai

from lrn.models.process import ComparisonResult, IncidentTriage, ReviewResult
from lrn.prompts import COMPARE_SYSTEM_PROMPT, REVIEW_SYSTEM_PROMPT
from lrn.state import get_config

GEMINI_FLASH_LITE = "gemini-2.5-flash-lite"
GEMINI_FLASH = "gemini-3.5-flash"


async def triage_message(
    prompt: str,
    message: str,
) -> IncidentTriage:
    """Call Gemini Flash Lite to triage a message into IncidentTriage."""
    config = get_config()
    client = genai.Client(api_key=config.gemini_api_key)
    response = await client.aio.models.generate_content(
        model=GEMINI_FLASH_LITE,
        contents=message,
        config={
            "system_instruction": prompt,
            "response_mime_type": "application/json",
            "response_json_schema": IncidentTriage.model_json_schema(),
        },
    )
    if not response.text:
        raise ValueError("Empty response from Gemini")
    return IncidentTriage.model_validate_json(response.text)


async def review_message(
    prompt: str,
    message: str,
) -> ReviewResult:
    """Call Gemini 3.5 Flash for expected triage output and an improved prompt."""
    config = get_config()
    client = genai.Client(api_key=config.gemini_api_key)
    payload = {
        "system_prompt_used": prompt,
        "incident_message": message,
    }
    response = await client.aio.models.generate_content(
        model=GEMINI_FLASH,
        contents=json.dumps(payload, indent=2),
        config={
            "system_instruction": REVIEW_SYSTEM_PROMPT,
            "response_mime_type": "application/json",
            "response_json_schema": ReviewResult.model_json_schema(),
        },
    )
    if not response.text:
        raise ValueError("Empty review response from Gemini")
    return ReviewResult.model_validate_json(response.text)


async def compare_outputs(
    expected_output: IncidentTriage,
    actual_output: IncidentTriage,
) -> ComparisonResult:
    """Score actual vs expected triage field-by-field with Flash Lite."""
    config = get_config()
    client = genai.Client(api_key=config.gemini_api_key)
    payload = {
        "expected_output": expected_output.model_dump(mode="json"),
        "actual_output": actual_output.model_dump(mode="json"),
    }
    response = await client.aio.models.generate_content(
        model=GEMINI_FLASH_LITE,
        contents=json.dumps(payload, indent=2),
        config={
            "system_instruction": COMPARE_SYSTEM_PROMPT,
            "response_mime_type": "application/json",
            "response_json_schema": ComparisonResult.model_json_schema(),
        },
    )
    if not response.text:
        raise ValueError("Empty comparison response from Gemini")
    return ComparisonResult.model_validate_json(response.text)
