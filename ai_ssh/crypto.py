from cryptography.fernet import Fernet, InvalidToken

from .config import CREDENTIALS_ENCRYPT_KEY


def _get_fernet() -> Fernet:
    return Fernet(CREDENTIALS_ENCRYPT_KEY.encode())


def encrypt_value(value: str | None) -> str | None:
    if value is None:
        return None
    fernet = _get_fernet()
    return fernet.encrypt(value.encode()).decode()


def decrypt_value(value: str | None) -> str | None:
    if value is None:
        return None
    fernet = _get_fernet()
    try:
        return fernet.decrypt(value.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Invalid encryption key or corrupted credential") from exc
