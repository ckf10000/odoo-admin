# Auth API - OAuth2.0 第三方认证模块

## 概述

为 Android/iOS App 或第三方客户端提供 OAuth2.0 认证服务，基于 Odoo 用户体系。

## API 接口

### 1. 登录获取 Token

```http
POST /api/v1/auth/token
Content-Type: application/json

{
    "grant_type": "password",
    "client_id": "xxx",       // 可选，不传使用默认客户端
    "username": "admin",
    "password": "admin123"
}
```

响应:

```json
{
  "success": true,
  "data": {
    "access_token": "xxx",
    "token_type": "Bearer",
    "expires_in": 7200,
    "refresh_token": "xxx",
    "scope": "user",
    "user": {
      "uid": 2,
      "login": "admin",
      "name": "Administrator",
      "email": "admin@example.com"
    }
  }
}
```

### 2. 刷新 Token

Access Token 过期后，用 Refresh Token 换取新 Token 对，需同时验证客户端身份。

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
    "grant_type": "refresh_token",
    "refresh_token": "xxx",
    "client_id": "xxx",          // 必填，客户端 ID
    "client_secret": "xxx"       // 必填，客户端密钥
}
```

> `client_secret` 编译在 App 二进制中，不通过网络明文传输（仅刷新时携带）。即使 refresh_token 在网络中被截获，攻击者缺少
> client_secret 也无法刷新。

### 3. 撤销 Token / 登出

```http
POST /api/v1/auth/revoke
Content-Type: application/json

{
    "token": "xxx"
}
```

或者:

```http
POST /api/v1/auth/logout
Authorization: Bearer xxx
```

### 4. 获取用户信息

```http
GET /api/v1/auth/userinfo
Authorization: Bearer xxx
```

### 5. 修改密码

需要已登录状态（Bearer Token 认证），验证旧密码后更新为新密码。

```http
POST /api/v1/auth/change-password
Authorization: Bearer xxx
Content-Type: application/json

{
    "old_password": "当前密码",
    "new_password": "新密码"
}
```

响应:

```json
{
  "success": true,
  "message": "密码修改成功",
  "data": null
}
```

校验规则:

- 旧密码不能为空
- 新密码不能为空且长度不能少于 6 位
- 新密码不能与旧密码相同
- 旧密码必须正确匹配当前用户密码

## 在其他 API 中使用 Bearer Token 认证

```python
from odoo.addons.auth_api.controllers.auth_controller import authenticate_bearer
from odoo import http
from odoo.http import request


class MyApiController(http.Controller):

    @http.route('/api/my/endpoint', type='json', auth='public', methods=['GET'], csrf=False)
    def my_endpoint(self, **kw):
        # Bearer Token 认证
        user = authenticate_bearer()

        # user 是 res.users 对象，已通过 Token 验证
        # request.env 已被更新为当前用户环境

        return {
            'success': True,
            'data': {
                'message': f'Hello, {user.name}!'
            }
        }
```

## Android App 示例

```kotlin
// 1. 登录
suspend fun login(username: String, password: String): LoginResult {
    val response = api.post("/api/v1/auth/token") {
        setBody(LoginRequest(
            grant_type = "password",
            username = username,
            password = password
        ))
    }
    val data = response.body<ApiResponse<LoginData>>()
    // 保存 token
    saveToken(data.data.access_token, data.data.refresh_token)
    return LoginResult(data.data.user)
}

// 2. 后续请求带上 Bearer Token
fun createApi(): ApiService {
    return Retrofit.Builder()
        .addInterceptor { chain ->
            val request = chain.request().newBuilder()
                .addHeader("Authorization", "Bearer ${getAccessToken()}")
                .build()
            chain.proceed(request)
        }
        // ...
}

// 3. Token 过期自动刷新（需 client_id + client_secret）
class TokenRefreshInterceptor(private val clientId: String,
                              private val clientSecret: String) : Interceptor {
    override fun intercept(chain: Chain): Response {
        var response = chain.proceed(chain.request())
        if (response.code == 401) {
            // 用 refresh_token + client_id + client_secret 刷新
            val newTokens = api.refreshToken(
                grant_type = "refresh_token",
                refresh_token = getRefreshToken(),
                client_id = clientId,
                client_secret = clientSecret
            )
            saveToken(newTokens.access_token, newTokens.refresh_token)
            // 重试原请求
            response = chain.proceed(chain.request().newBuilder()
                .addHeader("Authorization", "Bearer ${newTokens.access_token}")
                .build())
        }
        return response
    }
}
```

// 4. 修改密码
suspend fun changePassword(oldPwd: String, newPwd: String): Result<Unit> {
return try {
api.post("/api/v1/auth/change-password") {
setBody(ChangePasswordRequest(
old_password = oldPwd,
new_password = newPwd
))
}
Result.success(Unit)
} catch (e: Exception) {
Result.failure(e)
}
}

## 安全特性

- Token 存储使用 SHA-256 哈希，原 Token 不会明文存储
- Access Token 默认 2 小时过期
- Refresh Token 默认 30 天过期
- 刷新 Token 时自动撤销旧 Token（Token Rotation）
- 定时任务自动标记过期 Token 为已撤销（保留审计记录）
- 完整的登录日志审计
