import httpx

from server.config import SARVAM_API_KEY


async def translate(text: str, source_lang: str, target_lang: str) -> str:
    if not text:
        return text
    if not SARVAM_API_KEY:
        return text
    if source_lang == target_lang:
        return text

    url = "https://api.sarvam.ai/translate"
    headers = {
        "Authorization": f"Bearer {SARVAM_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "mayura:v1",
        "input": text,
        "source_language_code": source_lang,
        "target_language_code": target_lang,
    }

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            body = response.json()
            translated = body.get("translated_text") or body.get("output") or text
            return translated if isinstance(translated, str) else text
    except Exception:
        return text
