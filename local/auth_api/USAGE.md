# Auth API - 第三方认证使用文档

## 概述

为 Android/iOS App 提供 OAuth2.0 认证服务，基于 Odoo 用户体系。所有接口统一 POST 请求，`header` + `body` 格式，MD5 签名防篡改。

## 统一请求格式

```
POST /api/v1/auth/{action}
Content-Type: application/json

{
  "header": {
    "clientId": "xxx",
    "X-Token": "access_token | 空串",
    "X-Timestamp": "毫秒时间戳",
    "X-Nonce": "UUID随机串",
    "X-Sign": "签名值",
    "platformType": "android",
    ...
  },
  "body": { ... 业务参数 ... }
}
```

## 签名算法

```
bodyJSON = JSON.stringify(body, { sortedKeys, compact, noUnicodeEscape })
signStr  = X-Timestamp + X-Nonce + X-Token + bodyJSON + clientSecret
X-Sign   = MD5(signStr).hex.lower()
```

注意事项：

- `bodyJSON` 必须 key 排序、紧凑格式（无空格换行）
- 登录/刷新接口 `X-Token` 传空字符串 `""`
- `X-Timestamp` 有效期 ±5 分钟
- `X-Nonce` 每次请求生成新的 UUID

## API 接口

### 1. 登录获取 Token

```http
POST /api/v1/auth/token
Content-Type: application/json

{
  "header": {
    "clientId": "a3f8e9d1...",
    "X-Token": "",
    "X-Timestamp": "1720000000000",
    "X-Nonce": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "X-Sign": "计算出的 MD5 值",
    ...
  },
  "body": {
    "username": "admin",
    "password": "admin123",
    "tenant": "odoo.learn.dev"
  }
}
```

| body 参数  | 必填 | 说明           |
|----------|:--:|--------------|
| username | ✓  | Odoo 登录名     |
| password | ✓  | Odoo 密码      |
| tenant   |    | 数据库名（多租户时指定） |

响应:

```json
{
  "success": true,
  "message": "登录成功",
  "data": {
    "access_token": "d4e5f6a7...",
    "token_type": "Bearer",
    "expires_in": 7200,
    "refresh_token": "b8c9d0e1...",
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
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "header": {
    "clientId": "a3f8e9d1...",
    "X-Token": "",
    "X-Timestamp": "1720000000000",
    "X-Nonce": "...", "X-Sign": "...",
    ...
  },
  "body": {
    "grant_type": "refresh_token",
    "refresh_token": "b8c9d0e1..."
  }
}
```

| body 参数       | 必填 | 说明                  |
|---------------|:--:|---------------------|
| grant_type    | ✓  | 固定 `refresh_token`  |
| refresh_token | ✓  | 登录返回的 refresh_token |

> 签名已包含 `clientSecret`，无需在 body 中重复传 `client_id` / `client_secret`。

### 3. 撤销 Token

```http
POST /api/v1/auth/revoke
Content-Type: application/json

{
  "header": { "clientId": "...", "X-Token": "xxx", "X-Sign": "...", ... },
  "body": {
    "token": "要撤销的 access_token 或 refresh_token",
    "token_type_hint": "access_token"
  }
}
```

### 4. 登出

```http
POST /api/v1/auth/logout
Content-Type: application/json

{
  "header": { "clientId": "...", "X-Token": "当前token", "X-Sign": "...", ... },
  "body": {}
}
```

> 登出时服务端会更新 token 记录的 `header_data`（保存最后一次设备状态），然后撤销 token。

### 5. 获取用户信息

```http
POST /api/v1/auth/userinfo
Content-Type: application/json

{
  "header": { "clientId": "...", "X-Token": "当前token", "X-Sign": "...", ... },
  "body": {}
}
```

### 6. 修改密码

```http
POST /api/v1/auth/change-password
Content-Type: application/json

{
  "header": { "clientId": "...", "X-Token": "当前token", "X-Sign": "...", ... },
  "body": {
    "old_password": "当前密码",
    "new_password": "新密码"
  }
}
```

校验规则：

- 旧密码 / 新密码不能为空
- 新密码长度 ≥ 6 位
- 新旧密码不能相同

## Android 示例（Kotlin）

