"""
Trading Bot Task - Trading automatique 24/7
Priorité moyenne - exécution toutes les 10 secondes maximum
Stratégies multiples: scalping, swing, arbitrage
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

logger = setup_logging("trading_bot")

@dataclass
class TradingSignal:
    symbol: str
    action: str  # 'BUY' ou 'SELL'
    strategy: str
    confidence: float  # 0-1
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: float
    timestamp: datetime

@dataclass
class Position:
    symbol: str
    side: str  # 'LONG' ou 'SHORT'
    entry_price: float
    current_price: float
    size: float
    stop_loss: float
    take_profit: float
    pnl: float
    entry_time: datetime

class TradingBot:
    """Trading bot multi-stratégies 24/7"""
    
    def __init__(self):
        self.session = None
        self.positions = {}
        self.signals = []
        self.last_trade = datetime.min
        self.daily_trades = 0
        self.max_daily_trades = 50
        
        # Configuration trading
        self.max_position_size = 0.1  # 10% du capital max par position
        self.max_positions = 5  # Max 5 positions simultanées
        self.risk_per_trade = 0.02  # 2% de risque par trade
        
        # APIs exchanges
        self.exchanges = {
            "binance": "https://api.binance.com",
            "coinbase": "https://api.coinbase.com",
            "kraken": "https://api.kraken.com",
            "bybit": "https://api.bybit.com"
        }
        
        # Paires à trader (majeures + quelques altcoins)
        self.symbols = [
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT",
            "MATICUSDT", "DOTUSDT", "AVAXUSDT", "LINKUSDT", "UNIUSDT"
        ]
        
        # Timeframes pour analyse
        self.timeframes = ["1m", "5m", "15m", "1h", "4h", "1d"]
        
    async def initialize(self):
        """Initialisation de la session HTTP"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'ChicoBot-TradingBot/1.0',
                'Accept': 'application/json'
            }
        )
        
    async def get_market_data(self, symbol: str, timeframe: str = "1m", limit: int = 100) -> List[Dict]:
        """Récupération données de marché"""
        
        try:
            # Binance API pour les données
            url = f"{self.exchanges['binance']}/api/v3/klines"
            params = {
                'symbol': symbol,
                'interval': timeframe,
                'limit': limit
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Conversion en format standard
                    candles = []
                    for candle in data:
                        candles.append({
                            'timestamp': datetime.fromtimestamp(candle[0] / 1000),
                            'open': float(candle[1]),
                            'high': float(candle[2]),
                            'low': float(candle[3]),
                            'close': float(candle[4]),
                            'volume': float(candle[5])
                        })
                        
                    return candles
                else:
                    logger.error(f"Erreur API Binance pour {symbol}: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Erreur get_market_data {symbol}: {e}")
            return []
            
    async def analyze_scalping_opportunity(self, symbol: str) -> Optional[TradingSignal]:
        """Stratégie de scalping - trades rapides < 5min"""
        
        try:
            # Données 1 minute
            candles = await self.get_market_data(symbol, "1m", 20)
            if len(candles) < 20:
                return None
                
            # Indicateurs techniques
            closes = [c['close'] for c in candles]
            volumes = [c['volume'] for c in candles]
            
            # SMA rapides
            sma_5 = statistics.mean(closes[-5:])
            sma_20 = statistics.mean(closes[-20:])
            
            # RSI simplifié
            rsi = self._calculate_rsi(closes, 14)
            
            # Volume moyen
            avg_volume = statistics.mean(volumes[-10:])
            current_volume = volumes[-1]
            
            current_price = closes[-1]
            
            # Signal d'achat
            if (sma_5 > sma_20 and  # Trend haussier court terme
                rsi < 70 and  # Pas suracheté
                current_volume > avg_volume * 1.5 and  # Volume élevé
                len(self.positions) < self.max_positions):
                
                # Calcul stop loss et take profit (scalping)
                atr = self._calculate_atr(candles, 14)
                stop_loss = current_price - atr * 1.5
                take_profit = current_price + atr * 1.0
                
                # Taille position selon risque
                risk_amount = 1000 * self.risk_per_trade  # 1000 = capital fictif
                position_size = risk_amount / (current_price - stop_loss)
                position_size = min(position_size, 1000 * self.max_position_size / current_price)
                
                return TradingSignal(
                    symbol=symbol,
                    action="BUY",
                    strategy="scalping",
                    confidence=0.7,
                    entry_price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    position_size=position_size,
                    timestamp=datetime.now()
                )
                
            # Signal de vente
            elif (sma_5 < sma_20 and  # Trend baissier
                  rsi > 30 and  # Pas survendu
                  current_volume > avg_volume * 1.5):
                
                atr = self._calculate_atr(candles, 14)
                stop_loss = current_price + atr * 1.5
                take_profit = current_price - atr * 1.0
                
                risk_amount = 1000 * self.risk_per_trade
                position_size = risk_amount / (stop_loss - current_price)
                position_size = min(position_size, 1000 * self.max_position_size / current_price)
                
                return TradingSignal(
                    symbol=symbol,
                    action="SELL",
                    strategy="scalping",
                    confidence=0.7,
                    entry_price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    position_size=position_size,
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            logger.error(f"Erreur analyse scalping {symbol}: {e}")
            
        return None
        
    async def analyze_swing_opportunity(self, symbol: str) -> Optional[TradingSignal]:
        """Stratégie de swing trading - trades sur plusieurs heures/days"""
        
        try:
            # Données 1 heure
            candles = await self.get_market_data(symbol, "1h", 50)
            if len(candles) < 50:
                return None
                
            closes = [c['close'] for c in candles]
            
            # EMA pour trend
            ema_20 = self._calculate_ema(closes, 20)
            ema_50 = self._calculate_ema(closes, 50)
            
            # MACD simplifié
            macd_signal = self._calculate_macd(closes)
            
            current_price = closes[-1]
            
            # Signal swing trading
            if (ema_20 > ema_50 and  # Trend haussier
                macd_signal == 'bullish' and
                len(self.positions) < self.max_positions):
                
                # Stop loss plus large pour swing
                atr = self._calculate_atr(candles, 14)
                stop_loss = current_price - atr * 2.5
                take_profit = current_price + atr * 3.0
                
                risk_amount = 1000 * self.risk_per_trade
                position_size = risk_amount / (current_price - stop_loss)
                position_size = min(position_size, 1000 * self.max_position_size / current_price)
                
                return TradingSignal(
                    symbol=symbol,
                    action="BUY",
                    strategy="swing",
                    confidence=0.8,
                    entry_price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    position_size=position_size,
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            logger.error(f"Erreur analyse swing {symbol}: {e}")
            
        return None
        
    async def analyze_arbitrage_opportunity(self) -> Optional[TradingSignal]:
        """Stratégie d'arbitrage entre exchanges"""
        
        try:
            # Vérifier BTC sur plusieurs exchanges
            btc_prices = {}
            
            for exchange_name, base_url in self.exchanges.items():
                try:
                    if exchange_name == "binance":
                        url = f"{base_url}/api/v3/ticker/price?symbol=BTCUSDT"
                    elif exchange_name == "coinbase":
                        url = f"{base_url}/v2/prices/BTC-USD/spot"
                    elif exchange_name == "kraken":
                        url = f"{base_url}/0/public/Ticker?pair=XBTUSDT"
                    else:
                        continue
                        
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if exchange_name == "binance":
                                price = float(data['price'])
                            elif exchange_name == "coinbase":
                                price = float(data['data']['amount'])
                            elif exchange_name == "kraken":
                                price = float(data['result']['XXBTZUSD']['c'][0])
                            else:
                                continue
                                
                            btc_prices[exchange_name] = price
                            
                except Exception as e:
                    logger.debug(f"Erreur prix {exchange_name}: {e}")
                    continue
                    
            # Calculer arbitrage
            if len(btc_prices) >= 2:
                prices = list(btc_prices.values())
                max_price = max(prices)
                min_price = min(prices)
                
                spread = (max_price - min_price) / min_price
                
                # Arbitrage si spread > 0.5%
                if spread > 0.005:
                    high_exchange = [k for k, v in btc_prices.items() if v == max_price][0]
                    low_exchange = [k for k, v in btc_prices.items() if v == min_price][0]
                    
                    logger.info(f"🔄 Arbitrage détecté: {low_exchange} ({min_price}) -> {high_exchange} ({max_price}) spread: {spread:.2%}")
                    
                    # Signal d'arbitrage (vente sur exchange cher, achat sur exchange pas cher)
                    return TradingSignal(
                        symbol="BTCUSDT",
                        action="SELL",  # Vendre sur l'exchange cher
                        strategy="arbitrage",
                        confidence=0.9,
                        entry_price=max_price,
                        stop_loss=max_price * 0.995,  # Stop tight pour arbitrage
                        take_profit=min_price,
                        position_size=0.01,  # Petite taille pour arbitrage
                        timestamp=datetime.now()
                    )
                    
        except Exception as e:
            logger.error(f"Erreur analyse arbitrage: {e}")
            
        return None
        
    async def execute_signal(self, signal: TradingSignal) -> bool:
        """Exécution d'un signal de trading"""
        
        try:
            # Rate limiting
            if (datetime.now() - self.last_trade).total_seconds() < 10:
                return False
                
            if self.daily_trades >= self.max_daily_trades:
                logger.warning("Limite de trades quotidiens atteinte")
                return False
                
            # Simulation d'exécution (remplacer par vraie API)
            logger.info(f"📈 Exécution signal: {signal.action} {signal.symbol} @ {signal.entry_price}")
            logger.info(f"   Stratégie: {signal.strategy}")
            logger.info(f"   Taille: {signal.position_size}")
            logger.info(f"   Stop Loss: {signal.stop_loss}")
            logger.info(f"   Take Profit: {signal.take_profit}")
            
            # Créer position
            if signal.action == "BUY":
                side = "LONG"
            else:
                side = "SHORT"
                
            position = Position(
                symbol=signal.symbol,
                side=side,
                entry_price=signal.entry_price,
                current_price=signal.entry_price,
                size=signal.position_size,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit,
                pnl=0.0,
                entry_time=datetime.now()
            )
            
            self.positions[signal.symbol] = position
            self.signals.append(signal)
            self.last_trade = datetime.now()
            self.daily_trades += 1
            
            logger.info(f"✅ Position ouverte: {signal.symbol} {side}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur exécution signal: {e}")
            return False
            
    async def monitor_positions(self):
        """Monitoring des positions actives"""
        
        for symbol, position in list(self.positions.items()):
            try:
                # Prix actuel
                current_data = await self.get_market_data(symbol, "1m", 1)
                if not current_data:
                    continue
                    
                current_price = current_data[0]['close']
                position.current_price = current_price
                
                # Calculer PnL
                if position.side == "LONG":
                    pnl = (current_price - position.entry_price) * position.size
                else:
                    pnl = (position.entry_price - current_price) * position.size
                    
                position.pnl = pnl
                
                # Vérifier stop loss et take profit
                if position.side == "LONG":
                    if current_price <= position.stop_loss:
                        await self._close_position(symbol, "STOP_LOSS")
                    elif current_price >= position.take_profit:
                        await self._close_position(symbol, "TAKE_PROFIT")
                else:
                    if current_price >= position.stop_loss:
                        await self._close_position(symbol, "STOP_LOSS")
                    elif current_price <= position.take_profit:
                        await self._close_position(symbol, "TAKE_PROFIT")
                        
                # Log position
                logger.info(f"📊 Position {symbol}: {position.side} PnL: {pnl:.2f} USDT")
                
            except Exception as e:
                logger.error(f"Erreur monitoring position {symbol}: {e}")
                
    async def _close_position(self, symbol: str, reason: str):
        """Fermeture d'une position"""
        if symbol in self.positions:
            position = self.positions[symbol]
            
            logger.info(f"🔒 Fermeture position {symbol}: {reason}")
            logger.info(f"   PnL final: {position.pnl:.2f} USDT")
            
            del self.positions[symbol]
            
    def _calculate_rsi(self, closes: List[float], period: int = 14) -> float:
        """Calcul RSI"""
        if len(closes) < period + 1:
            return 50
            
        gains = []
        losses = []
        
        for i in range(1, len(closes)):
            change = closes[i] - closes[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
                
        avg_gain = statistics.mean(gains[-period:])
        avg_loss = statistics.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
        
    def _calculate_ema(self, closes: List[float], period: int) -> float:
        """Calcul EMA"""
        if len(closes) < period:
            return statistics.mean(closes[-period:])
            
        multiplier = 2 / (period + 1)
        ema = closes[0]
        
        for price in closes[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
            
        return ema
        
    def _calculate_macd(self, closes: List[float]) -> str:
        """Calcul MACD simplifié"""
        if len(closes) < 26:
            return "neutral"
            
        ema_12 = self._calculate_ema(closes[-12:], 12)
        ema_26 = self._calculate_ema(closes[-26:], 26)
        
        if ema_12 > ema_26:
            return "bullish"
        elif ema_12 < ema_26:
            return "bearish"
        else:
            return "neutral"
            
    def _calculate_atr(self, candles: List[Dict], period: int = 14) -> float:
        """Calcul ATR (Average True Range)"""
        if len(candles) < period + 1:
            return 0
            
        true_ranges = []
        
        for i in range(1, len(candles)):
            high = candles[i]['high']
            low = candles[i]['low']
            prev_close = candles[i-1]['close']
            
            tr1 = high - low
            tr2 = abs(high - prev_close)
            tr3 = abs(low - prev_close)
            
            true_ranges.append(max(tr1, tr2, tr3))
            
        return statistics.mean(true_ranges[-period:])
        
    async def cleanup(self):
        """Nettoyage des ressources"""
        if self.session:
            await self.session.close()

# Instance globale du trading bot
_trading_bot: Optional[TradingBot] = None

async def trading_bot_main():
    """Fonction principale du trading bot - appelée par TaskMaster"""
    global _trading_bot
    
    if _trading_bot is None:
        _trading_bot = TradingBot()
        await _trading_bot.initialize()
        
    try:
        # Monitoring positions existantes
        await _trading_bot.monitor_positions()
        
        # Analyse des opportunités
        all_signals = []
        
        # Arbitrage (priorité haute)
        arb_signal = await _trading_bot.analyze_arbitrage_opportunity()
        if arb_signal:
            all_signals.append(arb_signal)
            
        # Scalping sur plusieurs paires
        for symbol in _trading_bot.symbols[:5]:  # Limiter pour éviter surcharge
            scalp_signal = await _trading_bot.analyze_scalping_opportunity(symbol)
            if scalp_signal:
                all_signals.append(scalp_signal)
                
        # Swing trading
        for symbol in _trading_bot.symbols[:3]:
            swing_signal = await _trading_bot.analyze_swing_opportunity(symbol)
            if swing_signal:
                all_signals.append(swing_signal)
                
        # Filtrer et trier les signaux
        valid_signals = [s for s in all_signals if s.confidence > 0.7]
        valid_signals.sort(key=lambda x: x.confidence, reverse=True)
        
        # Exécuter le meilleur signal
        if valid_signals and len(_trading_bot.positions) < _trading_bot.max_positions:
            best_signal = valid_signals[0]
            await _trading_bot.execute_signal(best_signal)
            
        # Log statistiques
        if _trading_bot.positions:
            total_pnl = sum(p.pnl for p in _trading_bot.positions.values())
            logger.info(f"📈 Positions actives: {len(_trading_bot.positions)} | PnL total: {total_pnl:.2f} USDT")
            
        # Reset compteur quotidien
        if datetime.now().hour == 0 and datetime.now().minute == 0:
            _trading_bot.daily_trades = 0
            
    except Exception as e:
        logger.error(f"Erreur trading bot main: {e}")
