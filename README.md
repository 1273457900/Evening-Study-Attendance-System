# 相机拍照与实时水印应用

这是一个基于Python Flask的网页应用，允许用户通过网页访问摄像头、实时显示水印并拍照。

## 功能

- 网页访问摄像头
- 实时显示水印（带有当前时间）
- 自定义水印文字
- 自定义水印位置（左上角、右上角、左下角、右下角、中心）
- 自定义水印颜色
- 拍照并下载带水印的照片
- 支持前后摄像头切换

## 安装与运行

1. 确保您已安装Python和pip。

2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 生成HTTPS证书（首次运行时会自动执行）：

```bash
python generate_cert.py
```

4. 运行应用：

```bash
python app.py
```

5. 在浏览器中访问：

```
https://<您的IP地址>:5000
```

## HTTPS支持说明

由于浏览器安全策略，在移动设备上访问摄像头需要HTTPS连接。本应用通过自签名证书提供HTTPS支持。首次访问时，浏览器会显示安全警告，这是正常的，您需要：

1. 在浏览器中点击"高级"或"详细信息"
2. 选择"继续访问网站"或"接受风险并继续"
3. 由于使用的是自签名证书，这个警告只是提示证书不是由受信任的证书颁发机构签发的

## 在移动设备上使用

1. 确保您的电脑和移动设备在同一个局域网内
2. 在电脑上运行应用后，找到您的电脑局域网IP地址
3. 在移动设备浏览器中访问 `https://<您的电脑IP>:5000`
4. 允许浏览器访问摄像头
5. 如果使用的是非Chrome浏览器且遇到问题，建议尝试使用Chrome

## 注意事项

- 要使用摄像头功能，您的浏览器必须支持WebRTC
- 首次访问时，浏览器会请求摄像头访问权限，请选择"允许"
- 如果使用Windows，您可能需要安装OpenSSL。可以从 https://slproweb.com/products/Win32OpenSSL.html 下载

## 技术栈

- 后端：Python Flask
- 前端：HTML, CSS, JavaScript (原生)
- 相机API：WebRTC (navigator.mediaDevices)
- 安全：OpenSSL (自签名HTTPS证书)

## 许可

MIT 