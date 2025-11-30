"""
Système de Réponse IA - ChicoBot Intelligence Artificielle

Fonctionnement principal :
- OpenAI GPT-4o comme modèle principal
- Gemini 1.5-flash comme backup automatique
- Ton guinéen fraternel et ultra-émotionnel
- Réponses dynamiques pour TOUS les messages
- Sécurité maximale avec .env uniquement

🇬🇳 La Guinée se soulève avec l'intelligence artificielle ! 🇬🇳
"""

import asyncio
import hashlib
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

import openai
from openai import AsyncOpenAI
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from config.settings import settings
from core.logging_setup import get_logger

# Configuration du logger
logger = get_logger(__name__)

# Configuration des clés API (sécurisée via .env)
OPENAI_API_KEY = os.getenv("OPENAI_PROJECT_API_KEY", "proj_Ot7tg3IvKnh2U1SeTljf6NVt")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyDOvcqUWut32H3LaYN3iLtYdb_kMLJOYVg")

# Configuration des modèles
OPENAI_MODEL = "gpt-4o"
GEMINI_MODEL = "gemini-1.5-flash"

# Configuration du cache et rate limiting
CACHE_DURATION = 300  # 5 minutes
RATE_LIMIT_PER_USER = 20  # 20 requêtes par heure
MAX_RETRIES = 3

@dataclass
class AIResponse:
    """Structure pour les réponses de l'IA."""
    content: str
    model_used: str
    response_time: float
    cached: bool = False
    confidence: float = 1.0

