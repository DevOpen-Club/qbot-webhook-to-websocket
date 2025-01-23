# *-* coding:utf-8 *-*
'''
Author: WrunDorry
Date: 2025/01/23
Description: qbots-webhook-to-websocket
Licence: AGPL-v3
'''
# 导入所需模块
from fastapi import FastAPI, Request, Header, WebSocket, WebSocketDisconnect, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import hashlib
import string
import json
import sys
from binascii import unhexlify
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.backends import default_backend
import logging
import asyncio
import random
import sqlite3
from starlette.responses import Response

ADMIN_PWD="xxxxx" # 后台管理员密码
ADMIN_ENTER="/admin" # 后台入口路径，格式：/xxx

app = FastAPI()

# 配置跨域设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
template_dir = os.path.join(os.path.dirname(__file__), "templates")
if not os.path.isdir(template_dir):
    print(f"目录 {template_dir} 不存在")
else:
    print(f"目录 {template_dir} 存在")

# 配置模板引擎
templates = Jinja2Templates(directory=template_dir)


# 用于储存 WebSocket 连接对象的字典
active_connections = {}
database_file = os.path.join(os.path.dirname(__file__), "database.db")
# 连接到 SQLite 数据库（如果数据库不存在，则会自动创建）
conn = sqlite3.connect(database_file, check_same_thread=False)
cursor = conn.cursor()

# 创建表（如果表不存在）
cursor.execute("""
CREATE TABLE IF NOT EXISTS secrets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    secret TEXT NOT NULL UNIQUE,
    md5_token TEXT NOT NULL UNIQUE
)
""")
conn.commit()
def get_md5_hash(input_string):
    # 创建一个 md5 哈希对象
    md5_hash = hashlib.md5()
    
    # 更新哈希对象，使用字符串的字节形式
    md5_hash.update(input_string.encode('utf-8'))
    
    # 获取十六进制的哈希值
    hex_md5 = md5_hash.hexdigest()
    
    return hex_md5
def generate_random_string(length=50):
    # 定义可用字符集，包括字母和数字
    characters = string.ascii_letters + string.digits
    
    # 生成随机字符串
    random_string = ''.join(random.choice(characters) for _ in range(length))
    
    return random_string
# 配置签名计算函数
def generate_signature(bot_secret, event_ts, plain_token):
    while len(bot_secret) < 32:  # 生成 32 字节的 seed
        bot_secret = (bot_secret + bot_secret)[:32]
    
    # 生成私钥
    private_key = ed25519.Ed25519PrivateKey.from_private_bytes(bot_secret.encode())
    public_key = private_key.public_key()
    # 编码
    message = f"{event_ts}{plain_token}".encode()
    # 计算签名并 16 进制 hex 编码
    signature = private_key.sign(message).hex()
    
    return {
        "plain_token": plain_token,
        "signature": signature
    }  # 返回签名给 QQ 开放平台

# 定义 Payload 模型
class Payload(BaseModel):
    d: dict  # Payload 内容

# 配置日志
logging.basicConfig(level=logging.INFO)

def is_secret_valid(secret):
    cursor.execute("SELECT * FROM secrets WHERE secret = ?", (secret,))
    return cursor.fetchone() is not None
def is_token_valid(secret,token):
    token=get_md5_hash(token)
    cursor.execute("SELECT * FROM secrets WHERE secret = ?", (secret,))
    row=cursor.fetchone()
    if row:
        md5_token=row[2]
        if md5_token==token:
            return True
        else:
            return False
    else:
        return False
    
def is_admin(password, secret):
    admin_password = ADMIN_PWD
    if password == admin_password:
        print("密码正确")
    else:
        return False
    cursor.execute("SELECT * FROM secrets WHERE secret = ?", (secret,))
    row = cursor.fetchone()
    if row :
        return True
    return False

def is_admin_api(token):
    
    cursor.execute("SELECT md5_token FROM secrets ORDER BY id LIMIT 1")
    row = cursor.fetchone()
    if row :
        if token == row[0]:
            return True
        else:
            return False
    else:
        return False
