"""
Script de test pour le système IA ChicoBot

Test complet de l'intégration OpenAI GPT-4o + Gemini 1.5-flash
avec ton guinéen fraternel et ultra-émotionnel.

🇬🇳 La Guinée se soulève avec l'intelligence artificielle ! 🇬🇳
"""

import asyncio
import os
import sys
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.ai_response import generate_ai_response, get_ai_stats, clear_ai_cache, reset_ai_rate_limits
from core.database import database
from config.settings import settings

async def test_ai_response_system():
    """Test complet du système IA."""
    
    print("🇬🇳 DÉMARRAGE DES TESTS SYSTÈME IA CHICOBOT 🇬🇳")
    print("=" * 60)
    
    # Test 1: Test de base
    print("\n📋 Test 1: Réponse IA de base")
    try:
        response = await generate_ai_response(
            user_id=123456,
            message="Salut comment ça va ?",
            context="greeting"
        )
        
        print(f"✅ Modèle utilisé: {response.model_used}")
        print(f"✅ Temps de réponse: {response.response_time:.2f}s")
        print(f"✅ Contenu: {response.content[:100]}...")
        
        # Vérifier le ton guinéen
        assert "🇬🇳" in response.content, "❌ Drapeau guinéen manquant"
        assert "frère" in response.content.lower(), "❌ Ton fraternel manquant"
        assert len(response.content) > 50, "❌ Réponse trop courte"
        
        print("✅ Test 1 réussi")
        
    except Exception as e:
        print(f"❌ Test 1 échoué: {e}")
        return False
    
    # Test 2: Test contextes spécialisés
    print("\n📋 Test 2: Contextes spécialisés")
    contexts = ["start", "classement", "support", "trading", "bounty", "investment"]
    
    for context in contexts:
        try:
            response = await generate_ai_response(
                user_id=123456,
                message=f"/{context}",
                context=context
            )
            
            print(f"✅ Contexte {context}: {response.model_used} ({response.response_time:.2f}s)")
            
            # Vérifier que le contenu est contextuel
            assert len(response.content) > 100, f"❌ Réponse {context} trop courte"
            assert "🇬🇳" in response.content, f"❌ Drapeau manquant pour {context}"
            
        except Exception as e:
            print(f"❌ Contexte {context} échoué: {e}")
            return False
    
    print("✅ Test 2 réussi")
    
    # Test 3: Test avec infos utilisateur
    print("\n📋 Test 3: Personnalisation utilisateur")
    try:
        user_info = {
            "username": "test_user_gn",
            "total_earnings": 2500.0,
            "global_rank": 15,
            "guinea_rank": 3,
            "country": "GN"
        }
        
        response = await generate_ai_response(
            user_id=123456,
            message="Comment je gagne plus d'argent ?",
            context="general",
            user_info=user_info
        )
        
        print(f"✅ Personnalisation: {response.model_used}")
        
        # Vérifier que les infos utilisateur sont utilisées
        assert "test_user_gn" in response.content or "2500" in response.content, "❌ Personnalisation échouée"
        
        print("✅ Test 3 réussi")
        
    except Exception as e:
        print(f"❌ Test 3 échoué: {e}")
        return False
    
    # Test 4: Test du cache
    print("\n📋 Test 4: Système de cache")
    try:
        # Première requête
        response1 = await generate_ai_response(
            user_id=123456,
            message="Test cache",
            context="general"
        )
        
        # Deuxième requête identique (devrait être en cache)
        response2 = await generate_ai_response(
            user_id=123456,
            message="Test cache",
            context="general"
        )
        
        assert response2.cached, "❌ Cache ne fonctionne pas"
        assert response2.response_time < response1.response_time, "❌ Cache pas plus rapide"
        
        print(f"✅ Cache: {response2.cached} (temps: {response2.response_time:.3f}s)")
        print("✅ Test 4 réussi")
        
    except Exception as e:
        print(f"❌ Test 4 échoué: {e}")
        return False
    
    # Test 5: Test rate limiting
    print("\n📋 Test 5: Rate limiting")
    try:
        reset_ai_rate_limits()  # Réinitialiser
        
        # Envoyer plusieurs requêtes rapidement
        rate_limited = False
        for i in range(25):  # Plus que la limite de 20
            response = await generate_ai_response(
                user_id=999999,
                message=f"Test rate limit {i}",
                context="general"
            )
            
            if response.model_used == "rate_limit":
                rate_limited = True
                break
        
        assert rate_limited, "❌ Rate limiting ne fonctionne pas"
        print("✅ Test 5 réussi")
        
    except Exception as e:
        print(f"❌ Test 5 échoué: {e}")
        return False
    
    # Test 6: Test statistiques
    print("\n📋 Test 6: Statistiques système")
    try:
        stats = get_ai_stats()
        
        print(f"✅ Cache size: {stats['cache_size']}")
        print(f"✅ Active users: {stats['active_users']}")
        print(f"✅ OpenAI available: {stats['openai_available']}")
        print(f"✅ Gemini available: {stats['gemini_available']}")
        
        assert isinstance(stats['cache_size'], int), "❌ Cache size invalide"
        assert isinstance(stats['active_users'], int), "❌ Active users invalide"
        
        print("✅ Test 6 réussi")
        
    except Exception as e:
        print(f"❌ Test 6 échoué: {e}")
        return False
    
    # Test 7: Test fallback
    print("\n📋 Test 7: Fallback automatique")
    try:
        # Simuler une réponse avec fallback
        response = await generate_ai_response(
            user_id=123456,
            message="Test fallback",
            context="error"
        )
        
        print(f"✅ Fallback: {response.model_used}")
        assert len(response.content) > 50, "❌ Fallback trop court"
        assert "🇬🇳" in response.content, "❌ Fallback sans ton guinéen"
        
        print("✅ Test 7 réussi")
        
    except Exception as e:
        print(f"❌ Test 7 échoué: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🇬🇳 TOUS LES TESTS IA RÉUSSIS ! 🇬🇳")
    print("🚀 Le système ChicoBot IA est prêt ! 🚀")
    
    return True

