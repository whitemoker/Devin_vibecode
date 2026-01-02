"""
LLM client for making API calls to various providers.
Supports OpenAI, Anthropic, and other providers.
"""
import os
import json
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Response from an LLM API call."""
    content: str
    model: str
    provider: str
    usage: Dict[str, int]
    latency_ms: float
    raw_response: Optional[Any] = None


class BaseLLMClient(ABC):
    """Base class for LLM clients."""
    
    @abstractmethod
    def complete(self, messages: List[Dict], **kwargs) -> LLMResponse:
        """Make a completion request."""
        pass


class OpenAIClient(BaseLLMClient):
    """Client for OpenAI API."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", base_url: Optional[str] = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or "https://api.openai.com/v1"
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key, base_url=self.base_url)
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
    
    def complete(
        self, 
        messages: List[Dict], 
        temperature: float = 0.0,
        max_tokens: int = 2000,
        **kwargs
    ) -> LLMResponse:
        start_time = time.time()
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        return LLMResponse(
            content=response.choices[0].message.content,
            model=self.model,
            provider="openai",
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            latency_ms=latency_ms,
            raw_response=response
        )


class AnthropicClient(BaseLLMClient):
    """Client for Anthropic API."""
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key
        self.model = model
        
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
    
    def complete(
        self, 
        messages: List[Dict], 
        temperature: float = 0.0,
        max_tokens: int = 2000,
        **kwargs
    ) -> LLMResponse:
        start_time = time.time()
        
        # Convert messages format if needed
        system_message = None
        chat_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                chat_messages.append(msg)
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_message or "",
            messages=chat_messages,
            temperature=temperature,
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        return LLMResponse(
            content=response.content[0].text,
            model=self.model,
            provider="anthropic",
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            },
            latency_ms=latency_ms,
            raw_response=response
        )


class DeepSeekClient(BaseLLMClient):
    """Client for DeepSeek API (OpenAI-compatible)."""
    
    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.deepseek.com"
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key, base_url=self.base_url)
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
    
    def complete(
        self, 
        messages: List[Dict], 
        temperature: float = 0.0,
        max_tokens: int = 2000,
        **kwargs
    ) -> LLMResponse:
        start_time = time.time()
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        return LLMResponse(
            content=response.choices[0].message.content,
            model=self.model,
            provider="deepseek",
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            latency_ms=latency_ms,
            raw_response=response
        )


class MoonshotClient(BaseLLMClient):
    """Client for Kimi/Moonshot API (OpenAI-compatible)."""
    
    def __init__(self, api_key: str, model: str = "moonshot-v1-128k"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.moonshot.cn/v1"
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key, base_url=self.base_url)
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
    
    def complete(
        self, 
        messages: List[Dict], 
        temperature: float = 0.0,
        max_tokens: int = 2000,
        **kwargs
    ) -> LLMResponse:
        start_time = time.time()
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        return LLMResponse(
            content=response.choices[0].message.content,
            model=self.model,
            provider="moonshot",
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            latency_ms=latency_ms,
            raw_response=response
        )


class LLMClientFactory:
    """Factory for creating LLM clients."""
    
    @staticmethod
    def create(
        provider: str,
        model: str,
        api_key: Optional[str] = None,
        api_key_env: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> BaseLLMClient:
        """Create an LLM client based on provider."""
        
        # Get API key
        if api_key is None and api_key_env:
            api_key = os.environ.get(api_key_env)
        
        if not api_key:
            raise ValueError(f"API key not provided for {provider}")
        
        if provider == "openai":
            return OpenAIClient(api_key=api_key, model=model, base_url=base_url)
        elif provider == "anthropic":
            return AnthropicClient(api_key=api_key, model=model)
        elif provider == "deepseek":
            return DeepSeekClient(api_key=api_key, model=model)
        elif provider == "moonshot" or provider == "kimi":
            return MoonshotClient(api_key=api_key, model=model)
        else:
            raise ValueError(f"Unknown provider: {provider}")


class MultiModelClient:
    """Client that manages multiple LLM models for ensemble predictions."""
    
    def __init__(self):
        self.clients: Dict[str, BaseLLMClient] = {}
        self.weights: Dict[str, float] = {}
    
    def add_model(
        self, 
        name: str, 
        provider: str, 
        model: str,
        api_key: Optional[str] = None,
        api_key_env: Optional[str] = None,
        base_url: Optional[str] = None,
        weight: float = 1.0
    ):
        """Add a model to the ensemble."""
        try:
            client = LLMClientFactory.create(
                provider=provider,
                model=model,
                api_key=api_key,
                api_key_env=api_key_env,
                base_url=base_url
            )
            self.clients[name] = client
            self.weights[name] = weight
            logger.info(f"Added model: {name} ({provider}/{model})")
        except Exception as e:
            logger.warning(f"Failed to add model {name}: {e}")
    
    def complete_all(
        self, 
        messages: List[Dict],
        temperature: float = 0.0,
        max_tokens: int = 2000,
        **kwargs
    ) -> Dict[str, LLMResponse]:
        """Get completions from all models."""
        results = {}
        
        for name, client in self.clients.items():
            try:
                response = client.complete(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                results[name] = response
            except Exception as e:
                logger.error(f"Error from model {name}: {e}")
        
        return results
    
    def get_model_names(self) -> List[str]:
        """Get names of all registered models."""
        return list(self.clients.keys())
    
    def get_weight(self, name: str) -> float:
        """Get the weight for a model."""
        return self.weights.get(name, 1.0)
