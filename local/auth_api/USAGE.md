# Auth API - OAuth2.0 第三方认证模块

## 概述

为 Android/iOS App 或第三方客户端提供 OAuth2.0 认证服务，基于 Odoo 用户体系。

## API 接口

### 1. 登录获取 Token

```http
POST /api/auth/token
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

```http
POST /api/auth/refresh
Content-Type: application/json

{
    "grant_type": "refresh_token",
    "refresh_token": "xxx"
}
```

### 3. 撤销 Token / 登出

```http
POST /api/auth/revoke
Content-Type: application/json

{
    "token": "xxx"
}
```

或者:
```http
POST /api/auth/logout
Authorization: Bearer xxx
```

### 4. 获取用户信息

```http
GET /api/auth/userinfo
Authorization: Bearer xxx
```

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
    val response = api.post("/api/auth/token") {
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

// 3. Token 过期自动刷新
class TokenRefreshInterceptor : Interceptor {
    override fun intercept(chain: Chain): Response {
        var response = chain.proceed(chain.request())
        if (response.code == 401) {
            // 用 refresh_token 刷新
            val newTokens = refreshToken()
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

## 安全特性

- Token 存储使用 SHA-256 哈希，原 Token 不会明文存储
- Access Token 默认 2 小时过期
- Refresh Token 默认 30 天过期
- 刷新 Token 时自动撤销旧 Token（Token Rotation）
- 定时任务自动清理过期 Token
- 完整的登录日志审计
