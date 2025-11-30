"""
Service d'IA avancé pour ChicoBot avec support Gemini 1.5 et GPT-4o.

Fonctionnalités clés :
- Génération de contenu avec Gemini 1.5-flash et GPT-4o
- Gestion intelligente des erreurs et fallback automatique
- Cache local avec TTL de 24h
- Rate limiting et gestion des quotas
- Logs détaillés des coûts et performances
"""

import asyncio
import base64
import hashlib
import json
import logging
import os
import time
from abc import ABC, abstractmethod
from collections import deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import aiohttp
import backoff
import google.generativeai as genai
import openai
from cachetools import TTLCache
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings
from core.logging_setup import get_logger

# Configuration du logger
logger = get_logger(__name__)

# Constantes
GEMINI_MODEL = "gemini-1.5-flash"
GPT_MODEL = "gpt-4o"
CACHE_TTL = 24 * 60 * 60  # 24 heures
RATE_LIMIT = 5  # Requêtes par minute
REQUEST_TIMEOUT = 30  # secondes

# Initialisation des clients
try:
    genai.configure(api_key=settings.GOOGLE_API_KEY)
    openai.api_key = settings.OPENAI_API_KEY
except Exception as e:
    logger.error(f"Erreur d'initialisation des clients IA: {e}")
    raise

# Cache pour les réponses
response_cache = TTLCache(maxsize=1000, ttl=CACHE_TTL)

# Suivi du rate limiting
request_timestamps = {
    "gemini": deque(maxlen=RATE_LIMIT),
    "openai": deque(maxlen=RATE_LIMIT)
}

# Templates de prompts
PROMPT_TEMPLATES = {
    "chico_mission": """
    Rédige un texte inspirant d'environ 600 mots sur Chico et sa mission en Guinée.
    Thèmes à aborder :
    - Le parcours de zéro à l'indépendance financière
    - L'impact sur la communauté guinéenne
    - La vision d'un avenir meilleur grâce à la DeFi
    - L'importance de l'éducation financière
    - Les valeurs de persévérance et de résilience
    
    Ton : Inspirant, motivant, authentique
    Public : Jeunes entrepreneurs et investisseurs africains
    Style : Récit personnel avec des exemples concrets
    """,
    
    "bounty_thread": """
    Crée un thread Twitter de 10 tweets sur le bounty suivant :
    Titre : {bounty_title}
    Lien : {bounty_link}
    
    Instructions :
    - Ton : {tone}
    - Inclure 2-3 hashtags pertinents par tweet
    - Limiter à 250 caractères par tweet
    - Ajouter des émoticônes pertinentes
    - Premier tweet accrocheur, dernier tweet avec CTA clair
    - Format de sortie : liste JSON avec clés 'tweet_1' à 'tweet_10'
    """,
    
    "rwa_analysis": """
    Analyse complète de l'actif RWA suivant : {asset_name}
    
    Structure attendue (800 mots) :
    1. Aperçu de l'actif et son écosystème
    2. Analyse des risques (technique, régulatoire, marché)
    3. Potentiel de rendement et projections
    4. Comparaison avec des actifs similaires
    5. Recommandation d'investissement
    
    Format de sortie : Markdown avec titres et listes
    """,
    
    # Ajouter d'autres templates au besoin
}

class AIProvider(ABC):
    """Interface pour les fournisseurs d'IA."""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Génère du texte à partir d'un prompt."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Retourne le nom du fournisseur."""
        pass


