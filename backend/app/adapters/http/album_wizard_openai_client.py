"""
LangChain-based OpenAI client wrapper for Album Wizard.
"""

from typing import Optional
import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI


class AlbumWizardOpenAiClient:
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str],
        model_id: str,
        timeout_seconds: float,
    ):
        resolved_base_url = (base_url or "https://api.openai.com/v1").rstrip("/")
        if resolved_base_url.endswith("/responses"):
            resolved_base_url = resolved_base_url[: -len("/responses")]

        self._logger = logging.getLogger(__name__)
        self._llm = ChatOpenAI(
            model=model_id,
            openai_api_key=api_key,
            base_url=resolved_base_url,
            timeout=timeout_seconds,
            temperature=1
        )
        
    @staticmethod
    def _extract_text_content(content: object) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    text = item.get("text")
                    if isinstance(text, str):
                        parts.append(text)
            if parts:
                return "\n".join(parts)
        return ""

    async def analyze(self, system_prompt: str, user_prompt: str, image_data_url: str) -> dict:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=[
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": image_data_url}},
                ]
            ),
        ]
        response = await self._llm.ainvoke(messages)
        self._logger.debug("Album Wizard raw response: %s", response)

        output_text = self._extract_text_content(response.content)
        self._logger.error("RESULT: %s", output_text)
        if not output_text:
            self._logger.error(
                "Album Wizard response missing text content: response=%s",
                response,
            )
            raise ValueError("Album Wizard response missing text content.")

        try:
            parsed = json.loads(output_text)
        except json.JSONDecodeError:
            self._logger.error("Album Wizard response invalid JSON: %s", output_text)
            raise

        if isinstance(parsed, dict):
            return parsed
        return {"result": parsed}
