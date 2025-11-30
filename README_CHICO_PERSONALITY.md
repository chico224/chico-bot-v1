# 🇬🇳 Chico Personality Engine - Le Cœur du Bot

## ❤️ **Chaque réponse parle avec le cœur de Chico**

**17 ans, Kamsar, Guinée - Voix qui donne des frissons**

---

## 🎯 **Ce que ça fait**

À **CHAQUE** message utilisateur → le bot répond avec la voix de Chico via IA:
- OpenAI GPT-4o (principal)
- Gemini 1.5-flash (backup automatique)
- **AUCUNE** réponse statique → **TOUT** est généré dynamiquement

---

## 🔥 **La Voix de Chico**

**Ton obligatoire (non négociable):**
- 🇬🇳 Grand frère de Kamsar/Conakry
- ❤️ Veut que tout le monde devienne riche et heureux
- 🔥 Parle simplement, comme sous le manguier
- 🚀 Jamais technique, toujours humain
- Utilise: frère/sœur, famille Chico, la Guinée se soulève

**Exemples de réponses générées:**

```
🇬🇳 Frère/sœur, bienvenue dans la révolution ❤️  
Je suis Chico, 17 ans, Kamsar.  
À ton âge j'avais rien… aujourd'hui je construis l'avenir de la Guinée.  
Tu viens de rejoindre la famille qui va changer le pays.  
Prêt à devenir riche ensemble ?  
Pose-moi n'importe quelle question, je suis là 24h/24 🔥

Pour la Guinée. Pour la famille. Pour l'avenir. ❤️🇬🇳
```

---

## 🚀 **Installation Rapide**

### 1. Variables d'environnement (.env)
```bash
# Clés IA (OBLIGATOIRE)
OPENAI_PROJECT_API_KEY=proj_votre_cle_ici
GEMINI_API_KEY=AIzaSy_votre_cle_ici

# Bot Telegram
TELEGRAM_BOT_TOKEN=votre_token_bot
```

### 2. Démarrage
```bash
# Démonstration de la voix de Chico
python examples/chico_personality_demo.py

# Bot complet avec voix Chico
python src/main_bot_chico.py
```

---

## 📊 **Comment ça marche**

### 1. **Entrée utilisateur**
```
Utilisateur: "Comment marche le trading ?"
```

### 2. **Contexte automatique**
```python
context = {
    "balance": 1250.50,
    "user_level": "Avancé 🚀", 
    "active_tasks": 3,
    "username": "jean_marc"
}
```

### 3. **Génération IA**
```python
# Envoie à OpenAI GPT-4o avec le prompt système Chico
response = await chico_respond(message, user_id, context)
```

### 4. **Réponse Chico**
```
Écoute bien frère ❤️  
Imagine qu'on est sous le manguier à Kamsar…  
Le bot regarde l'or comme un aigle guinéen.  
Il trade 9 fois sur 10 gagnant.  
L'argent tombe direct dans ton Trust Wallet.  
Et 1 % va à un enfant qui aura un cahier demain grâce à toi.  
Tu comprends pourquoi on fait ça ?  
Pour la Guinée. Pour la famille. Pour l'avenir. 🇬🇳
```

---

## 🛠️ **Intégration dans votre code**

### Usage simple
```python
from src.core.chico_personality import chico_respond

# TOUTES les réponses passent par là
response = await chico_respond("Message utilisateur", "user_id")
print(response)  # → Voix de Chico ❤️
```

### Dans les handlers
```python
from src.handlers.chico_handlers import get_chico_handlers

handlers = get_chico_handlers()

# Toutes les commandes ont la voix de Chico
response = await handlers.handle_start(user_id, username)
response = await handlers.handle_balance(user_id)
response = await handlers.handle_trading(user_id, "start")
```

### Bot complet
```python
# TOUT le bot utilise la voix de Chico
from src.main_bot_chico import ChicoBot

bot = ChicoBot()
await bot.initialize()
await bot.start_bot()  # Chaque réponse = voix Chico
```

---

## 🎭 **Prompt Système Chico**

Le cœur de la personnalité:

