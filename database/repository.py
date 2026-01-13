"""Repository layer for database operations."""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import PendingRegistration as PendingRegistrationModel
from database.models import Player as PlayerModel
from models.player import PendingRegistration, Player

logger = logging.getLogger(__name__)


class PlayerRepository:
    """Repository for player-related database operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: AsyncSession instance
        """
        self.session = session

    async def add_player(self, player: Player) -> Player:
        """
        Add a new player to the database.

        Args:
            player: Player dataclass instance

        Returns:
            Player dataclass with database ID

        Raises:
            IntegrityError: If player with telegram_id already exists
        """
        try:
            db_player = PlayerModel(
                telegram_id=player.telegram_id,
                username=player.username,
                nickname=player.nickname,
                screenshot_path=player.screenshot_path,
                status=player.status,
                added_by=player.added_by,
                notes=player.notes,
            )
            self.session.add(db_player)
            await self.session.flush()
            await self.session.refresh(db_player)

            logger.info(f"Added player: {player.username} (telegram_id={player.telegram_id})")
            return self._to_dataclass(db_player)
        except IntegrityError:
            logger.error(f"Player already exists: {player.telegram_id}")
            raise
        except SQLAlchemyError as e:
            logger.error(f"Failed to add player: {e}")
            raise

    async def get_player(self, telegram_id: int) -> Optional[Player]:
        """
        Get player by telegram ID.

        Args:
            telegram_id: Telegram user ID

        Returns:
            Player dataclass or None if not found
        """
        try:
            stmt = select(PlayerModel).where(PlayerModel.telegram_id == telegram_id)
            result = await self.session.execute(stmt)
            db_player = result.scalar_one_or_none()

            if db_player:
                return self._to_dataclass(db_player)
            return None
        except SQLAlchemyError as e:
            logger.error(f"Failed to get player {telegram_id}: {e}")
            raise

    async def check_player_exists(self, telegram_id: int) -> bool:
        """
        Check if player exists in database.

        Args:
            telegram_id: Telegram user ID

        Returns:
            True if player exists, False otherwise
        """
        player = await self.get_player(telegram_id)
        return player is not None

    async def get_all_players(self) -> list[Player]:
        """
        Get all players from database.

        Returns:
            List of Player dataclasses
        """
        try:
            stmt = select(PlayerModel).order_by(PlayerModel.created_at.desc())
            result = await self.session.execute(stmt)
            db_players = result.scalars().all()

            return [self._to_dataclass(p) for p in db_players]
        except SQLAlchemyError as e:
            logger.error(f"Failed to get all players: {e}")
            raise

    async def update_player_status(self, telegram_id: int, status: str) -> bool:
        """
        Update player status.

        Args:
            telegram_id: Telegram user ID
            status: New status

        Returns:
            True if updated, False if player not found
        """
        try:
            stmt = select(PlayerModel).where(PlayerModel.telegram_id == telegram_id)
            result = await self.session.execute(stmt)
            db_player = result.scalar_one_or_none()

            if db_player:
                db_player.status = status
                await self.session.flush()
                logger.info(f"Updated player {telegram_id} status to {status}")
                return True
            return False
        except SQLAlchemyError as e:
            logger.error(f"Failed to update player {telegram_id} status: {e}")
            raise

    async def exclude_player(self, telegram_id: int, reason: str, excluded_by: str) -> bool:
        """
        Exclude player from the clan.

        Args:
            telegram_id: Telegram user ID
            reason: Reason for exclusion
            excluded_by: Who excluded the player

        Returns:
            True if excluded, False if player not found
        """
        try:
            stmt = select(PlayerModel).where(PlayerModel.telegram_id == telegram_id)
            result = await self.session.execute(stmt)
            db_player = result.scalar_one_or_none()

            if db_player:
                from datetime import datetime

                db_player.status = "Отчислен"
                db_player.exclusion_date = datetime.now()
                db_player.exclusion_reason = reason
                db_player.excluded_by = excluded_by
                await self.session.flush()
                logger.info(f"Excluded player {telegram_id}: {reason}")
                return True
            return False
        except SQLAlchemyError as e:
            logger.error(f"Failed to exclude player {telegram_id}: {e}")
            raise

    async def get_excluded_players(self) -> list[Player]:
        """
        Get all excluded players from database.

        Returns:
            List of Player dataclasses with status "Отчислен"
        """
        try:
            stmt = (
                select(PlayerModel)
                .where(PlayerModel.status == "Отчислен")
                .order_by(PlayerModel.exclusion_date.desc())
            )
            result = await self.session.execute(stmt)
            db_players = result.scalars().all()

            return [self._to_dataclass(p) for p in db_players]
        except SQLAlchemyError as e:
            logger.error(f"Failed to get excluded players: {e}")
            raise

    async def save_pending(self, pending: PendingRegistration) -> PendingRegistration:
        """
        Save a pending registration request.

        Args:
            pending: PendingRegistration dataclass instance

        Returns:
            PendingRegistration dataclass with database ID

        Raises:
            IntegrityError: If pending registration already exists
        """
        try:
            db_pending = PendingRegistrationModel(
                telegram_id=pending.telegram_id,
                username=pending.username,
                nickname=pending.nickname,
                screenshot_path=pending.screenshot_path,
            )
            self.session.add(db_pending)
            await self.session.flush()
            await self.session.refresh(db_pending)

            logger.info(
                f"Saved pending registration: {pending.username} (telegram_id={pending.telegram_id})"
            )
            return self._pending_to_dataclass(db_pending)
        except IntegrityError:
            logger.error(f"Pending registration already exists: {pending.telegram_id}")
            raise
        except SQLAlchemyError as e:
            logger.error(f"Failed to save pending registration: {e}")
            raise

    async def get_pending(self, telegram_id: int) -> Optional[PendingRegistration]:
        """
        Get pending registration by telegram ID.

        Args:
            telegram_id: Telegram user ID

        Returns:
            PendingRegistration dataclass or None if not found
        """
        try:
            stmt = select(PendingRegistrationModel).where(
                PendingRegistrationModel.telegram_id == telegram_id
            )
            result = await self.session.execute(stmt)
            db_pending = result.scalar_one_or_none()

            if db_pending:
                return self._pending_to_dataclass(db_pending)
            return None
        except SQLAlchemyError as e:
            logger.error(f"Failed to get pending registration {telegram_id}: {e}")
            raise

    async def get_pending_by_username(self, username: str) -> Optional[PendingRegistration]:
        """
        Get pending registration by username.

        Args:
            username: Telegram username

        Returns:
            PendingRegistration dataclass or None if not found
        """
        try:
            stmt = select(PendingRegistrationModel).where(
                PendingRegistrationModel.username == username
            )
            result = await self.session.execute(stmt)
            db_pending = result.scalar_one_or_none()

            if db_pending:
                return self._pending_to_dataclass(db_pending)
            return None
        except SQLAlchemyError as e:
            logger.error(f"Failed to get pending registration by username {username}: {e}")
            raise

    async def remove_pending(self, telegram_id: int) -> bool:
        """
        Remove pending registration.

        Args:
            telegram_id: Telegram user ID

        Returns:
            True if removed, False if not found
        """
        try:
            stmt = select(PendingRegistrationModel).where(
                PendingRegistrationModel.telegram_id == telegram_id
            )
            result = await self.session.execute(stmt)
            db_pending = result.scalar_one_or_none()

            if db_pending:
                await self.session.delete(db_pending)
                await self.session.flush()
                logger.info(f"Removed pending registration: telegram_id={telegram_id}")
                return True
            return False
        except SQLAlchemyError as e:
            logger.error(f"Failed to remove pending registration {telegram_id}: {e}")
            raise

    async def get_all_pending(self) -> list[PendingRegistration]:
        """
        Get all pending registrations.

        Returns:
            List of PendingRegistration dataclasses
        """
        try:
            stmt = select(PendingRegistrationModel).order_by(
                PendingRegistrationModel.created_at.desc()
            )
            result = await self.session.execute(stmt)
            db_pendings = result.scalars().all()

            return [self._pending_to_dataclass(p) for p in db_pendings]
        except SQLAlchemyError as e:
            logger.error(f"Failed to get all pending registrations: {e}")
            raise

    @staticmethod
    def _to_dataclass(db_player: PlayerModel) -> Player:
        """Convert SQLAlchemy model to dataclass."""
        return Player(
            telegram_id=db_player.telegram_id,
            username=db_player.username,
            nickname=db_player.nickname,
            screenshot_path=db_player.screenshot_path,
            registration_date=db_player.registration_date.strftime("%Y-%m-%d"),
            status=db_player.status,
            added_by=db_player.added_by,
            exclusion_date=db_player.exclusion_date.strftime("%Y-%m-%d %H:%M:%S")
            if db_player.exclusion_date
            else None,
            exclusion_reason=db_player.exclusion_reason,
            excluded_by=db_player.excluded_by,
            notes=db_player.notes or "",
        )

    @staticmethod
    def _pending_to_dataclass(db_pending: PendingRegistrationModel) -> PendingRegistration:
        """Convert SQLAlchemy model to dataclass."""
        return PendingRegistration(
            telegram_id=db_pending.telegram_id,
            username=db_pending.username,
            nickname=db_pending.nickname,
            screenshot_path=db_pending.screenshot_path,
            timestamp=db_pending.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        )
