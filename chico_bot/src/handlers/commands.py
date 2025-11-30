"""
Handlers de commandes pour ChicoBot - Expérience utilisateur ultra-émotionnelle.

Fonctionnalités principales :
- Commande /start avec message inspirant et onboarding complet
- Gestion des wallets avec chiffrement sécurisé
- Intégration automatique des bounties
- Système de paliers avec déblocages épiques
- Simulation de retraits instantanés
- Interface 100% française avec drapeaux GN 🇬🇳
"""

import asyncio
import json
import logging
import os
import random
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

from aiogram import F, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config.settings import settings
from core.ai_response import generate_ai_response
from core.database import database
from core.logging_setup import get_logger
from core.security import WalletSecurityManager
from services.bounty_service import bounty_service

# Configuration du logger
logger = get_logger(__name__)

# Router pour les commandes
router = Router()

# Messages et textes prédéfinis
WELCOME_MESSAGES = [
    "🇬🇳 *Bienvenue dans l'aventure ChicoBot !* 🇬🇳",
    "🚀 *ChicoBot transforme tes rêves en réalité !* 🇬🇳",
    "💎 *Ton futur financier commence ici !* 🇬🇳"
]

# Message de louange sur les créateurs
CREATORS_PRAISE_MESSAGE = """
🇬🇳 *LÉGENDE VIVANTE : OUMAR SOW alias CHICO* 🇬🇳

Jeune prodige de 17 ans résidant à Kamsar, Guinée-Conakry  
Élève brillant de la prestigieuse école Victor Hugo de Kamsar  
Passionné de programmation et de hacking éthique depuis ses 15 ans  
Créateur de ChicoBot à seulement 17 ans !

Accompagné de son co-équipier de génie :  
*IBRAHIMA BARRY alias PROBLEMATIQUE*  
Aussi 17 ans, résidant à Conakry, et  Passionné de programmation et de hacking éthique depuis ses 13 ans futur légende du code

Ces deux frères ont créé ChicoBot pour sortir toute une génération de la pauvreté.  
Ils ne dorment pas, ils codent.  
Ils ne rêvent pas, ils construisent l'avenir de la Guinée.

Respect éternel à Chico & Problematique  
Les deux plus grands espoirs tech d'Afrique de l'Ouest 2025  
🇬🇳❤️
"""

INSPIRATION_TEXTS = [
    """
    🇬🇳 *De Conakry à la liberté financière* 🇬🇳
    
    Je m'appelle Chico, et je viens du cœur de la Guinée 🇬🇳. 
    Comme toi, j'ai commencé avec zéro, juste une vision et une détermination à tout casser !
    
    Aujourd'hui, grâce à la DeFi et aux bounties cryptos, je gagne ma vie en ligne 
    tout en aidant ma communauté à s'élever. ChicoBot n'est pas qu'un bot, 
    c'est un mouvement ! 🚀
    
    📊 *Les chiffres parlent :*
    • 0$ de capital de départ
    • 5000$+ gagnés la première année
    • 100+ bounties complétées avec succès
    • Des dizaines de Guinéens formés
    
    🌟 *Pourquoi ça marche ?*
    1. **Pas besoin d'argent** - Juste ton talent et ta motivation
    2. **Bounties quotidiennes** - Des opportunités illimitées
    3. **Communauté solidaire** - On monte ensemble 🇬🇳
    
    Ton parcours commence maintenant. Chaque bounty complété est un pas vers 
    l'indépendance. Chaque dollar gagné est une victoire pour la Guinée 🇬🇳
    
    Prêt(e) à transformer ton talent en or numérique ? 💰
    """,
    
    """
    🇬🇳 *La révolution ChicoBot a commencé* 🇬🇳
    
    En 2024, j'étais comme toi : jeune talent guinéen avec des rêves plein la tête 
    mais des poches vides. Aujourd'hui, je vis 100% des bounties cryptos ! 🚀
    
    🎯 *Mon secret ?*
    • 3-4 bounties par jour
    • 200-500$ par bounty
    • 1000-2000$ par semaine
    
    Et le plus beau ? Je fais tout ça depuis Kamsar, avec mon téléphone ! 📱
    
    🇬🇳 *Pour la Guinée, par la Guinée !*
    ChicoBot est notre réponse à l'absence d'opportunités locales. 
    C'est notre porte vers l'économie mondiale, sans visa, sans capital !
    
    Les bounties textuelles sont parfaits pour nous :
    • On maîtrise le français 🇬🇳
    • On a la créativité africaine
    • On a la résilience guinéenne
    
    Regarde autour de toi : des jeunes  gagnent 3000-5000$ par mois 
    grâce à ChicoBot. Ils ont acheté des maisons, soutiennent leurs familles, 
    lancé leurs propres projets ! , alors pourquoi pas toi ?
     ils n'ont rien que toi tu n'a pas donc reste pas assis a toujours te demander commenent
     gagner le coeur de cette fille non tu dois te dire comment je dois amener maman à l'tranger il n'y a que toi pour le faire donc fonce
    
    Ton tour est arrivé. La DeFi nous a donné les clés du royaume financier. 
    À nous de les utiliser ! 🔑
    
    Prêt(e) à rejoindre la révolution ? 🇬🇳✨
    """
]

