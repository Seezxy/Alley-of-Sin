"""
存档加密模块
使用 Fernet (AES-128-GCM + HMAC) 加密用户数据
"""
import os
import json
import uuid
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken


def _is_dev_mode() -> bool:
    """检测是否为开发者模式"""
    if os.environ.get("GAME_DEV_MODE") == "1":
        return True
    if os.path.exists("data/.dev_mode"):
        return True
    # 也检查 AppData 目录
    try:
        from game.resource_utils import get_user_data_path
        if os.path.exists(get_user_data_path(".dev_mode")):
            return True
    except Exception:
        pass
    return False


def _get_key() -> bytes:
    """
    派生加密密钥
    使用硬编码种子 + 机器MAC地址，阻止跨机器复制存档
    """
    seed = b"evil_alley_game_save_v1_salt!" + uuid.getnode().to_bytes(6, "big")
    digest = hashlib.sha256(seed).digest()
    return base64.urlsafe_b64encode(digest)


def _get_fernet() -> Fernet:
    return Fernet(_get_key())


def encrypt_data(data: dict) -> bytes:
    """将字典加密为二进制数据"""
    fernet = _get_fernet()
    json_bytes = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return fernet.encrypt(json_bytes)


def decrypt_data(encrypted: bytes) -> dict:
    """解密二进制数据为字典，失败抛出 InvalidToken"""
    fernet = _get_fernet()
    json_bytes = fernet.decrypt(encrypted)
    return json.loads(json_bytes.decode("utf-8"))


def is_encrypted_file(filepath: str) -> bool:
    """检查文件是否为 Fernet 加密格式（以 gAAAAA 开头）"""
    if not os.path.exists(filepath):
        return False
    try:
        with open(filepath, "rb") as f:
            header = f.read(20)
        return header.startswith(b"gAAAAA")
    except IOError:
        return False


def migrate_plaintext_to_encrypted(plain_path: str, enc_path: str) -> bool:
    """
    将旧明文 JSON 文件迁移为加密格式
    成功返回 True，失败返回 False
    """
    try:
        with open(plain_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        encrypted = encrypt_data(data)
        os.makedirs(os.path.dirname(enc_path), exist_ok=True)
        with open(enc_path, "wb") as f:
            f.write(encrypted)
        os.remove(plain_path)
        print(f"已迁移旧存档: {plain_path} -> {enc_path}")
        return True
    except Exception as e:
        print(f"迁移旧存档失败: {e}")
        return False
