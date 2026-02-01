"""OpenAI provider implementation."""
import json
from typing import Any, Dict, Optional
from openai import AsyncOpenAI
from app.llm.provider import LLMProvider
from app.core.logging import get_logger

logger = get_logger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""
    
    def __init__(self, api_key: str, model: str):
        """Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            model: Model name (e.g., gpt-4o-mini)
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
    
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """Generate text completion using OpenAI."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("openai_error", error=str(e))
            raise
    
    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Generate structured JSON using OpenAI."""
        # Add JSON instruction to system prompt
        json_instruction = "\n\nYou MUST respond with valid JSON only. No other text."
        full_system_prompt = (system_prompt or "") + json_instruction
        
        messages = []
        if full_system_prompt:
            messages.append({"role": "system", "content": full_system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,  # Lower temp for structured output
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error("json_parse_error", error=str(e), content=content)
            raise
        except Exception as e:
            logger.error("openai_json_error", error=str(e))
            raise
