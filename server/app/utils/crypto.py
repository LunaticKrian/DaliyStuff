"""用户敏感配置（API Key 等）的加密 / 解密 / 掩码。

Fernet = AES128-CBC + HMAC_SHA256。主密钥优先取 ``ENCRYPTION_KEY``（标准 base64 32 字节，
或任意字符串经 SHA256 规整）；未配置时从 ``SECRET_KEY`` 经 PBKDF2HMAC 派生（固定盐，可复现，
仅适合单机自部署——生产应显式设置 ``ENCRYPTION_KEY``）。

⚠️ 轮换密钥后，已加密的旧密文将无法解密（decrypt 返回空串），用户需重新填写 API Key。
"""
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.config import settings

_PBKDF_SALT = b"pixelpack::fernet::v1"  # 固定盐：同一 SECRET_KEY 可复现同一密钥


def _load_fernet() -> Fernet:
    raw = (settings.ENCRYPTION_KEY or "").strip()
    if raw:
        try:
            return Fernet(raw.encode())  # 标准 Fernet 密钥（base64 urlsafe 32 字节）
        except (ValueError, TypeError):
            # 用户给的是任意口令：SHA256 规整成 32 字节再 base64
            key = base64.urlsafe_b64encode(hashlib.sha256(raw.encode()).digest())
            return Fernet(key)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(), length=32, salt=_PBKDF_SALT, iterations=200_000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(settings.SECRET_KEY.encode()))
    return Fernet(key)


_fernet = _load_fernet()  # 模块级单例


def encrypt(plain: str) -> str:
    """加密明文 → Fernet token 字符串；空值原样返回空串。"""
    if not plain:
        return ""
    return _fernet.encrypt(plain.encode("utf-8")).decode("ascii")


def decrypt(token: str) -> str:
    """解密 Fernet token → 明文；空串或无法解密均返回空串（不抛异常）。"""
    if not token:
        return ""
    try:
        return _fernet.decrypt(token.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError):
        return ""


def mask_key(plain: str) -> str:
    """sk-xxxx...xxxx → ``sk-****<末4位>``；长度不足 8 全部掩码。"""
    if not plain:
        return ""
    s = plain.strip()
    if len(s) <= 8:
        return "*" * len(s)
    return f"{s[:3]}****{s[-4:]}"
