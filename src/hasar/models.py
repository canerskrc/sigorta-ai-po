"""SQLAlchemy ORM modelleri."""

from datetime import date, datetime
from sqlalchemy import Date, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class HasarIhbar(Base):
    """Hasar ihbar kaydı."""

    __tablename__ = "hasar_ihbar"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tc_kimlik: Mapped[str] = mapped_column(String(11), nullable=False, index=True)
    hasar_tarihi: Mapped[date] = mapped_column(Date, nullable=False)
    aciklama: Mapped[str] = mapped_column(Text, nullable=False)
    notion_page_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    olusturulma_zamani: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
