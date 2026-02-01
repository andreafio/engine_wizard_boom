"""Google Gemini provider implementation."""
import json
from typing import Any, Dict, Optional
import google.generativeai as genai
from app.llm.provider import LLMProvider
from app.core.logging import get_logger

logger = get_logger(__name__)


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider."""
    
    def __init__(self, api_key: str, model: str):
        """Initialize Gemini provider.
        
        Args:
            api_key: Google API key
            model: Model name (e.g., gemini-pro)
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self.model_name = model
    
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """Generate text completion using Gemini."""
        # Gemini doesn't have async API in the same way, using sync
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )
            
            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            return response.text
        except Exception as e:
            logger.error("gemini_error", error=str(e))
            raise
    
    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Generate structured JSON using Gemini."""
        json_instruction = "\n\nYou MUST respond with valid JSON only. No other text."
        full_prompt = prompt + json_instruction
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{full_prompt}"
        
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=2000
            )
            
            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            content = response.text.strip()
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
            logger.error("gemini_json_error", error=str(e))
            raise
