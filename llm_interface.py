"""LLM Interface - Supports Anthropic, OpenAI, and Local Models"""
import json
import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import anthropic
import openai
import requests
from config import config

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, messages: List[Dict[str, str]], system: Optional[str] = None) -> str:
        pass
    
    @abstractmethod
    def generate_structured(self, messages: List[Dict[str, str]], system: Optional[str] = None) -> Dict[str, Any]:
        pass

class AnthropicProvider(LLMProvider):
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=config.llm.api_key)
        self.model = config.llm.model
        
    def generate(self, messages: List[Dict[str, str]], system: Optional[str] = None) -> str:
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=config.llm.max_tokens,
                temperature=config.llm.temperature,
                system=system or "",
                messages=messages
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    def generate_structured(self, messages: List[Dict[str, str]], system: Optional[str] = None) -> Dict[str, Any]:
        response_text = self.generate(messages, system)
        try:
            # Extract JSON from response
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            else:
                json_str = response_text.strip()
            return json.loads(json_str)
        except json.JSONDecodeError:
            logger.warning("Failed to parse structured response, returning as text")
            return {"response": response_text}

class OpenAIProvider(LLMProvider):
    def __init__(self):
        self.client = openai.OpenAI(api_key=config.llm.api_key)
        self.model = config.llm.model
        
    def generate(self, messages: List[Dict[str, str]], system: Optional[str] = None) -> str:
        try:
            if system:
                messages = [{"role": "system", "content": system}] + messages
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=config.llm.max_tokens,
                temperature=config.llm.temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def generate_structured(self, messages: List[Dict[str, str]], system: Optional[str] = None) -> Dict[str, Any]:
        response_text = self.generate(messages, system)
        try:
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            else:
                json_str = response_text.strip()
            return json.loads(json_str)
        except json.JSONDecodeError:
            return {"response": response_text}

class LocalProvider(LLMProvider):
    def __init__(self):
        self.base_url = config.llm.base_url or "http://localhost:11434"
        self.model = config.llm.model
        
    def generate(self, messages: List[Dict[str, str]], system: Optional[str] = None) -> str:
        try:
            if system:
                messages = [{"role": "system", "content": system}] + messages
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": config.llm.temperature,
                        "num_predict": config.llm.max_tokens
                    }
                },
                timeout=300
            )
            response.raise_for_status()
            return response.json()["message"]["content"]
        except Exception as e:
            logger.error(f"Local LLM error: {e}")
            raise
    
    def generate_structured(self, messages: List[Dict[str, str]], system: Optional[str] = None) -> Dict[str, Any]:
        response_text = self.generate(messages, system)
        try:
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            else:
                json_str = response_text.strip()
            return json.loads(json_str)
        except json.JSONDecodeError:
            return {"response": response_text}

class LLMInterface:
    def __init__(self):
        self.provider = self._get_provider()
        
    def _get_provider(self) -> LLMProvider:
        provider_map = {
            "anthropic": AnthropicProvider,
            "openai": OpenAIProvider,
            "local": LocalProvider
        }
        
        provider_class = provider_map.get(config.llm.provider)
        if not provider_class:
            raise ValueError(f"Unknown LLM provider: {config.llm.provider}")
        
        return provider_class()
    
    def generate(self, messages: List[Dict[str, str]], system: Optional[str] = None) -> str:
        return self.provider.generate(messages, system)
    
    def generate_structured(self, messages: List[Dict[str, str]], system: Optional[str] = None) -> Dict[str, Any]:
        return self.provider.generate_structured(messages, system)
    
    def build_messages(self, history: List[Dict[str, str]], new_message: str) -> List[Dict[str, str]]:
        """Build message list maintaining conversation history"""
        return history + [{"role": "user", "content": new_message}]

llm = LLMInterface()
