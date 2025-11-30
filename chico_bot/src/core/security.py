"""
Module de sécurité avancé pour le chiffrement des portefeuilles cryptographiques.

Ce module implémente un système de chiffrement de niveau entreprise pour les adresses
de portefeuilles cryptographiques, avec une attention particulière portée à la sécurité
et aux bonnes pratiques de l'industrie.
"""

import os
import hmac
import base64
import logging
import secrets
import hashlib
import functools
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any, Callable, TypeVar, cast, Type
from enum import Enum

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes, hmac as crypto_hmac
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature, InvalidTag
import aiosqlite

# Types pour les annotations de type
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])

# Constantes de sécurité
SALT_SIZE = 32  # 256 bits
HMAC_KEY_SIZE = 32  # 256 bits
PBKDF2_ITERATIONS = 600_000  # > 2025 OWASP recommandation
FERNET_OVERRIDE = None  # Pour les tests uniquement

class WalletType(str, Enum):
    """Types de portefeuilles supportés."""
    SOLANA = "solana"
    ETHEREUM = "ethereum"

class SecurityError(Exception):
    """Exception de base pour les erreurs de sécurité."""
    pass

class WalletValidationError(SecurityError):
    """Erreur de validation d'adresse de portefeuille."""
    pass

class EncryptionError(SecurityError):
    """Erreur lors du chiffrement/déchiffrement."""
    pass

class KeyDerivationError(SecurityError):
    """Erreur lors de la dérivation des clés."""
    pass

