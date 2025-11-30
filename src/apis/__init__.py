"""
Package APIs gratuites pour ChicoBot
Spécialement conçu pour la Guinée - Aucune vérification requise
"""

from .free_search_apis import FreeSearchAPIs, get_free_search_apis

__all__ = [
    'FreeSearchAPIs',
    'get_free_search_apis'
]

logger = get_logger(__name__)
logger.info("Package APIs gratuites chargé - Spécial Guinée 🇬🇳")
