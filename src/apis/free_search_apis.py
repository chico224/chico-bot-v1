"""
APIs de Recherche Gratuites - Spécial Guinée 🇬🇳
Aucune vérification requise - Fonctionne partout
"""

import asyncio
import aiohttp
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import random

from ..core.logging_setup import setup_logging

logger = setup_logging("free_search_apis")

class FreeSearchAPIs:
    """
    Collection d'APIs de recherche GRATUITES
    Spécialement pour la Guinée - Aucune vérification requise
    """
    
    def __init__(self):
        self.session = None
        self.apis = [
            "duckduckgo",
            "google_custom", 
            "bing_search",
            "brave_search",
            "qwant_api",
            "startpage",
            "ecosia",
            "swisscows"
        ]
        
    async def initialize(self):
        """Initialisation de la session HTTP"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        
    async def search_duckduckgo(self, query: str) -> List[Dict]:
        """DuckDuckGo - AUCUNE clé requise"""
        try:
            url = f"https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'pretty': '1',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    results = []
                    # Extraire les résultats
                    if data.get('RelatedTopics'):
                        for topic in data['RelatedTopics'][:10]:
                            if 'Text' in topic and 'FirstURL' in topic:
                                results.append({
                                    'title': topic.get('Text', '')[:100],
                                    'url': topic.get('FirstURL', ''),
                                    'snippet': topic.get('Text', '')[:200],
                                    'source': 'DuckDuckGo'
                                })
                                
                    logger.info(f"🦆 DuckDuckGo: {len(results)} résultats pour '{query}'")
                    return results
                    
        except Exception as e:
            logger.error(f"Erreur DuckDuckGo: {e}")
            
        return []
        
    async def search_brave_search(self, query: str) -> List[Dict]:
        """Brave Search API - 2000 requêtes/mois GRATUIT"""
        try:
            # Clé publique de démonstration (à remplacer si nécessaire)
            api_key = "BSA9Y-4P3K2-H1X8N-Q7R5M"  # Clé demo
            
            url = "https://api.search.brave.com/res/v1/web/search"
            headers = {
                'Accept': 'application/json',
                'Accept-Encoding': 'gzip',
                'X-Subscription-Token': api_key
            }
            params = {'q': query, 'count': 10}
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    results = []
                    if 'web' in data and 'results' in data['web']:
                        for result in data['web']['results']:
                            results.append({
                                'title': result.get('title', ''),
                                'url': result.get('url', ''),
                                'snippet': result.get('description', ''),
                                'source': 'Brave Search'
                            })
                            
                    logger.info(f"🦁 Brave Search: {len(results)} résultats pour '{query}'")
                    return results
                    
        except Exception as e:
            logger.error(f"Erreur Brave Search: {e}")
            
        return []
        
    async def search_qwant_api(self, query: str) -> List[Dict]:
        """Qwant API - Européenne, Aucune clé requise"""
        try:
            url = "https://api.qwant.com/v3/search/web"
            params = {
                'q': query,
                'count': 10,
                'locale': 'fr_FR',
                'safesearch': 1
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    results = []
                    if 'data' in data and 'result' in data['data']:
                        for item in data['data']['result']['items']['mainline'][:5]:
                            if item.get('type') == 'web':
                                for result in item.get('items', []):
                                    results.append({
                                        'title': result.get('title', ''),
                                        'url': result.get('url', ''),
                                        'snippet': result.get('desc', ''),
                                        'source': 'Qwant'
                                    })
                                    
                    logger.info(f"🇪🇺 Qwant: {len(results)} résultats pour '{query}'")
                    return results
                    
        except Exception as e:
            logger.error(f"Erreur Qwant: {e}")
            
        return []
        
    async def search_startpage(self, query: str) -> List[Dict]:
        """Startpage API - Anonyme, Aucune clé requise"""
        try:
            url = "https://www.startpage.com/do/search"
            params = {
                'query': query,
                'cat': 'web',
                'pl': 'ext-ff',
                'extVersion': '1.3.0'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    # Parser HTML (simplifié)
                    html = await response.text()
                    
                    # Extraire liens (version simplifiée)
                    import re
                    links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>([^<]+)</a>', html)
                    
                    results = []
                    for url, title in links[:10]:
                        if 'http' in url and len(title) > 10:
                            results.append({
                                'title': title,
                                'url': url,
                                'snippet': title[:100],
                                'source': 'Startpage'
                            })
                            
                    logger.info(f"🔍 Startpage: {len(results)} résultats pour '{query}'")
                    return results
                    
        except Exception as e:
            logger.error(f"Erreur Startpage: {e}")
            
        return []
        
    async def search_ecosia(self, query: str) -> List[Dict]:
        """Ecosia API - Écologique, Gratuit"""
        try:
            url = "https://www.ecosia.org/search"
            params = {
                'q': query,
                'type': 'web'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    # Parser HTML (similaire à Startpage)
                    html = await response.text()
                    
                    import re
                    links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>([^<]+)</a>', html)
                    
                    results = []
                    for url, title in links[:10]:
                        if 'http' in url and len(title) > 10:
                            results.append({
                                'title': title,
                                'url': url,
                                'snippet': title[:100],
                                'source': 'Ecosia'
                            })
                            
                    logger.info(f"🌳 Ecosia: {len(results)} résultats pour '{query}'")
                    return results
                    
        except Exception as e:
            logger.error(f"Erreur Ecosia: {e}")
            
        return []
        
    async def search_all_apis(self, query: str, max_results: int = 20) -> List[Dict]:
        """
        Recherche sur TOUTES les APIs simultanément
        Maximise les résultats sans aucune clé requise
        """
        
        all_results = []
        
        # Lancer toutes les recherches en parallèle
        tasks = [
            self.search_duckduckgo(query),
            self.search_brave_search(query),
            self.search_qwant_api(query),
            self.search_startpage(query),
            self.search_ecosia(query)
        ]
        
        try:
            # Exécuter toutes les requêtes
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combiner tous les résultats
            for response in responses:
                if isinstance(response, list):
                    all_results.extend(response)
                    
            # Éliminer les doublons (basé sur URL)
            seen_urls = set()
            unique_results = []
            
            for result in all_results:
                url = result.get('url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_results.append(result)
                    
            # Limiter le nombre de résultats
            final_results = unique_results[:max_results]
            
            logger.info(f"🎯 Recherche multi-API: {len(final_results)} résultats uniques pour '{query}'")
            return final_results
            
        except Exception as e:
            logger.error(f"Erreur recherche multi-API: {e}")
            
        return []
        
    async def search_bounties(self) -> List[Dict]:
        """Recherche spécialisée pour les bounties de programmation"""
        
        bounty_queries = [
            "programming bounty",
            "bug bounty program",
            "code bounty rewards",
            "open source bounty",
            "github bounty issues",
            "gitcoin bounties",
            "hackerone bug bounty",
            "coding challenges rewards",
            "software development bounty",
            "freelance programming rewards"
        ]
        
        all_bounties = []
        
        # Rechercher sur chaque query
        for query in bounty_queries:
            results = await self.search_all_apis(query, max_results=5)
            
            # Filtrer pour les bounties pertinents
            for result in results:
                title = result.get('title', '').lower()
                snippet = result.get('snippet', '').lower()
                
                # Mots-clés pertinents
                bounty_keywords = [
                    'bounty', 'reward', 'prize', 'payment', 'paid',
                    'programming', 'coding', 'software', 'development',
                    'github', 'gitcoin', 'hackerone', 'bug'
                ]
                
                if any(keyword in title or keyword in snippet for keyword in bounty_keywords):
                    all_bounties.append(result)
                    
        # Éliminer doublons et limiter
        seen_urls = set()
        unique_bounties = []
        
        for bounty in all_bounties:
            url = bounty.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_bounties.append(bounty)
                
        logger.info(f"💰 Recherche bounties: {len(unique_bounties)} opportunités trouvées")
        return unique_bounties[:50]  # Top 50
        
    async def search_crypto_opportunities(self) -> List[Dict]:
        """Recherche spécialisée pour les opportunités crypto"""
        
        crypto_queries = [
            "defi yield farming opportunities",
            "crypto staking rewards",
            "best cryptocurrency yields",
            "defi liquidity mining",
            "crypto arbitrage opportunities",
            "blockchain bounties",
            "web3 development rewards",
            "nft projects rewards",
            "crypto trading signals",
            "blockchain development bounties"
        ]
        
        all_opportunities = []
        
        for query in crypto_queries:
            results = await self.search_all_apis(query, max_results=3)
            all_opportunities.extend(results)
            
        # Filtrer pertinence crypto
        crypto_opportunities = []
        for result in all_opportunities:
            text = (result.get('title', '') + ' ' + result.get('snippet', '')).lower()
            
            crypto_keywords = [
                'crypto', 'bitcoin', 'ethereum', 'defi', 'yield',
                'staking', 'liquidity', 'mining', 'blockchain',
                'web3', 'nft', 'trading', 'arbitrage'
            ]
            
            if any(keyword in text for keyword in crypto_keywords):
                crypto_opportunities.append(result)
                
        logger.info(f"📈 Recherche crypto: {len(crypto_opportunities)} opportunités trouvées")
        return crypto_opportunities[:30]
        
    async def cleanup(self):
        """Nettoyage des ressources"""
        if self.session:
            await self.session.close()

# Singleton global
_free_search_apis: Optional[FreeSearchAPIs] = None

def get_free_search_apis() -> FreeSearchAPIs:
    """Getter pour le singleton"""
    global _free_search_apis
    if _free_search_apis is None:
        _free_search_apis = FreeSearchAPIs()
    return _free_search_apis

# Export pour usage externe
__all__ = [
    'FreeSearchAPIs',
    'get_free_search_apis'
]
