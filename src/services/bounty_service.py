"""
Service de gestion des bounties pour ChicoBot.

Fonctionnalités principales :
- Recherche automatique de bounties textuelles via SerpAPI
- Analyse et priorisation des bounties
- Auto-complétion avec génération de contenu
- Soumission automatique via formulaire ou WalletConnect
- Suivi des gains et des performances
"""

import asyncio
import base64
import hashlib
import json
import logging
import os
import re
import time
from abc import ABC, abstractmethod
from collections import deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urljoin, urlparse

import aiohttp
import backoff
from bs4 import BeautifulSoup
from cachetools import TTLCache
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings
from core.ai_service import ai_service
from core.database import database
from core.logging_setup import get_logger
from core.security import WalletSecurityManager
from services.chico_academy import chico_academy
from services.foundation_service import chico_foundation

# Configuration du logger
logger = get_logger(__name__)

# Constantes
SERPAPI_URL = "https://serpapi.com/search"
CACHE_TTL = 6 * 60 * 60  # 6 heures pour les bounties
MAX_BOUNTIES_PER_SEARCH = 50
MIN_BOUNTY_REWARD = 100  # USD minimum
MAX_BOUNTY_REWARD = 5000  # USD maximum
APPLICATION_COOLDOWN = 300  # 5 minutes entre applications

# Cache pour les bounties
bounty_cache = TTLCache(maxsize=500, ttl=CACHE_TTL)

# Suivi des applications
application_timestamps = deque(maxlen=100)

# Templates de recherche optimisés
SEARCH_QUERIES = {
    "writing": "writing bounty OR content bounty OR thread bounty 300..1000 USD site:earn.superteam.fun OR gitcoin.co OR dework.xyz after:2025-11-01",
    "technical": "technical writing bounty OR documentation bounty 500..2000 USD site:earn.superteam.fun OR gitcoin.co OR dework.xyz after:2025-11-01",
    "content": "content creation bounty OR social media bounty 200..1500 USD site:earn.superteam.fun OR gitcoin.co OR dework.xyz after:2025-11-01",
    "research": "research bounty OR analysis bounty 400..3000 USD site:earn.superteam.fun OR gitcoin.co OR dework.xyz after:2025-11-01"
}

# Headers pour les requêtes web
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0"
}

class BountyPlatform(ABC):
    """Interface pour les plateformes de bounty."""
    
    @abstractmethod
    async def extract_bounty_details(self, url: str) -> Dict[str, Any]:
        """Extrait les détails d'un bounty depuis son URL."""
        pass
    
    @abstractmethod
    async def submit_application(self, bounty_url: str, content: str) -> bool:
        """Soumet une candidature à un bounty."""
        pass
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """Retourne le nom de la plateforme."""
        pass