def secure_function(max_retries: int = 3, delay: float = 0.1):
    """
    Décorateur pour les fonctions sensibles avec gestion des erreurs et réessais.
    
    Args:
        max_retries: Nombre maximum de tentatives en cas d'échec
        delay: Délai entre les tentatives en secondes
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except (InvalidToken, InvalidSignature, InvalidTag) as e:
                    last_exception = e
                    logging.warning(
                        f"Tentative {attempt + 1}/{max_retries} échouée: {str(e)}"
                    )
                    if attempt == max_retries - 1:
                        raise EncryptionError(
                            f"Échec après {max_retries} tentatives: {str(e)}"
                        ) from e
                    await asyncio.sleep(delay * (2 ** attempt))  # Backoff exponentiel
                except Exception as e:
                    logging.error(f"Erreur inattendue dans {func.__name__}: {str(e)}")
                    raise
            raise last_exception
        return cast(F, wrapper)
    return decorator

class WalletSecurityManager:
    """Gestionnaire de sécurité pour les portefeuilles cryptographiques."""
    
    def __init__(self, db_path: str):
        """
        Initialise le gestionnaire de sécurité.
        
        Args:
            db_path: Chemin vers la base de données SQLite
        """
        self.db_path = db_path
        self._ensure_db_schema()
    
    async def _get_connection(self) -> aiosqlite.Connection:
        """Établit une connexion à la base de données."""
        return await aiosqlite.connect(self.db_path)
    
    def _ensure_db_schema(self) -> None:
        """Crée les tables nécessaires si elles n'existent pas."""
        # Cette méthode est synchrone car elle n'est appelée qu'à l'initialisation
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_keys (
                    user_id INTEGER PRIMARY KEY,
                    salt BLOB NOT NULL,
                    hmac_key BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
    
    @secure_function()
    async def _derive_user_key(self, user_id: int, salt: Optional[bytes] = None) -> Tuple[bytes, bytes, bytes]:
        """
        Dérive une clé utilisateur sécurisée à partir de l'ID utilisateur.
        
        Args:
            user_id: ID de l'utilisateur Telegram
            salt: Sel optionnel (généré si non fourni)
            
        Returns:
            Tuple[clé_fernet, sel, clé_hmac]
        """
        if salt is None:
            salt = secrets.token_bytes(SALT_SIZE)
        
        # Dérivation de la clé avec PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA512(),
            length=64,  # 512 bits pour Fernet + HMAC
            salt=salt,
            iterations=PBKDF2_ITERATIONS,
            backend=default_backend()
        )
        
        # Utilisation de l'ID utilisateur comme entrée
        key_material = kdf.derive(str(user_id).encode())
        
        # Séparation en clé Fernet (32 octets) et clé HMAC (32 octets)
        fernet_key = key_material[:32]
        hmac_key = key_material[32:]
        
        return fernet_key, salt, hmac_key
    
    @secure_function()
    async def _get_or_create_user_keys(self, user_id: int) -> Tuple[bytes, bytes]:
        """
        Récupère ou crée les clés de chiffrement pour un utilisateur.
        
        Args:
            user_id: ID de l'utilisateur Telegram
            
        Returns:
            Tuple[clé_fernet, clé_hmac]
        """
        async with await self._get_connection() as conn:
            # Vérifier si l'utilisateur existe déjà
            cursor = await conn.execute(
                'SELECT salt, hmac_key FROM user_keys WHERE user_id = ?',
                (user_id,)
            )
            row = await cursor.fetchone()
            
            if row:
                salt, stored_hmac_key = row[0], row[1]
                fernet_key, _, hmac_key = await self._derive_user_key(user_id, salt)
                
                # Vérifier l'intégrité de la clé HMAC
                if not hmac.compare_digest(hmac_key, stored_hmac_key):
                    raise SecurityError("Intégrité de la clé utilisateur compromise")
                    
                return fernet_key, hmac_key
            else:
                # Créer de nouvelles clés pour l'utilisateur
                fernet_key, salt, hmac_key = await self._derive_user_key(user_id)
                
                # Stocker le sel et la clé HMAC
                await conn.execute('''
                    INSERT INTO user_keys (user_id, salt, hmac_key)
                    VALUES (?, ?, ?)
                ''', (user_id, salt, hmac_key))
                await conn.commit()
                
                return fernet_key, hmac_key
    
    @secure_function()
    async def encrypt_wallet(self, user_id: int, address: str, wallet_type: WalletType) -> bytes:
        """
        Chiffre une adresse de portefeuille.
        
        Args:
            user_id: ID de l'utilisateur Telegram
            address: Adresse du portefeuille en clair
            wallet_type: Type de portefeuille
            
        Returns:
            bytes: Données chiffrées prêtes à être stockées
        """
        if not self.verify_wallet_address(address, wallet_type):
            raise WalletValidationError(f"Format d'adresse {wallet_type.value} invalide")
        
        try:
            # Obtenir les clés de l'utilisateur
            fernet_key, _ = await self._get_or_create_user_keys(user_id)
            
            # Créer une instance Fernet avec la clé dérivée
            fernet = Fernet(base64.urlsafe_b64encode(fernet_key))
            
            # Chiffrer l'adresse avec un timestamp pour éviter les attaques par rejeu
            timestamp = int(datetime.utcnow().timestamp()).to_bytes(8, 'big')
            data_to_encrypt = f"{wallet_type.value}:{address}".encode()
            encrypted = fernet.encrypt(timestamp + data_to_encrypt)
            
            return encrypted
            
        except Exception as e:
            logging.error(f"Erreur de chiffrement pour l'utilisateur {user_id}: {str(e)}")
            raise EncryptionError("Échec du chiffrement de l'adresse du portefeuille") from e
    
    @secure_function()
    async def decrypt_wallet(self, user_id: int, encrypted_data: bytes) -> Tuple[str, WalletType]:
        """
        Déchiffre une adresse de portefeuille.
        
        Args:
            user_id: ID de l'utilisateur Telegram
            encrypted_data: Données chiffrées
            
        Returns:
            Tuple[adresse, wallet_type]: L'adresse déchiffrée et son type
            
        Raises:
            EncryptionError: Si le déchiffrement échoue
            SecurityError: Si les données sont corrompues
        """
        try:
            # Obtenir les clés de l'utilisateur
            fernet_key, _ = await self._get_or_create_user_keys(user_id)
            
            # Créer une instance Fernet avec la clé dérivée
            fernet = Fernet(base64.urlsafe_b64encode(fernet_key))
            
            # Déchiffrer les données
            decrypted = fernet.decrypt(encrypted_data, ttl=60)  # 60 secondes de validité
            
            # Extraire le timestamp et vérifier qu'il est récent
            timestamp = int.from_bytes(decrypted[:8], 'big')
            if datetime.utcnow().timestamp() - timestamp > 30:  # 30 secondes de marge
                raise SecurityError("Données déchiffrées périmées")
            
            # Extraire le type de portefeuille et l'adresse
            data_parts = decrypted[8:].decode().split(':', 1)
            if len(data_parts) != 2:
                raise SecurityError("Données déchiffrées corrompues")
                
            wallet_type = WalletType(data_parts[0])
            address = data_parts[1]
            
            # Vérifier que l'adresse est toujours valide
            if not self.verify_wallet_address(address, wallet_type):
                raise SecurityError("Adresse de portefeuille invalide après déchiffrement")
                
            return address, wallet_type
            
        except InvalidToken as e:
            logging.warning(f"Tentative de déchiffrement invalide pour l'utilisateur {user_id}")
            raise EncryptionError("Échec du déchiffrement: jeton invalide") from e
        except Exception as e:
            logging.error(f"Erreur de déchiffrement pour l'utilisateur {user_id}: {str(e)}")
            raise EncryptionError("Échec du déchiffrement de l'adresse du portefeuille") from e
    
    @staticmethod
    def verify_wallet_address(address: str, wallet_type: WalletType) -> bool:
        """
        Vérifie si une adresse de portefeuille est valide.
        
        Args:
            address: Adresse à vérifier
            wallet_type: Type de portefeuille
            
        Returns:
            bool: True si l'adresse est valide, False sinon
        """
        if not address or not isinstance(address, str):
            return False
            
        try:
            if wallet_type == WalletType.ETHEREUM:
                # Vérification d'une adresse Ethereum (0x suivi de 40 caractères hexadécimaux)
                if not address.startswith('0x'):
                    return False
                if len(address) != 42:  # 0x + 40 caractères
                    return False
                int(address, 16)  # Vérifie que c'est bien de l'hexadécimal
                return True
                
            elif wallet_type == WalletType.SOLANA:
                # Vérification d'une adresse Solana (32-44 caractères alphanumériques)
                if not (32 <= len(address) <= 44):
                    return False
                # Vérifie que c'est en base58
                import base58
                base58.b58decode(address)
                return True
                
            return False
        except (ValueError, Exception):
            return False
    
    @secure_function()
    async def sign_message(self, user_id: int, message: str) -> str:
        """
        Signe un message avec une clé dérivée de l'utilisateur.
        
        Note: Dans une implémentation réelle, cette méthode utiliserait une vraie
        clé privée. Ici, nous simulons avec une clé dérivée.
        
        Args:
            user_id: ID de l'utilisateur Telegram
            message: Message à signer
            
        Returns:
            str: Signature en base64
        """
        try:
            # Dans une vraie implémentation, on utiliserait la vraie clé privée
            # Ici, on utilise une clé dérivée pour la simulation
            _, hmac_key = await self._get_or_create_user_keys(user_id)
            
            # Créer un HMAC du message
            h = hmac.HMAC(hmac_key, hashes.SHA256(), backend=default_backend())
            h.update(message.encode())
            signature = h.finalize()
            
            return base64.b64encode(signature).decode()
            
        except Exception as e:
            logging.error(f"Erreur lors de la signature pour l'utilisateur {user_id}: {str(e)}")
            raise SecurityError("Échec de la signature du message") from e

