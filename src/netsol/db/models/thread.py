import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from netsol.db.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from netsol.db.models.user import User
    from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from netsol.db.models.user import User
    from netsol.db.models.message import ChatMessage


class ChatThread(Base):
    __tablename__ = "chat_threads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    owner: Mapped["User"] = relationship(
        back_populates="threads",
    )
    
    messages: Mapped[list["ChatMessage"]] = relationship(
    back_populates="thread",
    cascade="all, delete-orphan",
    passive_deletes=True,
    )

    __table_args__ = (
        Index(
            "ix_chat_threads_owner_updated_id",
            "owner_id",
            "updated_at",
            "id",
        ),
    )