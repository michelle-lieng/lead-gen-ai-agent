"""
Chat service: each project's single, continuous agent conversation
"""

from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional, Tuple
import logging

from ..models.tables import ChatEntry, Project
from ..models.schemas import ChatEntryCreate
from .database_service import db_service
from ..exceptions import DatabaseFailureError, ProjectNotFoundError

logger = logging.getLogger(__name__)


class ChatService:
    """Service for reading and appending a project's conversation"""

    def get_history(
        self, project_id: int, before: Optional[int] = None, limit: int = 200
    ) -> Tuple[List[ChatEntry], bool]:
        """Return up to `limit` entries older than `before` (or the newest ones),
        oldest first, plus whether even older entries exist."""
        try:
            with db_service.get_session() as session:
                self._require_project(session, project_id)
                query = session.query(ChatEntry).filter(
                    ChatEntry.project_id == project_id
                )
                if before is not None:
                    query = query.filter(ChatEntry.id < before)
                # Fetch one extra to learn whether there is an older page
                newest_first = query.order_by(ChatEntry.id.desc()).limit(limit + 1).all()
                has_more = len(newest_first) > limit
                return list(reversed(newest_first[:limit])), has_more
        except SQLAlchemyError as e:
            logger.exception(f"❌ Error reading chat for project {project_id}")
            raise DatabaseFailureError(
                f"Failed to read chat for project {project_id}"
            ) from e

    def append(
        self, project_id: int, entries: List[ChatEntryCreate]
    ) -> List[ChatEntry]:
        """Append entries in order, returning them as saved"""
        try:
            with db_service.get_session() as session:
                self._require_project(session, project_id)
                rows = [
                    ChatEntry(
                        project_id=project_id,
                        role=entry.role,
                        kind=entry.kind,
                        text=entry.text,
                        payload=entry.payload,
                    )
                    for entry in entries
                ]
                # Added one at a time so ids follow the order they happened in
                for row in rows:
                    session.add(row)
                    session.flush()
                session.commit()
                for row in rows:
                    session.refresh(row)
                return rows
        except SQLAlchemyError as e:
            logger.exception(f"❌ Error appending chat for project {project_id}")
            raise DatabaseFailureError(
                f"Failed to save chat for project {project_id}"
            ) from e

    @staticmethod
    def _require_project(session, project_id: int) -> None:
        exists = session.query(Project.id).filter(Project.id == project_id).first()
        if not exists:
            raise ProjectNotFoundError(project_id)


# Global chat service instance
chat_service = ChatService()
