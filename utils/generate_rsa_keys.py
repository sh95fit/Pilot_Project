from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import os


def generate_rsa_key_pair():
    """RSA 키 페어 생성"""
    # private key 생성
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    # public key 추출
    public_key = private_key.public_key()
    
    # private key를 PEM 형식으로 직렬화
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # public key를 PEM 형식으로 직렬화
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return private_pem, public_pem


def save_keys_to_files():
    """키를 파일로 저장"""
    private_pem, public_pem = generate_rsa_key_pair()
    
    # config 디렉토리가 없으면 생성
    config_dir = "../config"
    os.makedirs(config_dir, exist_ok=True)
    
    # private key 저장
    with open(f"{config_dir}/private_key.pem", "wb") as f:
        f.write(private_pem)
    
    # public key 저장
    with open(f"{config_dir}/public_key.pem", "wb") as f:
        f.write(public_pem)
    
    print("✅ RSA key pair generated successfully!")
    print(f"📁 Private key saved to: {config_dir}/private_key.pem")
    print(f"📁 Public key saved to: {config_dir}/public_key.pem")


def print_keys_for_env():
    """환경변수용 키 출력"""
    private_pem, public_pem = generate_rsa_key_pair()
    
    print("=" * 60)
    print("🔑 Private Key for JWT_PRIVATE_KEY environment variable:")
    print("=" * 60)
    print(private_pem.decode('utf-8'))
    
    print("=" * 60)
    print("🔓 Public Key for JWT_PUBLIC_KEY environment variable:")
    print("=" * 60)
    print(public_pem.decode('utf-8'))
    
    print("=" * 60)
    print("📝 Add these to your environment files:")
    print("config/dev.env and config/main.env")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--env":
        print_keys_for_env()
    else:
        save_keys_to_files()