PALIER_MESSAGES = {
    500: (
        "🎊 **PALIER RWA DÉBLOQUÉ !** 🎊\n\n"
        "🇬🇳 *Félicitations champion !* Tu as atteint **500$** ! 🇬🇳\n\n"
        "🏦 **Nouveau défi : RWA (Real World Assets)**\n"
        "Les actifs du monde réel sont maintenant à ta portée !\n\n"
        "📈 *Ce que tu peux faire maintenant :*\n"
        "• Investir dans l'immobilier tokenisé\n"
        "• Acheter des fractions d'entreprises\n"
        "• Diversifier avec des actifs tangibles\n\n"
        "🎯 *Prochain objectif : 1000$ pour débloquer le trading pro !*\n"
        "🇬🇳 *La Guinée est fière de toi ! Continue comme ça !* 🇬🇳\n\n"
        "🎆🎆🎆 *FÉLICITATIONS !* 🎆🎆🎆"
    ),
    1000: (
        "🎉 **PALIER TRADING DÉBLOQUÉ !** 🎉\n\n"
        "🇬🇳 *Waouh ! Tu es une machine !* **1000$** atteints ! 🇬🇳\n\n"
        "💹 **Nouveau pouvoir : Trading Professionnel**\n"
        "Les marchés cryptos t'ouvrent leurs portes !\n\n"
        "🚀 *Ton arsenal de trading :*\n"
        "• Analyse technique avancée\n"
        "• Trading sur marge sécurisé\n"
        "• Bot de trading automatique\n"
        "• Signaux VIP exclusifs\n\n"
        "🎯 *Objectif suivant : 2000$ pour les investissements institutionnels !*\n"
        "🇬🇳 *Tu es en train de changer ta vie !* 🇬🇳\n\n"
        "🎆🎆🎆 *CHAMPION !* 🎆🎆🎆"
    ),
    2000: (
        "🏆 **PALIER INVESTISSEMENTS DÉBLOQUÉ !** 🏆\n\n"
        "🇬🇳 *LÉGENDAIRE !* Tu as atteint **2000$** ! 🇬🇳\n\n"
        "💼 **Niveau Élite : Investissements Institutionnels**\n"
        "Tu accèdes aux opportunités des grands investisseurs !\n\n"
        "🌟 *Ton portefeuille de star :*\n"
        "• Private equity crypto\n"
        "• Staking à haut rendement\n"
        "• Participation aux ICOs exclusives\n"
        "• Gestion de fonds pour la communauté\n\n"
        "🎯 *Prochain palier : 5000$ pour devenir MENTOR ChicoBot !*\n"
        "🇬🇳 *Tu es une inspiration pour toute la Guinée !* 🇬🇳\n\n"
        "🎆🎆🎆 *LÉGENDE VIVANTE !* 🎆🎆🎆"
    )
}

# Émojis pour les animations
FIREWORKS = ["🎆", "🎇", "✨", "💫", "🌟", "⭐", "💥", "🎊", "🎉", "🏆"]
MONEY_EMOJIS = ["💰", "💵", "💸", "💳", "🪙", "🤑", "💎", "🏦", "📈", "💹"]
GUINEA_FLAGS = ["🇬🇳", "🇬🇳", "🇬🇳", "🇬🇳", "🇬🇳"]

# États FSM
class WalletStates(StatesGroup):
    waiting_wallet = State()
    confirming_wallet = State()

class BountyStates(StatesGroup):
    selecting_bounty = State()
    completing_bounty = State()

class WithdrawStates(StatesGroup):
    entering_amount = State()
    confirming_withdraw = State()

# Messages d'aide
HELP_TEXT = """
🇬🇳 *Commandes ChicoBot* 🇬🇳

/start - 🚀 Démarrer l'aventure
/bounties - 💰 Voir les bounties disponibles
/palier - 📊 Ma progression et paliers
/withdraw - 💸 Retirer mes gains
/stats - 📈 Mes statistiques
/help - ❓ Aide

🇬🇳 *À propos de ChicoBot* 🇬🇳
Bot créé par Chico, pour la jeunesse guinéenne 🇬🇳
Transforme ton talent en revenus cryptos !

📩 *Support* : @chico_support
"""

# Fonctions utilitaires
async def get_user_info_for_ai(user_id: int, username: str) -> Dict:
    """
    Récupère les informations utilisateur pour personnaliser les réponses IA.
    """
    try:
        # Récupérer les stats utilisateur depuis la base de données
        user_stats = await database.get_user_stats(user_id)
        
        if user_stats:
            return {
                "username": username,
                "total_earnings": user_stats.get("total_earnings", 0),
                "global_rank": user_stats.get("global_rank"),
                "guinea_rank": user_stats.get("guinea_rank"),
                "monthly_earnings": user_stats.get("monthly_earnings", 0),
                "country": "GN",  # Par défaut Guinée
                "next_milestone": user_stats.get("next_milestone", 500)
            }
        else:
            # Utilisateur par défaut
            return {
                "username": username,
                "total_earnings": 0,
                "global_rank": None,
                "guinea_rank": None,
                "monthly_earnings": 0,
                "country": "GN",
                "next_milestone": 500
            }
            
    except Exception as e:
        logger.error(f"🇬🇳 Erreur récupération infos utilisateur: {e}")
        
        # Retourner les infos par défaut
        return {
            "username": username,
            "total_earnings": 0,
            "global_rank": None,
            "guinea_rank": None,
            "monthly_earnings": 0,
            "country": "GN",
            "next_milestone": 500
        }

