"""
Module de base de données asynchrone pour ChicoBot.

Utilise SQLAlchemy Core asynchrone avec aiosqlite pour les opérations de base de données.
"""

import asyncio
import datetime
import json
import logging
import os
import shutil
import sqlite3
import time
import zlib
from contextlib import asynccontextmanager
from decimal import Decimal
from enum import Enum, auto
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple, Union

import aiosqlite
import pytz
from cryptography.fernet import Fernet
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum as SQLAEnum,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    delete,
    event,
    func,
    select,
    text,
    update,
)
from sqlalchemy.dialects.sqlite import insert as sqlite_upsert
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from config.settings import settings
from core.logging_setup import get_logger

# Configuration du logger
logger = get_logger(__name__)

# Constantes
DB_FILE = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
DB_BACKUP_DIR = "db_backups"
DB_BACKUP_RETENTION_DAYS = 7

# Configuration de la base de données
DATABASE_URL = f"sqlite+aiosqlite:///{DB_FILE}"

# Métadonnées SQLAlchemy
metadata = MetaData()
Base = declarative_base(metadata=metadata)

# Enum pour les types de tâches
class TaskType(str, Enum):
    BOUNTY = "bounty"
    RWA = "rwa"
    TRADING = "trading"
    INVEST = "invest"

# Enum pour les statuts de tâches
class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

