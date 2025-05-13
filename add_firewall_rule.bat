@echo off
echo 正在为Flask应用添加防火墙规则（需要管理员权限）...
echo.

netsh advfirewall firewall add rule name="Python-Flask" dir=in action=allow program="%LOCALAPPDATA%\Programs\Python\Python*\python.exe" enable=yes profile=private,domain,public protocol=TCP localport=5000

netsh advfirewall firewall add rule name="Flask-Port-5000" dir=in action=allow protocol=TCP localport=5000 enable=yes profile=private,domain,public

echo.
echo 请重新运行 python app.py 并尝试在手机上访问
echo.
pause 