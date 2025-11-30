"""
Script de test d'intégration complet pour ChicoBot.

Teste tous les modules et services pour vérifier le bon fonctionnement.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config.settings import settings
from core.logging_setup import get_logger
from services.admin_system import admin_system
from services.bounty_service import bounty_service
from services.foundation_service import chico_foundation
from services.fortress_security import fortress_security
from services.investment_service import investment_engine
from services.trading_service import trading_engine

# Configuration du logger
logger = get_logger(__name__)

class IntegrationTester:
    """Testeur d'intégration complet."""
    
    def __init__(self):
        self.test_results = {}
        
    async def run_all_tests(self):
        """Exécute tous les tests d'intégration."""
        logger.info("🇬🇳 DÉMARRAGE DES TESTS D'INTÉGRATION CHICOBOT 🇬🇳")
        
        tests = [
            ("Configuration", self.test_configuration),
            ("Sécurité", self.test_security),
            ("Foundation", self.test_foundation),
            ("Admin System", self.test_admin_system),
            ("Bounty Service", self.test_bounty_service),
            ("Trading Service", self.test_trading_service),
            ("Investment Service", self.test_investment_service),
        ]
        
        for test_name, test_func in tests:
            try:
                logger.info(f"🧪 Test: {test_name}")
                result = await test_func()
                self.test_results[test_name] = result
                status = "✅ SUCCÈS" if result else "❌ ÉCHEC"
                logger.info(f"{status}: {test_name}")
            except Exception as e:
                logger.error(f"❌ ERREUR {test_name}: {e}")
                self.test_results[test_name] = False
        
        await self.print_summary()
    
    async def test_configuration(self) -> bool:
        """Teste la configuration."""
        try:
            # Vérifier les variables essentielles
            assert hasattr(settings, 'telegram_token')
            assert hasattr(settings, 'encryption_key')
            assert hasattr(settings, 'jwt_secret')
            
            logger.info("✅ Configuration validée")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur configuration: {e}")
            return False
    
    async def test_security(self) -> bool:
        """Teste le système de sécurité."""
        try:
            # Initialiser la forteresse
            success = await fortress_security.initialize()
            
            if success:
                logger.info("✅ Fortress Security initialisée")
                await fortress_security.shutdown()
                return True
            else:
                logger.error("❌ Échec initialisation Fortress Security")
                return False
        except Exception as e:
            logger.error(f"❌ Erreur sécurité: {e}")
            return False
    
    async def test_foundation(self) -> bool:
        """Teste la Chico Foundation."""
        try:
            # Initialiser la foundation
            success = await chico_foundation.initialize()
            
            if success:
                # Tester le traitement d'un gain
                result = await chico_foundation.process_gain(
                    user_id=12345,
                    username="test_user",
                    gain_amount=100.0,
                    gain_type="bounty"
                )
                
                # Vérifier que le traitement a réussi
                assert result["success"] == True
                assert result["foundation_amount"] == 1.0  # 1% de 100$
                assert result["user_net_amount"] == 99.0
                
                # Tester les statistiques
                stats = await chico_foundation.get_foundation_stats()
                assert stats["total_collected"] == 1.0
                
                logger.info("✅ Chico Foundation testée avec succès")
                return True
            else:
                logger.error("❌ Échec initialisation Chico Foundation")
                return False
        except Exception as e:
            logger.error(f"❌ Erreur foundation: {e}")
            return False
    
    async def test_admin_system(self) -> bool:
        """Teste le système admin."""
        try:
            # Initialiser le système admin
            success = await admin_system.initialize()
            
            if success:
                # Tester le démarrage du quiz
                quiz_result = await admin_system.start_admin_quiz(
                    user_id=12345,
                    username="test_admin"
                )
                
                assert quiz_result["success"] == True
                
                logger.info("✅ Système admin testé avec succès")
                return True
            else:
                logger.error("❌ Échec initialisation système admin")
                return False
        except Exception as e:
            logger.error(f"❌ Erreur admin system: {e}")
            return False
    
    async def test_bounty_service(self) -> bool:
        """Teste le service bounty."""
        try:
            # Initialiser le service
            success = await bounty_service.initialize()
            
            if success:
                # Tester la recherche de bounties
                bounties = await bounty_service.search_active_bounties("crypto", 5)
                assert isinstance(bounties, list)
                
                logger.info("✅ Bounty service testé avec succès")
                await bounty_service.shutdown()
                return True
            else:
                logger.error("❌ Échec initialisation bounty service")
                return False
        except Exception as e:
            logger.error(f"❌ Erreur bounty service: {e}")
            return False
    
    async def test_trading_service(self) -> bool:
        """Teste le service trading."""
        try:
            # Initialiser le service
            success = await trading_engine.initialize()
            
            if success:
                # Tester l'analyse d'un symbole
                analysis = await trading_engine.analyze_symbol("EURUSD")
                assert "signal" in analysis
                assert "confidence" in analysis
                
                logger.info("✅ Trading service testé avec succès")
                await trading_engine.shutdown()
                return True
            else:
                logger.error("❌ Échec initialisation trading service")
                return False
        except Exception as e:
            logger.error(f"❌ Erreur trading service: {e}")
            return False
    
    async def test_investment_service(self) -> bool:
        """Teste le service investment."""
        try:
            # Initialiser le service
            success = await investment_engine.initialize()
            
            if success:
                # Tester l'analyse des stratégies
                analysis = await investment_engine.engine.analyze_all_strategies()
                assert "portfolio_allocation" in analysis
                
                logger.info("✅ Investment service testé avec succès")
                await investment_engine.shutdown()
                return True
            else:
                logger.error("❌ Échec initialisation investment service")
                return False
        except Exception as e:
            logger.error(f"❌ Erreur investment service: {e}")
            return False
    
    async def print_summary(self):
        """Affiche le résumé des tests."""
        logger.info("\n" + "="*50)
        logger.info("🇬🇳 RÉSUMÉ DES TESTS D'INTÉGRATION 🇬🇳")
        logger.info("="*50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        failed_tests = total_tests - passed_tests
        
        for test_name, result in self.test_results.items():
            status = "✅ SUCCÈS" if result else "❌ ÉCHEC"
            logger.info(f"{status}: {test_name}")
        
        logger.info("="*50)
        logger.info(f"📊 Total: {total_tests} tests")
        logger.info(f"✅ Réussis: {passed_tests}")
        logger.info(f"❌ Échoués: {failed_tests}")
        logger.info(f"📈 Taux de réussite: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests == 0:
            logger.info("\n🎉 TOUS LES TESTS RÉUSSIS ! CHICOBOT EST PRÊT ! 🎉")
            logger.info("🇬🇳 La révolution cryptos de la Guinée peut commencer ! 🇬🇳")
        else:
            logger.info(f"\n⚠️ {failed_tests} test(s) échoué(s). Vérifiez les erreurs ci-dessus.")
        
        logger.info("="*50)

async def main():
    """Fonction principale du test."""
    try:
        tester = IntegrationTester()
        await tester.run_all_tests()
    except Exception as e:
        logger.error(f"❌ Erreur critique dans les tests: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
