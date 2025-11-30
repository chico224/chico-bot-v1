"""
Investment Engine Task - Investissements long terme
Priorité basse - exécution toutes les heures
Stratégies: DeFi staking, yield farming, long-term holds
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import aiohttp
import json
from dataclasses import dataclass
import statistics

from ..core.logging_setup import setup_logging

logger = setup_logging("investment_engine")

@dataclass
class InvestmentOpportunity:
    protocol: str
    strategy: str
    asset: str
    apy: float  # Annual Percentage Yield
    risk_level: str
    lock_period: timedelta  # Période de lock
    minimum_amount: float
    contract_address: str
    tvl: float  # Total Value Locked
    impermanent_loss_risk: float

@dataclass
class InvestmentPosition:
    opportunity: InvestmentOpportunity
    amount_invested: float
    current_value: float
    accrued_rewards: float
    start_date: datetime
    last_claim: datetime

class InvestmentEngine:
    """Engine d'investissement long terme - DeFi et yield farming"""
    
    def __init__(self):
        self.session = None
        self.positions = {}
        self.opportunities = []
        self.last_rebalance = datetime.min
        self.rebalance_interval = timedelta(days=7)  # Rebalance chaque semaine
        
        # Configuration investissement
        self.max_total_investment = 10000  # Max 10k USDT total
        self.max_per_protocol = 2000  # Max 2k par protocole
        self.min_apy_threshold = 5.0  # APY minimum 5%
        
        # Protocoles DeFi à monitorer
        self.protocols = {
            "aave": {
                "base_url": "https://api.aave.com",
                "pools": ["v2", "v3"],
                "strategies": ["lending", "liquidation"]
            },
            "compound": {
                "base_url": "https://api.compound.finance",
                "pools": ["v2", "v3"],
                "strategies": ["lending", "governance"]
            },
            "uniswap": {
                "base_url": "https://api.uniswap.org",
                "pools": ["v2", "v3"],
                "strategies": ["liquidity", "concentrated"]
            },
            "curve": {
                "base_url": "https://api.curve.fi",
                "pools": ["stable", "volatile"],
                "strategies": ["stable_pool", "crypto_pool"]
            },
            "lido": {
                "base_url": "https://api.lido.fi",
                "pools": ["steth"],
                "strategies": ["staking"]
            },
            "rocketpool": {
                "base_url": "https://api.rocketpool.net",
                "pools": ["reth"],
                "strategies": ["staking"]
            }
        }
        
        # Assets à considérer
        self.assets = {
            "stablecoins": ["USDT", "USDC", "DAI", "BUSD"],
            "major_cryptos": ["ETH", "BTC", "BNB"],
            "defi_tokens": ["AAVE", "COMP", "UNI", "CRV", "LDO", "RETH"]
        }
        
    async def initialize(self):
        """Initialisation de la session HTTP"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'ChicoBot-InvestmentEngine/1.0',
                'Accept': 'application/json'
            }
        )
        
    async def scan_aave_opportunities(self) -> List[InvestmentOpportunity]:
        """Scan des opportunités Aave (lending)"""
        opportunities = []
        
        try:
            # Aave V3
            url = f"{self.protocols['aave']['base_url']}/v3/data"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for pool_data in data.get('pools', []):
                        if pool_data.get('isActive', False):
                            # Taux d'intérêt actuel
                            supply_apy = float(pool_data.get('supplyAPY', 0)) * 100
                            
                            if supply_apy >= self.min_apy_threshold:
                                opportunity = InvestmentOpportunity(
                                    protocol="Aave",
                                    strategy="lending",
                                    asset=pool_data.get('symbol', 'USDT'),
                                    apy=supply_apy,
                                    risk_level="Low",
                                    lock_period=timedelta(0),  # No lock
                                    minimum_amount=float(pool_data.get('minAmount', 100)),
                                    contract_address=pool_data.get('aTokenAddress', ''),
                                    tvl=float(pool_data.get('totalLiquidity', 0)),
                                    impermanent_loss_risk=0.0  # Lending = no IL
                                )
                                opportunities.append(opportunity)
                                
        except Exception as e:
            logger.error(f"Erreur scan Aave: {e}")
            
        return opportunities
        
    async def scan_compound_opportunities(self) -> List[InvestmentOpportunity]:
        """Scan des opportunités Compound"""
        opportunities = []
        
        try:
            url = f"{self.protocols['compound']['base_url']}/ctoken"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for ctoken in data.get('cToken', []):
                        if ctoken.get('underlying_symbol') in self.assets['stablecoins']:
                            supply_rate = float(ctoken.get('supply_rate_per_block', 0))
                            
                            # Conversion en APY annuel (simplifié)
                            blocks_per_year = 2102400  # Ethereum blocks/year
                            apy = (supply_rate * blocks_per_year) * 100
                            
                            if apy >= self.min_apy_threshold:
                                opportunity = InvestmentOpportunity(
                                    protocol="Compound",
                                    strategy="lending",
                                    asset=ctoken.get('underlying_symbol', 'USDT'),
                                    apy=apy,
                                    risk_level="Low",
                                    lock_period=timedelta(0),
                                    minimum_amount=100.0,
                                    contract_address=ctoken.get('token_address', ''),
                                    tvl=float(ctoken.get('total_supply', 0)) * float(ctoken.get('exchange_rate', 1)),
                                    impermanent_loss_risk=0.0
                                )
                                opportunities.append(opportunity)
                                
        except Exception as e:
            logger.error(f"Erreur scan Compound: {e}")
            
        return opportunities
        
    async def scan_uniswap_opportunities(self) -> List[InvestmentOpportunity]:
        """Scan des opportunités Uniswap (liquidity providing)"""
        opportunities = []
        
        try:
            # Uniswap V3 API pour les pools
            url = f"{self.protocols['uniswap']['base_url']}/v3/pools"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for pool in data.get('pools', []):
                        # Filtrer les pools avec bon TVL et APY
                        tvl = float(pool.get('totalValueLockedUSD', 0))
                        
                        if tvl > 1000000:  # TVL > 1M
                            # Estimer APY basé sur fees
                            fee_tier = float(pool.get('feeTier', 3000)) / 10000  # 0.3% = 3000
                            volume_24h = float(pool.get('volumeUSD', 0))
                            
                            if volume_24h > 0:
                                fee_apy = (volume_24h * fee_tier * 365) / tvl * 100
                                
                                # Ajouter potentiel de rewards
                                total_apy = fee_apy + 2.0  # +2% rewards estimés
                                
                                if total_apy >= self.min_apy_threshold:
                                    token0 = pool.get('token0', {}).get('symbol', 'ETH')
                                    token1 = pool.get('token1', {}).get('symbol', 'USDT')
                                    
                                    # Calculer risque impermanent loss
                                    il_risk = self._calculate_il_risk(token0, token1)
                                    
                                    opportunity = InvestmentOpportunity(
                                        protocol="Uniswap",
                                        strategy="liquidity",
                                        asset=f"{token0}/{token1}",
                                        apy=total_apy,
                                        risk_level="Medium",
                                        lock_period=timedelta(0),
                                        minimum_amount=float(pool.get('liquidity', 100)),
                                        contract_address=pool.get('id', ''),
                                        tvl=tvl,
                                        impermanent_loss_risk=il_risk
                                    )
                                    opportunities.append(opportunity)
                                    
        except Exception as e:
            logger.error(f"Erreur scan Uniswap: {e}")
            
        return opportunities
        
    async def scan_curve_opportunities(self) -> List[InvestmentOpportunity]:
        """Scan des opportunités Curve (stable pools)"""
        opportunities = []
        
        try:
            url = f"{self.protocols['curve']['base_url']}/api/getPools"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for pool_data in data.get('poolData', []):
                        # Filtrer stable pools
                        if pool_data.get('isMeta', False) == False:  # Pas meta pools
                            apy = float(pool_data.get('apy', 0))
                            
                            if apy >= self.min_apy_threshold:
                                coins = pool_data.get('coins', [])
                                coin_symbols = [coin.get('symbol', '') for coin in coins]
                                
                                opportunity = InvestmentOpportunity(
                                    protocol="Curve",
                                    strategy="stable_pool",
                                    asset="+".join(coin_symbols[:3]),  # Max 3 coins
                                    apy=apy,
                                    risk_level="Low",
                                    lock_period=timedelta(0),
                                    minimum_amount=float(pool_data.get('baseApr', 100)),
                                    contract_address=pool_data.get('address', ''),
                                    tvl=float(pool_data.get('totalLiquidity', 0)),
                                    impermanent_loss_risk=0.1  # Stable pools = faible IL
                                )
                                opportunities.append(opportunity)
                                
        except Exception as e:
            logger.error(f"Erreur scan Curve: {e}")
            
        return opportunities
        
    async def scan_staking_opportunities(self) -> List[InvestmentOpportunity]:
        """Scan des opportunités de staking ETH"""
        opportunities = []
        
        try:
            # Lido stETH
            url = f"{self.protocols['lido']['base_url']}/v1/stats"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    steth_apy = float(data.get('yearlyApr', 0)) * 100
                    
                    if steth_apy >= self.min_apy_threshold:
                        opportunity = InvestmentOpportunity(
                            protocol="Lido",
                            strategy="staking",
                            asset="ETH",
                            apy=steth_apy,
                            risk_level="Medium",
                            lock_period=timedelta(days=7),  # 7 jours pour unstake
                            minimum_amount=float(data.get('stakeLimit', 0.1)),
                            contract_address="0xae7ab96520DEbA3Bcd8524C8945E2351e7b6C74B",  # Lido contract
                            tvl=float(data.get('totalPooledEther', 0)) * float(data.get('stEthPrice', 2000)),
                            impermanent_loss_risk=0.0  # Staking = no IL
                        )
                        opportunities.append(opportunity)
                        
            # Rocket Pool rETH
            url = f"{self.protocols['rocketpool']['base_url']}/v1/stats"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    reth_apy = float(data.get('apr', 0)) * 100
                    
                    if reth_apy >= self.min_apy_threshold:
                        opportunity = InvestmentOpportunity(
                            protocol="RocketPool",
                            strategy="staking",
                            asset="ETH",
                            apy=reth_apy,
                            risk_level="Medium",
                            lock_period=timedelta(days=14),  # 14 jours pour unstake
                            minimum_amount=0.01,  # Min 0.01 ETH
                            contract_address="0xae78736Cd615f374D3085123A210448E74Fc6393",  # rETH contract
                            tvl=float(data.get('totalRethSupply', 0)) * float(data.get('rethPrice', 2000)),
                            impermanent_loss_risk=0.0
                        )
                        opportunities.append(opportunity)
                        
        except Exception as e:
            logger.error(f"Erreur scan staking: {e}")
            
        return opportunities
        
    async def invest_in_opportunity(self, opportunity: InvestmentOpportunity, amount: float) -> bool:
        """Investissement dans une opportunité"""
        
        try:
            # Vérifications
            if amount < opportunity.minimum_amount:
                logger.warning(f"Montant insuffisant: {amount} < {opportunity.minimum_amount}")
                return False
                
            # Vérifier limite par protocole
            protocol_invested = sum(
                pos.amount_invested 
                for pos in self.positions.values() 
                if pos.opportunity.protocol == opportunity.protocol
            )
            
            if protocol_invested + amount > self.max_per_protocol:
                logger.warning(f"Limite protocole atteinte: {opportunity.protocol}")
                return False
                
            # Vérifier investissement total
            total_invested = sum(pos.amount_invested for pos in self.positions.values())
            if total_invested + amount > self.max_total_investment:
                logger.warning("Limite investissement totale atteinte")
                return False
                
            # Simulation d'investissement (remplacer par vraie interaction)
            logger.info(f"💰 Investissement: {amount} USDT dans {opportunity.protocol}")
            logger.info(f"   Stratégie: {opportunity.strategy}")
            logger.info(f"   Asset: {opportunity.asset}")
            logger.info(f"   APY: {opportunity.apy:.2f}%")
            logger.info(f"   Risque: {opportunity.risk_level}")
            
            # Créer position
            position = InvestmentPosition(
                opportunity=opportunity,
                amount_invested=amount,
                current_value=amount,
                accrued_rewards=0.0,
                start_date=datetime.now(),
                last_claim=datetime.now()
            )
            
            # Clé unique pour la position
            position_key = f"{opportunity.protocol}_{opportunity.asset}_{opportunity.strategy}"
            self.positions[position_key] = position
            
            logger.info(f"✅ Position créée: {position_key}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur investissement: {e}")
            return False
            
    async def update_positions(self):
        """Mise à jour des positions existantes"""
        
        for position_key, position in list(self.positions.items()):
            try:
                # Calculer rewards accumulés (simplifié)
                days_elapsed = (datetime.now() - position.start_date).days
                daily_rate = position.opportunity.apy / 365 / 100
                accrued_rewards = position.amount_invested * daily_rate * days_elapsed
                
                position.accrued_rewards = accrued_rewards
                
                # Mettre à jour valeur actuelle
                position.current_value = position.amount_invested + accrued_rewards
                
                # Log position
                logger.info(f"📊 Position {position_key}:")
                logger.info(f"   Investi: {position.amount_invested:.2f} USDT")
                logger.info(f"   Valeur actuelle: {position.current_value:.2f} USDT")
                logger.info(f"   Rewards: {position.accrued_rewards:.2f} USDT")
                logger.info(f"   Jours: {days_elapsed}")
                
                # Auto-claim périodique (tous les 30 jours)
                if days_elapsed > 0 and days_elapsed % 30 == 0:
                    await self._claim_rewards(position_key)
                    
            except Exception as e:
                logger.error(f"Erreur mise à jour position {position_key}: {e}")
                
    async def _claim_rewards(self, position_key: str):
        """Claim des rewards"""
        if position_key in self.positions:
            position = self.positions[position_key]
            
            logger.info(f"🎁 Claim rewards: {position.accrued_rewards:.2f} USDT")
            
            # Reset accrued rewards (simulé)
            position.last_claim = datetime.now()
            
    async def rebalance_portfolio(self):
        """Rebalancement automatique du portefeuille"""
        
        if datetime.now() - self.last_rebalance < self.rebalance_interval:
            return
            
        logger.info("🔄 Rebalancement portefeuille...")
        
        try:
            # Analyser performance des positions
            total_value = sum(pos.current_value for pos in self.positions.values())
            
            # Identifier sous-performants (< 3% APY)
            underperformers = []
            for position_key, position in self.positions.items():
                actual_apy = (position.accrued_rewards / position.amount_invested) * 365 / (datetime.now() - position.start_date).days * 100
                if actual_apy < 3.0:
                    underperformers.append((position_key, actual_apy))
                    
            # Vendre positions sous-performantes
            for position_key, actual_apy in underperformers:
                logger.info(f"📉 Vente position sous-performante: {position_key} ({actual_apy:.2f}% APY)")
                await self._close_position(position_key)
                
            # Réinvestir dans les meilleures opportunités actuelles
            if self.opportunities:
                best_opps = sorted(self.opportunities, key=lambda x: x.apy, reverse=True)[:3]
                available_capital = 1000  # Capital fictif à réinvestir
                
                for opp in best_opps:
                    if available_capital > opp.minimum_amount:
                        invest_amount = min(available_capital, 500)  # Max 500 par opp
                        await self.invest_in_opportunity(opp, invest_amount)
                        available_capital -= invest_amount
                        
            self.last_rebalance = datetime.now()
            logger.info("✅ Rebalancement terminé")
            
        except Exception as e:
            logger.error(f"Erreur rebalancement: {e}")
            
    async def _close_position(self, position_key: str):
        """Fermeture d'une position"""
        if position_key in self.positions:
            position = self.positions[position_key]
            
            logger.info(f"💸 Fermeture position: {position_key}")
            logger.info(f"   PnL: {position.accrued_rewards:.2f} USDT")
            
            del self.positions[position_key]
            
    def _calculate_il_risk(self, token0: str, token1: str) -> float:
        """Calculer risque impermanent loss"""
        # Stable coins = faible risque
        stablecoins = self.assets['stablecoins']
        
        if token0 in stablecoins and token1 in stablecoins:
            return 0.05  # 5% max
        elif token0 in stablecoins or token1 in stablecoins:
            return 0.15  # 15% max
        else:
            return 0.30  # 30% max pour crypto/crypto
            
    async def cleanup(self):
        """Nettoyage des ressources"""
        if self.session:
            await self.session.close()

