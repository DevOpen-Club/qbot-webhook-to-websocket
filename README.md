<p align="center">
  <a href="https://q.qq.com">
    <img src="https://fb-cdn.fanbook.cn/fanbook/app/files/chatroom/image/c10d371bbf1a9f316e0089ac29a9c9b7.png" width="120" height="120" style="border-radius: 20px;" alt="QQ机器人webhook">
  </a>
</p>
<h1 align="center">QQ机器人 WebHook -> WebSocket</h1>

# 项目简介

QQ机器人 WebHook to WebSocket 是一款 QQ 机器人 WebHook 到 WebSocket 的转换工具，可以将 QQ 开放平台推送的消息通过 WebSocket 协议推送到前端页面。

由于 QQ 官方声明，WebSocket 协议将在2024年年底不再维护，然而若将已有的机器人项目通过 WebHook 重构会耗费大量时间精力。所以为开发者提供此款工具，可以快速将 QQ 机器人 WebHook 转换为 WebSocket 协议，并通过 WebSocket 协议推送消息到机器人处理端。

# 法律声明
1. 项目基于`AGPL-3.0`协议开源，其基本要求包括：
- 版权声明：必须保留原作者的版权声明和许可声明。
- 源代码分发：如果发布了一个基于AGPL 3.0授权的软件的服务，那么必须提供服务所使用的源代码。
- 修改标识：如果对软件进行了修改，必须在源代码中标明修改的时间和范围。
- 许可文件：每个源代码文件都必须包含一个版权声明和许可声明。

具体的商用许可，请参考[AGPL-3.0](https://www.gnu.org/licenses/agpl-3.0.html)协议。

2. 使用此项目产生的任何法律纠纷，由使用者自行承担，与本项目无关。
3. 使用此项目从事的任何违规活动，造成违法行为与作者无关。
> 使用本程序即表示您已充分理解并同意本法律声明的所有内容。

# 项目文档
请查看 `doc.md`。

由于发布仓促，截至目前，推送的普通消息不会进行签名验证，而是直接推送到ws。后期会更新。

# TODO
- [ ] 消息推送签名校验 **【重要】**
- [ ] 增加ws掉线补发功能

# 作者的话
感谢您对本项目的关注，希望能为您提供帮助。

如果您有任何疑问或建议，欢迎通过以下方式联系我：
- 邮箱：devopen@foxmail.com & 2862443924@qq.com
- QQ群群主：296895721
## 捐赠
如果您觉得本项目对您有帮助，欢迎通过以下方式进行捐赠：
![微信赞赏码](https://fb-cdn.fanbook.cn/fanbook/app/files/chatroom/image/da89de9d5be8dc2917625921f1af9862.jpeg)

## 关于 Issues
若在使用中遇到问题，请提交 Issues 进行反馈。

提交的 Issues 请遵照以下规范：
- 标题：简明扼要地描述问题
- 内容：详细描述问题，包括复现步骤、期望结果、实际结果、截图、日志等。
- 标签：请选择合适的标签，如 bug、enhancement、question 等。

错误的提交 Issues 可能会被关闭，请谨慎提交。
## 关于 Pull Requests
若有意向参与本项目的开发，请提交 Pull Requests。

提交的 Pull Requests 请遵照以下规范：
- 对源码进行的修改，所有有意义的代码行必须有详细的注释。
- 遵循本项目的编码规范，包括变量命名、函数命名、注释规范等。
- 请确保提交的代码没有任何语法错误或逻辑错误。
- 请确保提交的代码通过了测试。

提交的 Pull Requests 可能会被合并或修改，请耐心等待。