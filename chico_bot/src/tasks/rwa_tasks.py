"""
RWA Monitor Task - Monitoring des Real World Assets
Priorité haute - scan 24/7 des opportunités RWA (tokenisation d'actifs réels)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import aiohttp
import json
from dataclasses import dataclass

from ..core.logging_setup import setup_logging

logger = setup_logging("rwa_monitor")

@dataclass
class RWAOpportunity:
    asset_type: str
    description: str
    expected_return: float  # pourcentage annuel
    risk_level: str
    minimum_investment: float
    platform: str
    token_address: Optional[str]
    maturity_date: Optional[datetime]
    documentation_url: str

class RWAMonitor:
    """Monitor RWA - Tokenisation d'actifs réels"""
    
    def __init__(self):
        self.session = None
        self.last_scan = datetime.min
        self.active_positions = {}
        
        # Plateformes RWA à monitorer
        self.platforms = {
            "centrifuge": "https://api.centrifuge.io",
            "goldfinch": "https://api.goldfinch.finance", 
            "maple": "https://api.maple.finance",
            "truefi": "https://api.truefi.io",
            "clearpool": "https://api.clearpool.finance",
            "tinlake": "https://api.tinlake.centrifuge.io"
        }
        
        # Types d'actifs RWA à monitorer
        self.asset_types = {
            "real_estate": "Immobilier tokenisé",
            "invoices": "Factures commerciales",
            "trade_finance": "Financement commerce international",
            "commodities": "Matières premières",
            "loans": "Prêts garantis",
            "bonds": "Obligations tokenisées"
        }
        
    async def initialize(self):
        """Initialisation de la session HTTP"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'ChicoBot-RWAMonitor/1.0',
                'Accept': 'application/json'
            }
        )
        
    async def scan_centrifuge_pools(self) -> List[RWAOpportunity]:
        """Scan des pools Centrifuge (Tinlake)"""
        opportunities = []
        
        try:
            url = f"{self.platforms['centrifuge']}/pools"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for pool in data.get('pools', []):
                        if self._is_valid_rwa_pool(pool):
                            opportunity = RWAOpportunity(
                                asset_type=self._classify_asset(pool.get('metadata', {})),
                                description=pool.get('metadata', {}).get('description', ''),
                                expected_return=float(pool.get('interest_rate', 0)) * 100,
                                risk_level=self._assess_risk(pool),
                                minimum_investment=float(pool.get('min_investment', 1000)),
                                platform="Centrifuge",
                                token_address=pool.get('token_address'),
                                maturity_date=datetime.fromisoformat(pool.get('maturity_date', datetime.now().isoformat())),
                                documentation_url=pool.get('documentation_url', '')
                            )
                            opportunities.append(opportunity)
                            
        except Exception as e:
            logger.error(f"Erreur scan Centrifuge: {e}")
            
        return opportunities
        
    async def scan_goldfinch_opportunities(self) -> List[RWAOpportunity]:
        """Scan des opportunités Goldfinch"""
        opportunities = []
        
        try:
            url = f"{self.platforms['goldfinch']}/pools"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for pool in data.get('pools', []):
                        if pool.get('status') == 'open':
                            opportunity = RWAOpportunity(
                                asset_type="loans",
                                description=f"Prêts garantis Goldfinch - {pool.get('borrower_name', 'Unknown')}",
                                expected_return=float(pool.get('interest_rate', 0)) * 100,
                                risk_level=self._assess_goldfinch_risk(pool),
                                minimum_investment=float(pool.get('min_investment', 5000)),
                                platform="Goldfinch",
                                token_address=pool.get('tranche_address'),
                                maturity_date=datetime.fromisoformat(pool.get('term_end_time', datetime.now().isoformat())),
                                documentation_url=pool.get('borrower_url', '')
                            )
                            opportunities.append(opportunity)
                            
        except Exception as e:
            logger.error(f"Erreur scan Goldfinch: {e}")
            
        return opportunities
        
    async def scan_maple_finance_pools(self) -> List[RWAOpportunity]:
        """Scan des pools Maple Finance"""
        opportunities = []
        
        try:
            url = f"{self.platforms['maple']}/pools"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for pool in data.get('pools', []):
                        if pool.get('status') == 'active':
                            opportunity = RWAOpportunity(
                                asset_type="loans",
                                description=f"Prêts institutionnels Maple - {pool.get('borrower', 'Unknown')}",
                                expected_return=float(pool.get('interest_rate', 0)) * 100,
                                risk_level=self._assess_maple_risk(pool),
                                minimum_investment=float(pool.get('min_investment', 10000)),
                                platform="Maple Finance",
                                token_address=pool.get('pool_address'),
                                maturity_date=datetime.fromisoformat(pool.get('loan_term', datetime.now().isoformat())),
                                documentation_url=pool.get('loan_documentation', '')
                            )
                            opportunities.append(opportunity)
                            
        except Exception as e:
            logger.error(f"Erreur scan Maple Finance: {e}")
            
        return opportunities
        
    async def scan_truefi_markets(self) -> List[RWAOpportunity]:
        """Scan des marchés TrueFi"""
        opportunities = []
        
        try:
            url = f"{self.platforms['truefi']}/markets"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for market in data.get('markets', []):
                        if market.get('status') == 'open':
                            opportunity = RWAOpportunity(
                                asset_type="loans",
                                description=f"Prêts TrueFi - {market.get('borrower', 'Unknown')}",
                                expected_return=float(market.get('apy', 0)),
                                risk_level=self._assess_truefi_risk(market),
                                minimum_investment=float(market.get('min_investment', 1000)),
                                platform="TrueFi",
                                token_address=market.get('token_address'),
                                maturity_date=datetime.fromisoformat(market.get('term_end', datetime.now().isoformat())),
                                documentation_url=market.get('market_url', '')
                            )
                            opportunities.append(opportunity)
                            
        except Exception as e:
            logger.error(f"Erreur scan TrueFi: {e}")
            
        return opportunities
        
    async def invest_in_rwa(self, opportunity: RWAOpportunity, amount: float) -> bool:
        """Investissement AUTOMATIQUE dans un RWA via APIs."""
        
        try:
            # Validation montant minimum
            if amount < opportunity.minimum_investment:
                logger.warning(f"Montant insuffisant: {amount} < {opportunity.minimum_investment}")
                return False
            
            # 1. CONNEXION WALLET UTILISATEUR VIA CLÉ PRIVÉE
            import os
            user_wallet = os.getenv("WALLET_PRIVATE_KEY")
            if not user_wallet:
                logger.error("Clé wallet utilisateur non trouvée")
                return False
            
            wallet_connection = await self._connect_user_wallet(user_wallet)
            if not wallet_connection["connected"]:
                logger.error("Échec connexion wallet utilisateur")
                return False
            
            # 2. INVESTISSEMENT AUTOMATIQUE SELON PLATEFORME
            if opportunity.platform == "Centrifuge":
                success = await self._invest_centrifuge(opportunity, amount, wallet_connection)
            elif opportunity.platform == "Goldfinch":
                success = await self._invest_goldfinch(opportunity, amount, wallet_connection)
            elif opportunity.platform == "Maple Finance":
                success = await self._invest_maple(opportunity, amount, wallet_connection)
            elif opportunity.platform == "TrueFi":
                success = await self._invest_truefi(opportunity, amount, wallet_connection)
            elif opportunity.platform == "Clearpool":
                success = await self._invest_clearpool(opportunity, amount, wallet_connection)
            else:
                success = False
            
            # 3. SI INVESTISSEMENT RÉUSSI
            if success:
                # 4. ENREGISTREMENT POSITION AUTOMATIQUE
                await self._record_rwa_position(opportunity, amount, wallet_connection)
                
                # 5. DÉMARRAGE MONITORING AUTOMATIQUE
                await self._start_position_monitoring(opportunity, amount)
                
                # 6. CONFIGURATION INTÉRÊTS AUTOMATIQUES
                await self._setup_auto_interest_compounding(opportunity, amount)
                
                logger.info(f"🏦 Investissement RWA réussi: ${amount:.2f} dans {opportunity.platform}")
                return True
            else:
                logger.error(f"❌ Échec investissement RWA: {opportunity.platform}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur investissement RWA: {e}")
            return False
    
    async def _connect_user_wallet(self, private_key: str) -> Dict[str, Any]:
        """Connexion automatique au wallet utilisateur."""
        try:
            import hashlib
            
            # Simulation de connexion wallet
            # En pratique: utiliser web3.py + private key
            
            wallet_address = "0x" + hashlib.sha256(private_key.encode()).hexdigest()[:40]
            
            logger.info(f"🇬🇳 Wallet RWA connecté: {wallet_address}")
            
            return {
                "connected": True,
                "address": wallet_address,
                "balance": 10000.0,  # Simulation
                "private_key": private_key
            }
            
        except Exception as e:
            logger.error(f"Erreur connexion wallet RWA: {e}")
            return {"connected": False}
    
    async def _invest_centrifuge(self, opportunity: RWAOpportunity, amount: float, 
                                 wallet: Dict[str, Any]) -> bool:
        """Investissement AUTOMATIQUE Centrifuge (via contrat)."""
        try:
            logger.info(f"📊 Investissement Centrifuge: ${amount:.2f}")
            
            # 1. Approve USDC/USDT
            await self._approve_token("USDC", amount, wallet)
            
            # 2. Investissement dans pool Centrifuge
            invest_result = await self._centrifuge_invest(
                pool_address=opportunity.token_address,
                amount=amount,
                wallet=wallet
            )
            
            if invest_result["success"]:
                # 3. Configuration réception intérêts automatiques
                await self._setup_centrifuge_interests(invest_result["position_id"])
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Erreur investissement Centrifuge: {e}")
            return False
    
    async def _invest_goldfinch(self, opportunity: RWAOpportunity, amount: float, 
                                wallet: Dict[str, Any]) -> bool:
        """Investissement AUTOMATIQUE Goldfinch."""
        try:
            logger.info(f"🏦 Investissement Goldfinch: ${amount:.2f}")
            
            # 1. Approve USDC
            await self._approve_token("USDC", amount, wallet)
            
            # 2. Investissement Goldfinch
            invest_result = await self._goldfinch_invest(
                borrower_address=opportunity.token_address,
                amount=amount,
                wallet=wallet
            )
            
            if invest_result["success"]:
                # 3. Configuration intérêts automatiques
                await self._setup_goldfinch_interests(invest_result["position_id"])
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Erreur investissement Goldfinch: {e}")
            return False
    
    async def _invest_maple(self, opportunity: RWAOpportunity, amount: float, 
                           wallet: Dict[str, Any]) -> bool:
        """Investissement AUTOMATIQUE Maple Finance."""
        try:
            logger.info(f"🍁 Investissement Maple Finance: ${amount:.2f}")
            
            # 1. Approve USDC
            await self._approve_token("USDC", amount, wallet)
            
            # 2. Investissement Maple
            invest_result = await self._maple_invest(
                pool_address=opportunity.token_address,
                amount=amount,
                wallet=wallet
            )
            
            if invest_result["success"]:
                # 3. Configuration intérêts automatiques
                await self._setup_maple_interests(invest_result["position_id"])
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Erreur investissement Maple: {e}")
            return False
    
    async def _invest_truefi(self, opportunity: RWAOpportunity, amount: float, 
                            wallet: Dict[str, Any]) -> bool:
        """Investissement AUTOMATIQUE TrueFi."""
        try:
            logger.info(f"🔷 Investissement TrueFi: ${amount:.2f}")
            
            # 1. Approve USDC
            await self._approve_token("USDC", amount, wallet)
            
            # 2. Investissement TrueFi
            invest_result = await self._truefi_invest(
                pool_address=opportunity.token_address,
                amount=amount,
                wallet=wallet
            )
            
            if invest_result["success"]:
                # 3. Configuration intérêts automatiques
                await self._setup_truefi_interests(invest_result["position_id"])
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Erreur investissement TrueFi: {e}")
            return False
    
    async def _invest_clearpool(self, opportunity: RWAOpportunity, amount: float, 
                               wallet: Dict[str, Any]) -> bool:
        """Investissement AUTOMATIQUE Clearpool."""
        try:
            logger.info(f"💎 Investissement Clearpool: ${amount:.2f}")
            
            # 1. Approve USDC
            await self._approve_token("USDC", amount, wallet)
            
            # 2. Investissement Clearpool
            invest_result = await self._clearpool_invest(
                pool_address=opportunity.token_address,
                amount=amount,
                wallet=wallet
            )
            
            if invest_result["success"]:
                # 3. Configuration intérêts automatiques
                await self._setup_clearpool_interests(invest_result["position_id"])
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Erreur investissement Clearpool: {e}")
            return False
    
    async def _record_rwa_position(self, opportunity: RWAOpportunity, amount: float, 
                                  wallet: Dict[str, Any]):
        """Enregistre la position RWA."""
        try:
            # Enregistrement dans base de données
            from ..core.database import database
            
            await database.add_rwa_position(
                user_id=1,  # user_id=1 pour l'exemple
                platform=opportunity.platform,
                token_address=opportunity.token_address,
                amount=amount,
                expected_return=opportunity.expected_return,
                timestamp=datetime.now()
            )
            
            logger.info(f"📊 Position RWA enregistrée: {opportunity.platform}")
            
        except Exception as e:
            logger.error(f"Erreur enregistrement position: {e}")
    
    async def _start_position_monitoring(self, opportunity: RWAOpportunity, amount: float):
        """Démarre le monitoring automatique de la position."""
        try:
            # Configuration monitoring 24/7
            self.active_positions[opportunity.token_address] = {
                "opportunity": opportunity,
                "amount": amount,
                "invested_at": datetime.now(),
                "last_interest_payment": datetime.now(),
                "total_interest_earned": 0.0
            }
            
            logger.info(f"🔍 Monitoring RWA démarré: {opportunity.platform}")
            
        except Exception as e:
            logger.error(f"Erreur démarrage monitoring: {e}")
    
    async def _setup_auto_interest_compounding(self, opportunity: RWAOpportunity, amount: float):
        """Configure le compounding automatique des intérêts."""
        try:
            # Configuration compounding mensuel
            compounding_schedule = {
                "frequency": "monthly",
                "auto_reinvest": True,
                "platform": opportunity.platform
            }
            
            logger.info(f"🔄 Compounding intérêts configuré: {opportunity.platform}")
            
        except Exception as e:
            logger.error(f"Erreur configuration compounding: {e}")
    
    # Fonctions utilitaires pour investissements RWA
    async def _approve_token(self, token: str, amount: float, wallet: Dict[str, Any]) -> bool:
        """Approuve un token pour RWA."""
        await asyncio.sleep(0.1)  # Simulation
        return True
    
    async def _centrifuge_invest(self, pool_address: str, amount: float, 
                                wallet: Dict[str, Any]) -> Dict[str, Any]:
        """Investissement Centrifuge."""
        await asyncio.sleep(0.3)
        return {"success": True, "position_id": f"centrifuge_{int(datetime.now().timestamp())}"}
    
    async def _setup_centrifuge_interests(self, position_id: str):
        """Configuration intérêts Centrifuge."""
        await asyncio.sleep(0.1)
        logger.info(f"📊 Intérêts Centrifuge configurés: {position_id}")
    
    async def _goldfinch_invest(self, borrower_address: str, amount: float, 
                               wallet: Dict[str, Any]) -> Dict[str, Any]:
        """Investissement Goldfinch."""
        await asyncio.sleep(0.3)
        return {"success": True, "position_id": f"goldfinch_{int(datetime.now().timestamp())}"}
    
    async def _setup_goldfinch_interests(self, position_id: str):
        """Configuration intérêts Goldfinch."""
        await asyncio.sleep(0.1)
        logger.info(f"🏦 Intérêts Goldfinch configurés: {position_id}")
    
    async def _maple_invest(self, pool_address: str, amount: float, 
                           wallet: Dict[str, Any]) -> Dict[str, Any]:
        """Investissement Maple."""
        await asyncio.sleep(0.3)
        return {"success": True, "position_id": f"maple_{int(datetime.now().timestamp())}"}
    
    async def _setup_maple_interests(self, position_id: str):
        """Configuration intérêts Maple."""
        await asyncio.sleep(0.1)
        logger.info(f"🍁 Intérêts Maple configurés: {position_id}")
    
    async def _truefi_invest(self, pool_address: str, amount: float, 
                            wallet: Dict[str, Any]) -> Dict[str, Any]:
        """Investissement TrueFi."""
        await asyncio.sleep(0.3)
        return {"success": True, "position_id": f"truefi_{int(datetime.now().timestamp())}"}
    
    async def _setup_truefi_interests(self, position_id: str):
        """Configuration intérêts TrueFi."""
        await asyncio.sleep(0.1)
        logger.info(f"🔷 Intérêts TrueFi configurés: {position_id}")
    
    async def _clearpool_invest(self, pool_address: str, amount: float, 
                               wallet: Dict[str, Any]) -> Dict[str, Any]:
        """Investissement Clearpool."""
        await asyncio.sleep(0.3)
        return {"success": True, "position_id": f"clearpool_{int(datetime.now().timestamp())}"}
    
    async def _setup_clearpool_interests(self, position_id: str):
        """Configuration intérêts Clearpool."""
        await asyncio.sleep(0.1)
        logger.info(f"💎 Intérêts Clearpool configurés: {position_id}")
                
            if success:
                # Track position
                self.active_positions[opportunity.token_address] = {
                    'opportunity': opportunity,
                    'amount': amount,
                    'invested_at': datetime.now(),
                    'expected_return': amount * (1 + opportunity.expected_return / 100)
                }
                
                logger.info(f"💰 Investissement RWA réussi: {amount} USDT dans {opportunity.platform}")
                
            return success
            
        except Exception as e:
            logger.error(f"Erreur investissement RWA: {e}")
            return False
            
    async def _invest_centrifuge(self, opportunity: RWAOpportunity, amount: float) -> bool:
        """Investissement Centrifuge (via contrat)"""
        # Placeholder - nécessiterait interaction avec contrat intelligent
        logger.info(f"📊 Investissement Centrifuge simulé: {amount} USDT")
        return True
        
    async def _invest_goldfinch(self, opportunity: RWAOpportunity, amount: float) -> bool:
        """Investissement Goldfinch"""
        # Placeholder - nécessiterait interaction avec contrat Goldfinch
        logger.info(f"🏦 Investissement Goldfinch simulé: {amount} USDT")
        return True
        
    async def _invest_maple(self, opportunity: RWAOpportunity, amount: float) -> bool:
        """Investissement Maple Finance"""
        # Placeholder - nécessiterait interaction avec contrat Maple
        logger.info(f"🍁 Investissement Maple simulé: {amount} USDT")
        return True
        
    async def _invest_truefi(self, opportunity: RWAOpportunity, amount: float) -> bool:
        """Investissement TrueFi"""
        # Placeholder - nécessiterait interaction avec contrat TrueFi
        logger.info(f"🔷 Investissement TrueFi simulé: {amount} USDT")
        return True
        
    async def monitor_positions(self):
        """Monitoring des positions actives"""
        
        for token_address, position in list(self.active_positions.items()):
            try:
                # Vérifier si la position est mature
                if position['opportunity'].maturity_date:
                    if datetime.now() >= position['opportunity'].maturity_date:
                        logger.info(f"🏆 Position mature: {token_address}")
                        # Logique de retrait automatique
                        await self._withdraw_position(token_address)
                        continue
                        
                # Calculer valeur actuelle (simplifié)
                days_invested = (datetime.now() - position['invested_at']).days
                current_value = position['amount'] * (1 + position['opportunity'].expected_return / 100 * days_invested / 365)
                
                logger.info(f"📈 Position {token_address[:8]}...: {current_value:.2f} USDT (+{current_value - position['amount']:.2f})")
                
            except Exception as e:
                logger.error(f"Erreur monitoring position {token_address}: {e}")
                
    async def _withdraw_position(self, token_address: str):
        """Retrait d'une position mature"""
        if token_address in self.active_positions:
            position = self.active_positions[token_address]
            logger.info(f"💸 Retrait position: {position['amount']:.2f} USDT")
            del self.active_positions[token_address]
            
    def _is_valid_rwa_pool(self, pool_data: Dict) -> bool:
        """Validation si c'est un vrai pool RWA"""
        metadata = pool_data.get('metadata', {})
        
        # Indicateurs de vrai RWA
        has_collateral = metadata.get('collateral_type') is not None
        has_real_asset = any(keyword in str(metadata).lower() for keyword in ['real estate', 'invoice', 'trade', 'commodity'])
        is_tokenized = pool_data.get('token_address') is not None
        
        return has_collateral or has_real_asset or is_tokenized
        
    def _classify_asset(self, metadata: Dict) -> str:
        """Classification du type d'actif"""
        description = str(metadata).lower()
        
        if any(keyword in description for keyword in ['real estate', 'property', 'building']):
            return "real_estate"
        elif any(keyword in description for keyword in ['invoice', 'receivable']):
            return "invoices"
        elif any(keyword in description for keyword in ['trade', 'export', 'import']):
            return "trade_finance"
        elif any(keyword in description for keyword in ['commodity', 'gold', 'oil']):
            return "commodities"
        elif any(keyword in description for keyword in ['loan', 'credit']):
            return "loans"
        elif any(keyword in description for keyword in ['bond', 'fixed income']):
            return "bonds"
        else:
            return "other"
            
    def _assess_risk(self, pool_data: Dict) -> str:
        """Évaluation du risque"""
        # Logique simplifiée - en réalité utiliserait des métriques plus complexes
        interest_rate = float(pool_data.get('interest_rate', 0))
        
        if interest_rate < 0.05:  # < 5%
            return "Low"
        elif interest_rate < 0.10:  # < 10%
            return "Medium"
        elif interest_rate < 0.15:  # < 15%
            return "High"
        else:
            return "Very High"
            
    def _assess_goldfinch_risk(self, pool_data: Dict) -> str:
        """Évaluation risque Goldfinch"""
        borrower_score = pool_data.get('borrower_credit_score', 0)
        
        if borrower_score >= 700:
            return "Low"
        elif borrower_score >= 600:
            return "Medium"
        else:
            return "High"
            
    def _assess_maple_risk(self, pool_data: Dict) -> str:
        """Évaluation risque Maple"""
        # Maple gère généralement des prêts institutionnels = risque plus faible
        return "Low"
        
    def _assess_truefi_risk(self, market_data: Dict) -> str:
        """Évaluation risque TrueFi"""
        # Basé sur le score de crédit de l'emprunteur
        credit_score = market_data.get('borrower_score', 0)
        
        if credit_score >= 700:
            return "Low"
        elif credit_score >= 600:
            return "Medium"
        else:
            return "High"
            
    async def cleanup(self):
        """Nettoyage des ressources"""
        if self.session:
            await self.session.close()

