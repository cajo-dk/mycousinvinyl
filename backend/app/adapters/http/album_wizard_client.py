"""
HTTP adapter for Album Wizard AI.
"""

from typing import Optional
from pathlib import Path

from app.application.ports.album_wizard_client import AlbumWizardClient, AlbumWizardAiResult
from app.adapters.http.album_wizard_openai_client import AlbumWizardOpenAiClient


class AlbumWizardClientAdapter(AlbumWizardClient):
    _SYSTEM_PROMPT_NAME = "wizard-system-prompt.txt"
    _USER_PROMPT_NAME = "wizard-user-prompt.txt"

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        model_id: Optional[str] = None,
        timeout_seconds: float = 30.0
    ):
        self._model_id = model_id
        self._openai_client = AlbumWizardOpenAiClient(
            base_url=base_url,
            api_key=api_key,
            model_id=model_id or "",
            timeout_seconds=timeout_seconds,
        )

    def _find_prompt_path(self, filename: str) -> Path:
        for parent in Path(__file__).resolve().parents:
            candidate = parent / filename
            if candidate.exists():
                return candidate
        raise ValueError(f"Prompt file not found: {filename}")

    def _load_prompt_text(self, filename: str) -> str:
        path = self._find_prompt_path(filename)
        return path.read_text(encoding="utf-8")

    def _normalize_ai_result(self, result: dict) -> AlbumWizardAiResult:
        if "image" not in result and "valid_image" in result:
            result["image"] = result["valid_image"]
        return result

    async def analyze_cover(self, image_data_url: str) -> AlbumWizardAiResult:
        if not self._model_id:
            raise ValueError("Album Wizard model ID is not configured.")

        system_prompt = self._load_prompt_text(self._SYSTEM_PROMPT_NAME)
        user_prompt = self._load_prompt_text(self._USER_PROMPT_NAME)

        parsed = await self._openai_client.analyze(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            image_data_url=image_data_url,
        )
        return self._normalize_ai_result(parsed)
