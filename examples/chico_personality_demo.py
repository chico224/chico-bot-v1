"""
Démonstration du moteur de personnalité Chico
Montre comment Chico répond avec sa voix unique à chaque message
"""

import asyncio
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

from src.core.chico_personality import chico_respond
from src.core.database import DatabaseManager

async def demo_chico_personality():
    """
    Démonstration de la voix de Chico
    Chaque réponse est générée par IA avec le ton de Chico - 17 ans, Kamsar
    """
    
    print("🇬🇳 DÉMONSTRATION CHICO PERSONALITY")
    print("="*60)
    print("Chaque réponse est générée par IA avec la voix de Chico")
    print("17 ans, Kamsar, Guinée - cœur immense")
    print("="*60)
    
    # Initialiser la base de données (pour le contexte)
    database = DatabaseManager()
    
    # Messages de test pour démontrer la voix de Chico
    test_messages = [
        "/start",
        "Comment marche le trading ?", 
        "J'ai peur de perdre mon argent",
        "Je veux déposer 500 USDT",
        "Montre-moi mes stats",
        "Qui es-tu Chico ?",
        "Pourquoi tu fais ça ?",
        "Je suis de Conakry aussi !",
        "Est-ce que ça marche vraiment ?",
        "Merci frère"
    ]
    
    user_id = "demo_user"
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n📩 Message {i}: {message}")
        print("─" * 50)
        
        try:
            # Générer la réponse avec la voix de Chico
            response = await chico_respond(message, user_id)
            
            print(f"🇬🇳 Réponse Chico:")
            print(response)
            print("─" * 50)
            
            # Pause entre les réponses
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            
    print("\n🇬🇳 Démonstration terminée !")
    print("Chaque réponse est unique et générée avec le cœur de Chico ❤️")

if __name__ == "__main__":
    # Vérifier les clés API
    if not os.getenv("OPENAI_PROJECT_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        print("❌ Configurez OPENAI_PROJECT_API_KEY ou GEMINI_API_KEY dans votre .env")
        print("📖 Copiez .env.example en .env et remplissez vos clés")
    else:
        asyncio.run(demo_chico_personality())