# Instance globale (à initialiser avec le chemin de la base de données)
wallet_security_manager = None

async def init_wallet_security(db_path: str) -> None:
    """
    Initialise le gestionnaire de sécurité des portefeuilles.
    
    Args:
        db_path: Chemin vers la base de données SQLite
    """
    global wallet_security_manager
    wallet_security_manager = WalletSecurityManager(db_path)

# Tests unitaires intégrés
if __name__ == "__main__":
    import asyncio
    import tempfile
    import unittest
    import os
    import sqlite3
    
    class TestWalletSecurity(unittest.IsolatedAsyncioTestCase):
        """Tests unitaires pour le module de sécurité des portefeuilles."""
        
        async def asyncSetUp(self):
            """Configure l'environnement de test."""
            self.temp_db = tempfile.NamedTemporaryFile(delete=False)
            self.db_path = self.temp_db.name
            self.temp_db.close()
            
            # Initialiser le gestionnaire de sécurité
            await init_wallet_security(self.db_path)
            self.security = wallet_security_manager
            
            # Données de test
            self.user_id = 123456789
            self.eth_address = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"  # Adresse ETH valide
            self.sol_address = "HNxFcTNHtQ4Q75JupG5mHsP5T44uPPDkBKHL5SxttoFm"  # Adresse Solana valide
        
        async def asyncTearDown(self):
            """Nettoie après les tests."""
            if os.path.exists(self.db_path):
                os.unlink(self.db_path)
        
        async def test_verify_ethereum_address(self):
            """Teste la validation des adresses Ethereum."""
            self.assertTrue(
                self.security.verify_wallet_address(
                    self.eth_address,
                    WalletType.ETHEREUM
                )
            )
            self.assertFalse(
                self.security.verify_wallet_address(
                    "0xinvalid",
                    WalletType.ETHEREUM
                )
            )
        
        async def test_verify_solana_address(self):
            """Teste la validation des adresses Solana."""
            self.assertTrue(
                self.security.verify_wallet_address(
                    self.sol_address,
                    WalletType.SOLANA
                )
            )
            self.assertFalse(
                self.security.verify_wallet_address(
                    "invalid",
                    WalletType.SOLANA
                )
            )
        
        async def test_encrypt_decrypt_ethereum(self):
            """Teste le chiffrement et déchiffrement d'une adresse Ethereum."""
            # Chiffrer
            encrypted = await self.security.encrypt_wallet(
                self.user_id,
                self.eth_address,
                WalletType.ETHEREUM
            )
            self.assertIsInstance(encrypted, bytes)
            
            # Déchiffrer
            decrypted, wallet_type = await self.security.decrypt_wallet(
                self.user_id,
                encrypted
            )
            
            self.assertEqual(decrypted, self.eth_address)
            self.assertEqual(wallet_type, WalletType.ETHEREUM)
        
        async def test_encrypt_decrypt_solana(self):
            """Teste le chiffrement et déchiffrement d'une adresse Solana."""
            # Chiffrer
            encrypted = await self.security.encrypt_wallet(
                self.user_id,
                self.sol_address,
                WalletType.SOLANA
            )
            self.assertIsInstance(encrypted, bytes)
            
            # Déchiffrer
            decrypted, wallet_type = await self.security.decrypt_wallet(
                self.user_id,
                encrypted
            )
            
            self.assertEqual(decrypted, self.sol_address)
            self.assertEqual(wallet_type, WalletType.SOLANA)
        
        async def test_invalid_decryption(self):
            """Teste le rejet de données chiffrées invalides."""
            # Données chiffrées valides
            encrypted = await self.security.encrypt_wallet(
                self.user_id,
                self.eth_address,
                WalletType.ETHEREUM
            )
            
            # Modifier un octet pour rendre les données invalides
            corrupted = bytearray(encrypted)
            corrupted[10] ^= 0xFF
            corrupted = bytes(corrupted)
            
            # Devrait échouer
            with self.assertRaises(EncryptionError):
                await self.security.decrypt_wallet(self.user_id, corrupted)
        
        async def test_message_signing(self):
            """Teste la signature de messages."""
            message = "Test message to sign"
            signature = await self.security.sign_message(self.user_id, message)
            
            # Vérifier que la signature est en base64
            import base64
            try:
                base64.b64decode(signature)
            except Exception:
                self.fail("La signature n'est pas en base64 valide")
            
            # Vérifier que la même entrée produit la même sortie
            same_signature = await self.security.sign_message(self.user_id, message)
            self.assertEqual(signature, same_signature)
            
            # Vérifier qu'un message différent produit une signature différente
            different_signature = await self.security.sign_message(
                self.user_id,
                message + " "
            )
            self.assertNotEqual(signature, different_signature)
    
    # Exécuter les tests
    if __name__ == "__main__":
        unittest.main()