# Modèle de données
class User(Base):
    __tablename__ = "users"
    
    telegram_id = Column(BigInteger, primary_key=True, autoincrement=False)
    wallet_encrypted = Column(Text, nullable=True)  # Chiffré avec la clé utilisateur
    total_earnings = Column(Float, default=0.0, nullable=False)
    current_palier = Column(Integer, default=0, nullable=False)  # 0 = débutant, 1 = RWA, 2 = trading, 3 = invest
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relations
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.telegram_id}, palier={self.current_palier}, earnings={self.total_earnings})>"

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False)
    type = Column(SQLAEnum(TaskType), nullable=False)
    status = Column(SQLAEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    earnings = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relations
    user = relationship("User", back_populates="tasks")
    
    def __repr__(self):
        return f"<Task(id={self.id}, type={self.type}, status={self.status}, user_id={self.user_id})>"

# Classe principale de la base de données
class Database:
    _instance = None
    _engine = None
    _session_factory = None
    _backup_task = None
    _fernet = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._initialized = False
        return cls._instance
    
    async def initialize(self):
        """Initialise la connexion à la base de données et effectue les migrations."""
        if self._initialized:
            return
            
        logger.info("Initialisation de la base de données...")
        
        # Créer le répertoire de sauvegarde si nécessaire
        os.makedirs(DB_BACKUP_DIR, exist_ok=True)
        
        # Configurer le moteur SQLAlchemy
        self._engine = create_async_engine(
            DATABASE_URL,
            echo=settings.DEBUG,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
        )
        
        # Configurer la session factory
        self._session_factory = sessionmaker(
            self._engine, 
            expire_on_commit=False,
            class_=AsyncSession
        )
        
        # Initialiser la clé de chiffrement pour les sauvegardes
        self._fernet = Fernet(settings.ENCRYPTION_KEY.encode())
        
        # Créer les tables si elles n'existent pas
        await self._create_tables()
        
        # Démarrer la tâche de sauvegarde automatique
        self._backup_task = asyncio.create_task(self._backup_scheduler())
        
        self._initialized = True
        logger.info("Base de données initialisée avec succès")
    
    async def _create_tables(self):
        """Crée les tables si elles n'existent pas."""
        async with self._engine.begin() as conn:
            # Activer WAL pour de meilleures performances en écriture
            await conn.execute(text("PRAGMA journal_mode=WAL"))
            # Activer les clés étrangères
            await conn.execute(text("PRAGMA foreign_keys=ON"))
            # Créer les tables
            await conn.run_sync(metadata.create_all)
            
            # Créer les index pour les performances
            await self._create_indexes(conn)
            
            # Vérifier et exécuter les migrations si nécessaire
            await self._run_migrations(conn)
    
    async def _create_indexes(self, conn):
        """Crée les index pour optimiser les requêtes fréquentes."""
        indexes = [
            """
            CREATE INDEX IF NOT EXISTS idx_tasks_user_id 
            ON tasks(user_id)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_tasks_status 
            ON tasks(status)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_tasks_type 
            ON tasks(type)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_users_earnings 
            ON users(total_earnings)
            """,
        ]
        
        for index_sql in indexes:
            try:
                await conn.execute(text(index_sql))
            except Exception as e:
                logger.error(f"Erreur lors de la création de l'index: {e}")
        
        # Création des tables du système de communauté
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username VARCHAR(255),
                first_name VARCHAR(255),
                last_name VARCHAR(255),
                phone VARCHAR(50),
                email VARCHAR(255),
                country VARCHAR(2) DEFAULT 'GN',
                city VARCHAR(255),
                wallet_address VARCHAR(255),
                wallet_encrypted TEXT,
                total_earnings DECIMAL(15,2) DEFAULT 0.0,
                current_palier INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                is_premium BOOLEAN DEFAULT FALSE,
                join_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                referral_code VARCHAR(50) UNIQUE,
                referred_by INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type VARCHAR(50) NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                status VARCHAR(50) DEFAULT 'pending',
                priority INTEGER DEFAULT 1,
                earnings DECIMAL(15,2) DEFAULT 0.0,
                completion_date DATETIME,
                deadline DATETIME,
                assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (telegram_id)
            )
        """))
        
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS bounty_earnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                bounty_id VARCHAR(255) NOT NULL,
                platform VARCHAR(100) NOT NULL,
                earnings DECIMAL(15,2) NOT NULL,
                proof_url TEXT,
                status VARCHAR(50) DEFAULT 'pending',
                verified_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (telegram_id)
            )
        """))
        
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS trading_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                symbol VARCHAR(20) NOT NULL,
                side VARCHAR(10) NOT NULL,
                quantity DECIMAL(20,8) NOT NULL,
                entry_price DECIMAL(20,8) NOT NULL,
                exit_price DECIMAL(20,8),
                pnl_amount DECIMAL(15,2),
                pnl_percentage DECIMAL(10,4),
                strategy VARCHAR(100),
                notes TEXT,
                trade_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (telegram_id)
            )
        """))
        
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS investment_returns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                strategy VARCHAR(100) NOT NULL,
                initial_amount DECIMAL(15,2) NOT NULL,
                current_value DECIMAL(15,2),
                returns DECIMAL(15,2),
                return_percentage DECIMAL(10,4),
                investment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (telegram_id)
            )
        """))
        
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS concours (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                start_time DATETIME NOT NULL,
                end_time DATETIME,
                is_finished BOOLEAN DEFAULT FALSE,
                winner_user_id INTEGER,
                prize_amount DECIMAL(15,2),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (winner_user_id) REFERENCES users (telegram_id)
            )
        """))
        
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS concours_winners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username VARCHAR(255) NOT NULL,
                prize_amount DECIMAL(15,2) NOT NULL,
                concours_date DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (telegram_id)
            )
        """))
        
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS foundation_donations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount DECIMAL(15,2) NOT NULL,
                source VARCHAR(100) NOT NULL,
                transaction_hash VARCHAR(255),
                status VARCHAR(50) DEFAULT 'pending',
                processed_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (telegram_id)
            )
        """))
        
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS academy_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                course_milestone INTEGER NOT NULL,
                is_unlocked BOOLEAN DEFAULT FALSE,
                is_completed BOOLEAN DEFAULT FALSE,
                unlocked_at DATETIME,
                completed_at DATETIME,
                quiz_score INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (telegram_id)
            )
        """))
        
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS admin_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER NOT NULL,
                action_type VARCHAR(100) NOT NULL,
                target_user_id INTEGER,
                description TEXT,
                metadata JSON,
                ip_address VARCHAR(45),
                user_agent TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (admin_id) REFERENCES users (telegram_id),
                FOREIGN KEY (target_user_id) REFERENCES users (telegram_id)
            )
        """))
    
    async def _run_migrations(self, conn):
        """Exécute les migrations de base de données si nécessaire."""
        # Table pour suivre les versions de la base de données
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version INTEGER NOT NULL,
            name TEXT NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Vérifier la version actuelle
        result = await conn.execute(
            text("SELECT MAX(version) as current_version FROM _migrations")
        )
        current_version = (await result.fetchone())[0] or 0
        
        # Liste des migrations à appliquer
        migrations = [
            (1, "initial_schema", """
                -- Migration initiale (déjà gérée par SQLAlchemy)
            """),
            (2, "add_updated_at_trigger", """
                -- Ajout des déclencheurs pour updated_at
                CREATE TRIGGER IF NOT EXISTS update_users_updated_at
                AFTER UPDATE ON users
                BEGIN
                    UPDATE users SET updated_at = CURRENT_TIMESTAMP 
                    WHERE telegram_id = NEW.telegram_id;
                END;
                
                CREATE TRIGGER IF NOT EXISTS update_tasks_updated_at
                AFTER UPDATE ON tasks
                BEGIN
                    UPDATE tasks SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = NEW.id;
                END;
            """),
            (3, "add_task_indices", """
                -- Ajout d'index supplémentaires pour les requêtes fréquentes
                CREATE INDEX IF NOT EXISTS idx_tasks_user_status 
                ON tasks(user_id, status);
                
                CREATE INDEX IF NOT EXISTS idx_tasks_created_at 
                ON tasks(created_at);
            """),
        ]
        
        # Appliquer les migrations manquantes
        for version, name, sql in migrations:
            if version > current_version:
                logger.info(f"Application de la migration {version}: {name}")
                try:
                    await conn.execute(text(sql))
                    await conn.execute(
                        text("""
                            INSERT INTO _migrations (version, name) 
                            VALUES (:version, :name)
                        """),
                        {"version": version, "name": name}
                    )
                    await conn.commit()
                except Exception as e:
                    await conn.rollback()
                    logger.error(f"Échec de la migration {version}: {e}")
                    raise
    
    @asynccontextmanager
    async def session_scope(self) -> AsyncGenerator[AsyncSession, None]:
        """Fournit une portée transactionnelle autour d'une série d'opérations."""
        if not self._initialized:
            await self.initialize()
            
        session = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Erreur de base de données: {e}")
            raise
        finally:
            await session.close()
    
    # Méthodes pour les utilisateurs
    async def get_or_create_user(self, telegram_id: int) -> User:
        """Récupère un utilisateur ou le crée s'il n'existe pas."""
        async with self.session_scope() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            
            if user is None:
                user = User(telegram_id=telegram_id)
                session.add(user)
                await session.flush()
                logger.info(f"Nouvel utilisateur créé: {telegram_id}")
            
            return user
    
    async def update_user_wallet(self, telegram_id: int, wallet_encrypted: str) -> bool:
        """Met à jour le portefeuille d'un utilisateur."""
        async with self.session_scope() as session:
            result = await session.execute(
                update(User)
                .where(User.telegram_id == telegram_id)
                .values(wallet_encrypted=wallet_encrypted)
                .returning(User.telegram_id)
            )
            return result.scalar_one_or_none() is not None
    
    async def get_user_earnings(self, telegram_id: int) -> float:
        """Récupère les gains totaux d'un utilisateur."""
        async with self.session_scope() as session:
            result = await session.execute(
                select(User.total_earnings)
                .where(User.telegram_id == telegram_id)
            )
            return result.scalar_one_or_none() or 0.0
    
    # Méthodes pour les tâches
    async def add_bounty_earnings(self, user_id: int, amount_usd: float) -> bool:
        """Ajoute des gains de bounty à l'utilisateur et vérifie le palier."""
        if amount_usd <= 0:
            raise ValueError("Le montant doit être supérieur à zéro")
        
        async with self.session_scope() as session:
            # Mettre à jour les gains de l'utilisateur
            await session.execute(
                update(User)
                .where(User.telegram_id == user_id)
                .values(total_earnings=User.total_earnings + amount_usd)
            )
            
            # Vérifier et mettre à jour le palier si nécessaire
            await self._check_and_update_palier(session, user_id)
            
            # Enregistrer la tâche de bounty
            task = Task(
                user_id=user_id,
                type=TaskType.BOUNTY,
                status=TaskStatus.COMPLETED,
                earnings=amount_usd
            )
            session.add(task)
            
            return True
    
    async def _check_and_update_palier(self, session: AsyncSession, user_id: int) -> int:
        """Vérifie et met à jour le palier d'un utilisateur si nécessaire."""
        # Récupérer les informations actuelles de l'utilisateur
        result = await session.execute(
            select(User.total_earnings, User.current_palier)
            .where(User.telegram_id == user_id)
        )
        earnings, current_palier = result.one()
        
        # Déterminer le nouveau palier
        new_palier = current_palier
        if earnings >= 2000 and current_palier < 3:
            new_palier = 3  # Niveau invest
        elif earnings >= 1000 and current_palier < 2:
            new_palier = 2  # Niveau trading
        elif earnings >= 500 and current_palier < 1:
            new_palier = 1  # Niveau RWA
        
        # Mettre à jour le palier si nécessaire
        if new_palier > current_palier:
            await session.execute(
                update(User)
                .where(User.telegram_id == user_id)
                .values(current_palier=new_palier)
            )
            
            # Créer automatiquement les nouvelles tâches
            if new_palier >= 1 and current_palier < 1:
                # Ajouter la tâche RWA
                rwa_task = Task(
                    user_id=user_id,
                    type=TaskType.RWA,
                    status=TaskStatus.PENDING,
                    earnings=0.0
                )
                session.add(rwa_task)
            
            if new_palier >= 2 and current_palier < 2:
                # Ajouter la tâche Trading
                trading_task = Task(
                    user_id=user_id,
                    type=TaskType.TRADING,
                    status=TaskStatus.PENDING,
                    earnings=0.0
                )
                session.add(trading_task)
            
            if new_palier >= 3 and current_palier < 3:
                # Ajouter la tâche Invest
                invest_task = Task(
                    user_id=user_id,
                    type=TaskType.INVEST,
                    status=TaskStatus.PENDING,
                    earnings=0.0
                )
                session.add(invest_task)
            
            logger.info(f"Nouveau palier débloqué pour l'utilisateur {user_id}: {new_palier}")
        
        return new_palier
    
    async def check_and_unlock_palier(self, user_id: int) -> int:
        """Vérifie et débloque automatiquement les paliers."""
        async with self.session_scope() as session:
            return await self._check_and_update_palier(session, user_id)
    
    async def get_active_tasks(self, user_id: int) -> List[Dict[str, Any]]:
        """Récupère les tâches actives d'un utilisateur."""
        async with self.session_scope() as session:
            result = await session.execute(
                select(Task)
                .where(
                    (Task.user_id == user_id) &
                    (Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.PAUSED]))
                )
                .order_by(Task.created_at.desc())
            )
            
            tasks = result.scalars().all()
            return [{
                "id": task.id,
                "type": task.type.value,
                "status": task.status.value,
                "earnings": task.earnings,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat() if task.updated_at else None
            } for task in tasks]
    
    # Méthodes de sauvegarde
    async def _backup_scheduler(self):
        """Planifie les sauvegardes automatiques de la base de données."""
        while True:
            try:
                # Exécuter la sauvegarde à minuit chaque jour
            logger.warning("Le fichier de base de données n'existe pas pour la sauvegarde")
            return None
        
        try:
            # Créer un nom de fichier avec la date et l'heure
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(DB_BACKUP_DIR, f"chicobot_backup_{timestamp}.db")
            
            # Copier le fichier de base de données
            shutil.copy2(DB_FILE, backup_file)
            
            logger.info(f"Sauvegarde créée: {backup_file}")
            return backup_file
            
        except Exception as e:
            logger.error(f"Échec de la sauvegarde: {e}")
            return None
    
    async def _cleanup_old_backups(self):
        """Supprime les anciennes sauvegardes selon la politique de rétention."""
        try:
            backup_files = []
            for filename in os.listdir(DB_BACKUP_DIR):
                if filename.startswith("chicobot_backup_") and filename.endswith(".db"):
                    file_path = os.path.join(DB_BACKUP_DIR, filename)
                    backup_files.append((file_path, os.path.getmtime(file_path)))
            
            # Trier par date de modification (du plus ancien au plus récent)
            backup_files.sort(key=lambda x: x[1])
            
            # Supprimer les anciennes sauvegardes si nécessaire
            if len(backup_files) > DB_BACKUP_RETENTION_DAYS:
                for i in range(len(backup_files) - DB_BACKUP_RETENTION_DAYS):
                    try:
                        os.remove(backup_files[i][0])
                        logger.info(f"Ancienne sauvegarde supprimée: {backup_files[i][0]}")
                    except Exception as e:
                        logger.error(f"Échec de la suppression de {backup_files[i][0]}: {e}")
                        
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des sauvegardes: {e}")
    
    # Méthodes utilitaires
    async def get_database_stats(self) -> Dict[str, Any]:
        """Récupère des statistiques sur la base de données."""
        async with self.session_scope() as session:
            # Nombre total d'utilisateurs
            result = await session.execute(select(func.count(User.telegram_id)))
            total_users = result.scalar()
            
            # Nombre total de tâches par statut
            result = await session.execute(
                select(Task.status, func.count(Task.id))
                .group_by(Task.status)
            )
            tasks_by_status = {status.value: count for status, count in result.all()}
            
            # Gains totaux
            result = await session.execute(select(func.sum(User.total_earnings)))
            total_earnings = result.scalar() or 0.0
            
            # Taille de la base de données
            db_size = os.path.getsize(DB_FILE) if os.path.exists(DB_FILE) else 0
            
            return {
                "total_users": total_users,
                "tasks_by_status": tasks_by_status,
                "total_earnings": total_earnings,
                "database_size_mb": db_size / (1024 * 1024),
                "last_backup": await self._get_last_backup_time()
            }
    
    async def _get_last_backup_time(self) -> Optional[datetime.datetime]:
        """Récupère la date de la dernière sauvegarde."""
        try:
            backup_files = []
            for filename in os.listdir(DB_BACKUP_DIR):
                if filename.startswith("chicobot_backup_") and filename.endswith(".db"):
                    file_path = os.path.join(DB_BACKUP_DIR, filename)
                    backup_files.append((file_path, os.path.getmtime(file_path)))
            
            if not backup_files:
                return None
                
            # Trier par date de modification (du plus récent au plus ancien)
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            return datetime.datetime.fromtimestamp(backup_files[0][1])
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la dernière sauvegarde: {e}")
            return None

