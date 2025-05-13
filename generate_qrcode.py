import socket
import subprocess
import os
import qrcode
from PIL import Image, ImageDraw, ImageFont

def get_ip_addresses():
    """获取本机所有可能的IP地址"""
    ip_list = []
    try:
        # 主IP地址
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            ip_list.append(ip)
        except:
            pass
        finally:
            s.close()
        
        # 使用ipconfig获取所有IP
        if os.name == 'nt':
            try:
                result = subprocess.check_output("ipconfig", shell=True).decode('gbk', errors='ignore')
                for line in result.split('\n'):
                    if "IPv4" in line and "地址" in line:
                        parts = line.split(":")
                        if len(parts) >= 2:
                            ip = parts[1].strip()
                            if ip not in ip_list and not ip.startswith("127."):
                                ip_list.append(ip)
            except:
                pass
    except:
        pass
    
    return ip_list

def generate_qrcode():
    """为所有IP地址生成HTTPS URL的二维码"""
    try:
        # 确保有qrcode库
        import qrcode
    except ImportError:
        print("缺少qrcode库，正在安装...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "qrcode[pil]"])
            print("qrcode库安装成功!")
            import qrcode
        except:
            print("安装qrcode库失败，请手动安装：pip install qrcode[pil]")
            return
    
    ip_list = get_ip_addresses()
    if not ip_list:
        print("无法获取IP地址")
        return
    
    print("\n为以下URL生成二维码:")
    
    for i, ip in enumerate(ip_list, 1):
        url = f"https://{ip}:5000"
        print(f"{i}. {url}")
        
        # 生成二维码
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 添加URL文本
        img_with_text = Image.new('RGB', (img.size[0], img.size[1] + 30), color='white')
        img_with_text.paste(img, (0, 0))
        
        try:
            # 尝试添加文本
            draw = ImageDraw.Draw(img_with_text)
            try:
                # 尝试使用系统字体
                font = ImageFont.truetype("arial.ttf", 15)
            except:
                # 如果没有可用字体，使用默认字体
                font = ImageFont.load_default()
                
            text_width = draw.textlength(url, font=font)
            position = ((img.size[0] - text_width) // 2, img.size[1] + 5)
            draw.text(position, url, fill="black", font=font)
        except:
            # 如果添加文本失败，直接使用原始二维码
            img_with_text = img
        
        # 保存二维码
        filename = f"qrcode_{i}.png"
        img_with_text.save(filename)
        print(f"二维码已保存为: {filename}")
    
    print("\n请使用手机扫描二维码访问应用")
    print("注意：手机会显示安全警告，请点击'高级'然后选择'继续前往'")

if __name__ == '__main__':
    # 检查是否安装了qrcode库
    try:
        import qrcode
    except ImportError:
        print("缺少qrcode库，请运行: pip install qrcode[pil]")
        import sys
        sys.exit(1)
        
    generate_qrcode() 