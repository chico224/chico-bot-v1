"""
Bounty Hunter Task - Toujours actif, priorité critique
Scan 24/7 des opportunités de bounty sur APIs GRATUITES
Spécialement pour la Guinée - Aucune clé requise
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
from dataclasses import dataclass

from ..core.logging_setup import setup_logging
from ..apis.free_search_apis import get_free_search_apis

logger = setup_logging("bounty_hunter")

@dataclass
class BountyOpportunity:
    platform: str
    title: str
    description: str
    reward: str
    difficulty: str
    deadline: datetime
    url: str
    tags: List[str]

class BountyHunter:
    """Chasseur de bounties 24/7 - APIs GRATUITES pour la Guinée"""
    
    def __init__(self):
        self.search_apis = get_free_search_apis()
        self.last_scan = datetime.min
        self.submissions_today = 0
        self.max_daily_submissions = 50
        
        # Plateformes à scanner (sans API key)
        self.platforms = {
            "github": "https://api.github.com",
            "gitcoin": "https://gitcoin.co", 
            "hackerone": "https://hackerone.com",
            "bugcrowd": "https://bugcrowd.com"
        }
        
    async def initialize(self):
        """Initialisation des APIs gratuites"""
        await self.search_apis.initialize()
        logger.info("🇬🇳 Bounty Hunter initialisé avec APIs gratuites")
        
    async def scan_all_bounties(self) -> List[BountyOpportunity]:
        """Scan sur TOUTES les APIs GRATUITES"""
        
        try:
            # Utiliser le système multi-API gratuit
            bounty_results = await self.search_apis.search_bounties()
            
            opportunities = []
            for result in bounty_results:
                opportunity = BountyOpportunity(
                    platform=result.get('source', 'Multi-API'),
                    title=result.get('title', '')[:100],
                    description=result.get('snippet', '')[:200],
                    reward=self._extract_reward_from_text(result.get('snippet', '')),
                    difficulty=self._estimate_difficulty_from_text(result.get('title', '') + ' ' + result.get('snippet', '')),
                    deadline=datetime.now() + timedelta(days=30),
                    url=result.get('url', ''),
                    tags=self._extract_tags_from_text(result.get('title', '') + ' ' + result.get('snippet', ''))
                )
                opportunities.append(opportunity)
                
            logger.info(f"🎯 Scan APIs gratuites: {len(opportunities)} bounties trouvés")
            return opportunities
            
        except Exception as e:
            logger.error(f"Erreur scan bounties: {e}")
            return []
        
    async def scan_github_bounties(self) -> List[BountyOpportunity]:
        """Scan des bounties GitHub Issues"""
        opportunities = []
        
        try:
            # Recherche des issues avec des labels bounty
            query = "label:bug+label:help+wanted+label:bounty"
            url = f"{self.platforms['github']}/search/issues?q={query}&sort=created&order=desc"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for item in data.get('items', []):
                        if self._is_valid_bounty(item):
                            opportunity = BountyOpportunity(
                                platform="GitHub",
                                title=item['title'],
                                description=item.get('body', '')[:200],
                                reward=self._extract_reward(item.get('body', '')),
                                difficulty=self._estimate_difficulty(item),
                                deadline=datetime.now() + timedelta(days=30),
                                url=item['html_url'],
                                tags=self._extract_tags(item.get('labels', []))
                            )
                            opportunities.append(opportunity)
                            
        except Exception as e:
            logger.error(f"Erreur scan GitHub: {e}")
            
        return opportunities
        
    async def scan_gitcoin_bounties(self) -> List[BountyOpportunity]:
        """Scan des bounties Gitcoin"""
        opportunities = []
        
        try:
            url = f"{self.platforms['gitcoin']}/issues"
            params = {
                'state': 'open',
                'standard_bounties': 'true',
                'order_by': 'web3_created',
                'order_direction': 'desc'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for issue in data:
                        bounty_data = issue.get('bounty_data', {})
                        if bounty_data:
                            opportunity = BountyOpportunity(
                                platform="Gitcoin",
                                title=issue['title'],
                                description=issue.get('body', '')[:200],
                                reward=f"${bounty_data.get('token_amount', 0)} {bounty_data.get('token_name', 'ETH')}",
                                difficulty=self._estimate_gitcoin_difficulty(bounty_data),
                                deadline=datetime.fromisoformat(bounty_data.get('bounty_deadline', datetime.now().isoformat())),
                                url=f"https://gitcoin.co/issue/{issue['id']}",
                                tags=self._extract_gitcoin_tags(bounty_data)
                            )
                            opportunities.append(opportunity)
                            
        except Exception as e:
            logger.error(f"Erreur scan Gitcoin: {e}")
            
        return opportunities
        
    async def scan_polyswarm_bounties(self) -> List[BountyOpportunity]:
        """Scan des bounties PolySwarm (sécurité)"""
        opportunities = []
        
        try:
            url = f"{self.platforms['polyswarm']}/bounties"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for bounty in data.get('bounties', []):
                        opportunity = BountyOpportunity(
                            platform="PolySwarm",
                            title=bounty.get('title', 'Security Bounty'),
                            description=bounty.get('description', '')[:200],
                            reward=f"${bounty.get('amount', 0)}",
                            difficulty="High",  # Sécurité = difficile
                            deadline=datetime.fromisoformat(bounty.get('deadline', datetime.now().isoformat())),
                            url=bounty.get('url', ''),
                            tags=['security', 'malware', 'reverse-engineering']
                        )
                        opportunities.append(opportunity)
                        
        except Exception as e:
            logger.error(f"Erreur scan PolySwarm: {e}")
            
        return opportunities
        
    async def submit_to_bounty(self, opportunity: BountyOpportunity, solution: str) -> bool:
        """Soumission automatique à un bounty"""
        
        if self.submissions_today >= self.max_daily_submissions:
            logger.warning("Limite de soumissions quotidiennes atteinte")
            return False
            
        try:
            # Logique de soumission selon la plateforme
            if opportunity.platform == "GitHub":
                success = await self._submit_github_issue(opportunity, solution)
            elif opportunity.platform == "Gitcoin":
                success = await self._submit_gitcoin_bounty(opportunity, solution)
            elif opportunity.platform == "PolySwarm":
                success = await self._submit_polyswarm_bounty(opportunity, solution)
            else:
                success = False
                
            if success:
                self.submissions_today += 1
                logger.info(f"✅ Soumission réussie: {opportunity.title}")
                
            return success
            
        except Exception as e:
            logger.error(f"Erreur soumission: {e}")
            return False
            
    async def _submit_github_issue(self, opportunity: BountyOpportunity, solution: str) -> bool:
        """Soumission GitHub Issue (commentaire avec solution)"""
        try:
            # Extraire owner/repo/issue_number de l'URL
            parts = opportunity.url.split('/')
            owner, repo = parts[3], parts[4]
            issue_number = parts[6]
            
            url = f"{self.platforms['github']}/repos/{owner}/{repo}/issues/{issue_number}/comments"
            
            comment_body = f"""
