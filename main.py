# *-* coding:utf-8 *-*

# 导入所需模块
from fastapi import FastAPI, Request, Header, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.backends import default_backend
import logging
import asyncio

app = FastAPI()

# 配置跨域设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 用于储存 WebSocket 连接对象的字典
active_connections = {}
heartbeat_status = True # 是否启用心跳检测
# 配置签名计算函数
def generate_signature(bot_secret, event_ts, plain_token):
    while len(bot_secret) < 32: # 生成 32 字节的 seed
        bot_secret = (bot_secret + bot_secret)[:32]
    
    # 生成私钥
    private_key = ed25519.Ed25519PrivateKey.from_private_bytes(bot_secret.encode())
    # 编码
    message = f"{event_ts}{plain_token}".encode()
    # 计算签名并 16 进制 hex 编码
    signature = private_key.sign(message).hex()
    
    return {
        "plain_token": plain_token,
        "signature": signature
    } # 返回签名给 QQ 开放平台

# 定义 Payload 模型
class Payload(BaseModel):
    d: dict  # Payload 内容

# 配置日志
logging.basicConfig(level=logging.INFO)

@app.post("/webhook") # 接收 QQ 开放平台的 webhook 请求
async def handle_webhook(
    request: Request,
    payload: Payload,
    user_agent: str = Header(None),
    x_bot_appid: str = Header(None),
    secret: str = None  # 通过URL查询参数获取secret
):
    
    secret = request.query_params.get('secret') # 从请求的URL中获取secret
    body_bytes = await request.body() # 获取请求体
    logging.info("收到消息 %s", body_bytes)
    body_str = body_bytes.decode('utf-8') # 解码为字符串
    
    if "event_ts" not in payload.d or "plain_token" not in payload.d: # 判断是不是第一次配置回调地址
        logging.info("消息事件") # 如果不是第一次配置回调地址，则忽略
    else: # 如果是，那么开始计算签名
        logging.info("回调地址配置事件")
        try: # 套一层 Try-Except 防止签名计算失败
            event_ts = payload.d["event_ts"] # 获取事件时间戳
            plain_token = payload.d["plain_token"] # 获取 需要计算的 token
            # 使用传入的secret计算签名
            result = generate_signature(secret, event_ts, plain_token) # 调用函数，计算签名
            logging.info("签名计算成功: %s", result)
            return result # 返回签名给 QQ 开放平台
        except KeyError as e:
            logging.error("签名计算时发生了错误: %s", e)
            pass

    # 这里是处理普通消息事件的部分

    if secret in active_connections: # 判断推送的消息所对应的 secret 的 websocket 是否连接
        logging.info("即将把消息推送给ws: %s", secret)
        await active_connections[secret].send_text(body_str) # 推送消息给对应的 websocket
        return {"message": "Data pushed to WebSocket"}
    else: # 如果没有连接，则返回错误信息
        logging.warning("对应secret的ws没有被连接: %s", secret)
        return {"message": "No active WebSocket connection found for secret"}

async def heartbeat(SecretArray=active_connections):
    if heartbeat_status:
        try:
            for secret in SecretArray:
                await active_connections[secret].send_text("ping")
                logging.info("发送心跳包: %s", secret)
                try:
                    response = await asyncio.wait_for(active_connections[secret].receive_text(), timeout=10)
                except asyncio.TimeoutError:
                    logging.warning(f"{secret}心跳响应超时：{secret}")
                    continue
                if response != "pong":
                    logging.warning(f"{secret}心跳响应异常：响应内容为{response}")
                    continue
                else:
                    logging.info(f"{secret}心跳响应正常：{response}")
                    continue
        except WebSocketDisconnect:
            try:
                await active_connections[secret].send_text("最后一次尝试发送心跳包") # 当连接断开时，向客户端发送消息
            except:
                logging.info(f"无法向 {secret} 发送消息，WebSocket连接已断开.")
            del active_connections[secret] # 当连接断开时，从字典中移除

# 启动心跳循环机制
async def start_heartbeat():
    while True:
        await asyncio.sleep(300)
        await heartbeat()

@app.websocket("/ws/{secret}") # 建立 WebSocket 服务端
async def websocket_endpoint(websocket: WebSocket, secret: str):
    await websocket.accept() # 接受 WebSocket 连接请求
    active_connections[secret] = websocket # 将当前连接存储到active_connections字典
    try:
        while True:
            data = await websocket.receive_text() # 获取客户端push过来的消息
            logging.info("收到来自ws的消息: %s", data)
    except WebSocketDisconnect:
                # 创建一个新的secret变量数组，并且添加secret到数组中
                SecretArray = [secret]
                await heartbeat(SecretArray) # 调用心跳检测函数

# 启动服务
if __name__ == "__main__":
    import uvicorn
    import asyncio
    if heartbeat_status==True:
        asyncio.run(heartbeat()) # 启动心跳检测
    uvicorn.run(app, host="0.0.0.0", port=8000) # 端口 8000 监听所有 IP
    
