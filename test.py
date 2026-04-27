import os
import socket
import subprocess
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import json
url = "http://ip-api.com/json"
try:
    with urllib.request.urlopen(url, timeout=5) as response:
        # 读取字节数据
        result = response.read()        
        # 转为字符串再解析 JSON
        data = json.loads(result.decode("utf-8"))
        print("返回结果：")
        print(data)
except Exception as e:
    print("请求失败：", e)
print("===== Node Starting =====", flush=True)

####################################
# 读取 Secrets
####################################

FRP_SERVER_ADDR = os.environ.get("FRP_SERVER_ADDR","")
FRP_SERVER_PORT = os.environ.get("FRP_SERVER_PORT", "80")
FRP_TOKEN = os.environ.get("FRP_TOKEN","")
FRP_GROUP_EXTRA = os.environ.get("FRP_GROUP_EXTRA","")

PROXY_PORT = int(os.environ.get("PROXY_PORT","1080"))
REMOTE_PORT = int(os.environ.get("REMOTE_PORT","6000"))  # 远程端口，默认 6000

SOCKS_PORT = PROXY_PORT + 1
WEB_PORT = int(os.environ.get("PORT", "7860"))

# 额外 gost 监听配置：格式为 "协议://地址:端口"，例如 "http://0.0.0.0:8080"
GOST_EXTRA_LISTEN = os.environ.get("GOST_EXTRA_LISTEN","")

# NODE_NAME = os.environ.get("NODE_NAME") or socket.gethostname()
# 1️⃣ 尝试读取用户自定义 NODE_NAME
NODE_NAME = os.environ.get("NODE_NAME")

# 2️⃣ 如果没有，自行从 HF_SPACE_REPO_ID 取值，并将 / 替换成 -
if not NODE_NAME:
    space_id = os.environ.get("HF_SPACE_REPO_ID", "hf-node")
    NODE_NAME = space_id.replace("/", "-")

print("FRP_SERVER_ADDR:", FRP_SERVER_ADDR, flush=True)
print("NODE_NAME:", NODE_NAME, flush=True)

####################################
# 生成 frpc.toml
####################################

config = f"""
serverAddr = "{FRP_SERVER_ADDR}"
serverPort = {FRP_SERVER_PORT}

auth.method = "token"
auth.token = "{FRP_TOKEN}"

[[proxies]]
name = "{NODE_NAME}"
type = "tcp"

localIP = "127.0.0.1"
localPort = {PROXY_PORT}

remotePort = {REMOTE_PORT}

loadBalancer.group = "proxy_pool{FRP_GROUP_EXTRA}"
loadBalancer.groupKey = "poolkey"

"""

# with open("/app/frpc.toml","w") as f:
#     f.write(config)

print("===== frpc.toml =====", flush=True)
# print(config, flush=True)

####################################
# 启动 gost
####################################

print("Starting gost...", flush=True)

gost_cmd = [
    "/app/gost",
    "-L", f"socks5://127.0.0.1:{PROXY_PORT}"
]

# 如果设置了额外的监听地址，添加到命令中
if GOST_EXTRA_LISTEN:
    print(f"Extra gost listen……", flush=True)
    gost_cmd.extend(["-L", GOST_EXTRA_LISTEN])

gost_process = subprocess.Popen(gost_cmd)

####################################
# 启动 frpc
####################################

print("Starting frpc...", flush=True)

frpc_process = subprocess.Popen(
[
"/app/frpc",
"-c",
"/app/frpc.toml"
]
)

####################################
# 检查进程
####################################

def monitor():
    while True:
        if gost_process.poll() is not None:
            print("gost stopped!", flush=True)

        if frpc_process.poll() is not None:
            print("frpc stopped!", flush=True)

        time.sleep(10)

threading.Thread(target=monitor, daemon=True).start()

####################################
# HF health server
####################################

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Node Running")

def start_server():
    server = HTTPServer(("0.0.0.0",WEB_PORT),Handler)
    print("Health server started on {WEB_PORT}", flush=True)
    server.serve_forever()

start_server()
