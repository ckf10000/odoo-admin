# Swagger API - OpenAPI 文档模块

自动扫描 Odoo 中所有 `/api/v1/` 前缀的路由，生成 **OpenAPI 3.0** 规范文档，并提供 **Swagger UI** 和 **ReDoc** 交互式页面。

## 快速开始

```bash
# 启动 Odoo
python odoo-bin -c odoo.windows.conf

# 浏览器访问
http://localhost:8069/api/swagger       # Swagger UI（推荐）
http://localhost:8069/api/swagger/redoc  # ReDoc
http://localhost:8069/api/swagger.json   # OpenAPI 3.0 JSON
```

## 使用流程

1. 在 Odoo 应用列表搜索 `Swagger`，点击安装
2. 打开 `http://localhost:8069/api/swagger`
3. 先调用 `/api/v1/auth/token` 登录获取 `access_token`
4. 直接 **Try it out** 测试各接口（需按统一请求格式构造 body）

## 模块依赖

```
base（Odoo 核心）
```

无需额外依赖 `common_lib`、`auth_api` 等——该模块只做路由扫描和文档生成，不耦合业务模块。

## 支持的接口分组

| Tag      | 描述                   | 来源模块             |
|----------|----------------------|------------------|
| 认证 Auth  | OAuth2.0 登录/登出/Token | `auth_api`       |
| 学习 - 分类  | 内容分类树                | `learn_api`      |
| 学习 - 内容  | 内容列表/详情/PDF          | `learn_api`      |
| 学习 - 答题  | 试卷答题/批阅/成绩           | `learn_api`      |
| 学习 - 错题本 | 错题管理                 | `learn_api`      |
| 学习 - 收藏  | 内容收藏                 | `learn_api`      |
| 学习 - 批注  | PDF 批注               | `learn_api`      |
| 学习 - 笔记  | 学习笔记                 | `learn_api`      |
| 学习 - 评论  | 评分与评论                | `learn_api`      |
| App 校验   | 版本/插件/素材/终端/渠道       | `app_manage_api` |

## 如何让新接口出现在文档中

只要符合以下条件，接口就会自动被收录：

1. 路由路径以 `/api/v1/` 开头
2. 使用 `@http.route` 装饰器注册
3. 模块已安装且正常加载

**最佳实践**：在接口的 docstring 中按以下格式写参数说明，文档会自动提取：

```python
@http.route("/api/v1/example/hello", type="http", auth="public", methods=["POST"], csrf=False)
def hello(self, **kwargs):
    """简短描述（会显示为接口摘要）

    详细描述（会显示为接口详细说明）

    Request Body (JSON):
    {
        "name": "张三",       // 用户姓名
        "age": 25,            // 年龄
        "optional_field": ""  // 可选字段
    }

    Response:
    {
        "success": true,
        "data": {
            "greeting": "Hello, 张三"
        }
    }
    """
    ...
```

- 以 `"key": value // description` 格式写的请求参数会被自动提取为 Schema
- `Response:` 后面的 JSON 会被提取为响应示例

## 工作原理

```
启动 Odoo
   │
   ├── 模块加载 → odoo.http._generate_routing_rules() 扫描所有模块
   │
   └── 请求 /api/swagger.json
         │
         ├── 从 nodb_routing_map 收集无数据库路由（如 /api/v1/auth/*）
         ├── 从 ir.http.routing_map() 收集数据库路由
         ├── 遍历所有 /api/v1/ 前缀的 Rule
         │     ├── 提取路径、HTTP 方法
         │     ├── 从 endpoint.original_endpoint 获取原始函数
         │     ├── 解析 docstring → 描述、参数、响应示例
         │     └── 按路径前缀推断 Tag 分组
         └── 输出 OpenAPI 3.0 JSON
```

Swagger UI 和 ReDoc 页面通过 **CDN** 加载前端资源，模块本身不打包 JS 文件。