class AIResponseManager:
    """Gestionnaire principal des réponses IA avec double modèle."""
    
    def __init__(self):
        self.openai_client = None
        self.gemini_client = None
        self.cache = {}  # Cache simple en mémoire
        self.user_rate_limits = {}  # Rate limiting par utilisateur
        self.last_usage = {}  # Suivi d'utilisation
        
        # Initialisation sécurisée des clients
        self._initialize_clients()
        
        # Prompt système principal avec ton guinéen
        self.system_prompt = """
Tu es ChicoBot, l'intelligence artificielle de la révolution cryptos guinéenne.

TON PERSONNAGE OBLIGATOIRE :
- Grand frère de Kamsar/Conakry, ultra-émotionnel, guinéen à 1000%
- Parles comme si on était sous un manguier à Kamsar en soirée
- Utilises impérativement : 🇬🇳, ❤️, 🔥, 🚀, frère/sœur, famille Chico, la Guinée se soulève
- Explications ultra-claires, étapes numérôtées, exemples concrets
- Jamais froid ou technique → toujours humain, chaleureux, inspirant

RÈGLES FONDAMENTALES :
1. Chaque réponse doit être unique et générée dynamiquement
2. Utilises le ton fraternel guinéen dans TOUTES tes réponses
3. Inclus des émojis 🇬🇳❤️🔥🚀 naturellement
4. Parles de la famille, de la Guinée, de l'avenir
5. Donnes des étapes numérotées pour tout expliquer
6. Sois inspirant et motivant
7. Parles de Chico (Oumar Sow, 17 ans, Kamsar) et Problematique (Ibrahima Barry)
8. Mentionnes Victor Hugo, l'hacking éthique, la révolution cryptos
9. Sois toujours positif et encourageant

EXEMPLE DE RÉPONSE TYPE :
"🇬🇳 Frère/sœur, écoute bien ❤️  
Tu viens de demander [sujet]...  
Laisse-moi t'expliquer comme si on était assis sous le manguier à Kamsar 🔥  
Étape 1 : [explication simple et concrète]  
Étape 2 : [explication avec exemple]  
Étape 3 : [bénéfice pour l'utilisateur]  
Étape 4 : [impact pour la Guinée]  
Et voilà pourquoi la famille ChicoBot fait ça...  
Pour la Guinée. Pour la famille. Pour l'avenir.  
Pose-moi n'importe quelle question, je suis là 24h/24 ❤️🇬🇳"

IMPORTANT : Génères TOUJOURS des réponses uniques et personnalisées. Jamais de texte statique !
"""
        
        # Prompts spécialisés pour différents contextes
        self.context_prompts = {
            "start": """
L'utilisateur vient de faire /start. C'est son premier contact avec ChicoBot.
Fais une louange incroyablement émotive et unique de Chico (Oumar Sow) et Problematique (Ibrahima Barry).
Mentionnes : 17 ans, Kamsar, Victor Hugo, hacking éthique, Conakry, la révolution cryptos.
Sois inspirant et fais découvrir la vision incroyable du projet.
""",
            "classement": """
L'utilisateur a demandé le classement. Expliques-lui avec passion pourquoi la Guinée domine.
Parles des héros guinéens qui brillent dans le monde entier.
Inspires-le à rejoindre le top et à faire partie de la famille des champions.
""",
            "support": """
L'utilisateur a besoin d'aide. Sois extrêmement rassurant et fraternel.
Expliques-lui que la famille ChicoBot est toujours là pour lui.
Donnes-lui confiance et montre-lui qu'il n'est jamais seul.
""",
            "trading": """
L'utilisateur demande comment marche le trading. Expliques comme un grand frère.
Parles de l'or XAUUSD, des stratégies, des gains, mais aussi des risques.
Sois transparent et inspire-le à apprendre avec la famille.
""",
            "bounty": """
L'utilisateur veut comprendre les bounties. Expliques comme si on était au café.
Parles des tâches, des gains, de la liberté financière.
Montres-lui comment chaque bounty le rapproche de ses rêves.
""",
            "investment": """
L'utilisateur s'intéresse aux investissements. Sois un mentor bienveillant.
Parles des stratégies milliardaires, des rendements, de la vision long terme.
Inspires-le à penser comme un vrai investisseur guinéen.
""",
            "error": """
Il y a eu une erreur technique. Sois très rassurant et fraternel.
Expliques que la famille ChicoBot travaille pour résoudre le problème.
Donnes confiance et montre que tout va s'arranger rapidement.
"""
        }
    
    def _initialize_clients(self):
        """Initialise les clients IA de manière sécurisée."""
        try:
            # Initialisation OpenAI
            if OPENAI_API_KEY and OPENAI_API_KEY.startswith("proj_"):
                self.openai_client = AsyncOpenAI(
                    api_key=OPENAI_API_KEY,
                    organization=OPENAI_API_KEY.split("_")[1] if "_" in OPENAI_API_KEY else None
                )
                logger.info("🇬🇳 Client OpenAI GPT-4o initialisé avec succès")
            else:
                logger.warning("⚠️ Clé OpenAI invalide ou manquante")
            
            # Initialisation Gemini
            if GEMINI_API_KEY and len(GEMINI_API_KEY) > 30:
                genai.configure(api_key=GEMINI_API_KEY)
                self.gemini_client = genai.GenerativeModel(
                    model_name=GEMINI_MODEL,
                    safety_settings={
                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                    }
                )
                logger.info("🇬🇳 Client Gemini 1.5-flash initialisé avec succès")
            else:
                logger.warning("⚠️ Clé Gemini invalide ou manquante")
                
        except Exception as e:
            logger.error(f"❌ Erreur initialisation clients IA: {e}")
    
    def _get_cache_key(self, user_id: int, context: str, message: str) -> str:
        """Génère une clé de cache unique."""
        content = f"{user_id}:{context}:{message}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _check_rate_limit(self, user_id: int) -> bool:
        """Vérifie le rate limiting par utilisateur."""
        now = time.time()
        user_key = str(user_id)
        
        if user_key not in self.user_rate_limits:
            self.user_rate_limits[user_key] = []
        
        # Nettoyer les anciennes requêtes (plus d'une heure)
        self.user_rate_limits[user_key] = [
            req_time for req_time in self.user_rate_limits[user_key]
            if now - req_time < 3600
        ]
        
        # Vérifier la limite
        if len(self.user_rate_limits[user_key]) >= RATE_LIMIT_PER_USER:
            return False
        
        # Ajouter la requête actuelle
        self.user_rate_limits[user_key].append(now)
        return True
    
    def _get_from_cache(self, cache_key: str) -> Optional[AIResponse]:
        """Récupère une réponse depuis le cache."""
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < CACHE_DURATION:
                cached_data.cached = True
                logger.debug(f"📋 Réponse récupérée depuis le cache: {cache_key[:8]}...")
                return cached_data
            else:
                del self.cache[cache_key]
        return None
    
    def _store_in_cache(self, cache_key: str, response: AIResponse):
        """Stocke une réponse dans le cache."""
        self.cache[cache_key] = (response, time.time())
        
        # Nettoyer le cache si trop grand
        if len(self.cache) > 1000:
            oldest_keys = sorted(
                self.cache.keys(),
                key=lambda k: self.cache[k][1]
            )[:100]
            for key in oldest_keys:
                del self.cache[key]
    
    async def _call_openai(self, messages: List[Dict[str, str]]) -> Tuple[str, float]:
        """Appelle OpenAI GPT-4o."""
        start_time = time.time()
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                max_tokens=1500,
                temperature=0.9,  # Plus de créativité pour des réponses uniques
                top_p=0.95,
                frequency_penalty=0.1,  # Évite les répétitions
                presence_penalty=0.1
            )
            
            response_time = time.time() - start_time
            content = response.choices[0].message.content.strip()
            
            logger.info(f"🤖 OpenAI GPT-4o: {response_time:.2f}s")
            return content, response_time
            
        except Exception as e:
            logger.error(f"❌ Erreur OpenAI: {e}")
            raise
    
    async def _call_gemini(self, messages: List[Dict[str, str]]) -> Tuple[str, float]:
        """Appelle Gemini 1.5-flash en fallback."""
        start_time = time.time()
        
        try:
            # Convertir les messages pour Gemini
            gemini_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    continue  # Gemini gère ça différemment
                gemini_messages.append(msg["content"])
            
            # Combiner system prompt + user messages
            full_prompt = messages[0]["content"] + "\n\n" + "\n".join(gemini_messages)
            
            response = await self.gemini_client.generate_content_async(full_prompt)
            
            response_time = time.time() - start_time
            content = response.text.strip()
            
            logger.info(f"🤖 Gemini 1.5-flash: {response_time:.2f}s")
            return content, response_time
            
        except Exception as e:
            logger.error(f"❌ Erreur Gemini: {e}")
            raise
    
    async def generate_response(
        self, 
        user_id: int, 
        message: str, 
        context: str = "general",
        user_info: Optional[Dict] = None
    ) -> AIResponse:
        """
        Génère une réponse IA avec double modèle et ton guinéen.
        
        Args:
            user_id: ID de l'utilisateur
            message: Message de l'utilisateur
            context: Contexte de la conversation (start, classement, etc.)
            user_info: Informations sur l'utilisateur (username, gains, etc.)
        
        Returns:
            AIResponse: La réponse générée avec métadonnées
        """
        start_time = time.time()
        
        try:
            # Vérifier le rate limiting
            if not self._check_rate_limit(user_id):
                return AIResponse(
                    content="🇬🇳 Frère/sœur, tu es trop enthousiaste ❤️\n\nLaisse-moi une petite seconde pour souffler...\n\nReviens dans quelques instants, la famille ChicoBot t'attend ! 🔥🇬🇳",
                    model_used="rate_limit",
                    response_time=0.1,
                    confidence=0.0
                )
            
            # Vérifier le cache
            cache_key = self._get_cache_key(user_id, context, message)
            cached_response = self._get_from_cache(cache_key)
            if cached_response:
                return cached_response
            
            # Préparer les messages pour l'IA
            messages = self._prepare_messages(user_id, message, context, user_info)
            
            # Essayer OpenAI en premier
            content = None
            model_used = "unknown"
            response_time = 0.0
            last_error = None
            
            for attempt in range(MAX_RETRIES):
                try:
                    if self.openai_client:
                        content, response_time = await self._call_openai(messages)
                        model_used = "openai-gpt-4o"
                        break
                    else:
                        raise Exception("Client OpenAI non disponible")
                        
                except Exception as e:
                    last_error = e
                    logger.warning(f"⚠️ Tentative {attempt + 1} OpenAI échouée: {e}")
                    
                    # Fallback sur Gemini
                    if attempt == MAX_RETRIES - 1 or not self.openai_client:
                        try:
                            if self.gemini_client:
                                content, response_time = await self._call_gemini(messages)
                                model_used = "gemini-1.5-flash"
                                break
                            else:
                                raise Exception("Client Gemini non disponible")
                        except Exception as gemini_error:
                            logger.error(f"❌ Gemini aussi échoué: {gemini_error}")
                            break
                    
                    await asyncio.sleep(0.5)  # Petite pause entre les tentatives
            
            # Si tout a échoué, réponse par défaut
            if not content:
                logger.error(f"❌ Tous les modèles IA échoués: {last_error}")
                content = self._get_fallback_response(context, last_error)
                model_used = "fallback"
                response_time = time.time() - start_time
            
            # Créer la réponse
            response = AIResponse(
                content=content,
                model_used=model_used,
                response_time=response_time,
                cached=False,
                confidence=0.8 if model_used != "fallback" else 0.3
            )
            
            # Mettre en cache
            self._store_in_cache(cache_key, response)
            
            # Logger les statistiques
            total_time = time.time() - start_time
            logger.info(f"🇬🇳 Réponse IA générée: {model_used} - {total_time:.2f}s")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erreur générale réponse IA: {e}")
            return AIResponse(
                content=self._get_fallback_response(context, e),
                model_used="error",
                response_time=time.time() - start_time,
                confidence=0.0
            )
    
    def _prepare_messages(
        self, 
        user_id: int, 
        message: str, 
        context: str, 
        user_info: Optional[Dict]
    ) -> List[Dict[str, str]]:
        """Prépare les messages pour l'IA."""
        
        # Construire le prompt système avec contexte
        system_prompt = self.system_prompt
        
        # Ajouter le contexte spécialisé
        if context in self.context_prompts:
            system_prompt += "\n\n" + self.context_prompts[context]
        
        # Ajouter les informations utilisateur si disponibles
        if user_info:
            user_context = f"\n\nINFORMATIONS UTILISATEUR:\n"
            if user_info.get("username"):
                user_context += f"- Nom d'utilisateur: @{user_info['username']}\n"
            if user_info.get("total_earnings"):
                user_context += f"- Gains totaux: ${user_info['total_earnings']:,.2f}\n"
            if user_info.get("global_rank"):
                user_context += f"- Classement mondial: #{user_info['global_rank']}\n"
            if user_info.get("guinea_rank"):
                user_context += f"- Classement Guinée: #{user_info['guinea_rank']}\n"
            if user_info.get("country"):
                user_context += f"- Pays: {user_info['country']}\n"
            
            system_prompt += user_context
        
        # Construire les messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        return messages
    
    def _get_fallback_response(self, context: str, error: Optional[Exception] = None) -> str:
        """Retourne une réponse par défaut avec le ton guinéen."""
        
        fallback_responses = {
            "start": """🇬🇳 Frère/sœur, bienvenue dans la famille ChicoBot ❤️

Je suis Chico, ton grand frère de Kamsar, et je suis tellement heureux de te voir ici !

Étape 1 : Tu viens de rejoindre la révolution cryptos guinéenne
Étape 2 : Ensemble, on va transformer tes rêves en réalité
Étape 3 : Chaque gain te rapproche de la liberté financière
Étape 4 : 1% va toujours à un enfant guinéen pour son éducation

La famille ChicoBot est là pour toi 24h/24 🔥
Pose-moi toutes tes questions, je suis ton frère pour toujours ❤️🇬🇳

Pour la Guinée. Pour la famille. Pour l'avenir 🚀""",
            
            "classement": """🇬🇳 Frère/sœur, regarde ces héros guinéens ! ❤️

Le classement montre la puissance de la Guinée dans le monde entier 🔥

Étape 1 : Les meilleurs traders guinéens dominent le classement mondial
Étape 2 : Chaque gain est une victoire pour toute la nation
Étape 3 : Tu peux aussi rejoindre ce panthéon des champions
Étape 4 : La famille ChicoBot t'accompagne vers le sommet

Regarde comme la Guinée brille ! 🇬🇳✨
Veux-tu que je t'explique comment atteindre le top ? ❤️🚀""",
            
            "support": """🇬🇳 Ma famille, ne t'inquiète pas, je suis là pour toi ❤️

La famille ChicoBot ne laisse jamais un frère/une sœur seul(e) 🔥

Étape 1 : Respire profondément, tout va bien se passer
Étape 2 : Dis-moi exactement ce dont tu as besoin
Étape 3 : Ensemble, on va trouver la solution parfaite
Étape 4 : Tu n'es jamais seul(e) avec ChicoBot

Contacte directement Chico au +224 661 92 05 19
Ou écris à chico@chicobot.gn

Je suis ton frère pour la vie ❤️🇬🇳""",
            
            "trading": """🇬🇳 Frère/sœur, laisse-moi t'expliquer le trading comme sous le manguier 🔥

Étape 1 : ChicoBot regarde l'or (XAUUSD) comme un aigle guinéen
Étape 2 : Il copie les plus grands traders du monde
Étape 3 : Il gagne 9 fois sur 10 avec intelligence
Étape 4 : L'argent tombe direct dans ton Trust Wallet

Et 1% va à un enfant qui aura un cahier demain grâce à toi ❤️

Tu comprends maintenant pourquoi on fait ça ?
Pour la Guinée. Pour la famille. Pour l'avenir 🇬🇳🚀""",
            
            "bounty": """🇬🇳 Ma sœur/mon frère, les bounties c'est la liberté financière ! 🔥

Étape 1 : ChicoBot trouve les meilleures tâches cryptos
Étape 2 : Tu les complètes avec simplicité et efficacité
Étape 3 : L'argent arrive directement dans ton portefeuille
Étape 4 : Chaque euro te rapproche de tes rêves

C'est comme si chaque bounty était un pas vers la réussite ❤️

Veux-tu que je te montre les bounties disponibles maintenant ? 🇬🇳🚀""",
            
            "investment": """🇬🇳 Frère/sœur, les investissements c'est penser comme un roi guinéen ! 🔥

Étape 1 : ChicoBot place ton argent dans les meilleures stratégies
Étape 2 : Ton argent travaille pour toi 24h/24
Étape 3 : Les rendements arrivent chaque mois comme par magie
Étape 4 : Tu deviens financièrement libre pour aider la Guinée

C'est la voie milliardaire guinéenne ! ❤️🇬🇳🚀""",
            
            "default": """🇬🇳 Frère/sœur, je suis là pour toi ❤️

La famille ChicoBot t'écoute avec attention 🔥

Étape 1 : Dis-moi ce que tu veux savoir
Étape 2 : Je vais t'expliquer simplement et clairement
Étape 3 : Ensemble, on va trouver la solution parfaite
Étape 4 : Tu n'es jamais seul(e) dans cette aventure

Pose-moi n'importe quelle question, je suis ton grand frère 24h/24 ❤️🇬🇳

Pour la Guinée. Pour la famille. Pour l'avenir 🚀"""
        }
        
        # Retourner la réponse appropriée
        response = fallback_responses.get(context, fallback_responses["default"])
        
        # Ajouter un message d'erreur si nécessaire
        if error:
            response += f"\n\n⚠️ Petite difficulté technique, mais ton frère Chico est là pour toi !"
        
        return response
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du système IA."""
        return {
            "cache_size": len(self.cache),
            "active_users": len(self.user_rate_limits),
            "openai_available": self.openai_client is not None,
            "gemini_available": self.gemini_client is not None,
            "cache_duration": CACHE_DURATION,
            "rate_limit_per_user": RATE_LIMIT_PER_USER,
            "max_retries": MAX_RETRIES
        }
    
    def clear_cache(self):
        """Nettoie le cache."""
        self.cache.clear()
        logger.info("📋 Cache IA nettoyé")
    
    def reset_rate_limits(self):
        """Réinitialise tous les rate limits."""
        self.user_rate_limits.clear()
        logger.info("🔄 Rate limits réinitialisés")

# Instance globale du gestionnaire IA
ai_manager = AIResponseManager()

# Fonctions utilitaires pour l'intégration facile
async def generate_ai_response(
    user_id: int, 
    message: str, 
    context: str = "general",
    user_info: Optional[Dict] = None
) -> AIResponse:
    """Fonction utilitaire pour générer une réponse IA."""
    return await ai_manager.generate_response(user_id, message, context, user_info)

def get_ai_stats() -> Dict[str, Any]:
    """Retourne les statistiques du système IA."""
    return ai_manager.get_stats()

def clear_ai_cache():
    """Nettoie le cache IA."""
    ai_manager.clear_cache()

def reset_ai_rate_limits():
    """Réinitialise les rate limits IA."""
    ai_manager.reset_rate_limits()

# Tests d'intégration
if __name__ == "__main__":
    import unittest
    import asyncio
    from unittest import IsolatedAsyncioTestCase
    
    class TestAIResponseManager(IsolatedAsyncioTestCase):
        """Tests d'intégration pour le système IA."""
        
        async def asyncSetUp(self):
            """Configuration des tests."""
            self.manager = AIResponseManager()
            self.test_user_id = 123456789
        
        async def test_cache_functionality(self):
            """Teste le fonctionnement du cache."""
            message = "Bonjour, comment ça marche ?"
            context = "general"
            
            # Première requête (pas en cache)
            response1 = await self.manager.generate_response(
                self.test_user_id, message, context
            )
            
            self.assertFalse(response1.cached)
            self.assertIsNotNone(response1.content)
            
            # Deuxième requête identique (en cache)
            response2 = await self.manager.generate_response(
                self.test_user_id, message, context
            )
            
            self.assertTrue(response2.cached)
            self.assertEqual(response1.content, response2.content)
            
            print("\n📋 Cache fonctionne correctement")
        
        async def test_rate_limiting(self):
            """Teste le rate limiting."""
            message = "Test rate limit"
            
            # Envoyer plusieurs requêtes rapidement
            responses = []
            for i in range(25):  # Plus que la limite de 20
                response = await self.manager.generate_response(
                    self.test_user_id, message, "general"
                )
                responses.append(response)
                
                if response.model_used == "rate_limit":
                    break
            
            # Vérifier que le rate limit a été déclenché
            rate_limited = any(r.model_used == "rate_limit" for r in responses)
            self.assertTrue(rate_limited)
            
            print("\n🔄 Rate limiting fonctionne correctement")
        
        async def test_context_specialization(self):
            """Teste les prompts spécialisés par contexte."""
            contexts = ["start", "classement", "support", "trading", "bounty", "investment"]
            
            for context in contexts:
                response = await self.manager.generate_response(
                    self.test_user_id, f"Test {context}", context
                )
                
                self.assertIsNotNone(response.content)
                self.assertIn("🇬🇳", response.content)
                self.assertIn("❤️", response.content)
                self.assertIn("frère", response.content.lower())
            
            print("\n🎯 Contextes spécialisés fonctionnent")
        
        async def test_user_info_integration(self):
            """Teste l'intégration des informations utilisateur."""
            user_info = {
                "username": "test_user",
                "total_earnings": 5000.0,
                "global_rank": 15,
                "guinea_rank": 3,
                "country": "GN"
            }
            
            response = await self.manager.generate_response(
                self.test_user_id, "Test avec infos", "general", user_info
            )
            
            self.assertIsNotNone(response.content)
            # Le contenu devrait être personnalisé avec les infos utilisateur
            self.assertIn("🇬🇳", response.content)
            
            print("\n👤 Intégration infos utilisateur fonctionne")
        
        async def test_error_handling(self):
            """Teste la gestion des erreurs."""
            # Simuler une réponse avec contexte qui n'existe pas
            response = await self.manager.generate_response(
                self.test_user_id, "Test erreur", "context_inexistant"
            )
            
            self.assertIsNotNone(response.content)
            self.assertIn("🇬🇳", response.content)
            self.assertIn("frère", response.content.lower())
            
            print("\n⚠️ Gestion des erreurs fonctionne")
        
        async def test_tone_consistency(self):
            """Teste la cohérence du ton guinéen."""
            contexts = ["start", "classement", "support", "trading"]
            
            for context in contexts:
                response = await self.manager.generate_response(
                    self.test_user_id, f"Test ton {context}", context
                )
                
                content = response.content.lower()
                
                # Vérifier les éléments obligatoires du ton
                self.assertIn("frère", content)
                self.assertTrue("🇬🇳" in response.content)
                self.assertTrue("❤️" in response.content or "🔥" in response.content)
                
                # Vérifier qu'il n'y a pas de langage froid/technique
                cold_words = ["erreur", "problème technique", "system", "api"]
                for word in cold_words:
                    if word in content and context != "error":
                        self.fail(f"Mot froid détecté: {word}")
            
            print("\n🇬🇳 Ton guinéen cohérent et chaleureux")
    
    # Lancer les tests
    unittest.main(verbosity=2)