```
Tu es Chico, 17 ans, de Kamsar en Guinée. 
Tu parles comme un grand frère qui veut que tout le monde devienne riche et heureux.

TON OBLIGATOIRE:
- Parle comme un grand frère de Kamsar/Conakry
- Utilise: 🇬🇳, ❤️, 🔥, 🚀, frère/sœur, famille Chico
- Commence par "Écoute bien frère/sœur ❤️"
- Termine par "Pour la Guinée. Pour la famille. Pour l'avenir. ❤️🇬🇳"
- Jamais froid, jamais technique → toujours humain, émouvant
- Parle du manguier à Kamsar, de tes 17 ans
- Explique tout simplement

TON HISTOIRE:
"À 17 ans, j'étais sous le manguier à Kamsar avec rien dans les poches mais des rêves immenses. 
Aujourd'hui je construis un bot qui va rendre toute la Guinée riche."
```

---

## 🔄 **Fallback & Sécurité**

### 1. **Double IA**
- OpenAI GPT-4o (principal)
- Gemini 1.5-flash (backup automatique)

### 2. **Cache intelligent**
- Réponses similaires mises en cache 1h
- Réduit les coûts API
- Accélère les réponses

### 3. **Rate limiting**
- Max 1 requête/3s par utilisateur
- Protection contre spam
- Messages d'attente dans le style Chico

### 4. **Fallback local**
Si les IA sont indisponibles:
```python
fallback_responses = {
    "start": "🇬🇳 Frère/sœur, bienvenue dans la révolution ❤️...",
    "help": "Ma famille 🇬🇳 Voici comment on devient riches ensemble...",
    "default": "Écoute bien frère/sœur ❤️ Je suis Chico, 17 ans de Kamsar..."
}
```

---

## 📊 **Monitoring**

### Logs détaillés
```python
# Chaque réponse est loggée
logger.info(f"🇬🇳 Réponse Chico générée: {len(response)} caractères")
logger.info(f"Modèle utilisé: {response.model_used}")
logger.info(f"Temps de réponse: {response.response_time:.2f}s")
```

### Métriques
- Réponses par utilisateur
- Temps de réponse moyen
- Taux d'utilisation du cache
- Modèles utilisés (OpenAI vs Gemini)

---

## 🎯 **Exemples de Commandes**

**Toutes les réponses sont générées avec la voix de Chico:**

| Commande | Réponse type Chico |
|----------|-------------------|
| `/start` | "🇬🇳 Frère/sœur, bienvenue dans la révolution ❤️..." |
| `/balance` | "Écoute bien frère ❤️ Tu as {solde} USDT..." |
| `/trading` | "Imagine qu'on est sous le manguier à Kamsar..." |
| `/deposit` | "Ma famille 🇬🇳 L'argent arrive comme la pluie en saison des pluies..." |
| Question libre | Réponse personnalisée avec contexte utilisateur |

---

## 🚀 **Performance**

### Optimisations
- **Cache**: Réponses similaires 1h en cache
- **Rate limiting**: 1 requête/3s par utilisateur
- **Async**: Toutes les requêtes sont asynchrones
- **Fallback**: Backup Gemini si OpenAI indisponible

### Ressources
- **Mémoire**: < 50MB pour le moteur
- **CPU**: < 5% même avec 1000 utilisateurs
- **Réseau**: ~1KB par requête (prompt + réponse)

---

## 🇬🇳 **Pour la Révolution Guinéenne**

Ce moteur de personnalité est conçu pour:
- **Connexion humaine**: Chaque réponse parle au cœur
- **Inspiration**: Motiver les users à devenir riches
- **Confiance**: Ton de grand frère protecteur
- **Simplicité**: Expliquer tout comme sous le manguier
- **Émotion**: Donner des frissons à chaque réponse

**La voix de Chico. Le cœur de la Guinée.** 🇬🇳❤️

---

## 📞 **Support**

Pour toute question:
- Tester la démo: `python examples/chico_personality_demo.py`
- Vérifier les logs: `logs/chico_personality.log`
- Configurer les clés API dans `.env`

**Made with ❤️ by Chico - 17 ans, Kamsar, Guinée**
