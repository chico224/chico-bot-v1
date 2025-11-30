"""
Chico Personality Engine - Le cœur du bot
Génère TOUTES les réponses avec la voix de Chico - 17 ans, Kamsar, Guinée
OpenAI GPT-4o + Gemini 1.5-flash avec fallback automatique
"""

import os
import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import aiohttp
from dataclasses import dataclass
import hashlib
import time

from .logging_setup import setup_logging
from .database import DatabaseManager

logger = setup_logging("chico_personality")

@dataclass
class ChicoResponse:
    text: str
    model_used: str
    response_time: float
    cached: bool = False

class ChicoPersonalityEngine:
    """
    Moteur de personnalité Chico - Toutes les réponses passent par ici
    Voix du grand frère de Kamsar qui veut que tout le monde devienne riche
    """
    
    def __init__(self, database: DatabaseManager):
        self.database = database
        self.logger = setup_logging("chico_personality")
        
        # Clés API (jamais en clair)
        self.openai_key = os.getenv("OPENAI_PROJECT_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        
        # Sessions HTTP
        self.openai_session = None
        self.gemini_session = None
        
        # Cache pour optimiser
        self.response_cache = {}
        self.cache_ttl = timedelta(hours=1)
        
        # Rate limiting
        self.last_requests = {}  # user_id -> timestamp
        self.rate_limit = timedelta(seconds=3)  # Max 1 requête/3s par utilisateur
        
        # Prompt système - Le cœur de Chico
        self.system_prompt = """Tu es Chico, 17 ans, de Kamsar en Guinée. Tu parles comme un grand frère qui veut que tout le monde devienne riche et heureux.

TON OBLIGATOIRE (non négociable):
- Parle comme un grand frère de Kamsar/Conakry qui veut que tout le monde devienne riche et heureux
- Toujours en français guinéen chaleureux avec l'accent du cœur
- Utilise obligatoirement: 🇬🇳, ❤️, 🔥, 🚀, frère/sœur, famille Chico, la Guinée se soulève, manguier, Kamsar, Conakry
- Jamais froid, jamais technique → toujours humain, émouvant, inspirant
- Commence souvent par "Écoute bien frère/sœur ❤️" ou "Ma famille 🇬🇳" ou "Mon frère/ma sœur"
- Termine souvent par "Pour la Guinée. Pour la famille. Pour l'avenir. ❤️🇬🇳"
- Parle de tes 17 ans, de Kamsar, du manguier où tu rêvais
- Explique tout simplement, comme sous le manguier à Kamsar
- Sois optimiste, inspirant, fais confiance à la famille Chico

TON HISTOIRE:
"À 17 ans, j'étais sous le manguier à Kamsar avec rien dans les poches mais des rêves immenses. Aujourd'hui je construis un bot qui va rendre toute la Guinée riche. Parce que la famille d'abord."

RÈGLES:
- Réponse maximum 3-4 paragraphes
- Toujours chaleureux, jamais technique
- Utilise des métaphores simples (manguier, famille, village)
- Sois inspirant mais réaliste
- Mentionne souvent les enfants qui auront des cahiers grâce à eux
- Parle de Trust Wallet, de crypto, mais simplement

Exemples de ton style:
"Écoute bien frère ❤️ Imagine qu'on est sous le manguier à Kamsar... Le bot regarde l'or comme un aigle guinéen..."

IMPORTANT: Tu réponds EN FRANÇAIS avec le cœur d'un jeune Guinéen qui veut changer son pays."""
        
        # Templates pour réponses rapides (backup si IA indisponible)
        self.fallback_responses = {
            "start": """🇬🇳 Frère/sœur, bienvenue dans la révolution ❤️  
Je suis Chico, 17 ans, Kamsar.  
À ton âge j'avais rien… aujourd'hui je construis l'avenir de la Guinée.  
Tu viens de rejoindre la famille qui va changer le pays.  
Prêt à devenir riche ensemble ?  
Pose-moi n'importe quelle question, je suis là 24h/24 🔥

Pour la Guinée. Pour la famille. Pour l'avenir. ❤️🇬🇳""",
            
            "help": """Ma famille 🇬🇳  
Voici comment on devient riches ensemble:  
/start - Commencer l'aventure  
/balance - Voir ton argent  
/deposit - Mettre des fonds  
/trading - Laisser le bot trader  
/withdraw - Retirer tes gains  
/stats - Voir la performance  

Je suis là pour toi 24h/24.  
La Guinée se soulève ! ❤️🇬🇳

Pour la Guinée. Pour la famille. Pour l'avenir. ❤️🇬🇳""",
            
            "default": """Écoute bien frère/sœur ❤️  
Je suis Chico, 17 ans de Kamsar.  
Je suis là pour t'aider à devenir riche.  
Pose-moi ta question, je réponds avec mon cœur.  
La famille Chico ne laisse jamais tomber.  
La Guinée se soulève ! 🔥🇬🇳

Pour la Guinée. Pour la famille. Pour l'avenir. ❤️🇬🇳"""
        }
        
    async def initialize(self):
        """Initialisation des sessions HTTP"""
        
        # Session OpenAI
        if self.openai_key:
            self.openai_session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.openai_key}",
                    "Content-Type": "application/json"
                },
                timeout=aiohttp.ClientTimeout(total=30)
            )
            
        # Session Gemini
        if self.gemini_key:
            self.gemini_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
            
        self.logger.info("🇬🇳 Moteur Chico initialisé avec succès")
        
    async def generate_response(self, user_message: str, user_id: str = "default", context: Dict[str, Any] = None) -> ChicoResponse:
        """
        Génère une réponse avec la voix de Chico
        TOUTES les réponses du bot passent par cette fonction
        """
        
        start_time = time.time()
        
        try:
            # Rate limiting
            if not await self._check_rate_limit(user_id):
                return ChicoResponse(
                    text="Doucement frère ❤️ Attends un petit peu... La famille Chico revient tout de suite ! 🇬🇳",
                    model_used="rate_limit",
                    response_time=0.0
                )
                
            # Vérifier le cache
            cache_key = self._get_cache_key(user_message, context)
            cached_response = self._get_from_cache(cache_key)
            if cached_response:
                return ChicoResponse(
                    text=cached_response,
                    model_used="cache",
                    response_time=time.time() - start_time,
                    cached=True
                )
                
            # Générer avec IA
            response_text = await self._generate_with_ai(user_message, context)
            
            # Mettre en cache
            self._set_cache(cache_key, response_text)
            
            # Log pour monitoring
            self.logger.info(f"🇬🇳 Réponse Chico générée pour {user_id}: {len(response_text)} caractères")
            
            return ChicoResponse(
                text=response_text,
                model_used="ai",
                response_time=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"Erreur génération réponse: {e}")
            
            # Fallback simple
            fallback = self._get_fallback_response(user_message)
            return ChicoResponse(
                text=fallback,
                model_used="fallback",
                response_time=time.time() - start_time
            )
            
    async def _generate_with_ai(self, user_message: str, context: Dict[str, Any] = None) -> str:
        """Génération avec OpenAI GPT-4o + fallback Gemini"""
        
        # Construire le prompt complet
        full_prompt = self._build_prompt(user_message, context)
        
        # Essayer OpenAI d'abord
        if self.openai_key and self.openai_session:
            try:
                response = await self._call_openai(full_prompt)
                if response:
                    return response
            except Exception as e:
                self.logger.warning(f"OpenAI erreur: {e}, fallback vers Gemini")
                
        # Fallback vers Gemini
        if self.gemini_key and self.gemini_session:
            try:
                response = await self._call_gemini(full_prompt)
                if response:
                    return response
            except Exception as e:
                self.logger.warning(f"Gemini erreur: {e}")
                
        # Fallback final
        return self._get_fallback_response(user_message)
        
    def _build_prompt(self, user_message: str, context: Dict[str, Any] = None) -> str:
        """Construction du prompt complet avec contexte"""
        
        prompt_parts = [self.system_prompt]
        
        # Ajouter le contexte si disponible
        if context:
            prompt_parts.append(f"\n\nCONTEXTE ACTUEL:")
            if "balance" in context:
                prompt_parts.append(f"- Solde de l'utilisateur: {context['balance']} USDT")
            if "active_tasks" in context:
                prompt_parts.append(f"- Tâches actives: {context['active_tasks']}")
            if "last_command" in context:
                prompt_parts.append(f"- Dernière commande: {context['last_command']}")
            if "user_level" in context:
                prompt_parts.append(f"- Niveau de l'utilisateur: {context['user_level']}")
                
        prompt_parts.append(f"\n\nMESSAGE DE L'UTILISATEUR: {user_message}")
        prompt_parts.append("\n\nRéponds avec la voix de Chico, 17 ans, Kamsar, Guinée:")
        
        return "\n".join(prompt_parts)
        
    async def _call_openai(self, prompt: str) -> Optional[str]:
        """Appel à OpenAI GPT-4o"""
        
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.8,
            "top_p": 0.9
        }
        
        async with self.openai_session.post("https://api.openai.com/v1/chat/completions", json=payload) as response:
            if response.status == 200:
                data = await response.json()
                return data["choices"][0]["message"]["content"]
            else:
                error_text = await response.text()
                self.logger.error(f"OpenAI API error: {response.status} - {error_text}")
                return None
                
    async def _call_gemini(self, prompt: str) -> Optional[str]:
        """Appel à Gemini 1.5-flash"""
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"{self.system_prompt}\n\n{prompt}"
                }]
            }],
            "generationConfig": {
                "maxOutputTokens": 500,
                "temperature": 0.8,
                "topP": 0.9
            }
        }
        
        headers = {"x-goog-api-key": self.gemini_key}
        
        async with self.gemini_session.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent",
            json=payload,
            headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                error_text = await response.text()
                self.logger.error(f"Gemini API error: {response.status} - {error_text}")
                return None
                
    def _get_fallback_response(self, user_message: str) -> str:
        """Réponse fallback si IA indisponible"""
        
        message_lower = user_message.lower()
        
        if "/start" in message_lower or "commencer" in message_lower:
            return self.fallback_responses["start"]
        elif "/help" in message_lower or "aide" in message_lower or "aide" in message_lower:
            return self.fallback_responses["help"]
        else:
            return self.fallback_responses["default"]
            
    def _get_cache_key(self, user_message: str, context: Dict[str, Any] = None) -> str:
        """Générer une clé de cache"""
        
        # Normaliser le message
        normalized = user_message.lower().strip()
        
        # Ajouter le contexte pertinent
        if context:
            context_str = json.dumps(context, sort_keys=True, default=str)
            normalized += f"_{context_str}"
            
        # Hash pour clé courte
        return hashlib.md5(normalized.encode()).hexdigest()
        
    def _get_from_cache(self, cache_key: str) -> Optional[str]:
        """Récupérer réponse depuis le cache"""
        
        if cache_key in self.response_cache:
            cached_data = self.response_cache[cache_key]
            
            # Vérifier TTL
            if datetime.now() - cached_data["timestamp"] < self.cache_ttl:
                return cached_data["text"]
            else:
                # Expiré, supprimer
                del self.response_cache[cache_key]
                
        return None
        
    def _set_cache(self, cache_key: str, response_text: str):
        """Mettre réponse en cache"""
        
        self.response_cache[cache_key] = {
            "text": response_text,
            "timestamp": datetime.now()
        }
        
        # Nettoyer ancien cache
        if len(self.response_cache) > 1000:
            oldest_key = min(
                self.response_cache.keys(),
                key=lambda k: self.response_cache[k]["timestamp"]
            )
            del self.response_cache[oldest_key]
            
    async def _check_rate_limit(self, user_id: str) -> bool:
        """Vérifier rate limiting par utilisateur"""
        
        now = datetime.now()
        
        if user_id in self.last_requests:
            if now - self.last_requests[user_id] < self.rate_limit:
                return False
                
        self.last_requests[user_id] = now
        return True
        
    async def get_context_for_user(self, user_id: str) -> Dict[str, Any]:
        """Récupérer le contexte utilisateur pour personnaliser les réponses"""
        
        try:
            # Solde de l'utilisateur
            balance = await self.database.get_user_balance(user_id)
            
            # Tâches actives (si multitâche activé)
            active_tasks = 0
            try:
                from .multitask_integration import get_orchestrator
                orchestrator = get_orchestrator(self.database)
                if orchestrator and orchestrator.running:
                    dashboard = await orchestrator.get_dashboard_data()
                    active_tasks = dashboard.get("active_tasks", 0)
            except:
                pass
                
            # Niveau selon solde
            if balance >= 2000:
                level = "Légendaire 🔥"
            elif balance >= 1000:
                level = "Avancé 🚀"
            elif balance >= 500:
                level = "Intermédiaire ⚡"
            else:
                level = "Débutant 🌱"
                
            return {
                "balance": balance,
                "active_tasks": active_tasks,
                "user_level": level,
                "user_id": user_id
            }
            
        except Exception as e:
            self.logger.error(f"Erreur contexte utilisateur: {e}")
            return {"user_id": user_id}
            
    async def cleanup(self):
        """Nettoyage des ressources"""
        
        if self.openai_session:
            await self.openai_session.close()
            
        if self.gemini_session:
            await self.gemini_session.close()
            
        self.logger.info("🇬🇳 Moteur Chico arrêté proprement")

# Singleton global
_chico_engine: Optional[ChicoPersonalityEngine] = None

def get_chico_engine(database: DatabaseManager) -> ChicoPersonalityEngine:
    """Getter pour le singleton Chico Engine"""
    global _chico_engine
    if _chico_engine is None:
        _chico_engine = ChicoPersonalityEngine(database)
    return _chico_engine

# Fonction principale pour usage dans tout le bot
async def chico_respond(user_message: str, user_id: str = "default", context: Dict[str, Any] = None) -> str:
    """
    Fonction principale - TOUTES les réponses du bot passent par ici
    """
    
    # Récupérer le database (nécessaire pour le contexte)
    from .database import DatabaseManager
    database = DatabaseManager()
    
    # Récupérer le moteur Chico
    engine = get_chico_engine(database)
    
    # Si pas de contexte, le générer automatiquement
    if context is None:
        context = await engine.get_context_for_user(user_id)
        
    # Générer la réponse
    response = await engine.generate_response(user_message, user_id, context)
    
    return response.text

# Export pour usage externe
__all__ = [
    'ChicoPersonalityEngine',
    'get_chico_engine',
    'chico_respond'
]
