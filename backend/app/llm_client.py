from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Any, Optional

import httpx

from .config import Settings
from .storage import Storage, utc_now_iso

logger = logging.getLogger("uvicorn.error")


class LLMCallError(Exception):
    def __init__(self, message: str, retryable: bool = True) -> None:
        super().__init__(message)
        self.retryable = retryable


class LLMClient:
    def __init__(self, settings: Settings, storage: Storage) -> None:
        self.settings = settings
        self.storage = storage

    def _normalize_messages(self, messages: list[dict[str, str]]) -> list[dict[str, str]]:
        system_parts: list[str] = []
        others: list[dict[str, str]] = []
        for m in messages:
            if m.get("role") == "system":
                if m.get("content"):
                    system_parts.append(m["content"])
            else:
                others.append(m)
        normalized: list[dict[str, str]] = []
        if system_parts:
            normalized.append({"role": "system", "content": "\n\n".join(system_parts)})
        normalized.extend(others)
        return normalized

    async def chat_json(
        self,
        session_id: str,
        turn_id: int,
        purpose: str,
        messages: list[dict[str, str]],
    ) -> dict[str, Any]:
        if self.settings.llm_p_input_usd_per_1m > 0.10:
            raise LLMCallError(
                "Входной тариф модели превышает допустимый предел $0.10 за 1M токенов.",
                retryable=False,
            )

        call_id = f"call_{uuid.uuid4().hex}"
        started_at = utc_now_iso()
        url = f"{self.settings.llm_base_url.rstrip('/')}/chat/completions"

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.settings.llm_api_key.strip():
            headers["Authorization"] = f"Bearer {self.settings.llm_api_key.strip()}"

        payload: dict[str, Any] = {
            "model": self.settings.llm_model_id,
            "messages": self._normalize_messages(messages),
            "temperature": 0.1,
        }
        if self.settings.llm_use_response_format:
            payload["response_format"] = {"type": "json_object"}

        raw_usage: Optional[dict[str, Any]] = None
        provider_response_id: Optional[str] = None
        status = "ok"

        logger.info("Calling LLM at %s with model=%s", url, self.settings.llm_model_id)

        try:
            async with httpx.AsyncClient(
                timeout=self.settings.llm_timeout_seconds,
                trust_env=False,
            ) as client:
                resp = await client.post(url, headers=headers, json=payload)

            finished_at = utc_now_iso()

            if resp.status_code >= 400:
                status = f"http_{resp.status_code}"
                logger.error("LLM HTTP %s at %s: %s", resp.status_code, url, resp.text[:500])
                self._log_call(
                    call_id=call_id,
                    session_id=session_id,
                    turn_id=turn_id,
                    provider_response_id=None,
                    purpose=purpose,
                    started_at=started_at,
                    finished_at=finished_at,
                    status=status,
                    raw_usage=None,
                )
                raise LLMCallError(
                    f"Модельный API вернул ошибку {resp.status_code}: {resp.text[:200]}",
                    retryable=resp.status_code >= 500 or resp.status_code == 429,
                )

            data = resp.json()
            provider_response_id = data.get("id")
            raw_usage = data.get("usage")
            content = data["choices"][0]["message"]["content"]

            self._log_call(
                call_id=call_id,
                session_id=session_id,
                turn_id=turn_id,
                provider_response_id=provider_response_id,
                purpose=purpose,
                started_at=started_at,
                finished_at=finished_at,
                status=status,
                raw_usage=raw_usage,
            )

            return self._parse_json_content(content)

        except httpx.TimeoutException:
            finished_at = utc_now_iso()
            logger.error("LLM timeout at %s after %ss", url, self.settings.llm_timeout_seconds)
            self._log_call(
                call_id=call_id,
                session_id=session_id,
                turn_id=turn_id,
                provider_response_id=None,
                purpose=purpose,
                started_at=started_at,
                finished_at=finished_at,
                status="timeout",
                raw_usage=None,
            )
            raise LLMCallError(
                "Превышено время ожидания ответа от модели. Повторите запрос.",
                retryable=True,
            )
        except LLMCallError:
            raise
        except Exception as exc:
            finished_at = utc_now_iso()
            logger.exception("LLM error at %s: %s", url, exc)
            self._log_call(
                call_id=call_id,
                session_id=session_id,
                turn_id=turn_id,
                provider_response_id=provider_response_id,
                purpose=purpose,
                started_at=started_at,
                finished_at=finished_at,
                status="error",
                raw_usage=raw_usage,
            )
            raise LLMCallError(
                f"Ошибка взаимодействия с моделью ({url}): {exc}",
                retryable=True,
            )

    def _parse_json_content(self, content: str) -> dict[str, Any]:
        cleaned = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
            return {
                "intent": "design",
                "assistant_text": cleaned,
                "flows": [],
                "missing_fields": [],
                "unsupported_requests": [],
            }

    def _log_call(
        self,
        call_id: str,
        session_id: str,
        turn_id: int,
        provider_response_id: Optional[str],
        purpose: str,
        started_at: str,
        finished_at: str,
        status: str,
        raw_usage: Optional[dict[str, Any]],
    ) -> None:
        p_in = self.settings.llm_p_input_usd_per_1m
        p_out = self.settings.llm_p_output_usd_per_1m

        if raw_usage and raw_usage.get("prompt_tokens") is not None:
            prompt_tokens = int(raw_usage["prompt_tokens"])
            completion_tokens = int(raw_usage.get("completion_tokens") or 0)
            details_in = raw_usage.get("prompt_tokens_details") or {}
            details_out = raw_usage.get("completion_tokens_details") or {}
            cached_tokens = details_in.get("cached_tokens")
            reasoning_tokens = details_out.get("reasoning_tokens")

            est_in = (prompt_tokens * p_in) / 1_000_000.0
            est_out = (completion_tokens * p_out) / 1_000_000.0
            est_tot = est_in + est_out
            provider_cost = raw_usage.get("cost")
            usage_source = "api_response"
        else:
            prompt_tokens = None
            completion_tokens = None
            cached_tokens = None
            reasoning_tokens = None
            est_in = None
            est_out = None
            est_tot = None
            provider_cost = None
            usage_source = "unknown"

        self.storage.record_llm_call(
            {
                "call_id": call_id,
                "session_id": session_id,
                "turn_id": turn_id,
                "provider_response_id": provider_response_id,
                "model_id": self.settings.llm_model_id,
                "provider": self.settings.llm_provider,
                "purpose": purpose,
                "started_at": started_at,
                "finished_at": finished_at,
                "status": status,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "cached_tokens": cached_tokens,
                "reasoning_tokens": reasoning_tokens,
                "p_input": p_in,
                "p_output": p_out,
                "estimated_cost_input": est_in,
                "estimated_cost_output": est_out,
                "estimated_cost_total": est_tot,
                "provider_usage_cost": float(provider_cost)
                if provider_cost is not None
                else None,
                "usage_source": usage_source,
                "raw_usage": raw_usage,
            }
        )
