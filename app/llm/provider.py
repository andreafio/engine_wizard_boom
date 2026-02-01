"""LLM provider interface and prompts."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """Generate text completion.
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        pass
    
    @abstractmethod
    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Generate structured JSON response.
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            schema: Expected JSON schema
            
        Returns:
            Parsed JSON object
        """
        pass


class ProviderFactory:
    """Factory for creating LLM providers."""
    
    @staticmethod
    def create(provider_name: str, api_key: str, model: str) -> LLMProvider:
        """Create an LLM provider instance.
        
        Args:
            provider_name: Provider type (openai, gemini, claude)
            api_key: API key
            model: Model name
            
        Returns:
            LLMProvider instance
        """
        if provider_name == "openai":
            from app.llm.openai_provider import OpenAIProvider
            return OpenAIProvider(api_key, model)
        elif provider_name == "gemini":
            from app.llm.gemini_provider import GeminiProvider
            return GeminiProvider(api_key, model)
        elif provider_name == "claude":
            from app.llm.claude_provider import ClaudeProvider
            return ClaudeProvider(api_key, model)
        else:
            raise ValueError(f"Unknown provider: {provider_name}")
