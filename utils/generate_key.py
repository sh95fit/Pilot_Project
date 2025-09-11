import secrets

key_str = secrets.token_urlsafe(32)  # 43~44자 문자열
key_bytes = key_str.encode()[:32]     # 바이트로 32바이트 자름
print(len(key_bytes))
print(key_bytes)

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# 1. Private Key 생성
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048  # 2048 또는 4096 비트
)

# 2. Private Key PEM 형식으로 저장
private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.TraditionalOpenSSL,
    encryption_algorithm=serialization.NoEncryption()  # 필요 시 암호화 가능
)

with open("private_key.pem", "wb") as f:
    f.write(private_pem)

# 3. Public Key 추출
public_key = private_key.public_key()
public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

with open("public_key.pem", "wb") as f:
    f.write(public_pem)

print("Private/Public Key PEM 파일 생성 완료")