```kotlin
import java.security.MessageDigest
import org.json.JSONObject

// ========== 签名工具 ==========
object SignUtil {
    val CLIENT_ID = "a3f8e9d1..."      // 编译时注入
    val CLIENT_SECRET = "b9c2..."       // 编译时注入

    fun sign(timestamp: String, nonce: String, token: String, body: JSONObject): String {
        val bodyJson = body.toString()  // key 排序、紧凑 JSON
        val raw = "$timestamp$nonce$token$bodyJson$CLIENT_SECRET"
        val md5 = MessageDigest.getInstance("MD5").digest(raw.toByteArray())
        return md5.joinToString("") { "%02x".format(it) }
    }
}

// ========== 请求体封装 ==========
data class ApiRequest(val header: JSONObject, val body: JSONObject)

fun buildRequest(token: String, body: JSONObject): ApiRequest {
    val timestamp = System.currentTimeMillis().toString()
    val nonce = UUID.randomUUID().toString()
    val sign = SignUtil.sign(timestamp, nonce, token, body)

    val header = JSONObject().apply {
        put("clientId", SignUtil.CLIENT_ID)
        put("X-Token", token)
        put("X-Timestamp", timestamp)
        put("X-Nonce", nonce)
        put("X-Sign", sign)
        // 设备信息
        put("platformType", "android")
        put("platformVersion", Build.VERSION.RELEASE)
        put("deviceBrand", Build.BRAND)
        put("deviceModel", Build.MODEL)
        put("sdkVersion", Build.VERSION.SDK_INT.toString())
        put("appVersion", BuildConfig.VERSION_NAME)
        put("appBuild", BuildConfig.VERSION_CODE.toString())
        put("appChannel", BuildConfig.FLAVOR ?: "official")
        put("appBuildType", if (BuildConfig.DEBUG) "debug" else "release")
        put("networkType", getNetworkType())
        put("screenWidth", resources.displayMetrics.widthPixels)
        put("screenHeight", resources.displayMetrics.heightPixels)
        put("screenDensity", resources.displayMetrics.density)
        put("language", Locale.getDefault().toLanguageTag())
        put("timezone", TimeZone.getDefault().id)
    }
    return ApiRequest(header, body)
}

// ========== API 调用 ==========
suspend fun login(username: String, password: String): LoginResult {
    val body = JSONObject().apply {
        put("username", username)
        put("password", password)
        put("tenant", "odoo.learn.dev")
    }
    val request = buildRequest(token = "", body = body)
    val response = api.post("/api/v1/auth/token", request)
    val data = response.body<ApiResponse<LoginData>>()
    saveToken(data.data.access_token, data.data.refresh_token)
    return LoginResult(data.data.user)
}

suspend fun refreshToken(): Boolean {
    val body = JSONObject().apply {
        put("grant_type", "refresh_token")
        put("refresh_token", getRefreshToken())
    }
    val request = buildRequest(token = "", body = body)
    val response = api.post("/api/v1/auth/refresh", request)
    val data = response.body<ApiResponse<LoginData>>()
    if (data.success) {
        saveToken(data.data.access_token, data.data.refresh_token)
        return true
    }
    return false
}

suspend fun logout() {
    val request = buildRequest(token = getAccessToken(), body = JSONObject())
    api.post("/api/v1/auth/logout", request)
    clearToken()
}

suspend fun changePassword(oldPwd: String, newPwd: String): Boolean {
    val body = JSONObject().apply {
        put("old_password", oldPwd)
        put("new_password", newPwd)
    }
    val request = buildRequest(token = getAccessToken(), body = body)
    val response = api.post("/api/v1/auth/change-password", request)
    return response.body<ApiResponse<Any>>().success
}

// ========== Token 自动刷新拦截器 ==========
class TokenInterceptor : Interceptor {
    override fun intercept(chain: Chain): Response {
        val original = chain.request()
        val request = buildRequest(getAccessToken(), parseBody(original))
        var response = chain.proceed(original.newBuilder()
            .post(request.toString().toRequestBody("application/json".toMediaType()))
            .build())

        if (response.code == 401 && refreshToken()) {
            // 用新 token 重试
            val retry = buildRequest(getAccessToken(), parseBody(original))
            response.close()
            response = chain.proceed(original.newBuilder()
                .post(retry.toString().toRequestBody("application/json".toMediaType()))
                .build())
        }
        return response
    }
}
```

## 安全特性

- **签名防篡改**：每个请求基于 clientSecret 签名，中间人无法伪造
- **时间戳防重放**：±5 分钟窗口，过期请求自动拒绝
- **Token 哈希存储**：SHA-256 存储，原文不落库
- **Token Rotation**：刷新时旧 Token 自动撤销
- **设备审计**：`header_data` 完整记录每次登录/登出的设备环境
- **过期清理**：定时任务每小时标记过期 Token
