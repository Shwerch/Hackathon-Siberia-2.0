import json
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Literal, Optional
from openai import APITimeoutError, AsyncOpenAI, BadRequestError
from app.config import settings
from app.models.usage import CallLogEntry

logger = logging.getLogger("uvicorn.error")


class TrackedLLMClient:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key or "no-key",
            base_url=settings.openai_base_url,
            timeout=settings.llm_timeout_seconds,
            max_retries=0,
        )

    @staticmethod
    def strip_thinking(text: str) -> str:
        # Убираем как закрытые, так и оборванные блоки <think>
        cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        cleaned = re.sub(r"<think>.*$", "", cleaned, flags=re.DOTALL)
        return cleaned.strip()

    async def chat_completion(
        self,
        *,
        session_id: str,
        turn_id: int,
        purpose: Literal["extract_intent", "generate_reply"],
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 2400,
        json_mode: bool = False,
    ) -> tuple[str, CallLogEntry]:
        call_id = str(uuid.uuid4())
        started_dt = datetime.now(timezone.utc)
        t0 = time.perf_counter()

        kwargs: dict[str, Any] = {
            "model": settings.model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        status: Literal["ok", "error", "timeout"] = "ok"
        error_msg: Optional[str] = None
        content = ""
        provider_response_id: Optional[str] = None
        usage_status: Literal["confirmed", "unknown"] = "unknown"
        in_tok: Optional[int] = None
        out_tok: Optional[int] = None
        cached_tok: Optional[int] = None
        reasoning_tok: Optional[int] = None
        actual_cost: Optional[float] = None

        try:
            try:
                resp = await self.client.chat.completions.create(**kwargs)
            except BadRequestError:
                if "response_format" in kwargs:
                    kwargs.pop("response_format")
                    resp = await self.client.chat.completions.create(**kwargs)
                else:
                    raise

            provider_response_id = getattr(resp, "id", None)
            raw_content = resp.choices[0].message.content or ""
            content = self.strip_thinking(raw_content)

            if not content:
                status = "error"
                error_msg = "Модель вернула пустой content (возможно, весь лимит ушёл в reasoning/think)"
                logger.warning("LLM empty content [%s], finish_reason=%s", purpose, resp.choices[0].finish_reason)

            usage = getattr(resp, "usage", None)
            if usage is not None and getattr(usage, "prompt_tokens", None) is not None:
                usage_status = "confirmed"
                in_tok = int(usage.prompt_tokens)
                out_tok = int(getattr(usage, "completion_tokens", 0) or 0)
                prompt_details = getattr(usage, "prompt_tokens_details", None)
                if prompt_details is not None:
                    cached_tok = getattr(prompt_details, "cached_tokens", None)
                comp_details = getattr(usage, "completion_tokens_details", None)
                if comp_details is not None:
                    reasoning_tok = getattr(comp_details, "reasoning_tokens", None)
                raw_cost = getattr(usage, "cost", None)
                if raw_cost is not None:
                    actual_cost = float(raw_cost)
        except (APITimeoutError, TimeoutError) as exc:
            status = "timeout"
            error_msg = str(exc)
            logger.error("LLM timeout [%s]: %s", purpose, exc)
        except Exception as exc:
            status = "error"
            error_msg = str(exc)
            logger.error("LLM error [%s]: %s", purpose, exc)

        finished_dt = datetime.now(timezone.utc)
        duration_ms = round((time.perf_counter() - t0) * 1000, 2)

        eval_in: Optional[float] = None
        eval_out: Optional[float] = None
        eval_total: Optional[float] = None
        if usage_status == "confirmed" and in_tok is not None and out_tok is not None:
            eval_in = (in_tok * settings.input_price_per_1m) / 1_000_000
            eval_out = (out_tok * settings.output_price_per_1m) / 1_000_000
            eval_total = eval_in + eval_out

        entry = CallLogEntry(
            session_id=session_id,
            turn_id=turn_id,
            call_id=call_id,
            model_id=settings.model_id,
            openrouter_model_id=settings.openrouter_model_id,
            provider=settings.provider_name,
            purpose=purpose,
            started_at=started_dt.isoformat(),
            finished_at=finished_dt.isoformat(),
            duration_ms=duration_ms,
            status=status,
            provider_response_id=provider_response_id,
            usage_status=usage_status,
            input_tokens=in_tok,
            output_tokens=out_tok,
            cached_tokens=cached_tok,
            reasoning_tokens=reasoning_tok,
            input_price_per_1m=settings.input_price_per_1m,
            output_price_per_1m=settings.output_price_per_1m,
            evaluation_input_cost_usd=eval_in,
            evaluation_output_cost_usd=eval_out,
            evaluation_cost_usd=eval_total,
            actual_cost_usd=actual_cost,
            error_message=error_msg,
        )
        return content, entry

    @staticmethod
    def parse_json_safe(raw: str) -> dict[str, Any]:
        cleaned = TrackedLLMClient.strip_thinking(raw)
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start : end + 1]
        return json.loads(cleaned)
