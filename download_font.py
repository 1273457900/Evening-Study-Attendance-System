import os
import requests

# 确保目录存在
font_dir = os.path.join('static', 'fonts')
os.makedirs(font_dir, exist_ok=True)

# 思源黑体下载链接（开源字体）
font_url = "https://github.com/adobe-fonts/source-han-sans/raw/release/OTF/SimplifiedChinese/SourceHanSansSC-Regular.otf"
font_path = os.path.join(font_dir, "SourceHanSansSC-Regular.otf")

print(f"正在下载字体到: {font_path}")
response = requests.get(font_url)
with open(font_path, 'wb') as f:
    f.write(response.content)

print("字体下载完成！") 