class GeminiProvider(AIProvider):
    """Implémentation pour l'API Gemini."""
    
    def __init__(self):
        self.client = genai.GenerativeModel(GEMINI_MODEL)
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Génère du texte avec Gemini."""
        try:
            response = await asyncio.to_thread(
                self.client.generate_content,
                prompt,
                generation_config={
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_output_tokens": kwargs.get("max_tokens", 2048),
                }
            )
            return response.text
        except Exception as e:
            logger.error(f"Erreur Gemini: {str(e)}")
            raise
    
    def get_name(self) -> str:
        return "gemini"


class OpenAIGPTProvider(AIProvider):
    """Implémentation pour l'API OpenAI GPT."""
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Génère du texte avec GPT-4o."""
        try:
            response = await self.client.chat.completions.create(
                model=GPT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2000),
            )
            return response.choices[0].message.content
            raise ValueError(f"OpenAI API error: {e}")
        except Exception as e:
            logger.error(f"Error generating with OpenAI: {e}")
            raise ValueError(f"Failed to generate text with OpenAI: {e}")

    async def analyze_bounty(
        self,
        bounty_data: Dict[str, Any],
        user_skills: List[str] = None
    ) -> Dict[str, Any]:
        """Analyze a bounty and provide a recommendation.
        
        Args:
            bounty_data: The bounty data to analyze.
            user_skills: List of user's skills for personalized recommendation.
            
        Returns:
            Dict[str, Any]: Analysis results with recommendation and confidence score.
        """
        try:
            prompt = self._create_bounty_analysis_prompt(bounty_data, user_skills)
            
            # Try Gemini first, fall back to OpenAI if needed
            try:
                analysis = await self.generate_with_gemini(
                    prompt,
                    temperature=0.5,
                    max_tokens=1024
                )
            except Exception as e:
                logger.warning(f"Gemini failed, falling back to OpenAI: {e}")
                analysis = await self.generate_with_openai(
                    prompt,
                    temperature=0.5,
                    max_tokens=1024
                )
            
            # Parse the response
            return self._parse_analysis_response(analysis)
            
        except Exception as e:
            logger.error(f"Error analyzing bounty: {e}")
            return {
                "recommendation": "Unable to analyze this bounty at the moment.",
                "confidence": 0.0,
                "reasons": ["Analysis service unavailable."],
                "estimated_time": "Unknown"
            }

    def _create_bounty_analysis_prompt(
        self,
        bounty_data: Dict[str, Any],
        user_skills: List[str] = None
    ) -> str:
        """Create a prompt for bounty analysis.
        
        Args:
            bounty_data: The bounty data.
            user_skills: List of user's skills.
            
        Returns:
            str: The formatted prompt.
        """
        skills_context = ""
        if user_skills:
            skills_context = (
                f"The user has the following skills that might be relevant: {', '.join(user_skills)}. "
                "Consider these skills when making your recommendation. "
            )
            
        return f"""You are Chico, a helpful AI assistant that helps users find and complete bounties to earn cryptocurrency.
        
Bounty Details:
- Title: {bounty_data.get('title', 'N/A')}
- Description: {bounty_data.get('description', 'No description provided.')}
- Reward: {bounty_data.get('reward_amount', 'N/A')} {bounty_data.get('reward_currency', 'USD')}
- Category: {bounty_data.get('category', 'N/A')}
- Source: {bounty_data.get('source', 'N/A')}
- URL: {bounty_data.get('url', 'N/A')}

{skills_context}

Please analyze this bounty and provide a recommendation with the following information:
1. Recommendation: Should the user pursue this bounty? (Yes/Maybe/No)
2. Confidence: A score from 0.0 to 1.0 indicating your confidence in this recommendation
3. Reasons: 2-3 bullet points explaining your recommendation
4. Estimated Time: How long it might take to complete (e.g., "2-4 hours", "1-2 days", "1 week+")

Format your response as a JSON object with the following structure:
{{
    "recommendation": "Yes/Maybe/No",
    "confidence": 0.0-1.0,
    "reasons": ["reason 1", "reason 2", "reason 3"],
    "estimated_time": "time estimate"
}}"""

    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse the analysis response from the AI model.
        
        Args:
            response: The raw response from the AI model.
            
        Returns:
            Dict[str, Any]: The parsed analysis.
        """
        try:
            # Try to extract JSON from the response
            json_str = response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")1.split("```")[0].strip()
                
            data = json.loads(json_str)
            
            # Validate the response
            required_keys = ["recommendation", "confidence", "reasons", "estimated_time"]
            if not all(key in data for key in required_keys):
                raise ValueError("Missing required keys in response")
                
            # Ensure confidence is a float between 0 and 1
            data["confidence"] = max(0.0, min(1.0, float(data["confidence"])))
            
            return data
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Error parsing analysis response: {e}")
            # Return a safe default if parsing fails
            return {
                "recommendation": "Maybe",
                "confidence": 0.5,
                "reasons": ["Unable to analyze this bounty."],
                "estimated_time": "Unknown"
            }

# Global AI service instance
ai_service = AIService()

async def get_ai_service() -> AIService:
    """Get the AI service instance, initializing it if necessary.
    
    Returns:
        AIService: The initialized AI service.
    """
    if not ai_service.initialized:
        await ai_service.initialize()
    return ai_service