@app.post("/webhook")  # 接收 QQ 开放平台的 webhook 请求
async def handle_webhook(
    request: Request,
    payload: Payload,
    user_agent: str = Header(None),
    x_bot_appid: str = Header(None),
    secret: str = None  # 通过URL查询参数获取secret
):
    secret = request.query_params.get('secret')  # 从请求的URL中获取secret
    token = request.query_params.get('token')  # 从请求的URL中获取token
    if not token:
        logging.error("没有提供 token 参数")
        return {"msg": "error"}
    
    if not secret:
        logging.error("没有提供 secret 参数")
        return {"msg": "error"}

    if not is_secret_valid(secret):
        logging.error("无效的 secret: %s", secret)
        return {"msg": "error"}
    
    if not is_token_valid(secret,token):
        logging.error("无效的 token: %s", token)
        return {"msg": "error"}
    body_bytes = await request.body()  # 获取请求体
    logging.info("收到消息 %s", body_bytes)
    body_str = body_bytes.decode('utf-8')  # 解码为字符串
    
    if "event_ts" not in payload.d or "plain_token" not in payload.d:  # 判断是不是第一次配置回调地址
        logging.info("消息事件")  # 如果不是第一次配置回调地址，则忽略
    else:  # 如果是，那么开始计算签名
        logging.info("回调地址配置事件")
        try:  # 套一层 Try-Except 防止签名计算失败
            event_ts = payload.d["event_ts"]  # 获取事件时间戳
            plain_token = payload.d["plain_token"]  # 获取 需要计算的 token
            # 使用传入的secret计算签名
            result = generate_signature(secret, event_ts, plain_token)  # 调用函数，计算签名
            logging.info("签名计算成功: %s", result)
            return result  # 返回签名给 QQ 开放平台
        except KeyError as e:
            logging.error("签名计算时发生了错误: %s", e)
            pass

    # 这里是处理普通消息事件的部分

    if secret in active_connections:  # 判断推送的消息所对应的 secret 的 websocket 是否连接
        logging.info("即将把消息推送给 ws: %s", secret)
        for connection in active_connections[secret]:
            await connection.send_text(body_str)  # 推送消息给所有与此 secret 连接的 websocket
        return {"message": "Data pushed to WebSocket"}
    else:  # 如果没有连接，则返回错误信息
        logging.warning("对应 secret 的 ws 没有被连接: %s", secret)
        return {"message": "No active WebSocket connection found for secret"}

@app.websocket("/ws/{secret}/{token}")  # 建立 WebSocket 服务端
async def websocket_endpoint(websocket: WebSocket, secret: str, token: str):
    if not is_token_valid(secret,token):
        logging.error("无效的 token: %s", token)
        await websocket.close(code=1008, reason="Invalid token")
    if not is_secret_valid(secret):
        logging.error("无效的 secret: %s", secret)
        await websocket.close(code=1008, reason="Invalid secret")
        return

    await websocket.accept()  # 接受 WebSocket 连接请求
    if secret not in active_connections:
        active_connections[secret] = []
    active_connections[secret].append(websocket)  # 将当前连接存储到 active_connections 字典里的列表中
    try:
        while True:
            data = await websocket.receive_text()  # 获取客户端 push 过来的消息
            logging.info("收到来自 ws 的消息: %s", data)
    except WebSocketDisconnect:
        logging.info(f"{secret} 的 WebSocket 连接断开.")
        active_connections[secret].remove(websocket)  # 当连接断开时，从列表中移除
        if not active_connections[secret]:  # 如果列表为空，移除该 key
            del active_connections[secret]

