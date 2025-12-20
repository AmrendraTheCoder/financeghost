"""
LLM Service
Wrapper for Google AI Studio and OpenAI API calls with retry logic
"""

import json
from typing import Dict, Any, Optional, List
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
import os

from ..config import settings

logger = logging.getLogger(__name__)

# Try to import Google GenAI
GENAI_AVAILABLE = False
try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    logger.info("google-genai not installed. Will use OpenAI if available.")

# Try to import OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.info("OpenAI not installed.")


class LLMService:
    """Service for interacting with LLM (Google AI Studio or OpenAI)"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        use_vertex: bool = True,
        project_id: Optional[str] = None,
        location: str = "us-central1"
    ):
        self.api_key = api_key or settings.openai_api_key
        self.google_api_key = settings.google_api_key
        self.project_id = project_id or settings.google_cloud_project
        self.location = location
        
        self.genai_client = None
        self.openai_client = None
        self.backend = None
        
        # Try Google AI Studio first (free API key)
        if GENAI_AVAILABLE and self.google_api_key:
            try:
                from google import genai
                self.genai_client = genai.Client(api_key=self.google_api_key)
                self.backend = "gemini"
                logger.info("Google AI Studio (Gemini) initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Google AI: {e}")
        
        # Try Vertex AI next (requires billing)
        if not self.backend and GENAI_AVAILABLE and self.project_id:
            try:
                from google import genai
                self.genai_client = genai.Client(
                    vertexai=True,
                    project=self.project_id,
                    location=self.location
                )
                self.backend = "vertex"
                logger.info(f"Vertex AI initialized with project: {self.project_id}")
            except Exception as e:
                logger.warning(f"Failed to initialize Vertex AI: {e}")
        
        # Fallback to OpenAI
        if not self.backend and OPENAI_AVAILABLE and self.api_key:
            try:
                self.openai_client = OpenAI(api_key=self.api_key)
                self.backend = "openai"
                logger.info(f"Using OpenAI ({settings.openai_model}) as LLM backend")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}")
        
        if not self.backend:
            logger.warning("No LLM backend available. Processing will use regex fallback.")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2000
    ) -> str:
        """
        Get completion from LLM
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt for context
            temperature: Randomness (0-1)
            max_tokens: Maximum response length
            
        Returns:
            LLM response text
        """
        if self.backend in ("gemini", "vertex") and self.genai_client:
            return self._complete_gemini(prompt, system_prompt, temperature, max_tokens)
        elif self.backend == "openai" and self.openai_client:
            return self._complete_openai(prompt, system_prompt, temperature, max_tokens)
        else:
            raise ValueError("No LLM backend available")
    
    def _complete_gemini(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Complete using Gemini (AI Studio or Vertex AI)"""
        full_prompt = ""
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n"
        full_prompt += prompt
        
        # Use flash model for speed
        response = self.genai_client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=full_prompt,
            config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
        )
        
        return response.text
    
    def _complete_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Complete using OpenAI"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.openai_client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
    
    def extract_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get structured JSON output from LLM
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            schema_hint: Optional JSON schema hint for better extraction
            
        Returns:
            Parsed JSON dictionary
        """
        json_system = system_prompt or ""
        json_system += "\n\nIMPORTANT: Respond ONLY with valid JSON. No markdown, no explanation, just the JSON object."
        
        if schema_hint:
            json_system += f"\n\nExpected JSON structure:\n{schema_hint}"
        
        response = self.complete(prompt, system_prompt=json_system)
        
        # Clean response - remove markdown code blocks if present
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}\nResponse: {response[:500]}")
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            raise ValueError(f"Failed to parse LLM response as JSON: {e}")
    
    def classify(
        self,
        text: str,
        categories: List[str],
        context: Optional[str] = None
    ) -> str:
        """
        Classify text into one of the given categories
        
        Args:
            text: Text to classify
            categories: List of possible categories
            context: Optional context for classification
            
        Returns:
            Selected category
        """
        categories_str = ", ".join(categories)
        prompt = f"""Classify the following text into exactly one of these categories: {categories_str}

Text: {text}

{f"Context: {context}" if context else ""}

Respond with ONLY the category name, nothing else."""

        response = self.complete(prompt, temperature=0.0, max_tokens=50)
        response = response.strip().lower()
        
        # Find best matching category
        for cat in categories:
            if cat.lower() in response or response in cat.lower():
                return cat
        
        return categories[0]  # Default to first category if no match


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create LLM service singleton"""
    global _llm_service
    if _llm_service is None:
        # Prefer Vertex AI if project is configured
        use_vertex = bool(settings.google_cloud_project)
        _llm_service = LLMService(use_vertex=use_vertex)
    return _llm_service
