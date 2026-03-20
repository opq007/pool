FROM ubuntu:22.04
RUN apt update && \
    apt install -y wget curl python3
COPY app.py /app/app.py
COPY gost /usr/local/bin/gost
COPY frpc /usr/local/bin/frpc
# 赋予执行权限
RUN chmod +x /usr/local/bin/gost /usr/local/bin/frpc
# HF Spaces 要求监听 7860
EXPOSE 7860
# 启动主程序
CMD ["python3","/app/app.py"]