# Instance globale de l'investment engine
_investment_engine: Optional[InvestmentEngine] = None

async def investment_engine_main():
    """Fonction principale de l'investment engine - appelée par TaskMaster"""
    global _investment_engine
    
    if _investment_engine is None:
        _investment_engine = InvestmentEngine()
        await _investment_engine.initialize()
        
    try:
        # Scan de toutes les opportunités
        all_opportunities = []
        
        # Aave
        aave_opps = await _investment_engine.scan_aave_opportunities()
        all_opportunities.extend(aave_opps)
        logger.info(f"🏦 Aave: {len(aave_opps)} opportunités")
        
        # Compound
        compound_opps = await _investment_engine.scan_compound_opportunities()
        all_opportunities.extend(compound_opps)
        logger.info(f"🏦 Compound: {len(compound_opps)} opportunités")
        
        # Uniswap
        uniswap_opps = await _investment_engine.scan_uniswap_opportunities()
        all_opportunities.extend(uniswap_opps)
        logger.info(f"🦄 Uniswap: {len(uniswap_opps)} opportunités")
        
        # Curve
        curve_opps = await _investment_engine.scan_curve_opportunities()
        all_opportunities.extend(curve_opps)
        logger.info(f"📈 Curve: {len(curve_opps)} opportunités")
        
        # Staking
        staking_opps = await _investment_engine.scan_staking_opportunities()
        all_opportunities.extend(staking_opps)
        logger.info(f"🔒 Staking: {len(staking_opps)} opportunités")
        
        # Filtrer et stocker les meilleures opportunités
        valid_opps = [opp for opp in all_opportunities if opp.apy >= _investment_engine.min_apy_threshold]
        valid_opps.sort(key=lambda x: x.apy, reverse=True)
        
        _investment_engine.opportunities = valid_opps[:20]  # Top 20
        
        # Log des meilleures opportunités
        if valid_opps:
            logger.info(f"🎯 Top 5 opportunités d'investissement:")
            for i, opp in enumerate(valid_opps[:5], 1):
                logger.info(f"  {i}. {opp.protocol} - {opp.strategy} ({opp.asset}) - {opp.apy:.2f}% APY")
                
        # Mise à jour des positions existantes
        await _investment_engine.update_positions()
        
        # Rebalancement périodique
        await _investment_engine.rebalance_portfolio()
        
        # Investissement automatique si capital disponible et bonnes opportunités
        total_invested = sum(pos.amount_invested for pos in _investment_engine.positions.values())
        available_capital = _investment_engine.max_total_investment - total_invested
        
        if available_capital > 500 and valid_opps:
            best_opp = valid_opps[0]
            invest_amount = min(available_capital, 1000)  # Max 1000 par investissement
            
            if invest_amount >= best_opp.minimum_amount:
                await _investment_engine.invest_in_opportunity(best_opp, invest_amount)
                
        # Statistiques du portefeuille
        if _investment_engine.positions:
            total_value = sum(pos.current_value for pos in _investment_engine.positions.values())
            total_rewards = sum(pos.accrued_rewards for pos in _investment_engine.positions.values())
            
            logger.info(f"📊 Portefeuille: {len(_investment_engine.positions)} positions")
            logger.info(f"   Valeur totale: {total_value:.2f} USDT")
            logger.info(f"   Rewards totaux: {total_rewards:.2f} USDT")
            logger.info(f"   APY moyen: {(total_rewards / total_invested) * 100:.2f}%")
            
    except Exception as e:
        logger.error(f"Erreur investment engine main: {e}")
