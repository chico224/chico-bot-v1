# ChicoBot - Guide Déploiement Railway

## 🚀 Déploiement Railway - 1-Click Deploy

### Étape 1: Prérequis
1. **Compte Railway** : https://railway.app
2. **GitHub** : Repository avec le code chico-bot-v1
3. **Variables .env** : Configurer toutes les clés

### Étape 2: Configuration Railway

#### 1. **Connectez Railway à GitHub**
```bash
# Sur railway.app
# 1. Login avec GitHub
# 2. "New Project" → "Deploy from GitHub repo"
# 3. Sélectionner votre repo chico-bot-v1
```

#### 2. **Configuration automatique**
Railway détectera automatiquement:
- ✅ Python 3.11 (via requirements.txt)
- ✅ Point d'entrée main.py
- ✅ Variables d'environnement depuis .env

#### 3. **Variables d'environnement Railway**
Dans Railway Dashboard → Settings → Variables:

```bash
# Bot Telegram
TELEGRAM_BOT_TOKEN=votre_token_bot
TELEGRAM_ADMIN_CHAT_ID=votre_chat_id

# Clés API Trading
MT5_LOGIN=votre_login_mt5
MT5_PASSWORD=votre_password_mt5
MT5_SERVER=votre_serveur_mt5

# Wallet Utilisateur
WALLET_PRIVATE_KEY=votre_cle_privee_wallet

# Foundation
FOUNDATION_WALLET=0x...adresse_foundation

# APIs IA
OPENAI_PROJECT_API_KEY=votre_cle_openai
GEMINI_API_KEY=votre_cle_gemini

# Sécurité
ENCRYPTION_KEY=votre_cle_encryption_32_chars
JWT_SECRET=votre_secret_jwt_32_chars

# Base de données
DATABASE_URL=sqlite:///chicobot.db

# Environnement
ENVIRONMENT=production

# Support Chico
CHICO_WHATSAPP=+224620000000
CHICO_CALL=+224620000001
PROBLEMATIQUE_WHATSAPP=+224620000002
PROBLEMATIQUE_CALL=+224620000003
```

### Étape 3: Déploiement Automatique

#### Option A: **Interface Railway (Recommandé)**
1. **New Project** → **Deploy from GitHub repo**
2. **Sélectionner** votre repo `chico-bot-v1`
3. **Add Variables** (copier-coller les variables ci-dessus)
4. **Deploy** → Railway build et déploie automatiquement

#### Option B: **CLI Railway**
```bash
# Installation CLI
npm install -g @railway/cli

# Login
railway login

# Initialisation
railway init

# Ajouter variables
railway variables set TELEGRAM_BOT_TOKEN=votre_token
railway variables set TELEGRAM_ADMIN_CHAT_ID=votre_chat_id
railway variables set WALLET_PRIVATE_KEY=votre_cle_privee
# ... ajouter toutes les autres variables

# Déploiement
railway up
```

### Étape 4: Vérification Déploiement

#### 1. **Logs Railway**
Dans Railway Dashboard → Logs:
```bash
🇬🇳 Démarrage de ChicoBot pour la Guinée 🇬🇳
✅ Base de données initialisée
🚀 ChicoBot est prêt à servir la Guinée !
```

#### 2. **Test Bot Telegram**
```bash
# Envoyer /start à votre bot
# Bot répond automatiquement
```

#### 3. **URL Railway**
Votre bot sera disponible à:
```
https://votre-projet.railway.app
```

### Étape 5: Monitoring et Maintenance

#### **Logs en temps réel**
```bash
railway logs
```

#### **Redéploiement automatique**
- Chaque `git push` → Redéploiement automatique
- Variables modifiées → Restart automatique

#### **Scaling**
- **Free tier** : 500h/mois suffisant pour bot 24/7
- **Pro** : $20/mois pour production intensive

---

## 🎯 **Déploiement Express - 5 Minutes**

### 1. **Push sur GitHub**
```bash
git add .
git commit -m "ChicoBot v1.0 - Ready for Railway deployment"
git push origin main
```

### 2. **Déploiement Railway**
1. https://railway.app → Login GitHub
2. New Project → Deploy from GitHub
3. Sélectionner `chico-bot-v1`
4. Ajouter variables .env (voir ci-dessus)
5. Cliquer **Deploy**

### 3. **Bot Actif**
- ✅ Bot démarre automatiquement
- ✅ Bounties 100% autonomes
- ✅ Trading 24/7 automatique
- ✅ Investissements automatiques
- ✅ RWA intérêts automatiques

---

## 🚨 **Dépannage Railway**

### **Build Failed**
```bash
# Vérifier requirements.txt
pip install -r requirements.txt

# Vérifier structure
ls -la main.py
```

### **Runtime Error**
```bash
# Vérifier variables
railway variables list

# Vérifier logs
railway logs --tail 100
```

### **Bot ne répond pas**
```bash
# Vérifier token Telegram
curl https://api.telegram.org/bot<TOKEN>/getMe

# Redémarrer service
railway restart
```

---

## 🎉 **DÉPLOIEMENT RÉUSSI !**

**ChicoBot est maintenant actif sur Railway et travaille 100% automatiquement :**

- ✅ **Bounties** : Scan → Soumet → Reçoit paiement automatiquement
- ✅ **Trading** : MT5 → Trades → Envoie gains automatiquement  
- ✅ **Investissements** : DeFi → Stake → Compound automatiquement
- ✅ **RWA** : Ondo → Intérêts → Compound automatiquement

**La révolution guinéenne commence maintenant sur Railway !** 🇬🇳🚀💰

---

*Pour le support : Chico WhatsApp +224620000000*
