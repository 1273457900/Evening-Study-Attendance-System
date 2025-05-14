# 使用官方的 Python 运行时作为父镜像
FROM python:3.13.2

# 设置环境变量，确保 Python 输出直接打印到控制台，不会被缓存
ENV PYTHONUNBUFFERED 1

# 设置工作目录为 /project
WORKDIR /project

# 将本地的 requirements.txt 文件复制到容器中的 /project 目录下
COPY requirements.txt /project/

# 使用清华源安装依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 将本地的文件复制到容器中的 /project 目录下
COPY . /project

# 暴露容器内部的 5000 端口
EXPOSE 5000

# 挂载宿主机的路径到容器内的路径
VOLUME /vol1/1000/1晚自习签到/晚自习签到 /project

# 定义容器启动后执行的命令，运行 app.py
CMD ["python", "app.py"]