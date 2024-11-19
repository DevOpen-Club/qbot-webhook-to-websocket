# QQ机器人 WebHook -> Websocket 易用版使用文档

# 开发前言

QQ机器人 WebHook 是 QQ 机器人提供的一种消息推送方式，通过 WebHook 接口，可以将消息实时推送到 QQ 机器人的服务端上。

然而在易语言中，Webhook 接口的实现并不方便，因此，本文档将介绍如何在易语言中使用 Websocket 接口来实现 QQ 机器人 WebHook。

# 准备工作
- 一个拥有公网IP的服务器
- 一个QQ机器人（用于测试
- 一个备案的域名（用于接收 Webhook 推送，QQ开放平台强制备案
- 服务器安装宝塔面板，宝塔面板拥有 Python 的最新环境（宝塔面板拥有部署环境，项目本身不依赖宝塔面板

## Step 1：创建python站点

宝塔面板中：网站管理 -> Python项目 -> 添加 Python 项目，填写相关内容，指定好python文件位置以及目录，创建虚拟环境。

## Step 2：安装依赖库

在虚拟环境中，使用 宝塔面板的[模块] 安装依赖库：

```
fastapi
cryptography
pydantic
uvicorn
```
安装后，尝试启动项目

## Step 3：绑定域名、SSL
点击创建的项目设置 -> 域名管理 -> 绑定域名

如何绑定这里不过多赘述。

再点击外网访问 -> 开启外网映射 -> 端口8000放行，已开启，代理路由：/

重启python项目，验证域名是否可以访问（能打开就行）。

再点击 SSL 证书，申请免费的 来此加密 证书即可。尝试是否可以 HTTPS 访问。如果正常访问，那么恭喜你，你已经成功部署了一个 Websocket 版本的 QQ 机器人 WebHook。

## Step 4：测试可用性
### 4.1 开放平台测试
打开QQ开放平台，找到事件通知地址配置区域，输入你的地址：https://{域名}/webhook?secret={机器人密钥}

其中，请将 {域名} 替换为你的域名，{机器人密钥} 替换为你的机器人密钥。密钥应该类似于 iChChjFlHnJqNuRyV3b9hFSJDNds5。

完成配置后，你应该看到开放平台推送了回调验证，不提示任何信息、可以保存配置即代表部署成功！可以保存了。

**进行配置前，需要连接 WebSocket 至对应 Secret，否则无法完成签名计算、消息推送**

保存后，请配置【事件接收】。

### 4.2 Websocket测试
WebSocket统一连接地址格式：`ws://{域名}/ws?secret={机器人密钥}`

> 【WebSocket文档】请见附录。 WebSocket Python Demo 请见`websocket_demo.py`

其中，请将 {域名} 替换为你的域名，{机器人密钥} 替换为你的机器人密钥。密钥应该类似于 iChChChDjFlHnJqNuRyV3b9hFSJDNds5。

打开你的 WebSocket 测试工具，输入上述地址，连接成功后，尝试在群/频道内@机器人 消息，看看 ws 里有没有收到消息。

# 附录1：如何修改HTTP服务端口
服务端口默认为 8000.如果需要修改，请打开`main.py`，拖动至最下方，修改以下内容：
```python
uvicorn.run(app, host="0.0.0.0", port=8000)
```
为
```python
uvicorn.run(app, host="0.0.0.0", port={端口})
```
即可（{端口} 替换为你需要的端口号）。

# 附录2：WebSocket文档
**基础科普**
- WebSocket 协议是 HTML5 开始提供的一种协议，它是基于 TCP 协议的一种新的网络通信协议。
- WebSocket 协议在单个 TCP 连接上可以进行双向通信，实时地进行数据传输。

**使用者基本逻辑时序图**
![WebSocket使用者基本逻辑时序图](https://fb-cdn.fanbook.cn/fanbook/app/files/chatroom/image/b5f9acb3c497b34652f3d63b468b33f2.png)

**WebSocket 统一连接地址**
```
ws://{域名}/ws/机器人密钥}
```
**WebSocket 生命心跳**

代码未进行心跳验证。无需发送心跳包。开发者请自行维护好 WebSocket 连接（即掉线重连）。

**WebSocket 消息结构**

参考：[QQ机器人文档 通用数据结构 Payload](https://bot.q.qq.com/wiki/develop/api-v2/dev-prepare/interface-framework/event-emit.html#%E9%80%9A%E7%94%A8%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84-payload)

**其他说明**
- 目前，Websocket 连接成功建立后才能够正常收到由 WebHook 推送的消息。
