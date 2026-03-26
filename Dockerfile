FROM python:3.11-alpine
WORKDIR /app
# 复制文件
COPY app.py .
COPY gost /usr/local/bin/gost
COPY frpc /usr/local/bin/frpc
# 安装必要依赖 + 设置权限（合并层）
RUN chmod +x /usr/local/bin/gost /usr/local/bin/frpc
EXPOSE 7860
CMD ["python3", "app.py"]