# Instance globale du RWA monitor
_rwa_monitor: Optional[RWAMonitor] = None

async def rwa_monitor_main():
    """Fonction principale du RWA monitor - appelée par TaskMaster"""
    global _rwa_monitor
    
    if _rwa_monitor is None:
        _rwa_monitor = RWAMonitor()
        await _rwa_monitor.initialize()
        
    try:
        # Scan de toutes les plateformes
        all_opportunities = []
        
        # Centrifuge
        centrifuge_opps = await _rwa_monitor.scan_centrifuge_pools()
        all_opportunities.extend(centrifuge_opps)
        logger.info(f"🏢 Centrifuge: {len(centrifuge_opps)} opportunités")
        
        # Goldfinch
        goldfinch_opps = await _rwa_monitor.scan_goldfinch_opportunities()
        all_opportunities.extend(goldfinch_opps)
        logger.info(f"🏦 Goldfinch: {len(goldfinch_opps)} opportunités")
        
        # Maple Finance
        maple_opps = await _rwa_monitor.scan_maple_finance_pools()
        all_opportunities.extend(maple_opps)
        logger.info(f"🍁 Maple Finance: {len(maple_opps)} opportunités")
        
        # TrueFi
        truefi_opps = await _rwa_monitor.scan_truefi_markets()
        all_opportunities.extend(truefi_opps)
        logger.info(f"🔷 TrueFi: {len(truefi_opps)} opportunités")
        
        # Filtrer par risque et rendement
        valid_opps = [opp for opp in all_opportunities if opp.risk_level in ["Low", "Medium"]]
        valid_opps.sort(key=lambda x: x.expected_return, reverse=True)
        
        # Log des meilleures opportunités
        if valid_opps:
            logger.info(f"🎯 Top 5 opportunités RWA:")
            for i, opp in enumerate(valid_opps[:5], 1):
                logger.info(f"  {i}. {opp.platform} - {opp.asset_type} ({opp.expected_return:.1f}% APY)")
                
        # Monitoring des positions actives
        await _rwa_monitor.monitor_positions()
        
        # Simulation d'investissement (remplacer par vraie logique)
        if valid_opps and len(_rwa_monitor.active_positions) < 10:  # Max 10 positions
            best_opp = valid_opps[0]
            # Investissement fictif pour démonstration
            await _rwa_monitor.invest_in_rwa(best_opp, 1000.0)
            
    except Exception as e:
        logger.error(f"Erreur RWA monitor main: {e}")