@app.get(ADMIN_ENTER, response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post(ADMIN_ENTER+"/login")
async def login(response: Response, password: str = Form(...), secret: str = Form(...)):
    if not is_admin(password, secret):
        logging.error("登录失败: 无效的密码或 secret")
        return {"msg": "error"+secret+""}
    
    response = RedirectResponse(url=ADMIN_ENTER+"/manage", status_code=303)
    response.set_cookie(key="admin_secret", value=secret)
    response.set_cookie(key="admin_password", value=password)
    return response

@app.get(ADMIN_ENTER+"/manage", response_class=HTMLResponse)
async def manage_secrets(request: Request):
    admin_secret = request.cookies.get("admin_secret")
    admin_password=request.cookies.get("admin_password")
    if not admin_secret or not is_admin(admin_password, admin_secret):
        logging.error("未授权访问管理页面")
        return RedirectResponse(url="/", status_code=303)
    
    cursor.execute("SELECT * FROM secrets")
    secrets = cursor.fetchall()
    return templates.TemplateResponse("manage.html", {"request": request, "secrets": secrets})

@app.post(ADMIN_ENTER+"/create_secret")
async def create_secret(request: Request,secret: str = Form(...)):
    admin_secret = request.cookies.get("admin_secret")  # 使用传入的 secret 作为管理员 secret
    admin_password=request.cookies.get("admin_password")  # 使用传入的 password 作为管理员密码
    if not is_admin(admin_password, admin_secret):
        logging.error("未授权创建 secret")
        return {"msg": "error"}
    
    try:
        token=generate_random_string(10)
        md5_token=get_md5_hash(token)
        cursor.execute("INSERT INTO secrets (secret,md5_token) VALUES (?,?)", (secret,md5_token,))
        conn.commit()
        logging.info("成功创建 secret: %s", secret)
        return {"msg": "成功了，可以返回/{ADMIN_ENTER}/manage页面查看【请注意保护token，token只显示一次】","token":token}
    except sqlite3.IntegrityError:
        logging.error("secret 已经存在: %s", secret)
        return {"msg": "error"}

@app.post(ADMIN_ENTER+"/delete_secret")
async def delete_secret(request: Request,secret: str = Form(...)):
    admin_secret = secret  # 使用传入的 secret 作为管理员 secret
    admin_password=request.cookies.get("admin_password")  # 使用传入的 password 作为管理员密码
    if not is_admin(admin_password, admin_secret):
    
        logging.error("未授权删除 secret")
        return {"msg": "error"}
    
    try:
        cursor.execute("DELETE FROM secrets WHERE secret = ?", (secret,))
        conn.commit()
        logging.info("成功删除 secret: %s", secret)
        return {"msg": "success"}
    except Exception as e:
        logging.error("删除 secret 时发生错误: %s", e)
        return {"msg": "error"}
@app.post(ADMIN_ENTER+"/api")
async def api(request: Request):
    token = request.query_params.get('token')
    if not is_admin_api(token):
        logging.error("未授权访问 API")
        return {"msg": "error"}
    data=await request.body()
    try:
        data=json.loads(data)
    except:
        return {"status":False,"code":201,"msg":"解析出错不是合法的json"}
    if data['action']=='create_secret':
        sql="INSERT INTO secrets (secret,md5_token) VALUES (?,?)"
        try:
            token=generate_random_string(10)
            md5_token=get_md5_hash(token)
            cursor.execute(sql,(data['secret'],md5_token,))
            conn.commit()
            return {"status":True,"code":200,"msg":"创建成功，请注意保护token，token只显示一次","token":token}
        except:
            return {"status":False,"code":201,"msg":"创建失败"}
    elif data['action']=='delete_secret':
        sql="DELETE FROM secrets WHERE secret = ?"
        try:
            cursor.execute(sql,(data['secret'],))
            conn.commit()
            return {"status":True,"code":200,"msg":"删除成功"}
        except:
            return {"status":False,"code":201,"msg":"删除失败"}
    elif data['action']=='is_secrets':
        sql="SELECT * FROM secrets WHERE secret = ?"
        try:
            cursor.execute(sql,(data['secret'],))
            row=cursor.fetchone()
            if row:
                return {"status":True,"code":200,"msg":"存在"}
            else:
                return {"status":False,"code":201,"msg":"不存在"}
        except:
            return {"status":False,"code":201,"msg":"查询失败"}
        
    else:
        return {"status":False,"code":201,"msg":"未知的操作"}
            
# 启动服务
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)  # 端口 8000 监听所有 IP