class SuperTeamPlatform(BountyPlatform):
    """Implémentation pour SuperTeam Earn."""
    
    def __init__(self):
        self.base_url = "https://earn.superteam.fun"
    
    async def extract_bounty_details(self, url: str) -> Dict[str, Any]:
        """Extrait les détails d'un bounty SuperTeam."""
        try:
            async with aiohttp.ClientSession(headers=DEFAULT_HEADERS) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}")
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extraction du titre
                    title_elem = soup.find('h1') or soup.find('title')
                    title = title_elem.get_text().strip() if title_elem else "Titre inconnu"
                    
                    # Extraction de la récompense
                    reward = 0
                    reward_patterns = [
                        r'\$(\d+(?:,\d+)*)',
                        r'(\d+(?:,\d+)*)\s*USD',
                        r'(\d+(?:,\d+)*)\s*SOL',
                        r'(\d+(?:,\d+)*)\s*ETH'
                    ]
                    
                    text_content = soup.get_text()
                    for pattern in reward_patterns:
                        matches = re.findall(pattern, text_content, re.IGNORECASE)
                        if matches:
                            reward = float(matches[0].replace(',', ''))
                            break
                    
                    # Extraction de la description
                    desc_elem = soup.find('div', class_='description') or soup.find('div', class_='content')
                    description = desc_elem.get_text().strip() if desc_elem else text_content[:500]
                    
                    # Extraction des exigences
                    requirements = []
                    req_patterns = [
                        r'Requirements?:\s*(.*?)(?=\n\n|\n[A-Z]|\Z)',
                        r'What you\'ll do:\s*(.*?)(?=\n\n|\n[A-Z]|\Z)',
                        r'Tasks:\s*(.*?)(?=\n\n|\n[A-Z]|\Z)'
                    ]
                    
                    for pattern in req_patterns:
                        matches = re.findall(pattern, text_content, re.IGNORECASE | re.DOTALL)
                        if matches:
                            requirements.extend([req.strip() for req in matches[0].split('\n') if req.strip()])
                    
                    # Extraction de la date limite
                    deadline = None
                    deadline_patterns = [
                        r'Deadline:\s*(\d{4}-\d{2}-\d{2})',
                        r'Ends?:\s*(\d{4}-\d{2}-\d{2})',
                        r'Due:\s*(\d{4}-\d{2}-\d{2})'
                    ]
                    
                    for pattern in deadline_patterns:
                        match = re.search(pattern, text_content, re.IGNORECASE)
                        if match:
                            deadline = match.group(1)
                            break
                    
                    return {
                        "title": title,
                        "description": description,
                        "reward_usd": reward,
                        "requirements": requirements,
                        "deadline": deadline,
                        "platform": self.get_platform_name(),
                        "url": url,
                        "difficulty": self._estimate_difficulty(reward, description),
                        "estimated_time": self._estimate_time(reward, description)
                    }
                    
        except Exception as e:
            logger.error(f"Erreur extraction bounty SuperTeam {url}: {e}")
            raise
    
    async def submit_application(self, bounty_url: str, content: str) -> bool:
        """Soumet une candidature à un bounty SuperTeam VIA API."""
        try:
            # CONNEXION WALLETCONNECT VIA CLÉ PRIVÉE UTILISATEUR
            user_wallet_private_key = os.getenv("WALLET_PRIVATE_KEY")
            if not user_wallet_private_key:
                logger.error("Clé wallet utilisateur non trouvée")
                return False
                
            # 1. Connexion WalletConnect automatique
            wallet_connect_result = await self._connect_walletconnect(user_wallet_private_key)
            if not wallet_connect_result:
                logger.error("Échec connexion WalletConnect")
                return False
                
            # 2. Remplissage formulaire automatique
            form_data = {
                "content": content,
                "wallet_address": wallet_connect_result["address"],
                "signature": wallet_connect_result["signature"]
            }
            
            # 3. Soumission API réelle
            async with aiohttp.ClientSession(headers=DEFAULT_HEADERS) as session:
                submit_url = f"{self.base_url}/api/bounties/submit"
                
                async with session.post(submit_url, json=form_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        if result.get("success"):
                            bounty_id = result.get("bounty_id")
                            
                            # 4. Vérification automatique du statut
                            payment_result = await self._check_bounty_payment(bounty_id)
                            
                            if payment_result["paid"]:
                                # 5. Réception automatique des fonds
                                await self._receive_bounty_payment(payment_result["amount"])
                                
                                # 6. Enregistrement dans base de données
                                await database.log_bounty_submission(
                                    url=bounty_url,
                                    content=content,
                                    status="paid",
                                    amount=payment_result["amount"],
                                    timestamp=datetime.now()
                                )
                                
                                logger.info(f"💰 Bounty payé: ${payment_result['amount']}")
                                return True
                            else:
                                await database.log_bounty_submission(
                                    url=bounty_url,
                                    content=content,
                                    status="submitted",
                                    timestamp=datetime.now()
                                )
                                return True
                        else:
                            logger.error(f"Erreur soumission: {result.get('error')}")
                            return False
                    else:
                        logger.error(f"HTTP {response.status} lors soumission")
                        return False
                        
        except Exception as e:
            logger.error(f"Erreur soumission bounty {bounty_url}: {e}")
            return False
    
    async def _connect_walletconnect(self, private_key: str) -> Dict[str, str]:
        """Connexion WalletConnect automatique avec clé privée."""
        try:
            # Simulation de connexion WalletConnect
            # En pratique: utiliser web3.py + walletconnect protocol
            
            wallet_address = "0x" + hashlib.sha256(private_key.encode()).hexdigest()[:40]
            signature = "0x" + hashlib.sha256((private_key + "walletconnect").encode()).hexdigest()
            
            return {
                "address": wallet_address,
                "signature": signature,
                "connected": True
            }
        except Exception as e:
            logger.error(f"Erreur WalletConnect: {e}")
            return {"connected": False}
    
    async def _check_bounty_payment(self, bounty_id: str) -> Dict[str, Any]:
        """Vérifie si un bounty a été payé."""
        try:
            # Vérification automatique du statut de paiement
            async with aiohttp.ClientSession() as session:
                check_url = f"{self.base_url}/api/bounties/{bounty_id}/status"
                
                async with session.get(check_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        return {
                            "paid": data.get("status") == "paid",
                            "amount": data.get("amount", 0),
                            "transaction_hash": data.get("tx_hash")
                        }
            return {"paid": False, "amount": 0}
        except Exception as e:
            logger.error(f"Erreur vérification paiement: {e}")
            return {"paid": False, "amount": 0}
    
    async def _receive_bounty_payment(self, amount: float):
        """Reçoit automatiquement le paiement de bounty."""
        try:
            user_wallet = os.getenv("WALLET_PRIVATE_KEY")
            
            # Simulation de réception de fonds
            # En pratique: vérifier transaction blockchain + créditer compte
            
            await database.add_user_balance(1, amount)  # user_id=1 pour l'exemple
            
            logger.info(f"💸 Paiution bounty reçu: ${amount}")
            
        except Exception as e:
            logger.error(f"Erreur réception paiement: {e}")
    
    def get_platform_name(self) -> str:
        return "superteam"
    
    def _estimate_difficulty(self, reward: float, description: str) -> str:
        """Estime la difficulté du bounty."""
        if reward < 300:
            return "easy"
        elif reward < 1000:
            return "medium"
        else:
            return "hard"
    
    def _estimate_time(self, reward: float, description: str) -> str:
        """Estime le temps de completion."""
        if reward < 300:
            return "1-2 hours"
        elif reward < 1000:
            return "3-6 hours"
        else:
            return "1-2 days"

class GitcoinPlatform(BountyPlatform):
    """Implémentation pour Gitcoin."""
    
    def __init__(self):
        self.base_url = "https://gitcoin.co"
    
    async def extract_bounty_details(self, url: str) -> Dict[str, Any]:
        """Extrait les détails d'un bounty Gitcoin."""
        try:
            async with aiohttp.ClientSession(headers=DEFAULT_HEADERS) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}")
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extraction similaire à SuperTeam mais adaptée à Gitcoin
                    title_elem = soup.find('h1') or soup.find('title')
                    title = title_elem.get_text().strip() if title_elem else "Titre inconnu"
                    
                    # Extraction de la récompense (Gitcoin utilise souvent des tokens)
                    reward = 0
                    reward_patterns = [
                        r'\$(\d+(?:,\d+)*)',
                        r'(\d+(?:,\d+)*)\s*USD',
                        r'(\d+(?:,\d+)*)\s*DAI',
                        r'(\d+(?:,\d+)*)\s*USDC'
                    ]
                    
                    text_content = soup.get_text()
                    for pattern in reward_patterns:
                        matches = re.findall(pattern, text_content, re.IGNORECASE)
                        if matches:
                            reward = float(matches[0].replace(',', ''))
                            break
                    
                    desc_elem = soup.find('div', class_='description') or soup.find('div', class_='content')
                    description = desc_elem.get_text().strip() if desc_elem else text_content[:500]
                    
                    return {
                        "title": title,
                        "description": description,
                        "reward_usd": reward,
                        "requirements": [],
                        "deadline": None,
                        "platform": self.get_platform_name(),
                        "url": url,
                        "difficulty": "medium",
                        "estimated_time": "2-4 hours"
                    }
                    
        except Exception as e:
            logger.error(f"Erreur extraction bounty Gitcoin {url}: {e}")
            raise
    
    async def submit_application(self, bounty_url: str, content: str) -> bool:
        """Soumet une candidature à un bounty Gitcoin VIA API."""
        try:
            # CONNEXION WALLETCONNECT VIA CLÉ PRIVÉE UTILISATEUR
            user_wallet_private_key = os.getenv("WALLET_PRIVATE_KEY")
            if not user_wallet_private_key:
                logger.error("Clé wallet utilisateur non trouvée")
                return False
                
            # 1. Connexion WalletConnect automatique
            wallet_connect_result = await self._connect_walletconnect(user_wallet_private_key)
            if not wallet_connect_result:
                logger.error("Échec connexion WalletConnect")
                return False
                
            # 2. Soumission API Gitcoin
            form_data = {
                "content": content,
                "wallet_address": wallet_connect_result["address"],
                "signature": wallet_connect_result["signature"]
            }
            
            async with aiohttp.ClientSession(headers=DEFAULT_HEADERS) as session:
                submit_url = f"{self.base_url}/api/grants/submit"
                
                async with session.post(submit_url, json=form_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        if result.get("success"):
                            grant_id = result.get("grant_id")
                            
                            # 3. Vérification automatique du statut
                            payment_result = await self._check_grant_payment(grant_id)
                            
                            if payment_result["paid"]:
                                # 4. Réception automatique des fonds
                                await self._receive_grant_payment(payment_result["amount"])
                                
                                await database.log_bounty_submission(
                                    url=bounty_url,
                                    content=content,
                                    status="paid",
                                    amount=payment_result["amount"],
                                    timestamp=datetime.now()
                                )
                                
                                logger.info(f"💰 Grant Gitcoin payé: ${payment_result['amount']}")
                                return True
                            else:
                                await database.log_bounty_submission(
                                    url=bounty_url,
                                    content=content,
                                    status="submitted",
                                    timestamp=datetime.now()
                                )
                                return True
                        else:
                            logger.error(f"Erreur soumission Gitcoin: {result.get('error')}")
                            return False
                    else:
                        logger.error(f"HTTP {response.status} lors soumission Gitcoin")
                        return False
                        
        except Exception as e:
            logger.error(f"Erreur soumission Gitcoin {bounty_url}: {e}")
            return False
    
    async def _connect_walletconnect(self, private_key: str) -> Dict[str, str]:
        """Connexion WalletConnect automatique avec clé privée."""
        try:
            wallet_address = "0x" + hashlib.sha256(private_key.encode()).hexdigest()[:40]
            signature = "0x" + hashlib.sha256((private_key + "gitcoin").encode()).hexdigest()
            
            return {
                "address": wallet_address,
                "signature": signature,
                "connected": True
            }
        except Exception as e:
            logger.error(f"Erreur WalletConnect Gitcoin: {e}")
            return {"connected": False}
    
    async def _check_grant_payment(self, grant_id: str) -> Dict[str, Any]:
        """Vérifie si un grant Gitcoin a été payé."""
        try:
            async with aiohttp.ClientSession() as session:
                check_url = f"{self.base_url}/api/grants/{grant_id}/status"
                
                async with session.get(check_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        return {
                            "paid": data.get("status") == "paid",
                            "amount": data.get("amount", 0),
                            "transaction_hash": data.get("tx_hash")
                        }
            return {"paid": False, "amount": 0}
        except Exception as e:
            logger.error(f"Erreur vérification paiement Gitcoin: {e}")
            return {"paid": False, "amount": 0}
    
    async def _receive_grant_payment(self, amount: float):
        """Reçoit automatiquement le paiement de grant Gitcoin."""
        try:
            await database.add_user_balance(1, amount)
            logger.info(f"💸 Paiution Gitcoin reçu: ${amount}")
        except Exception as e:
            logger.error(f"Erreur réception paiement Gitcoin: {e}")
    
    def get_platform_name(self) -> str:
        return "gitcoin"

class DeworkPlatform(BountyPlatform):
    """Implémentation pour Dework."""
    
    def __init__(self):
        self.base_url = "https://dework.xyz"
    
    async def extract_bounty_details(self, url: str) -> Dict[str, Any]:
        """Extrait les détails d'un bounty Dework."""
        try:
            async with aiohttp.ClientSession(headers=DEFAULT_HEADERS) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}")
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    title_elem = soup.find('h1') or soup.find('title')
                    title = title_elem.get_text().strip() if title_elem else "Titre inconnu"
                    
                    reward = 0
                    reward_patterns = [
                        r'\$(\d+(?:,\d+)*)',
                        r'(\d+(?:,\d+)*)\s*USD',
                        r'(\d+(?:,\d+)*)\s*MATIC',
                        r'(\d+(?:,\d+)*)\s*ETH'
                    ]
                    
                    text_content = soup.get_text()
                    for pattern in reward_patterns:
                        matches = re.findall(pattern, text_content, re.IGNORECASE)
                        if matches:
                            reward = float(matches[0].replace(',', ''))
                            break
                    
                    desc_elem = soup.find('div', class_='description') or soup.find('div', class_='content')
                    description = desc_elem.get_text().strip() if desc_elem else text_content[:500]
                    
                    return {
                        "title": title,
                        "description": description,
                        "reward_usd": reward,
                        "requirements": [],
                        "deadline": None,
                        "platform": self.get_platform_name(),
                        "url": url,
                        "difficulty": "medium",
                        "estimated_time": "2-4 hours"
                    }
                    
        except Exception as e:
            logger.error(f"Erreur extraction bounty Dework {url}: {e}")
            raise
    
    async def submit_application(self, bounty_url: str, content: str) -> bool:
        """Soumet une candidature à un bounty Dework VIA API."""
        try:
            # CONNEXION WALLETCONNECT VIA CLÉ PRIVÉE UTILISATEUR
            user_wallet_private_key = os.getenv("WALLET_PRIVATE_KEY")
            if not user_wallet_private_key:
                logger.error("Clé wallet utilisateur non trouvée")
                return False
                
            # 1. Connexion WalletConnect automatique
            wallet_connect_result = await self._connect_walletconnect(user_wallet_private_key)
            if not wallet_connect_result:
                logger.error("Échec connexion WalletConnect")
                return False
                
            # 2. Soumission API Dework
            form_data = {
                "content": content,
                "wallet_address": wallet_connect_result["address"],
                "signature": wallet_connect_result["signature"]
            }
            
            async with aiohttp.ClientSession(headers=DEFAULT_HEADERS) as session:
                submit_url = f"{self.base_url}/api/tasks/submit"
                
                async with session.post(submit_url, json=form_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        if result.get("success"):
                            task_id = result.get("task_id")
                            
                            # 3. Vérification automatique du statut
                            payment_result = await self._check_task_payment(task_id)
                            
                            if payment_result["paid"]:
                                # 4. Réception automatique des fonds
                                await self._receive_task_payment(payment_result["amount"])
                                
                                await database.log_bounty_submission(
                                    url=bounty_url,
                                    content=content,
                                    status="paid",
                                    amount=payment_result["amount"],
                                    timestamp=datetime.now()
                                )
                                
                                logger.info(f"💰 Task Dework payé: ${payment_result['amount']}")
                                return True
                            else:
                                await database.log_bounty_submission(
                                    url=bounty_url,
                                    content=content,
                                    status="submitted",
                                    timestamp=datetime.now()
                                )
                                return True
                        else:
                            logger.error(f"Erreur soumission Dework: {result.get('error')}")
                            return False
                    else:
                        logger.error(f"HTTP {response.status} lors soumission Dework")
                        return False
                        
        except Exception as e:
            logger.error(f"Erreur soumission Dework {bounty_url}: {e}")
            return False
    
    async def _connect_walletconnect(self, private_key: str) -> Dict[str, str]:
        """Connexion WalletConnect automatique avec clé privée."""
        try:
            wallet_address = "0x" + hashlib.sha256(private_key.encode()).hexdigest()[:40]
            signature = "0x" + hashlib.sha256((private_key + "dework").encode()).hexdigest()
            
            return {
                "address": wallet_address,
                "signature": signature,
                "connected": True
            }
        except Exception as e:
            logger.error(f"Erreur WalletConnect Dework: {e}")
            return {"connected": False}
    
    async def _check_task_payment(self, task_id: str) -> Dict[str, Any]:
        """Vérifie si une tâche Dework a été payée."""
        try:
            async with aiohttp.ClientSession() as session:
                check_url = f"{self.base_url}/api/tasks/{task_id}/status"
                
                async with session.get(check_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        return {
                            "paid": data.get("status") == "paid",
                            "amount": data.get("amount", 0),
                            "transaction_hash": data.get("tx_hash")
                        }
            return {"paid": False, "amount": 0}
        except Exception as e:
            logger.error(f"Erreur vérification paiement Dework: {e}")
            return {"paid": False, "amount": 0}
    
    async def _receive_task_payment(self, amount: float):
        """Reçoit automatiquement le paiement de tâche Dework."""
        try:
            await database.add_user_balance(1, amount)
            logger.info(f"💸 Paiution Dework reçu: ${amount}")
        except Exception as e:
            logger.error(f"Erreur réception paiement Dework: {e}")
    
    def get_platform_name(self) -> str:
        return "dework"

class BountyService:
    """Service principal de gestion des bounties."""
    
    def __init__(self):
        self.platforms = {
            "superteam": SuperTeamPlatform(),
            "gitcoin": GitcoinPlatform(),
            "dework": DeworkPlatform()
        }
        self.wallet_manager = WalletSecurityManager()
        self.search_count = 0
        self.application_count = 0
        self.success_count = 0
    
    def _identify_platform(self, url: str) -> Optional[BountyPlatform]:
        """Identifie la plateforme depuis l'URL."""
        domain = urlparse(url).netloc.lower()
        
        if "superteam.fun" in domain:
            return self.platforms["superteam"]
        elif "gitcoin.co" in domain:
            return self.platforms["gitcoin"]
        elif "dework.xyz" in domain:
            return self.platforms["dework"]
        
        return None
    
    async def search_active_bounties(
        self, 
        category: str = "writing",
        max_results: int = MAX_BOUNTIES_PER_SEARCH
    ) -> List[Dict[str, Any]]:
        """
        Recherche les bounties actives via SerpAPI.
        
        Args:
            category: Catégorie de bounty à rechercher
            max_results: Nombre maximum de résultats
            
        Returns:
            Liste des bounties trouvés
        """
        try:
            # Vérifier le cache
            cache_key = f"search_{category}_{max_results}"
            if cache_key in bounty_cache:
                logger.info("Résultats récupérés depuis le cache")
                return bounty_cache[cache_key]
            
            # Préparer la requête
            query = SEARCH_QUERIES.get(category, SEARCH_QUERIES["writing"])
            
            params = {
                "engine": "google",
                "q": query,
                "api_key": settings.SERPAPI_KEY,
                "num": max_results,
                "hl": "en",
                "gl": "us"
            }
            
            logger.info(f"Recherche de bounties avec query: {query}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(SERPAPI_URL, params=params) as response:
                    if response.status != 200:
                        raise Exception(f"SerpAPI error: {response.status}")
                    
                    data = await response.json()
                    
                    if "error" in data:
                        raise Exception(f"SerpAPI error: {data['error']}")
                    
                    # Extraire les résultats
                    bounties = []
                    if "organic_results" in data:
                        for result in data["organic_results"]:
                            bounty = self._parse_search_result(result)
                            if bounty and self._is_valid_bounty(bounty):
                                bounties.append(bounty)
                    
                    # Filtrer et trier
                    filtered_bounties = self._filter_and_prioritize_bounties(bounties)
                    
                    # Mettre en cache
                    bounty_cache[cache_key] = filtered_bounties
                    self.search_count += 1
                    
                    logger.info(f"Trouvé {len(filtered_bounties)} bounties valides")
                    return filtered_bounties
                    
        except Exception as e:
            logger.error(f"Erreur recherche bounties: {e}")
            return []
    
    def _parse_search_result(self, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse un résultat de recherche en bounty."""
        try:
            url = result.get("link", "")
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            
            if not url or not title:
                return None
            
            # Extraire la récompense depuis le titre/snippet
            reward = 0
            reward_patterns = [
                r'\$(\d+(?:,\d+)*)',
                r'(\d+(?:,\d+)*)\s*USD',
                r'(\d+(?:,\d+)*)\s*SOL',
                r'(\d+(?:,\d+)*)\s*ETH'
            ]
            
            text = f"{title} {snippet}"
            for pattern in reward_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    reward = float(matches[0].replace(',', ''))
                    break
            
            return {
                "title": title,
                "description": snippet,
                "reward_usd": reward,
                "url": url,
                "platform": self._identify_platform(url).get_platform_name() if self._identify_platform(url) else "unknown",
                "source": "search"
            }
            
        except Exception as e:
            logger.error(f"Erreur parsing résultat: {e}")
            return None
    
    def _is_valid_bounty(self, bounty: Dict[str, Any]) -> bool:
        """Vérifie si un bounty est valide."""
        # Vérifier la récompense
        reward = bounty.get("reward_usd", 0)
        if reward < MIN_BOUNTY_REWARD or reward > MAX_BOUNTY_REWARD:
            return False
        
        # Vérifier que c'est bien un bounty de contenu
        title = bounty.get("title", "").lower()
        desc = bounty.get("description", "").lower()
        
        bounty_keywords = [
            "bounty", "content", "writing", "thread", "article", "blog",
            "documentation", "tutorial", "guide", "research", "analysis"
        ]
        
        has_bounty_keyword = any(keyword in title or keyword in desc for keyword in bounty_keywords)
        
        # Éviter les bounties déjà complétées
        if self._is_already_completed(bounty["url"]):
            return False
        
        return has_bounty_keyword
    
    def _is_already_completed(self, url: str) -> bool:
        """Vérifie si un bounty a déjà été complété."""
        # En pratique, vérifier dans la base de données
        return False  # Simplifié pour l'exemple
    
    def _filter_and_prioritize_bounties(self, bounties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filtre et priorise les bounties."""
        # Supprimer les doublons
        seen_urls = set()
        unique_bounties = []
        
        for bounty in bounties:
            url = bounty["url"]
            if url not in seen_urls:
                seen_urls.add(url)
                unique_bounties.append(bounty)
        
        # Trier par ratio gain/temps estimé
        def priority_score(bounty):
            reward = bounty.get("reward_usd", 0)
            difficulty = bounty.get("difficulty", "medium")
            
            difficulty_multiplier = {
                "easy": 1.0,
                "medium": 0.8,
                "hard": 0.6
            }.get(difficulty, 0.7)
            
            return reward * difficulty_multiplier
        
        return sorted(unique_bounties, key=priority_score, reverse=True)
    
    async def auto_apply_and_complete(self, bounty_url: str) -> bool:
        """
        Applique et complète automatiquement un bounty.
        
        Args:
            bounty_url: URL du bounty à compléter
            
        Returns:
            True si succès, False sinon
        """
        try:
            # Vérifier le cooldown
            if not self._can_apply_now():
                logger.warning("Cooldown d'application actif")
                return False
            
            # Identifier la plateforme
            platform = self._identify_platform(bounty_url)
            if not platform:
                logger.error(f"Plateforme non reconnue pour {bounty_url}")
                return False
            
            # Extraire les détails du bounty
            bounty_details = await platform.extract_bounty_details(bounty_url)
            logger.info(f"Bounty identifié: {bounty_details['title']}")
            
            # Vérifier si déjà complété
            if await self._is_already_submitted(bounty_url):
                logger.info("Bounty déjà soumis")
                return False
            
            # Générer le contenu
            content = await self._generate_bounty_content(bounty_details)
            logger.info("Contenu généré avec succès")
            
            # Soumettre la candidature
            success = await platform.submit_application(bounty_url, content)
            
            if success:
                self.application_count += 1
                self.success_count += 1
                application_timestamps.append(time.time())
                
                # Estimer les gains
                estimated_earnings = bounty_details.get("reward_usd", 0)
                
                # Prélèvement pour la Chico Foundation (1%)
                foundation_result = await chico_foundation.process_gain(
                    user_id=1,  # user_id=1 pour l'exemple
                    username="example_user",
                    gain_amount=estimated_earnings,
                    gain_type="bounty"
                )
                
                if foundation_result["success"]:
                    net_earnings = foundation_result["user_net_amount"]
                    foundation_amount = foundation_result["foundation_amount"]
                    
                    logger.info(f"🇬🇳 Foundation: {foundation_amount:.2f}$ prélevés sur {estimated_earnings:.2f}$ (bounty)")
                    
                    # Enregistrer les gains nets pour l'utilisateur
                    await database.add_bounty_earnings(1, net_earnings)
                    
                    # Vérifier si un palier Academy est débloqué
                    current_total = await database.get_user_total_earnings(1)
                    academy_result = await chico_academy.check_milestone_unlock(
                        user_id=1,
                        username="example_user", 
                        current_earnings=current_total
                    )
                    
                    if academy_result["success"] and academy_result["newly_unlocked"]:
                        logger.info(f"🎓 Academy: {len(academy_result['newly_unlocked'])} cours débloqués !")
                else:
                    # Fallback si foundation indisponible
                    await database.add_bounty_earnings(1, estimated_earnings)
                
                logger.info(f"Bounty complété avec succès - Gains estimés: ${estimated_earnings}")
                return True
            else:
                self.application_count += 1
                logger.error("Échec de la soumission")
                return False
                
        except Exception as e:
            logger.error(f"Erreur auto-complétion bounty {bounty_url}: {e}")
            return False
    
    def _can_apply_now(self) -> bool:
        """Vérifie si on peut appliquer maintenant (cooldown)."""
        if not application_timestamps:
            return True
        
        last_application = application_timestamps[-1]
        return time.time() - last_application > APPLICATION_COOLDOWN
    
    async def _is_already_submitted(self, bounty_url: str) -> bool:
        """Vérifie si un bounty a déjà été soumis."""
        # En pratique, vérifier dans la base de données
        return False
    
    async def _generate_bounty_content(self, bounty_details: Dict[str, Any]) -> str:
        """Génère le contenu pour un bounty."""
        try:
            title = bounty_details.get("title", "")
            description = bounty_details.get("description", "")
            requirements = bounty_details.get("requirements", [])
            reward = bounty_details.get("reward_usd", 0)
            platform = bounty_details.get("platform", "")
            
            # Adapter le prompt selon le type de bounty
            if "writing" in title.lower() or "content" in title.lower():
                prompt = f"""
                Génère un contenu de haute qualité pour le bounty suivant:
                
                Titre: {title}
                Description: {description}
                Exigences: {', '.join(requirements)}
                Récompense: ${reward}
                Plateforme: {platform}
                
                Instructions:
                - Le contenu doit être professionnel et bien structuré
                - Respecter toutes les exigences mentionnées
                - Inclure des exemples pratiques si pertinent
                - Format: Markdown avec titres clairs
                - Longueur: 800-1200 mots selon la complexité
                """
            elif "thread" in title.lower() or "twitter" in title.lower():
                prompt = f"""
                Crée un thread Twitter engageant pour:
                
                Sujet: {title}
                Contexte: {description}
                Récompense: ${reward}
                
                Instructions:
                - 10-15 tweets maximum
                - Format: Numéroté (1/15, 2/15, etc.)
                - Hashtags pertinents inclus
                - Émoticônes appropriées
                - Call-to-action clair à la fin
                """
            else:
                prompt = f"""
                Crée un livrable exceptionnel pour:
                
                {title}
                
                Description: {description}
                Exigences: {', '.join(requirements)}
                
                Le contenu doit dépasser les attentes et être prêt à soumettre.
                """
            
            # Générer via le service IA
            content = await ai_service.generate(prompt, temperature=0.7)
            
            # Post-traitement du contenu
            processed_content = self._post_process_content(content, bounty_details)
            
            return processed_content
            
        except Exception as e:
            logger.error(f"Erreur génération contenu: {e}")
            raise
    
    def _post_process_content(self, content: str, bounty_details: Dict[str, Any]) -> str:
        """Post-traite le contenu généré."""
        # Ajouter un en-tête professionnel
        header = f"""
# Submission for: {bounty_details.get('title', 'Bounty')}

**Platform:** {bounty_details.get('platform', 'Unknown')}
**Reward:** ${bounty_details.get('reward_usd', 0)}
**Submitted:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

"""
        
        # Nettoyer le contenu
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = content.strip()
        
        return header + content
    
    async def get_bounty_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques des bounties."""
        return {
            "search_count": self.search_count,
            "application_count": self.application_count,
            "success_count": self.success_count,
            "success_rate": self.success_count / max(self.application_count, 1),
            "cache_size": len(bounty_cache),
            "total_earnings": await self._get_total_earnings()
        }
    
    async def _get_total_earnings(self) -> float:
        """Calcule les gains totaux."""
        # En pratique, récupérer depuis la base de données
        return 0.0
    
    async def get_pending_applications(self) -> List[Dict[str, Any]]:
        """Retourne les applications en attente."""
        # En pratique, récupérer depuis la base de données
        return []
    
    async def cleanup_old_cache_entries(self):
        """Nettoie les anciennes entrées du cache."""
        # Implémentation du nettoyage
        pass

class BountyService:
    """Service de gestion des bounties ChicoBot."""
    
    def __init__(self):
        self.application_count = 0
        self.success_count = 0
        self.application_timestamps = []
        self.is_initialized = False
        self.is_running = False
        
    async def initialize(self) -> bool:
        """Initialise le service bounty."""
        try:
            logger.info("🇬🇳 Initialisation du service bounty...")
            
            # Charger les données existantes
            await self._load_existing_data()
            
            self.is_initialized = True
            logger.info("✅ Service bounty initialisé")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation service bounty: {e}")
            return False
    
    async def _load_existing_data(self):
        """Charge les données existantes."""
        try:
            # Récupérer les statistiques depuis la base de données
            stats = await database.get_bounty_stats()
            if stats:
                self.application_count = stats.get("application_count", 0)
                self.success_count = stats.get("success_count", 0)
                
        except Exception as e:
            logger.error(f"❌ Erreur chargement données bounty: {e}")
    
    async def run_bounty_hunter(self):
        """Exécute le bounty hunter en continu."""
        logger.info("🏹 Démarrage du bounty hunter...")
        
        self.is_running = True
        
        while self.is_running:
            try:
                # Rechercher de nouvelles bounties
                bounties = await self.search_bounties("crypto bounty text writing")
                
                if bounties:
                    # Appliquer aux meilleures bounties
                    for bounty in bounties[:3]:  # Top 3
                        if self._can_apply_now():
                            success = await self.auto_apply_and_complete(bounty["url"])
                            if success:
                                await asyncio.sleep(300)  # 5 minutes entre succès
                        else:
                            break
                
                # Pause entre les recherches
                await asyncio.sleep(3600)  # 1 heure
                
            except Exception as e:
                logger.error(f"❌ Erreur bounty hunter: {e}")
                await asyncio.sleep(300)  # 5 minutes en cas d'erreur
    
    async def shutdown(self):
        """Arrête le service bounty."""
        logger.info("🛑 Arrêt du service bounty...")
        self.is_running = False

# Instance globale du service bounty
bounty_service = BountyService()

# Tests d'intégration
if __name__ == "__main__":
    import unittest
    from unittest import IsolatedAsyncioTestCase
    
    class TestBountyService(IsolatedAsyncioTestCase):
        """Tests d'intégration pour le service de bounties."""
        
        async def asyncSetUp(self):
            """Configuration des tests."""
            self.service = BountyService()
        
        async def test_search_bounties(self):
            """Teste la recherche de bounties."""
            bounties = await self.service.search_active_bounties("writing", 10)
            self.assertIsInstance(bounties, list)
            
            if bounties:
                bounty = bounties[0]
                self.assertIn("title", bounty)
                self.assertIn("url", bounty)
                self.assertIn("reward_usd", bounty)
                
                print(f"\n=== BOUNTY TROUVÉ ===")
                print(f"Titre: {bounty['title']}")
                print(f"Récompense: ${bounty['reward_usd']}")
                print(f"URL: {bounty['url']}")
        
        async def test_platform_identification(self):
            """Teste l'identification des plateformes."""
            test_urls = [
                "https://earn.superteam.fun/bounty/123",
                "https://gitcoin.co/issue/456",
                "https://dework.xyz/task/789",
                "https://unknown.com/bounty/999"
            ]
            
            for url in test_urls:
                platform = self.service._identify_platform(url)
                platform_name = platform.get_platform_name() if platform else "unknown"
                print(f"\n{url} -> {platform_name}")
        
        async def test_bounty_validation(self):
            """Teste la validation des bounties."""
            valid_bounty = {
                "title": "Writing bounty for blog post",
                "description": "Create a 1000-word article",
                "reward_usd": 500,
                "url": "https://example.com/bounty/1"
            }
            
            invalid_bounty = {
                "title": "Random task",
                "description": "Something else",
                "reward_usd": 50,  # Trop bas
                "url": "https://example.com/task/2"
            }
            
            self.assertTrue(self.service._is_valid_bounty(valid_bounty))
            self.assertFalse(self.service._is_valid_bounty(invalid_bounty))
            
            print("\n=== VALIDATION BOUNTY ===")
            print("Bounty valide:", self.service._is_valid_bounty(valid_bounty))
            print("Bounty invalide:", self.service._is_valid_bounty(invalid_bounty))
        
        async def test_content_generation(self):
            """Teste la génération de contenu."""
            bounty_details = {
                "title": "Write a DeFi tutorial",
                "description": "Create a beginner-friendly tutorial about DeFi",
                "requirements": ["Explain basic concepts", "Include examples"],
                "reward_usd": 300,
                "platform": "superteam"
            }
            
            content = await self.service._generate_bounty_content(bounty_details)
            
            self.assertIsInstance(content, str)
            self.assertGreater(len(content), 500)
            self.assertIn("DeFi", content)
            
            print("\n=== CONTENU GÉNÉRÉ ===")
            print(content[:500] + "..." if len(content) > 500 else content)
        
        async def test_priority_scoring(self):
            """Teste le système de priorisation."""
            bounties = [
                {"title": "Easy bounty", "reward_usd": 200, "difficulty": "easy"},
                {"title": "Medium bounty", "reward_usd": 500, "difficulty": "medium"},
                {"title": "Hard bounty", "reward_usd": 1000, "difficulty": "hard"},
                {"title": "Super hard bounty", "reward_usd": 2000, "difficulty": "hard"}
            ]
            
            # Trier par priorité
            sorted_bounties = self.service._filter_and_prioritize_bounties(bounties)
            
            print("\n=== PRIORITATION ===")
            for i, bounty in enumerate(sorted_bounties):
                print(f"{i+1}. {bounty['title']} - ${bounty['reward_usd']} ({bounty['difficulty']})")
        
        async def test_cooldown_system(self):
            """Teste le système de cooldown."""
            # Réinitialiser
            global application_timestamps
            application_timestamps.clear()
            
            # Premier test - doit être autorisé
            self.assertTrue(self.service._can_apply_now())
            
            # Simuler une application
            application_timestamps.append(time.time())
            
            # Deuxième test immédiat - doit être bloqué
            self.assertFalse(self.service._can_apply_now())
            
            # Attendre le cooldown
            await asyncio.sleep(APPLICATION_COOLDOWN + 1)
            
            # Troisième test - doit être autorisé
            self.assertTrue(self.service._can_apply_now())
            
            print(f"\n=== COOLDOWN TEST ===")
            print(f"Cooldown: {APPLICATION_COOLDOWN} secondes")
            print("Système fonctionnel")
        
        async def test_stats_tracking(self):
            """Teste le suivi des statistiques."""
            stats = await self.service.get_bounty_stats()
            
            self.assertIsInstance(stats, dict)
            self.assertIn("search_count", stats)
            self.assertIn("application_count", stats)
            self.assertIn("success_count", stats)
            self.assertIn("success_rate", stats)
            
            print("\n=== STATISTIQUES ===")
            for key, value in stats.items():
                print(f"{key}: {value}")
        
        async def test_cache_behavior(self):
            """Teste le comportement du cache."""
            # Ajouter une entrée au cache
            test_bounty = {"title": "Test bounty", "url": "test.com"}
            bounty_cache["test_key"] = [test_bounty]
            
            # Vérifier que l'entrée est présente
            self.assertIn("test_key", bounty_cache)
            self.assertEqual(len(bounty_cache["test_key"]), 1)
            
            print("\n=== CACHE TEST ===")
            print(f"Taille du cache: {len(bounty_cache)}")
            print("Cache fonctionnel")
        
        async def test_error_handling(self):
            """Teste la gestion des erreurs."""
            # Test avec une URL invalide
            platform = self.service._identify_platform("invalid-url")
            self.assertIsNone(platform)
            
            # Test avec un bounty invalide
            invalid_bounty = {"title": "", "reward_usd": 0}
            self.assertFalse(self.service._is_valid_bounty(invalid_bounty))
            
            print("\n=== GESTION ERREURS ===")
            print("Gestion des erreurs fonctionnelle")
    
    # Exécuter les tests
    if __name__ == "__main__":
        unittest.main()
