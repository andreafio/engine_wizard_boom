"""Anthropic Claude provider implementation."""
import json
from typing import Any, Dict, Optional
from anthropic import AsyncAnthropic
from app.llm.provider import LLMProvider
from app.core.logging import get_logger

logger = get_logger(__name__)


class ClaudeProvider(LLMProvider):
    """Anthropic Claude LLM provider."""
    
    def __init__(self, api_key: str, model: str):
        """Initialize Claude provider.
        
        Args:
            api_key: Anthropic API key
            model: Model name (e.g., claude-3-sonnet-20240229)
        """
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
    
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """Generate text completion using Claude."""
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt or "",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            logger.error("claude_error", error=str(e))
            raise
    
    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Generate structured JSON using Claude."""
        json_instruction = "\n\nYou MUST respond with valid JSON only. No other text."
        full_prompt = prompt + json_instruction
        
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,
                system=system_prompt or "",
                messages=[
                    {"role": "user", "content": full_prompt}
                ]
            )
            
            content = response.content[0].text.strip()
            # Remove markdown code blocks if present
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            
            return json.loads(content.strip())
        except json.JSONDecodeError as e:
            logger.error("json_parse_error", error=str(e), content=content)
            raise
        except Exception as e:
            logger.error("claude_json_error", error=str(e))
            raise
