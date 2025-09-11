from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class CryptoHandler:
    def __init__(self, encryption_key: str, salt_key: str):
        """
        암호화 키를 받아 Fernet 인스턴스 생성 (키 길이 : 32byte)
        """
        if len(encryption_key.encode()) != 32 :
            # 키 길이가 32byte가 아닐 경우 해시를 통해 32바이트로 변환
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt= salt_key,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(encryption_key.encode()))
        else:
            key = base64.urlsafe_b64encode(encryption_key.encode())
            
        self.fernet = Fernet(key)

    def encrypt(self, data: str) -> str:
        """
        문자열을 암호화하고 base64 인코딩된 문자열 반환
        """
        encrypted = self.fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """
        base64 디코딩 후 복호화하여 원본 문자열 반환
        """
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt data: {e}")