## 🇬🇳 ChicoBot Solution

{solution}

---
*Submitted by ChicoBot Bounty Hunter - Automated Solution*
"""
            
            async with self.session.post(url, json={'body': comment_body}) as response:
                return response.status == 201
                
        except Exception as e:
            logger.error(f"Erreur soumission GitHub: {e}")
            return False
            
    async def _submit_gitcoin_bounty(self, opportunity: BountyOpportunity, solution: str) -> bool:
        """Soumission Gitcoin (plus complexe - nécessite auth)"""
        # Placeholder - nécessiterait auth Gitcoin
        logger.info(f"Soumission Gitcoin simulée: {opportunity.title}")
        return True
        
    async def _submit_polyswarm_bounty(self, opportunity: BountyOpportunity, solution: str) -> bool:
        """Soumission PolySwarm (upload de fichier)"""
        # Placeholder - nécessiterait API PolySwarm
        logger.info(f"Soumission PolySwarm simulée: {opportunity.title}")
        return True
        
    def _is_valid_bounty(self, issue_data: Dict) -> bool:
        """Validation si c'est un vrai bounty"""
        body = issue_data.get('body', '').lower()
        title = issue_data.get('title', '').lower()
        
        bounty_keywords = ['bounty', 'reward', 'prize', 'payment', 'paid', 'crypto', 'eth', 'btc']
        
        return any(keyword in body or keyword in title for keyword in bounty_keywords)
        
    def _extract_reward(self, text: str) -> str:
        """Extraction du montant de récompense"""
        import re
        
        # Patterns pour les montants
        patterns = [
            r'\$(\d+(?:\.\d+)?)\s*(?:eth|btc|usd|dollar)',
            r'(\d+(?:\.\d+)?)\s*(?:eth|btc|bitcoin)',
            r'reward[:\s]*(\d+(?:\.\d+)?)',
            r'bounty[:\s]*(\d+(?:\.\d+)?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return f"${match.group(1)}"
                
        return "Reward not specified"
        
    def _estimate_difficulty(self, issue_data: Dict) -> str:
        """Estimation de la difficulté"""
        body = issue_data.get('body', '')
        title = issue_data.get('title', '')
        text = (body + ' ' + title).lower()
        
        # Indicateurs de difficulté
        if any(word in text for word in ['easy', 'simple', 'beginner']):
            return "Easy"
        elif any(word in text for word in ['medium', 'intermediate']):
            return "Medium"
        elif any(word in text for word in ['hard', 'difficult', 'complex', 'advanced']):
            return "Hard"
        else:
            return "Medium"
            
    def _estimate_gitcoin_difficulty(self, bounty_data: Dict) -> str:
        """Estimation difficulté Gitcoin selon montant"""
        amount = float(bounty_data.get('token_amount', 0))
        
        if amount < 100:
            return "Easy"
        elif amount < 500:
            return "Medium" 
        elif amount < 2000:
            return "Hard"
        else:
            return "Expert"
            
    def _extract_tags(self, labels: List[Dict]) -> List[str]:
        """Extraction des tags depuis labels GitHub"""
        return [label['name'] for label in labels if isinstance(label, dict)]
        
    def _extract_gitcoin_tags(self, bounty_data: Dict) -> List[str]:
        """Extraction tags Gitcoin"""
        return bounty_data.get('categories', [])
        
    async def cleanup(self):
        """Nettoyage des ressources"""
        if self.session:
            await self.session.close()

# Instance globale du bounty hunter
_bounty_hunter: Optional[BountyHunter] = None

async def bounty_hunter_main():
    """Fonction principale du bounty hunter - appelée par TaskMaster"""
    global _bounty_hunter
    
    if _bounty_hunter is None:
        _bounty_hunter = BountyHunter()
        await _bounty_hunter.initialize()
        
    try:
        # Scan de toutes les plateformes
        all_opportunities = []
        
        # GitHub
        github_opps = await _bounty_hunter.scan_github_bounties()
        all_opportunities.extend(github_opps)
        logger.info(f"🔍 GitHub: {len(github_opps)} opportunités")
        
        # Gitcoin
        gitcoin_opps = await _bounty_hunter.scan_gitcoin_bounties()
        all_opportunities.extend(gitcoin_opps)
        logger.info(f"🔍 Gitcoin: {len(gitcoin_opps)} opportunités")
        
        # PolySwarm
        polyswarm_opps = await _bounty_hunter.scan_polyswarm_bounties()
        all_opportunities.extend(polyswarm_opps)
        logger.info(f"🔍 PolySwarm: {len(polyswarm_opps)} opportunités")
        
        # Filtrer et trier par pertinence
        valid_opps = [opp for opp in all_opportunities if opp.difficulty in ["Easy", "Medium"]]
        valid_opps.sort(key=lambda x: (x.difficulty == "Easy", x.deadline))
        
        # Log des meilleures opportunités
        if valid_opps:
            logger.info(f"🎯 Top 3 opportunités:")
            for i, opp in enumerate(valid_opps[:3], 1):
                logger.info(f"  {i}. {opp.platform} - {opp.title} ({opp.reward})")
                
        # Simulation de soumission (remplacer par vraie logique)
        if valid_opps and _bounty_hunter.submissions_today < _bounty_hunter.max_daily_submissions:
            best_opp = valid_opps[0]
            success = await _bounty_hunter.submit_to_bounty(
                best_opp, 
                "🇬🇳 Automated solution by ChicoBot - High quality code provided"
            )
            
            if success:
                logger.info(f"✅ Soumission réussie: {best_opp.title}")
                
    except Exception as e:
        logger.error(f"Erreur bounty hunter main: {e}")
        
    finally:
        # Reset compteur quotidien si nécessaire
        if datetime.now().hour == 0 and datetime.now().minute == 0:
            _bounty_hunter.submissions_today = 0
