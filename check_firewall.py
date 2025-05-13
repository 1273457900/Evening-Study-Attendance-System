import os
import subprocess
import sys

def check_windows_firewall():
    """检查Windows防火墙状态并尝试创建规则允许Flask应用通过"""
    print("正在检查Windows防火墙状态...")
    
    # 检查防火墙状态
    try:
        # 尝试不同的编码
        encodings = ['gbk', 'utf-8', 'cp936', 'cp1252']
        result = None
        
        for encoding in encodings:
            try:
                result = subprocess.check_output("netsh advfirewall show allprofiles", shell=True).decode(encoding)
                break
            except UnicodeDecodeError:
                continue
                
        if not result:
            raise Exception("无法解码命令输出，请手动检查防火墙状态")
            
        # 更简单的检查方式：检查是否有"状态"后跟"关闭"
        domain_off = "状态                               域" in result and "关闭" in result.split("状态                               域")[1].split("\n")[0]
        private_off = "状态                               专用" in result and "关闭" in result.split("状态                               专用")[1].split("\n")[0]
        public_off = "状态                               公用" in result and "关闭" in result.split("状态                               公用")[1].split("\n")[0]
        
        # 英文系统的检查
        if "State" in result:
            domain_off = "State                                 Domain" in result and "OFF" in result.split("State                                 Domain")[1].split("\n")[0].upper()
            private_off = "State                                 Private" in result and "OFF" in result.split("State                                 Private")[1].split("\n")[0].upper()
            public_off = "State                                 Public" in result and "OFF" in result.split("State                                 Public")[1].split("\n")[0].upper()
        
        status = {
            "Domain/域": "关闭" if domain_off else "开启",
            "Private/专用": "关闭" if private_off else "开启",
            "Public/公用": "关闭" if public_off else "开启"
        }
        
        print("\n防火墙状态:")
        for profile, state in status.items():
            print(f"  {profile}网络: {state}")
            
        if all(state == "关闭" for state in status.values()):
            print("\n所有防火墙配置文件都已关闭，应该不会阻止Flask应用程序。")
            return True
            
        print("\n如果您无法从手机访问应用，可能是防火墙阻止了连接。")
        print("您可以尝试以下操作之一:")
        print("1. 临时关闭防火墙(不建议在公共网络中使用)")
        print("   管理员命令: netsh advfirewall set allprofiles state off")
        print("2. 为Python和Flask添加防火墙规则")
        
        # 是否要添加防火墙规则
        print("\n注意：添加防火墙规则需要管理员权限。如果当前不是管理员权限运行，请手动以管理员身份运行。")
        return False
        
    except Exception as e:
        print(f"检查防火墙时出错: {e}")
        print("\n建议手动检查防火墙设置，确保Python和端口5000没有被阻止")
        print("您可以在Windows Defender防火墙中添加入站规则，允许Python.exe和端口5000")
        return False

if __name__ == "__main__":
    if os.name == 'nt':  # Windows
        check_windows_firewall()
        
        print("\n=== 网络连接检查 ===")
        print("请确保您的手机和电脑在同一Wi-Fi网络下。以下是可能的IP地址:")
        try:
            # 使用ipconfig获取所有IP地址
            result = subprocess.check_output("ipconfig", shell=True).decode('gbk', errors='ignore')
            for line in result.split('\n'):
                if "IPv4" in line and "地址" in line:
                    print(f"  {line.strip()}")
            print("在手机浏览器中访问: https://[上面的IP地址]:5000")
        except:
            print("无法获取IP地址")
    else:
        print("此脚本仅支持Windows系统。") 