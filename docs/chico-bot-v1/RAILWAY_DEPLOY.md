# ChicoBot - Déploiement Railway Express

## 🚀 DÉPLOIEMENT RAILWAY - 5 MINUTES TOP CHRONO

### ÉTAPE 1: **Préparer le Repository**
```bash
# 1. Push sur GitHub
git add .
git commit -m "ChicoBot v1.0 - Ready for Railway"
git push origin main
```

### ÉTAPE 2: **Déploiement Railway (Interface Web)**
1. **Ouvrir** https://railway.app
2. **Login** avec GitHub
3. **New Project** → **Deploy from GitHub repo**
4. **Sélectionner** votre repo `chico-bot-v1`
5. **Cliquer Deploy**

### ÉTAPE 3: **Configuration Variables**
Dans Railway Dashboard → Settings → Variables:

```bash
# OBLIGATOIRES
TELEGRAM_BOT_TOKEN=votre_token_bot_telegram
TELEGRAM_ADMIN_CHAT_ID=votre_chat_id_admin
WALLET_PRIVATE_KEY=votre_cle_privee_wallet

# TRADING (optionnel)
MT5_LOGIN=votre_login_mt5
MT5_PASSWORD=votre_password_mt5
MT5_SERVER=votre_serveur_mt5

# FOUNDATION
FOUNDATION_WALLET=0x...adresse_wallet_foundation

# APIs IA
OPENAI_PROJECT_API_KEY=votre_cle_openai
GEMINI_API_KEY=votre_cle_gemini

# SÉCURITÉ
ENCRYPTION_KEY=votre_cle_32_chars_minimum
JWT_SECRET=votre_secret_32_chars_minimum

# ENVIRONNEMENT
ENVIRONMENT=production
DATABASE_URL=sqlite:///chicobot.db

# SUPPORT CHICO
CHICO_WHATSAPP=+224620000000
CHICO_CALL=+224620000001
PROBLEMATIQUE_WHATSAPP=+224620000002
PROBLEMATIQUE_CALL=+224620000003
```

### ÉTAPE 4: **Vérification Déploiement**
1. **Logs Railway** : Vérifier "🇬🇳 Démarrage de ChicoBot"
2. **Test Bot** : Envoyer `/start` à votre bot Telegram
3. **Confirmation** : Bot répond automatiquement

---

## 🎯 **SCRIPTS DÉPLOIEMENT AUTOMATIQUE**

### **Windows**
```bash
# Exécuter
deploy-railway.bat
```

### **Linux/Mac**
```bash
# Exécuter
chmod +x deploy-railway.sh
./deploy-railway.sh
```

---

## 🤖 **BOUTON DÉPLOIEMENT ONE-CLICK**

### **Railway Deploy Button**
Ajouter à votre README.md:

```markdown
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/votre-username/chico-bot-v1)
```

---

## ✅ **DÉPLOIEMENT RÉUSSI - QU'EST-CE QUI SE PASSE ?**

Une fois déployé, ChicoBot travaille **100% automatiquement**:

### 🎯 **Bounties Automatiques**
- ✅ Scan 24/7 des bounties SuperTeam/Gitcoin/Dework
- ✅ Rédaction automatique des propositions
- ✅ Soumission automatique via WalletConnect
- ✅ Réception automatique des paiements sur votre wallet

### 📊 **Trading Automatique**
- ✅ Connexion MT5 automatique
- ✅ Trades 24/7 avec SL/TP automatiques
- ✅ Surveillance positions jusqu'au trigger
- ✅ Transfert automatique des gains sur votre wallet

### 🏦 **Investissements Automatiques**
- ✅ Investissements DeFi (Aave, Lido, RocketPool)
- ✅ Staking et yield farming configurés
- ✅ Compounding hebdomadaire automatique
- ✅ Monitoring continu des positions

### 🏛️ **RWA Automatique**
- ✅ Investissements Ondo/USDY/Centrifuge/Goldfinch
- ✅ Réception automatique des intérêts mensuels
- ✅ Compounding automatique des intérêts
- ✅ Monitoring 24/7 des positions

---

## 🎉 **MISSION ACCOMPLIE !**

**ChicoBot est maintenant actif sur Railway et vous rend riche automatiquement :**

- ✅ **0 interaction humaine** après `/start`
- ✅ **4 sources de revenus** simultanées
- ✅ **Foundation 1%** prélevé automatiquement
- ✅ **Gains transférés** directement sur votre wallet
- ✅ **Disponible 24/7** sur infrastructure Railway

**La révolution guinéenne commence maintenant !** 🇬🇳🚀💰

---

## 📞 **SUPPORT DÉPLOIEMENT**

- 📞 **Chico WhatsApp** : +224 620 00 00 00
- 📞 **Chico Appel** : +224 620 00 00 01
- 📞 **Problematique WhatsApp** : +224 620 00 00 02
- 📞 **Problematique Appel** : +224 620 00 00 03

**Pour la Guinée. Pour la famille. Pour l'avenir.** ❤️