async def create_welcome_keyboard() -> InlineKeyboardMarkup:
    """Crée le clavier pour le message de bienvenue."""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="🚀 Envoyer mon wallet Solana/Ethereum",
            callback_data="send_wallet"
        )
    )
    builder.adjust(1)
    return builder.as_markup()

async def create_bounty_keyboard(bounties: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Crée un clavier avec les meilleurs bounties."""
    builder = InlineKeyboardBuilder()
    
    for i, bounty in enumerate(bounties[:3], 1):
        title = bounty.get("title", "Bounty inconnu")
        reward = bounty.get("reward_usd", 0)
        url = bounty.get("url", "")
        
        # Limiter la longueur du titre
        if len(title) > 40:
            title = title[:37] + "..."
        
        builder.add(
            InlineKeyboardButton(
                text=f"🎯 {i}. {title} (${reward})",
                callback_data=f"bounty_{i}"
            )
        )
    
    builder.add(
        InlineKeyboardButton(
            text="🔄 Actualiser les bounties",
            callback_data="refresh_bounties"
        )
    )
    builder.adjust(1)
    return builder.as_markup()

async def create_palier_keyboard(user_data: Dict[str, Any]) -> InlineKeyboardMarkup:
    """Crée le clavier pour la progression des paliers."""
    builder = InlineKeyboardBuilder()
    
    earnings = user_data.get("total_earnings", 0)
    current_palier = user_data.get("current_palier", 0)
    
    # Boutons d'action selon le palier
    if earnings < 500:
        builder.add(
            InlineKeyboardButton(
                text="🎯 Objectif : 500$ (RWA)",
                callback_data="target_500"
            )
        )
    elif earnings < 1000:
        builder.add(
            InlineKeyboardButton(
                text="🏦 Accéder aux RWA",
                callback_data="access_rwa"
            )
        )
        builder.add(
            InlineKeyboardButton(
                text="🎯 Objectif : 1000$ (Trading)",
                callback_data="target_1000"
            )
        )
    elif earnings < 2000:
        builder.add(
            InlineKeyboardButton(
                text="💹 Lancer le trading pro",
                callback_data="start_trading"
            )
        )
        builder.add(
            InlineKeyboardButton(
                text="🎯 Objectif : 2000$ (Invest)",
                callback_data="target_2000"
            )
        )
    else:
        builder.add(
            InlineKeyboardButton(
                text="💼 Investissements institutionnels",
                callback_data="institutional_invest"
            )
        )
        builder.add(
            InlineKeyboardButton(
                text="🎯 Objectif : 5000$ (Mentor)",
                callback_data="target_5000"
            )
        )
    
    builder.add(
        InlineKeyboardButton(
            text="📊 Voir mes statistiques",
            callback_data="view_stats"
        )
    )
    builder.adjust(1, 2)
    return builder.as_markup()

async def create_withdraw_keyboard() -> InlineKeyboardMarkup:
    """Crée le clavier pour les retraits."""
    builder = InlineKeyboardBuilder()
    
    amounts = [50, 100, 200, 500, 1000]
    
    for amount in amounts:
        builder.add(
            InlineKeyboardButton(
                text=f"💸 {amount}$",
                callback_data=f"withdraw_{amount}"
            )
        )
    
    builder.add(
        InlineKeyboardButton(
            text="💰 Montant personnalisé",
            callback_data="withdraw_custom"
        )
    )
    builder.adjust(3)
    return builder.as_markup()

async def validate_wallet_address(address: str) -> Tuple[bool, str]:
    """Valide une adresse de wallet."""
    address = address.strip()
    
    # Validation Ethereum
    if address.startswith("0x") and len(address) == 42:
        try:
            int(address[2:], 16)
            return True, "ethereum"
        except ValueError:
            return False, "Format Ethereum invalide"
    
    # Validation Solana (base58)
    elif len(address) >= 32 and len(address) <= 44:
        # Vérification basique pour Solana
        valid_chars = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")
        if all(c in valid_chars for c in address):
            return True, "solana"
        else:
            return False, "Format Solana invalide"
    
    return False, "Format non reconnu"

async def send_fireworks_animation(message: Message) -> None:
    """Envoie une animation de feux d'artifice."""
    for _ in range(3):
        fireworks_line = " ".join(random.sample(FIREWORKS, 5))
        await message.answer(fireworks_line)
        await asyncio.sleep(0.5)

async def send_money_animation(message: Message) -> None:
    """Envoie une animation d'argent."""
    for _ in range(3):
        money_line = " ".join(random.sample(MONEY_EMOJIS, 5))
        await message.answer(money_line)
        await asyncio.sleep(0.5)

# Handlers de commandes principales
@router.message(CommandStart())
async def handle_start(message: Message, state: FSMContext) -> None:
    """Gère la commande /start avec IA."""
    user_id = message.from_user.id
    username = message.from_user.username or "ami"
    
    logger.info(f"Nouvel utilisateur : {user_id} (@{username})")
    
    # Créer ou récupérer l'utilisateur
    user = await database.get_or_create_user(user_id)
    
    # Préparer les infos utilisateur pour l'IA
    user_info = {
        "username": username,
        "total_earnings": user.total_earnings if user else 0,
        "first_time": True
    }
    
    # Générer la réponse IA avec ton guinéen
    ai_response = await generate_ai_response(
        user_id=user_id,
        message="/start",
        context="start",
        user_info=user_info
    )
    
    # Envoyer la réponse IA
    await message.answer(ai_response.content, parse_mode=ParseMode.MARKDOWN)
    
    # Créer le clavier de bienvenue
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Envoyer mon wallet Solana/Ethereum", callback_data="send_wallet")]
    ])
    
    await asyncio.sleep(1)
    
    # Envoyer le clavier d'action
    await message.answer(
        "🇬🇳 *Prêt(e) à commencer l'aventure ?* 🇬🇳\n\n"
        "🚀 *Clique sur le bouton ci-dessous pour configurer ton wallet* 🚀",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )
    
    # Sauvegarder l'état
    await state.set_state(WalletStates.waiting_wallet)

