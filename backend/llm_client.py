"""Unified LLM interface supporting OpenAI, Anthropic, and Google Gemini.

Supports both standard API keys and custom gateways:
- OpenAI: standard API key, or custom base_url for gateways
- Anthropic: standard API key, or AWS Bedrock with bearer token
- Gemini: standard API key via google-genai SDK
"""

from __future__ import annotations

import asyncio
import logging
import os

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)

# Bedrock API keys are read from this env var by boto3; set once from settings.
if settings.claude_bearer_token:
    os.environ.setdefault("AWS_BEARER_TOKEN_BEDROCK", settings.claude_bearer_token)

# Bedrock model ID mapping (only used for Bedrock path)
BEDROCK_MODEL_MAP = {
    "claude-opus-4-6": "us.anthropic.claude-opus-4-6-v1",
    "claude-sonnet-4-20250514": "us.anthropic.claude-sonnet-4-20250514-v1:0",
    "claude-sonnet-4-5": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "claude-3-5-haiku-20241022": "us.anthropic.claude-3-5-haiku-20241022-v1:0",
}


class LLMClient:
    """Unified client for OpenAI, Anthropic, and Gemini LLM providers."""

    def __init__(self, provider: str | None = None, model: str | None = None):
        self.provider = provider or settings.llm_provider
        self.model = model or settings.llm_model

        if self.provider == "openai":
            self._init_openai()
        elif self.provider == "anthropic":
            self._init_anthropic()
        elif self.provider == "gemini":
            self._init_gemini()

    def _init_openai(self):
        import openai

        kwargs: dict = {}
        if settings.openai_base_url:
            # Custom gateway (e.g., Salesforce Research Gateway)
            kwargs["base_url"] = settings.openai_base_url
            kwargs["api_key"] = settings.openai_api_key
            kwargs["default_headers"] = {"X-Api-Key": settings.openai_api_key}
        elif settings.prismtrace_api_key:
            # Zero-code PRISM proxy: traces model calls without call-site changes.
            # Proxy reads the provider key from x-api-key (not only Authorization).
            host = settings.prismtrace_host.rstrip("/")
            kwargs["base_url"] = f"{host}/proxy/openai/v1"
            kwargs["api_key"] = settings.openai_api_key
            kwargs["default_headers"] = {
                "X-PRISMtrace-Key": settings.prismtrace_api_key,
                "x-api-key": settings.openai_api_key,
            }
        else:
            # Standard OpenAI API
            kwargs["api_key"] = settings.openai_api_key

        self._openai_client = openai.AsyncOpenAI(**kwargs)

    def _init_anthropic(self):
        if settings.claude_bearer_token:
            import boto3

            self._bedrock_client = boto3.client("bedrock-runtime", region_name="us-east-1")
            self._use_bedrock = True
        else:
            import anthropic

            kwargs: dict = {"api_key": settings.anthropic_api_key}
            if settings.prismtrace_api_key:
                host = settings.prismtrace_host.rstrip("/")
                kwargs["base_url"] = f"{host}/proxy/anthropic"
                kwargs["default_headers"] = {
                    "X-PRISMtrace-Key": settings.prismtrace_api_key,
                    "x-api-key": settings.anthropic_api_key,
                }
            self._anthropic_client = anthropic.AsyncAnthropic(**kwargs)
            self._use_bedrock = False

    def _init_gemini(self):
        self._gemini_proxy_url = None
        if settings.prismtrace_api_key:
            # PRISM accepts messages and returns content blocks, not Gemini's native schema.
            host = settings.prismtrace_host.rstrip("/")
            self._gemini_proxy_url = (
                f"{host}/proxy/gemini/v1beta/models/{self.model}:generateContent"
            )
            self._gemini_proxy_headers = {
                "X-PRISMtrace-Key": settings.prismtrace_api_key,
                "x-api-key": settings.gemini_api_key,
            }
        else:
            from google import genai

            self._gemini_client = genai.Client(api_key=settings.gemini_api_key)

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        """Send a completion request and return the text response."""
        if self.provider == "openai":
            return await self._complete_openai(system_prompt, user_prompt, temperature, max_tokens)
        elif self.provider == "anthropic":
            if self._use_bedrock:
                return await self._complete_bedrock(
                    system_prompt, user_prompt, temperature, max_tokens
                )
            return await self._complete_anthropic(
                system_prompt, user_prompt, temperature, max_tokens
            )
        elif self.provider == "gemini":
            return await self._complete_gemini(system_prompt, user_prompt, temperature, max_tokens)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    async def _complete_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        response = await self._openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    async def _complete_anthropic(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        response = await self._anthropic_client.messages.create(
            model=self.model,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return "".join(block.text for block in response.content if block.type == "text")

    async def _complete_bedrock(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        model_id = BEDROCK_MODEL_MAP.get(self.model, self.model)
        response = await asyncio.to_thread(
            self._bedrock_client.converse,
            modelId=model_id,
            messages=[{"role": "user", "content": [{"text": user_prompt}]}],
            system=[{"text": system_prompt}],
            inferenceConfig={"maxTokens": max_tokens, "temperature": temperature},
        )
        return "".join(
            block["text"] for block in response["output"]["message"]["content"] if "text" in block
        )

    async def _complete_gemini(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        if self._gemini_proxy_url:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self._gemini_proxy_url,
                    headers=self._gemini_proxy_headers,
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                )
                response.raise_for_status()
                return "".join(
                    block["text"]
                    for block in response.json()["content"]
                    if block.get("type") == "text"
                )

        from google.genai import types

        response = await asyncio.to_thread(
            self._gemini_client.models.generate_content,
            model=self.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        return response.text or ""