async def test_database_integration():
    """Test l'intégration avec la base de données."""
    
    print("\n📋 Test 8: Intégration base de données")
    try:
        # Initialiser la base de données
        await database.initialize()
        
        # Créer un utilisateur test
        user = await database.get_or_create_user(123456)
        assert user is not None, "❌ Création utilisateur échouée"
        
        # Tester les stats
        stats = await database.get_user_stats(123456)
        print(f"✅ Stats utilisateur: {stats}")
        
        print("✅ Test 8 réussi")
        
    except Exception as e:
        print(f"❌ Test 8 échoué: {e}")
        return False
    
    return True

async def test_environment_variables():
    """Test les variables d'environnement."""
    
    print("\n📋 Test 9: Variables d'environnement")
    try:
        # Vérifier les clés API
        openai_key = os.getenv("OPENAI_PROJECT_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")
        
        print(f"✅ OpenAI key: {'✅' if openai_key else '❌'}")
        print(f"✅ Gemini key: {'✅' if gemini_key else '❌'}")
        
        # Au moins une des deux clés doit être présente
        assert openai_key or gemini_key, "❌ Aucune clé IA disponible"
        
        print("✅ Test 9 réussi")
        
    except Exception as e:
        print(f"❌ Test 9 échoué: {e}")
        return False
    
    return True

async def main():
    """Fonction principale de test."""
    
    print("🇬🇳 CHICOBOT - SYSTÈME DE TEST IA COMPLET 🇬🇳")
    print("=" * 60)
    
    # Tests à exécuter
    tests = [
        ("Système IA", test_ai_response_system),
        ("Base de données", test_database_integration),
        ("Variables d'environnement", test_environment_variables)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🚀 Exécution: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} échoué: {e}")
            results.append((test_name, False))
    
    # Résumé final
    print("\n" + "=" * 60)
    print("🇬🇳 RÉSUMÉ DES TESTS 🇬🇳")
    print("=" * 60)
    
    success_count = 0
    for test_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        print(f"{test_name}: {status}")
        if result:
            success_count += 1
    
    print(f"\n📊 Résultat: {success_count}/{len(results)} tests réussis")
    
    if success_count == len(results):
        print("\n🎉 TOUS LES TESTS RÉUSSIS !")
        print("🇬🇳 ChicoBot IA est prêt à révolutionner la Guinée ! 🇬🇳")
        print("🚀 Lance 'python main.py' pour démarrer le bot !")
    else:
        print("\n⚠️ Certains tests ont échoué")
        print("🔧 Vérifiez la configuration avant de lancer le bot")
    
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
