from sqlalchemy import Column, Integer, BigInteger, String, Float, Date, ForeignKey, Boolean, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class User(Base):
    __tablename__ = 'user'

    tg_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    fio: Mapped[str]
    username: Mapped[str]
    money: Mapped[float] = mapped_column(default=0)
    lvl: Mapped[int] = mapped_column(default=1)
    is_admin: Mapped[bool] = mapped_column(default=False)
    is_banned: Mapped[bool] = mapped_column(default=False)
    last_upgrade: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    wallet: Mapped[str] = mapped_column(nullable=True)
    is_get_nft: Mapped[bool] = mapped_column(default=False)
    nft_request: Mapped[bool] = mapped_column(default=False)
    nft_link: Mapped[str] = mapped_column(nullable=True)
    nft_token: Mapped[str] = mapped_column(nullable=True)
