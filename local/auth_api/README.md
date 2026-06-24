# Auth API - OAuth2.0 认证模块

为 Odoo 提供标准的 **OAuth2.0 Password Grant** 认证能力，供移动端 App 和第三方客户端接入。

## 快速开始

### 1. 注册客户端

在 Odoo 后台 **OAuth2.0 客户端** 菜单中创建一个客户端记录：

| 字段                | 值             | 说明               |
|-------------------|---------------|------------------|
| 客户端名称             | Android App   | 任意名称，仅用于后台识别     |
| Client ID         | `a3f8e9d1...` | 自动生成，写死在 App 代码中 |
| Client Secret     | `b9c2...`     | 自动生成，服务器端保管      |
| Access Token 有效期  | 2（小时）         | 默认即可             |
| Refresh Token 有效期 | 30（天）         | 默认即可             |

### 2. App 端调用

```
# 第一步：登录获取 Token
POST /api/auth/token
Content-Type: application/json

{
    "login": "13800138000",
    "password": "xxxxxx",
    "client_id": "a3f8e9d1..."
}

↓ 返回

{
    "success": true,
    "data": {
        "access_token": "d4e5f6a7...",
        "refresh_token": "b8c9d0e1...",
        "token_type": "Bearer",
        "expires_in": 7200,
        "user": {
            "uid": 2,
            "login": "13800138000",
            "name": "张三",
            "email": "zhangsan@example.com"
        }
    }
}
```

```bash
# 第二步：带着 Token 调用业务接口
GET /api/learn/v1/contents
Authorization: Bearer d4e5f6a7...

# 第三步：Token 快过期时刷新
POST /api/auth/refresh
{
    "grant_type": "refresh_token",
    "refresh_token": "b8c9d0e1...",
    "client_id": "a3f8e9d1...",
    "client_secret": "b9c2..."
}

# 第四步：登出
POST /api/auth/logout
Authorization: Bearer d4e5f6a7...
```

### 3. App 端完整场景

用户从打开 App 到正常使用的完整流程，Token 刷新对用户完全透明：

```
用户打开 App                                 refresh_token 泄露？
  │                                               │
  ├─ 1. 输入账号密码                                  ├─ 攻击者抓包拿到 refresh_token
  │   POST /api/auth/token                          │
  │   返回: {                                        ├─ 但他没有 client_secret
  │     access_token  (2h 有效)                      │   → POST /api/auth/refresh
  │     refresh_token (30d 有效)                     │   校验 client_secret 失败
  │   }                                             │   → 拒绝刷新 ✓
  │                                                 │
  ├─ 2. 缓存 Token 到本地，正常使用                        │
  │   每次业务请求带 Authorization: Bearer <access_token>   │
  │                                                 │
  │   假如 access_token 被中间人截获：                     │
  │     → 2 小时后自动过期，影响有限 ✓                       │
  │                                                 │
  ├─ 3. access_token 过期                             │
  │   业务接口返回 401                                 │
  │   App 自动调 POST /api/auth/refresh               │
  │   带上 refresh_token + client_id + client_secret   │
  │   返回新的 Token 对                                │
  │   旧 Token 自动撤销                                │
  │   → 用户完全无感知，不需要重新输入密码                    │
  │                                                 │
  └─ 4. 用户登出 / 卸载 App                             │
      POST /api/auth/logout                         │
      → Token 撤销，立即失效                            │
```

**为什么这样设计？**

| Token 类型 | 有效期 | 用途 | 安全策略 |
|-----------|--------|------|---------|
| access_token | 2 小时 | 每次请求都带 | 短期有效，泄露影响有限 |
| refresh_token | 30 天 | 仅在刷新时用 | 必须配合 client_secret（编译在 App 里） |
| client_secret | 永久 | 证明客户端身份 | 编译在 App 二进制中，不通过网络传输（仅刷新时） |

## API 接口

| 方法   | 路径                   | 认证     | 说明                         |
|------|----------------------|--------|----------------------------|
| POST | `/api/auth/token`    | public | 用户名+密码登录，返回 Token 对        |
| POST | `/api/auth/refresh`  | public | 用 Refresh Token 换新 Token 对 |
| POST | `/api/auth/revoke`   | public | 撤销指定 Token                 |
| GET  | `/api/auth/userinfo` | Bearer | 获取当前用户信息                   |
| POST | `/api/auth/logout`   | Bearer | 登出，撤销当前 Token              |

> 接口文档详情见 Swagger：`http://localhost:8069/api/swagger`

## 模型说明

### `auth.client` — OAuth 客户端

每个接入的第三方 App 对应一条记录：

```
┌─────────────────────────────────┐
│  auth.client                    │
├─────────────────────────────────┤
│  name: "Android App"            │  客户端名称
│  client_id: "a3f8..."           │  唯一标识（自动生成）
│  client_secret: "b9e1..."       │  密钥（自动生成）
│  access_token_expiry: 2h        │  Access Token 有效期
│  refresh_token_expiry: 30d      │  Refresh Token 有效期
│  active: True                   │  开关
└─────────────────────────────────┘
```

### `auth.token` — Token 会话

用户每次登录产生一条记录，记录完整的 Token 生命周期：

```
一个客户端（Android App）
  ├── Token(张三) → access_token: "d4e5..."  expires: 20:00
  ├── Token(李四) → access_token: "f6a7..."  expires: 21:30
  └── Token(王五) → access_token: "b8c9..."  expires: 18:45  已撤销
```

每条 Token 记录包含：用户、客户端、access_token / refresh_token、过期时间、撤销状态、设备信息和 IP（用于审计）。

## 安全机制

| 机制            | 实现                                    |
|---------------|---------------------------------------|
| Token 存储      | SHA-256 哈希存储，原文不落库                    |
| Access Token  | 短期有效（默认 2h），过期自动拒绝                    |
| Refresh Token | 长期有效（默认 30d），刷新时旧 Token 自动撤销          |
| 撤销            | 支持手动撤销、登出撤销、客户端一键撤销全部 Token           |
| 过期清理          | `_cleanup_expired_tokens()` 可通过定时任务调用 |
| 设备追踪          | 记录 IP 地址和设备信息，异常可追溯                   |

## Token 生命周期

```
用户登录
  │
  ├─ POST /api/auth/token
  │    验证用户名+密码+客户端 ✓
  │    → 创建 auth.token 记录
  │    → 返回 access_token + refresh_token
  │
  ├─ 正常使用（2 小时内）
  │   每次 API 请求带 Authorization: Bearer <access_token>
  │   → _find_by_access_token() 验证
  │
  ├─ Token 即将过期
  │   POST /api/auth/refresh
  │   → 旧 Token 自动撤销
  │   → 返回新 Token 对
  │
  └─ 用户登出
      POST /api/auth/logout
      → is_revoked = True
      → Token 立即失效
```

## 模块依赖

```
base → auth_api → (learn_api, app_manage_api 等业务模块)
```

`auth_api` 只依赖 `base`，业务模块依赖 `auth_api` 即可获得 OAuth 认证能力。`learn_common` 中的 `get_user()` 已封装好
Bearer Token 认证逻辑，业务模块直接调用即可。
