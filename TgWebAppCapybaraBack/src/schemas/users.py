from pydantic import BaseModel


class UserRegisterSchema(BaseModel):
    """Схема данных для регистрации пользователя."""

    tg_id: int
    fio: str
    username: str


class UserWalletSchema(BaseModel):

    tg_id: int
    wallet: str


class UserAcceptNft(BaseModel):

    tg_id: int
    link: str
    token: str