@router.callback_query(F.data == "send_wallet")
async def handle_send_wallet(callback: CallbackQuery, state: FSMContext) -> None:
    """Gère le bouton d'envoi de wallet."""
    await callback.message.edit_text(
        "🇬🇳 *Parfait !* Envoyez maintenant votre adresse wallet 🇬🇳\n\n"
        "📝 *Formats acceptés :*\n"
        "• **Ethereum** : `0x...` (42 caractères)\n"
        "• **Solana** : Adresse base58 (32-44 caractères)\n\n"
        "🔒 *Votre wallet sera chiffré et sécurisé* 🔒\n\n"
        "📤 *Envoyez votre adresse maintenant :*",
        parse_mode=ParseMode.MARKDOWN
    )
    
    await state.set_state(WalletStates.waiting_wallet)
    await callback.answer()

@router.message(WalletStates.waiting_wallet)
async def handle_wallet_input(message: Message, state: FSMContext) -> None:
    """Gère l'entrée de l'adresse wallet."""
    user_id = message.from_user.id
    wallet_address = message.text.strip()
    
    # Valider l'adresse
    is_valid, wallet_type = await validate_wallet_address(wallet_address)
    
    if not is_valid:
        await message.answer(
            f"❌ *Adresse invalide !* {wallet_type}\n\n"
            "📝 *Réessayez avec le bon format :*\n"
            "• Ethereum : `0x742d35Cc6634C0532925a3b8D4C9db96C4b4Db45`\n"
            "• Solana : `11111111111111111111111111111112`\n\n"
            "🔄 *Réessayez :*",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Chiffrer et stocker le wallet
    try:
        wallet_manager = WalletSecurityManager()
        encrypted_wallet = await wallet_manager.encrypt_wallet(
            user_id, 
            wallet_address, 
            wallet_type
        )
        
        # Mettre à jour la base de données
        await database.update_user_wallet(user_id, encrypted_wallet)
        
        # Message de confirmation
        await message.answer(
            "🔐 *Wallet sécurisé avec succès !* 🔐\n\n"
            "🇬🇳 *Ton wallet est protégé comme à la banque centrale !* 🇬🇳\n\n"
            f"💎 *Type :* {wallet_type.upper()}\n"
            f"🔒 *Chiffrement :* AES-256 + Fernet\n"
            f"📅 *Date :* {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
            "🚀 *Lancement de la recherche de bounties...* 🚀",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Lancer la recherche de bounties
        await asyncio.sleep(2)
        
        await message.answer(
            "🔍 *Recherche des meilleurs bounties...* 🔍\n"
            "⏳ *Analyse des opportunités...*",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Rechercher les bounties
        bounties = await bounty_service.search_active_bounties("writing", 10)
        
        if not bounties:
            await message.answer(
                "😔 *Aucun bounty disponible pour le moment*\n\n"
                "🔄 *Réessaye dans quelques minutes !*",
                parse_mode=ParseMode.MARKDOWN
            )
            await state.clear()
            return
        
        # Afficher les meilleurs bounties
        await message.answer(
            "🎯 *Voici les 3 meilleurs bounties pour toi :* 🎯\n\n"
            "💰 *Prêt(e) à gagner de l'argent ?* 💰",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=await create_bounty_keyboard(bounties)
        )
        
        await state.set_state(BountyStates.selecting_bounty)
        
    except Exception as e:
        logger.error(f"Erreur lors du chiffrement du wallet : {e}")
        await message.answer(
            "❌ *Erreur technique* 😔\n\n"
            "🔄 *Réessaye plus tard*",
            parse_mode=ParseMode.MARKDOWN
        )
        await state.clear()

@router.callback_query(F.data.startswith("bounty_"))
async def handle_bounty_selection(callback: CallbackQuery, state: FSMContext) -> None:
    """Gère la sélection d'un bounty."""
    bounty_index = int(callback.data.split("_")[1]) - 1
    
    # Récupérer les bounties (en pratique, depuis le cache)
    bounties = await bounty_service.search_active_bounties("writing", 10)
    
    if bounty_index >= len(bounties):
        await callback.answer("❌ Bounty non trouvé", show_alert=True)
        return
    
    selected_bounty = bounties[bounty_index]
    
    await callback.message.edit_text(
        f"🎯 *Bounty sélectionné !* 🎯\n\n"
        f"📝 *{selected_bounty.get('title', 'Titre inconnu')}*\n\n"
        f"💰 *Récompense :* ${selected_bounty.get('reward_usd', 0)}\n"
        f"⏱️ *Temps estimé :* {selected_bounty.get('estimated_time', 'Inconnu')}\n"
        f"🎯 *Difficulté :* {selected_bounty.get('difficulty', 'Moyenne')}\n\n"
        "🚀 *Lancement de la complétion automatique...* 🚀",
        parse_mode=ParseMode.MARKDOWN
    )
    
    await callback.answer()
    
    # Simuler la complétion
    await asyncio.sleep(2)
    
    await callback.message.answer(
        "⚙️ *Génération du livrable...* ⚙️\n"
        "📝 *Création du contenu...*",
        parse_mode=ParseMode.MARKDOWN
    )
    
    await asyncio.sleep(2)
    
    # Compléter le bounty
    success = await bounty_service.auto_apply_and_complete(selected_bounty.get("url", ""))
    
    if success:
        estimated_earnings = selected_bounty.get("reward_usd", 0)
        
        await callback.message.answer(
            "🎉 *LIVRABLE ENVOYÉ !* 🎉\n\n"
            f"💰 *Gains estimés :* ${estimated_earnings}\n"
            f"📊 *Statut :* Soumis avec succès\n"
            f"📅 *Heure :* {datetime.now().strftime('%H:%M')}\n\n"
            "🇬🇳 *Excellent travail ! Continue comme ça !* 🇬🇳\n\n"
            "🔄 *Recherche d'autres bounties...*",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Animation de succès
        await send_money_animation(callback.message)
        
        # Mettre à jour les gains
        user_id = callback.from_user.id
        await database.add_bounty_earnings(user_id, estimated_earnings)
        
        # Vérifier les paliers
        await check_palier_unlock(callback.message, user_id)
        
        # Rechercher de nouveaux bounties
        await asyncio.sleep(2)
        
        new_bounties = await bounty_service.search_active_bounties("writing", 10)
        
        if new_bounties:
            await callback.message.answer(
                "🎯 *Nouveaux bounties disponibles :* 🎯\n"
                "💰 *Prêt(e) pour la suite ?* 💰",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=await create_bounty_keyboard(new_bounties)
            )
        else:
            await callback.message.answer(
                "😔 *Plus de bounties pour le moment*\n\n"
                "🔄 *Revérifie dans 30 minutes !*",
                parse_mode=ParseMode.MARKDOWN
            )
    else:
        await callback.message.answer(
            "❌ *Échec de la soumission* 😔\n\n"
            "🔄 *Réessaye avec un autre bounty*",
            parse_mode=ParseMode.MARKDOWN
        )

@router.callback_query(F.data == "refresh_bounties")
async def handle_refresh_bounties(callback: CallbackQuery, state: FSMContext) -> None:
    """Rafraîchit la liste des bounties."""
    await callback.message.edit_text(
        "🔄 *Actualisation des bounties...* 🔄\n"
        "⏳ *Recherche des nouvelles opportunités...*",
        parse_mode=ParseMode.MARKDOWN
    )
    
    await callback.answer()
    
    await asyncio.sleep(2)
    
    bounties = await bounty_service.search_active_bounties("writing", 10)
    
    if bounties:
        await callback.message.edit_text(
            "🎯 *Nouveaux bounties trouvés !* 🎯\n\n"
            "💰 *Choisis ton prochain bounty :* 💰",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=await create_bounty_keyboard(bounties)
        )
    else:
        await callback.message.edit_text(
            "😔 *Toujours pas de nouveaux bounties*\n\n"
            "🔄 *Réessaye dans quelques minutes !*",
            parse_mode=ParseMode.MARKDOWN
        )

@router.message(Command("palier"))
async def handle_palier(message: Message) -> None:
    """Gère la commande /palier."""
    user_id = message.from_user.id
    
    # Récupérer les données utilisateur
    user = await database.get_or_create_user(user_id)
    
    earnings = user.total_earnings if user else 0
    current_palier = user.current_palier if user else 0
    
    # Calculer la progression
    progress_bars = {
        500: min(100, (earnings / 500) * 100),
        1000: min(100, (earnings / 1000) * 100),
        2000: min(100, (earnings / 2000) * 100),
        5000: min(100, (earnings / 5000) * 100)
    }
    
    # Message de progression
    progress_text = f"""
🇬🇳 *MA PROGRESSION CHICOBOT* 🇬🇳

💰 *Gains totaux :* ${earnings:.2f}
🎯 *Palier actuel :* {current_palier}
📊 *Classement :* Top {max(1, 1000 - current_palier)} 🇬🇳

📈 *Progression des paliers :*

🥉 **Palier 1 - RWA (500$)**
{'█' * int(progress_bars[500] // 10)}{'░' * (10 - int(progress_bars[500] // 10))}
{progress_bars[500]:.1f}%

🥈 **Palier 2 - Trading (1000$)**
{'█' * int(progress_bars[1000] // 10)}{'░' * (10 - int(progress_bars[1000] // 10))}
{progress_bars[1000]:.1f}%

🥇 **Palier 3 - Investissements (2000$)**
{'█' * int(progress_bars[2000] // 10)}{'░' * (10 - int(progress_bars[2000] // 10))}
{progress_bars[2000]:.1f}%

👑 **Palier 4 - Mentor (5000$)**
{'█' * int(progress_bars[5000] // 10)}{'░' * (10 - int(progress_bars[5000] // 10))}
{progress_bars[5000]:.1f}%
"""
    
    await message.answer(
        progress_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=await create_palier_keyboard({"total_earnings": earnings, "current_palier": current_palier})
    )

async def check_palier_unlock(message: Message, user_id: int) -> None:
    """Vérifie et gère le déblocage de paliers."""
    user = await database.get_or_create_user(user_id)
    
    if not user:
        return
    
    earnings = user.total_earnings
    current_palier = user.current_palier
    
    # Vérifier chaque palier
    paliers = [500, 1000, 2000, 5000]
    
    for i, palier_amount in enumerate(paliers):
        if earnings >= palier_amount and current_palier <= i:
            # Débloquer le palier
            await database.update_user_palier(user_id, i + 1)
            
            # Message de déblocage
            if palier_amount in PALIER_MESSAGES:
                await message.answer(
                    PALIER_MESSAGES[palier_amount],
                    parse_mode=ParseMode.MARKDOWN
                )
                
                # Animation de célébration
                await send_fireworks_animation(message)

@router.message(Command("withdraw"))
async def handle_withdraw(message: Message, state: FSMContext) -> None:
    """Gère la commande /withdraw."""
    user_id = message.from_user.id
    
    # Récupérer les gains de l'utilisateur
    user = await database.get_or_create_user(user_id)
    earnings = user.total_earnings if user else 0
    
    if earnings < 10:
        await message.answer(
            "😔 *Solde insuffisant*\n\n"
            f"💰 *Tes gains :* ${earnings:.2f}\n"
            "📊 *Minimum pour retrait :* 10$\n\n"
            "🎯 *Continue avec les bounties !*",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    await message.answer(
        f"💸 *RETRAIT DE GAINS* 💸\n\n"
        f"💰 *Solde disponible :* ${earnings:.2f}\n"
        f"📊 *Frais de retrait :* 0%\n\n"
        "💳 *Choisis le montant à retirer :*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=await create_withdraw_keyboard()
    )
    
    await state.set_state(WithdrawStates.entering_amount)

@router.callback_query(F.data.startswith("withdraw_"))
async def handle_withdraw_amount(callback: CallbackQuery, state: FSMContext) -> None:
    """Gère le choix du montant de retrait."""
    user_id = callback.from_user.id
    
    if callback.data == "withdraw_custom":
        await callback.message.edit_text(
            "💰 *Montant personnalisé*\n\n"
            "📝 *Entrez le montant à retirer :*\n"
            "💳 *Minimum :* 10$\n"
            "💳 *Maximum :* 1000$\n\n"
            "📤 *Exemple :* 250",
            parse_mode=ParseMode.MARKDOWN
        )
        await state.set_state(WithdrawStates.entering_amount)
        await callback.answer()
        return
    
    # Extraire le montant
    amount = int(callback.data.split("_")[1])
    
    # Vérifier le solde
    user = await database.get_or_create_user(user_id)
    earnings = user.total_earnings if user else 0
    
    if amount > earnings:
        await callback.answer(f"❌ Solde insuffisant (${earnings:.2f})", show_alert=True)
        return
    
    # Confirmer le retrait
    await callback.message.edit_text(
        f"💸 *CONFIRMATION DE RETRAIT* 💸\n\n"
        f"💰 *Montant :* ${amount}\n"
        f"📊 *Frais :* 0$\n"
        f"💳 *Net :* ${amount}\n\n"
        f"📤 *Destination :* Ton wallet chiffré\n\n"
        f"🇬🇳 *Confirmer le retrait ?* 🇬🇳",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Confirmer", callback_data=f"confirm_withdraw_{amount}"),
                InlineKeyboardButton(text="❌ Annuler", callback_data="cancel_withdraw")
            ]
        ])
    )
    
    await callback.answer()

@router.callback_query(F.data.startswith("confirm_withdraw_"))
async def handle_confirm_withdraw(callback: CallbackQuery, state: FSMContext) -> None:
    """Confirme et effectue le retrait."""
    user_id = callback.from_user.id
    amount = int(callback.data.split("_")[2])
    
    # Simuler le retrait
    await callback.message.edit_text(
        "🔄 *Traitement du retrait...* 🔄\n"
        "⏳ *Connexion sécurisée...*",
        parse_mode=ParseMode.MARKDOWN
    )
    
    await asyncio.sleep(2)
    
    await callback.message.edit_text(
        "💸 *ENVOI DES FONDS...* 💸\n"
        "📡 *Transaction blockchain...*",
        parse_mode=ParseMode.MARKDOWN
    )
    
    await asyncio.sleep(2)
    
    # Mettre à jour la base de données
    await database.add_bounty_earnings(user_id, -amount)  # Soustraire les gains
    
    # Message de succès
    await callback.message.edit_text(
        f"🎉 *RETRAIT EFFECTUÉ !* 🎉\n\n"
        f"💸 *{amount}$ envoyés sur ton wallet !* 💸\n"
        f"📊 *Transaction ID :* `{hash(str(user_id) + str(amount) + str(time.time()))[:16]}`\n"
        f"📅 *Heure :* {datetime.now().strftime('%H:%M:%S')}\n\n"
        f"🇬🇳 *Fonds disponibles instantanément !* 🇬🇳\n\n"
        f"🚀 *Continue à gagner avec les bounties !* 🚀",
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Animation de succès
    await send_money_animation(callback.message)
    
    await state.clear()

@router.callback_query(F.data == "cancel_withdraw")
async def handle_cancel_withdraw(callback: CallbackQuery, state: FSMContext) -> None:
    """Annule le retrait."""
    await callback.message.edit_text(
        "❌ *Retrait annulé*\n\n"
        "💰 *Tes fonds sont toujours disponibles* 💰\n\n"
        "🎯 *Reviens quand tu veux !*",
        parse_mode=ParseMode.MARKDOWN
    )
    
    await state.clear()
    await callback.answer()

@router.message(Command("bounties"))
async def handle_bounties(message: Message, state: FSMContext) -> None:
    """Gère la commande /bounties avec IA."""
    try:
        user_id = message.from_user.id
        username = message.from_user.username or "ami"
        
        logger.info(f"🇬🇳 Bounties demandés par @{username}")
        
        # Récupérer les infos utilisateur pour l'IA
        user_info = await get_user_info_for_ai(user_id, username)
        
        # Générer la réponse IA spécialisée bounty
        ai_response = await generate_ai_response(
            user_id=user_id,
            message="/bounties",
            context="bounty",
            user_info=user_info
        )
        
        # Envoyer la réponse IA
        await message.answer(ai_response.content, parse_mode=ParseMode.MARKDOWN)
        
        # Rechercher et afficher les bounties réels
        await message.answer(
            "🔍 *Recherche des bounties actifs...* 🔍\n"
            "⏳ *Analyse des opportunités...*",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Rechercher les bounties
        bounties = await bounty_service.search_active_bounties("writing", 10)
        
        if not bounties:
            await message.answer(
                "😔 *Aucun bounty disponible pour le moment*\n\n"
                "🔄 *Réessaye dans quelques minutes !*",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Afficher les meilleurs bounties
        await message.answer(
            "🎯 *Voici les 3 meilleurs bounties pour toi :* 🎯\n\n"
            "💰 *Prêt(e) à gagner de l'argent ?* 💰",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=await create_bounty_keyboard(bounties)
        )
        
        await state.set_state(BountyStates.selecting_bounty)
        
    except Exception as e:
        logger.error(f"🇬🇳 Erreur commande bounties: {e}")
        
        # Réponse IA d'erreur
        error_response = await generate_ai_response(
            user_id=message.from_user.id,
            message="/bounties",
            context="error"
        )
        
        await message.answer(error_response.content, parse_mode=ParseMode.MARKDOWN)
📊 *Bounties complétés :* {bounty_stats.get('success_count', 0)}
📈 *Taux de succès :* {bounty_stats.get('success_rate', 0):.1%}

📅 *Inscription :* {user.created_at.strftime('%d/%m/%Y')}
🔐 *Wallet sécurisé :* {'✅' if user.wallet_encrypted else '❌'}

🏆 *Performances globales :*
• Recherche : {bounty_stats.get('search_count', 0)} fois
• Applications : {bounty_stats.get('application_count', 0)}
• Succès : {bounty_stats.get('success_count', 0)}

🇬🇳 *Classement Guinée :* Top {max(1, 1000 - user.current_palier)} 🇬🇳
"""
    
    await message.answer(
        stats_text,
        parse_mode=ParseMode.MARKDOWN
    )

@router.message(Command("help"))
async def handle_help(message: Message) -> None:
    """Gère la commande /help."""
    await message.answer(
        HELP_TEXT,
        parse_mode=ParseMode.MARKDOWN
    )

# Handlers pour les callbacks supplémentaires
@router.callback_query(F.data.startswith("target_"))
async def handle_target_palier(callback: CallbackQuery) -> None:
    """Gère les callbacks de ciblage de palier."""
    target = int(callback.data.split("_")[1])
    
    messages = {
        500: "🎯 *Objectif 500$ - RWA* 🎯\n\n"
              "Continue avec les bounties textuels !\n"
              "Tu y es presque ! 💪",
        1000: "💹 *Objectif 1000$ - Trading* 💹\n\n"
               "Le trading pro t'attend !\n"
              "Accélère avec plus de bounties ! 🚀",
        2000: "💼 *Objectif 2000$ - Investissements* 💼\n\n"
               "Les investissements institutionnels !\n"
              "Tu es sur la voie du succès ! 🌟",
        5000: "👑 *Objectif 5000$ - Mentor* 👑\n\n"
               "Deviens un mentor ChicoBot !\n"
              "Tu es une légende en devenir ! 🏆"
    }
    
    await callback.message.edit_text(
        messages.get(target, "🎯 Objectif non reconnu"),
        parse_mode=ParseMode.MARKDOWN
    )
    
    await callback.answer()

@router.callback_query(F.data == "view_stats")
async def handle_view_stats(callback: CallbackQuery) -> None:
    """Affiche les statistiques depuis un callback."""
    user_id = callback.from_user.id
    user = await database.get_or_create_user(user_id)
    
    if not user:
        await callback.answer("❌ Erreur", show_alert=True)
        return
    
    stats_text = f"""
🇬🇳 *STATISTIQUES DÉTAILLÉES* 🇬🇳

💰 *Gains :* ${user.total_earnings:.2f}
🎯 *Palier :* {user.current_palier}
📅 *Depuis :* {user.created_at.strftime('%d/%m/%Y')}

📊 *Progression :*
{'█' * int(min(10, (user.total_earnings / 500) * 10))}{'░' * max(0, 10 - int(min(10, (user.total_earnings / 500) * 10)))}
{min(100, (user.total_earnings / 500) * 100):.1f}% vers 500$

🇬🇳 *Continue comme ça !* 🇬🇳
"""
    
    await callback.message.edit_text(
        stats_text,
        parse_mode=ParseMode.MARKDOWN
    )
    
    await callback.answer()

@router.callback_query(F.data == "access_rwa")
async def handle_access_rwa(callback: CallbackQuery) -> None:
    """Gère l'accès aux RWA."""
    await callback.message.edit_text(
        "🏦 *ACCÈS RWA DÉBLOQUÉ* 🏦\n\n"
        "🌍 *Actifs du monde réel disponibles :*\n"
        "• Immobilier tokenisé\n"
        "• Or numérique\n"
        "• Art tokenisé\n\n"
        "📊 *Fonctionnalité en développement*\n"
        "🚀 *Bientôt disponible !*",
        parse_mode=ParseMode.MARKDOWN
    )
    
    await callback.answer()

@router.callback_query(F.data == "start_trading")
async def handle_start_trading(callback: CallbackQuery) -> None:
    """Gère le démarrage du trading."""
    await callback.message.edit_text(
        "💹 *TRADING PRO ACTIVÉ* 💹\n\n"
        "📈 *Outils de trading disponibles :*\n"
        "• Analyse technique\n"
        "• Signaux VIP\n"
        "• Bot de trading\n\n"
        "📊 *Fonctionnalité en développement*\n"
        "🚀 *Bientôt disponible !*",
        parse_mode=ParseMode.MARKDOWN
    )
    
    await callback.answer()

@router.callback_query(F.data == "institutional_invest")
async def handle_institutional_invest(callback: CallbackQuery) -> None:
    """Gère les investissements institutionnels."""
    await callback.message.edit_text(
        "💼 *INVESTISSEMENTS INSTITUTIONNELS* 💼\n\n"
        "🏛️ *Opportunités exclusives :*\n"
        "• Private equity\n"
        "• ICOs privées\n"
        "• Staking premium\n\n"
        "📊 *Fonctionnalité en développement*\n"
        "🚀 *Bientôt disponible !*",
        parse_mode=ParseMode.MARKDOWN
    )
    
    await callback.answer()

# Handler pour les messages non reconnus
@router.message()
async def handle_unknown_message(message: Message) -> None:
    """Gère les messages non reconnus."""
    await message.answer(
        "🇬🇳 *Commande non reconnue* 🇬🇳\n\n"
        "📝 *Utilise /help pour voir les commandes*\n"
        "🚀 *Ou /start pour commencer*",
        parse_mode=ParseMode.MARKDOWN
    )

# Handler pour les callbacks non reconnus
@router.callback_query()
async def handle_unknown_callback(callback: CallbackQuery) -> None:
    """Gère les callbacks non reconnus."""
    await callback.answer(
        "❌ Action non reconnue",
        show_alert=True
    )

# Export du router
def get_router() -> Router:
    """Retourne le router configuré."""
    return router