# Instance globale de la base de données
database = Database()

# Fonction utilitaire pour initialiser la base de données
async def init_db() -> Database:
    """Initialise la base de données et retourne l'instance."""
    await database.initialize()
    return database

# Tests unitaires
if __name__ == "__main__":
    import unittest
    import tempfile
    import shutil
    import asyncio
    
    async def record_concours_winner(self, user_id: int, username: str, prize_amount: float, concours_date: datetime):
        """Enregistre un gagnant de concours."""
        try:
            query = """
                INSERT INTO concours_winners (user_id, username, prize_amount, concours_date)
                VALUES (?, ?, ?, ?)
            """
            await self.execute_query(query, (user_id, username, prize_amount, concours_date))
            logger.info(f"🇬🇳 Gagnant concours enregistré: {username} - {prize_amount:.2f}$")
        except Exception as e:
            logger.error(f"🇬🇳 Erreur enregistrement gagnant concours: {e}")
    
    async def get_last_concours(self) -> Optional[Dict]:
        """Récupère le dernier concours."""
        try:
            query = """
                SELECT * FROM concours 
                ORDER BY start_time DESC 
                LIMIT 1
            """
            results = await self.fetch_query(query)
            return results[0] if results else None
        except Exception as e:
            logger.error(f"🇬🇳 Erreur récupération dernier concours: {e}")
            return None
    
    async def create_concours(self, group_id: int, start_time: datetime):
        """Crée un nouveau concours."""
        try:
            query = """
                INSERT INTO concours (group_id, start_time, is_finished)
                VALUES (?, ?, ?)
            """
            await self.execute_query(query, (group_id, start_time, False))
            logger.info(f"🇬🇳 Concours créé: {group_id} - {start_time}")
        except Exception as e:
            logger.error(f"🇬🇳 Erreur création concours: {e}")
    
    async def finish_concours(self, concours_id: int):
        """Marque un concours comme terminé."""
        try:
            query = """
                UPDATE concours 
                SET is_finished = ?, end_time = ?
                WHERE id = ?
            """
            await self.execute_query(query, (True, datetime.now(), concours_id))
            logger.info(f"🇬🇳 Concours {concours_id} marqué comme terminé")
        except Exception as e:
            logger.error(f"🇬🇳 Erreur terminaison concours: {e}")
    
    async def get_all_users_with_earnings(self) -> List[Dict]:
        """Récupère tous les utilisateurs avec leurs gains."""
        try:
            query = """
                SELECT 
                    u.user_id,
                    u.username,
                    u.first_name,
                    u.country,
                    u.city,
                    u.join_date,
                    COALESCE(SUM(b.earnings), 0) + COALESCE(SUM(t.pnl_amount), 0) + COALESCE(SUM(i.returns), 0) as total_earnings
                FROM users u
                LEFT JOIN bounty_earnings b ON u.user_id = b.user_id
                LEFT JOIN trading_results t ON u.user_id = t.user_id
                LEFT JOIN investment_returns i ON u.user_id = i.user_id
                GROUP BY u.user_id, u.username, u.first_name, u.country, u.city, u.join_date
                ORDER BY total_earnings DESC
            """
            results = await self.fetch_query(query)
            return results
        except Exception as e:
            logger.error(f"🇬🇳 Erreur récupération utilisateurs avec gains: {e}")
            return []
    
    async def get_active_users(self, days: int = 30) -> List[Dict]:
        """Récupère les utilisateurs actifs sur les N derniers jours."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            query = """
                SELECT DISTINCT u.user_id, u.username, u.first_name
                FROM users u
                LEFT JOIN bounty_earnings b ON u.user_id = b.user_id AND b.created_at >= ?
                LEFT JOIN trading_results t ON u.user_id = t.user_id AND t.created_at >= ?
                LEFT JOIN investment_returns i ON u.user_id = i.user_id AND i.created_at >= ?
                WHERE b.earnings IS NOT NULL OR t.pnl_amount IS NOT NULL OR i.returns IS NOT NULL
            """
            results = await self.fetch_query(query, (cutoff_date, cutoff_date, cutoff_date))
            return results
        except Exception as e:
            logger.error(f"🇬🇳 Erreur récupération utilisateurs actifs: {e}")
            return []
    
    async def get_monthly_top_users(self, limit: int = 10) -> List[Dict]:
        """Récupère le top des utilisateurs du mois."""
        try:
            start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            query = """
                SELECT 
                    u.user_id,
                    u.username,
                    COALESCE(SUM(b.earnings), 0) + COALESCE(SUM(t.pnl_amount), 0) + COALESCE(SUM(i.returns), 0) as monthly_earnings,
                    ROW_NUMBER() OVER (ORDER BY COALESCE(SUM(b.earnings), 0) + COALESCE(SUM(t.pnl_amount), 0) + COALESCE(SUM(i.returns), 0) DESC) as monthly_rank
                FROM users u
                LEFT JOIN bounty_earnings b ON u.user_id = b.user_id AND b.created_at >= ?
                LEFT JOIN trading_results t ON u.user_id = t.user_id AND t.created_at >= ?
                LEFT JOIN investment_returns i ON u.user_id = i.user_id AND i.created_at >= ?
                GROUP BY u.user_id, u.username
                ORDER BY monthly_earnings DESC
                LIMIT ?
            """
            results = await self.fetch_query(query, (start_of_month, start_of_month, start_of_month, limit))
            return results
        except Exception as e:
            logger.error(f"🇬🇳 Erreur récupération top mensuel: {e}")
            return []
    
    async def get_admin_monthly_earnings(self) -> float:
        """Calcule les gains mensuels des admins."""
        try:
            start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            admin_ids = [1, 2, 3]  # IDs des admins (Chico, Problematique, etc.)
            
            query = """
                SELECT COALESCE(SUM(b.earnings), 0) + COALESCE(SUM(t.pnl_amount), 0) + COALESCE(SUM(i.returns), 0) as total_earnings
                FROM users u
                LEFT JOIN bounty_earnings b ON u.user_id = b.user_id AND b.created_at >= ?
                LEFT JOIN trading_results t ON u.user_id = t.user_id AND t.created_at >= ?
                LEFT JOIN investment_returns i ON u.user_id = i.user_id AND i.created_at >= ?
                WHERE u.user_id IN ({})
            """.format(','.join(map(str, admin_ids)))
            
            results = await self.fetch_query(query, (start_of_month, start_of_month, start_of_month))
            return results[0]['total_earnings'] if results else 0.0
        except Exception as e:
            logger.error(f"🇬🇳 Erreur calcul gains admins: {e}")
            return 0.0
    
    async def get_user_stats(self, user_id: int) -> Optional[Dict]:
        """Récupère les statistiques complètes d'un utilisateur."""
        try:
            # Gains totaux
            total_query = """
                SELECT COALESCE(SUM(b.earnings), 0) + COALESCE(SUM(t.pnl_amount), 0) + COALESCE(SUM(i.returns), 0) as total_earnings
                FROM users u
                LEFT JOIN bounty_earnings b ON u.user_id = b.user_id
                LEFT JOIN trading_results t ON u.user_id = t.user_id
                LEFT JOIN investment_returns i ON u.user_id = i.user_id
                WHERE u.user_id = ?
            """
            total_results = await self.fetch_query(total_query, (user_id,))
            
            if not total_results or total_results[0]['total_earnings'] == 0:
                return None
            
            total_earnings = total_results[0]['total_earnings']
            
            # Classements
            global_rank_query = """
                SELECT COUNT(*) + 1 as rank
                FROM (
                    SELECT 
                        u.user_id,
                        COALESCE(SUM(b.earnings), 0) + COALESCE(SUM(t.pnl_amount), 0) + COALESCE(SUM(i.returns), 0) as earnings
                    FROM users u
                    LEFT JOIN bounty_earnings b ON u.user_id = b.user_id
                    LEFT JOIN trading_results t ON u.user_id = t.user_id
                    LEFT JOIN investment_returns i ON u.user_id = i.user_id
                    GROUP BY u.user_id
                    HAVING earnings > ?
                ) ranked
                WHERE earnings > ?
            """
            global_rank_results = await self.fetch_query(global_rank_query, (total_earnings, total_earnings))
            global_rank = global_rank_results[0]['rank'] if global_rank_results else 1
            
            # Classement Guinée
            guinea_rank_query = """
                SELECT COUNT(*) + 1 as rank
                FROM (
                    SELECT 
                        u.user_id,
                        COALESCE(SUM(b.earnings), 0) + COALESCE(SUM(t.pnl_amount), 0) + COALESCE(SUM(i.returns), 0) as earnings
                    FROM users u
                    LEFT JOIN bounty_earnings b ON u.user_id = b.user_id
                    LEFT JOIN trading_results t ON u.user_id = t.user_id
                    LEFT JOIN investment_returns i ON u.user_id = i.user_id
                    WHERE u.country = 'GN'
                    GROUP BY u.user_id
                    HAVING earnings > ?
                ) ranked
                WHERE earnings > ?
            """
            guinea_rank_results = await self.fetch_query(guinea_rank_query, (total_earnings, total_earnings))
            guinea_rank = guinea_rank_results[0]['rank'] if guinea_rank_results else 1
            
            # Gains mensuels
            start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            monthly_query = """
                SELECT COALESCE(SUM(b.earnings), 0) + COALESCE(SUM(t.pnl_amount), 0) + COALESCE(SUM(i.returns), 0) as monthly_earnings
                FROM users u
                LEFT JOIN bounty_earnings b ON u.user_id = b.user_id AND b.created_at >= ?
                LEFT JOIN trading_results t ON u.user_id = t.user_id AND t.created_at >= ?
                LEFT JOIN investment_returns i ON u.user_id = i.user_id AND i.created_at >= ?
                WHERE u.user_id = ?
            """
            monthly_results = await self.fetch_query(monthly_query, (start_of_month, start_of_month, start_of_month, user_id))
            monthly_earnings = monthly_results[0]['monthly_earnings'] if monthly_results else 0.0
            
            # Prochain palier
            milestones = [500, 1000, 2000, 5000, 10000, 25000, 50000, 100000]
            next_milestone = None
            for milestone in milestones:
                if total_earnings < milestone:
                    next_milestone = milestone
                    break
            
            return {
                'user_id': user_id,
                'total_earnings': total_earnings,
                'global_rank': global_rank,
                'guinea_rank': guinea_rank,
                'monthly_earnings': monthly_earnings,
                'next_milestone': next_milestone or milestones[-1] + 50000
            }
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur stats utilisateur {user_id}: {e}")
            return None
    
    async def get_user_total_earnings(self, user_id: int) -> float:
        """Calcule les gains totaux d'un utilisateur."""
        try:
            query = """
                SELECT COALESCE(SUM(b.earnings), 0) + COALESCE(SUM(t.pnl_amount), 0) + COALESCE(SUM(i.returns), 0) as total_earnings
                FROM users u
                LEFT JOIN bounty_earnings b ON u.user_id = b.user_id
                LEFT JOIN trading_results t ON u.user_id = t.user_id
                LEFT JOIN investment_returns i ON u.user_id = i.user_id
                WHERE u.user_id = ?
            """
            results = await self.fetch_query(query, (user_id,))
            return results[0]['total_earnings'] if results else 0.0
        except Exception as e:
            logger.error(f"🇬🇳 Erreur calcul gains utilisateur {user_id}: {e}")
            return 0.0
    
    class TestDatabase(unittest.IsolatedAsyncioTestCase):
        """Tests unitaires pour le module de base de données."""
        
        async def asyncSetUp(self):
            """Configure l'environnement de test."""
            # Créer un fichier de base de données temporaire
            self.temp_dir = tempfile.mkdtemp()
            self.db_path = os.path.join(self.temp_dir, "test.db")
            
            # Configurer la base de données de test
            global DATABASE_URL
            DATABASE_URL = f"sqlite+aiosqlite:///{self.db_path}"
            
            # Initialiser la base de données
            self.db = Database()
            await self.db.initialize()
            
            # Créer un utilisateur de test
            self.test_user_id = 123456789
            self.test_user = await self.db.get_or_create_user(self.test_user_id)
        
        async def asyncTearDown(self):
            """Nettoie après les tests."""
            # Fermer la connexion à la base de données
            if hasattr(self, 'db') and self.db._engine:
                await self.db._engine.dispose()
            
            # Supprimer le répertoire temporaire
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        
        async def test_create_user(self):
            """Teste la création d'un utilisateur."""
            user_id = 987654321
            user = await self.db.get_or_create_user(user_id)
            
            self.assertIsNotNone(user)
            self.assertEqual(user.telegram_id, user_id)
            self.assertEqual(user.total_earnings, 0.0)
            self.assertEqual(user.current_palier, 0)
        
        async def test_add_bounty_earnings(self):
            """Teste l'ajout de gains de bounty."""
            # Ajouter 300$ de gains
            await self.db.add_bounty_earnings(self.test_user_id, 300.0)
            
            # Vérifier que les gains ont été ajoutés
            earnings = await self.db.get_user_earnings(self.test_user_id)
            self.assertEqual(earnings, 300.0)
            
            # Vérifier que le palier n'a pas changé (seuil à 500$)
            user = await self.db.get_or_create_user(self.test_user_id)
            self.assertEqual(user.current_palier, 0)
            
            # Ajouter 300$ supplémentaires (total 600$)
            await self.db.add_bounty_earnings(self.test_user_id, 300.0)
            
            # Vérifier que le palier a été mis à jour à 1 (RWA débloqué)
            user = await self.db.get_or_create_user(self.test_user_id)
            self.assertEqual(user.current_palier, 1)
            
            # Vérifier que la tâche RWA a été créée
            tasks = await self.db.get_active_tasks(self.test_user_id)
            self.assertTrue(any(task["type"] == "rwa" for task in tasks))
        
        async def test_check_and_unlock_palier(self):
            """Teste le déblocage des paliers."""
            # Mettre à jour manuellement les gains
            async with self.db.session_scope() as session:
                await session.execute(
                    update(User)
                    .where(User.telegram_id == self.test_user_id)
                    .values(total_earnings=1500.0)
                )
            
            # Vérifier et débloquer les paliers
            new_palier = await self.db.check_and_unlock_palier(self.test_user_id)
            
            # Vérifier que le palier a été mis à jour à 2 (trading débloqué)
            self.assertEqual(new_palier, 2)
            
            # Vérifier que les tâches RWA et Trading ont été créées
            tasks = await self.db.get_active_tasks(self.test_user_id)
            task_types = {task["type"] for task in tasks}
            self.assertIn("rwa", task_types)
            self.assertIn("trading", task_types)
        
        async def test_get_active_tasks(self):
            """Teste la récupération des tâches actives."""
            # Créer quelques tâches
            async with self.db.session_scope() as session:
                tasks = [
                    Task(
                        user_id=self.test_user_id,
                        type=TaskType.BOUNTY,
                        status=TaskStatus.COMPLETED,
                        earnings=100.0
                    ),
                    Task(
                        user_id=self.test_user_id,
                        type=TaskType.RWA,
                        status=TaskStatus.IN_PROGRESS,
                        earnings=0.0
                    ),
                    Task(
                        user_id=self.test_user_id,
                        type=TaskType.TRADING,
                        status=TaskStatus.PAUSED,
                        earnings=0.0
                    )
                ]
                session.add_all(tasks)
            
            # Récupérer les tâches actives (doit exclure la tâche COMPLETED)
            active_tasks = await self.db.get_active_tasks(self.test_user_id)
            
            # Vérifier que seules les tâches actives sont retournées
            self.assertEqual(len(active_tasks), 2)
            self.assertTrue(all(task["status"] != "completed" for task in active_tasks))
        
        async def test_backup_creation(self):
            """Teste la création d'une sauvegarde."""
            # Créer une sauvegarde
            backup_file = await self.db.create_backup()
            
            # Vérifier que le fichier de sauvegarde existe
            self.assertTrue(os.path.exists(backup_file))
            
            # Nettoyer
            if os.path.exists(backup_file):
                os.remove(backup_file)
    
    # Exécuter les tests
    if __name__ == "__main__":
        unittest.main()
