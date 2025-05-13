import os
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from datetime import datetime, timedelta
import socket
import ipaddress

def generate_ssl_cert():
    """生成自签名SSL证书"""
    try:
        # 获取本机IP和主机名
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        # 如果已经存在证书，则不重新生成
        if os.path.exists('cert.pem') and os.path.exists('key.pem'):
            print("证书已存在，无需重新生成")
            return True
        
        # 生成私钥
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # 创建自签名证书
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, u"CN"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"China"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, u"Local"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"晚自习签到系统"),
            x509.NameAttribute(NameOID.COMMON_NAME, hostname),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            # 证书有效期为10年
            datetime.utcnow() + timedelta(days=3650)
        ).add_extension(
            x509.SubjectAlternativeName([
                # 允许通过IP访问
                x509.IPAddress(ipaddress.IPv4Address(local_ip)),
                # 允许通过localhost访问
                x509.IPAddress(ipaddress.IPv4Address('127.0.0.1')),
                # 允许通过主机名访问
                x509.DNSName(hostname),
                x509.DNSName('localhost')
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # 保存私钥
        with open("key.pem", "wb") as key_file:
            key_file.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # 保存证书
        with open("cert.pem", "wb") as cert_file:
            cert_file.write(cert.public_bytes(serialization.Encoding.PEM))
        
        print("SSL证书生成成功")
        return True
    
    except Exception as e:
        print(f"生成SSL证书失败: {str(e)}")
        return False

if __name__ == "__main__":
    generate_ssl_cert() 