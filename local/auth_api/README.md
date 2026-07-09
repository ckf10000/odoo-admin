# Auth API - OAuth2.0 认证模块

为 Odoo 提供 OAuth2.0 认证能力，供移动端 App 接入。所有接口使用统一请求格式，通过 HMAC-MD5 签名保证安全性。

## 快速开始

### 1. 注册客户端

在 Odoo 后台 **OAuth2.0 客户端** 菜单中创建客户端记录：

| 字段                | 值                   | 说明             |
|-------------------|---------------------|----------------|
| 客户端名称             | Android App         | 任意名称           |
| Client ID         | `a3f8e9d1...`（自动生成） | 写死在 App 代码中    |
| Client Secret     | `b9c2...`（自动生成）     | 编译在 App 中，用于签名 |
| Access Token 有效期  | 2（小时）               | 默认即可           |
| Refresh Token 有效期 | 30（天）               | 默认即可           |

### 2. 统一请求格式

所有接口均为 `POST`，请求体格式：

```json
{
  "header": {
    "clientId": "a3f8e9d1...",
    "X-Token": "登录后的 access_token（登录接口传空串）",
    "X-Timestamp": "1720000000000",
    "X-Nonce": "随机字符串（UUID）",
    "X-Sign": "签名值（见下方签名算法）",
    "platformType": "android",
    "platformVersion": "14",
    "deviceBrand": "HUAWEI",
    "deviceModel": "Mate 60 Pro",
    "deviceId": "a1b2c3d4...",
    "rooted": false,
    "sdkVersion": "33",
    "networkType": "wifi",
    "screenWidth": 1260,
    "screenHeight": 2720,
    "screenDensity": 3.0,
    "language": "zh-CN",
    "timezone": "Asia/Shanghai",
    "imei": "",
    "oaid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "appVersion": "2.1.0",
    "appBuild": "20260701",
    "appChannel": "official",
    "appBuildType": "release"
  },
  "body": {
    "username": "admin",
    "password": "admin123",
    "tenant": "odoo.learn.dev"
  }
}
```

### 3. 签名算法

```
bodyJSON = JSON.stringify(body, 无空格, key排序)
signStr  = timestamp + nonce + token + bodyJSON + clientSecret
X-Sign   = MD5(signStr).toLowerCase()
```

- 登录/刷新时 `token` 为空字符串 `""`
- `bodyJSON` 需使用 key 排序、不带空格的紧凑 JSON
- 时间戳有效期 ±5 分钟（防重放）

### 4. 接口调用示例

```bash
# 第一步：登录
POST /api/v1/auth/token
{
  "header": {
    "clientId": "a3f8e9d1...",
    "X-Token": "",
    "X-Timestamp": "1720000000000",
    "X-Nonce": "a1b2c3d4...",
    "X-Sign": "计算出的MD5值",
    ...
  },
  "body": {
    "username": "admin",
    "password": "admin123",
    "tenant": "odoo.learn.dev"
  }
}

↓ 返回 { "success": true, "data": { "access_token": "...", "refresh_token": "...", "user": {...} } }

# 第二步：获取用户信息
POST /api/v1/auth/userinfo
{
  "header": { ..., "X-Token": "访问令牌", ... },
  "body": {}
}

# 第三步：修改密码
POST /api/v1/auth/change-password
{
  "header": { ..., "X-Token": "访问令牌", ... },
  "body": { "old_password": "旧密码", "new_password": "新密码" }
}

# 第四步：登出
POST /api/v1/auth/logout
{
  "header": { ..., "X-Token": "访问令牌", ... },
  "body": {}
}
```

## API 接口

| 方法   | 路径                             | 说明                         |
|------|--------------------------------|----------------------------|
| POST | `/api/v1/auth/token`           | 用户名+密码登录，返回 Token 对        |
| POST | `/api/v1/auth/refresh`         | 用 Refresh Token 换新 Token 对 |
| POST | `/api/v1/auth/revoke`          | 撤销指定 Token                 |
| POST | `/api/v1/auth/userinfo`        | 获取当前用户信息                   |
| POST | `/api/v1/auth/logout`          | 登出，撤销当前 Token              |
| POST | `/api/v1/auth/change-password` | 修改当前用户密码                   |

## 模型说明

### `auth.client` — OAuth 客户端

```
┌─────────────────────────────────┐
│  auth.client                    │
├─────────────────────────────────┤
│  name: "Android App"            │  客户端名称
│  client_id: "a3f8..."           │  唯一标识（自动生成）
│  client_secret: "b9e1..."       │  密钥，用于签名验证
│  access_token_expiry: 2h        │  Access Token 有效期
│  refresh_token_expiry: 30d      │  Refresh Token 有效期
│  active: True                   │  开关
└─────────────────────────────────┘
```

### `auth.token` — Token 会话

```
一个客户端（Android App）
  ├── Token(张三) → access_token: "d4e5..."  expires: 20:00  header_data: "{...}"
  ├── Token(李四) → access_token: "f6a7..."  expires: 21:30  header_data: "{...}"
  └── Token(王五) → access_token: "b8c9..."  expires: 18:45  已撤销
```

每条 Token 记录包含：用户、客户端、access_token / refresh_token、过期时间、撤销状态、`header_data`（完整设备/环境信息 JSON）、IP
地址。

## 安全机制

| 机制            | 实现                                                       |
|---------------|----------------------------------------------------------|
| 签名验证          | MD5(timestamp + nonce + token + bodyJSON + clientSecret) |
| 时间戳防重放        | ±5 分钟窗口，过时拒绝                                             |
| Token 存储      | SHA-256 哈希存储，原文不落库                                       |
| Access Token  | 短期有效（默认 2h）                                              |
| Refresh Token | 长期有效（默认 30d），刷新时旧 Token 自动撤销                             |
| 设备追踪          | header_data 字段完整记录每次请求的设备/环境信息                           |
| 过期清理          | 定时任务每小时标记过期 Token 为已撤销                                   |

## Token 生命周期

```
用户登录
  │
  ├─ POST /api/v1/auth/token
  │    验证签名 → 验证用户名+密码
  │    → 创建 auth.token 记录（含 header_data）
  │    → 返回 access_token + refresh_token
  │
  ├─ 正常使用（2 小时内）
  │   每次 API 请求验证签名 → 验证 Token
  │
  ├─ Token 即将过期
  │   POST /api/v1/auth/refresh（verify_signature, refresh_token）
  │   → 旧 Token 自动撤销
  │   → 返回新 Token 对
  │
  └─ 用户登出
      POST /api/v1/auth/logout
      → 更新 header_data（最后状态）
      → is_revoked = True
      → Token 立即失效
```

## 模块依赖

```
base → auth_api → learn_api / app_manage_api 等业务模块
```

业务模块通过 `common_lib.api_verify_auth()` 即可获得签名 + Token 认证能力。
