# -*- coding: utf-8 -*-
"""
Swagger / OpenAPI 3.0 文档生成器

自动扫描所有已注册的 /api/ 路由，生成 OpenAPI 3.0 规范文档，
并提供 Swagger UI 和 ReDoc 交互式页面。
"""
import json
import re
import inspect
from odoo import http
from odoo.http import request, Response

SWAGGER_UI_HTML = """\
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>API 文档 - Swagger UI</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css" />
    <style>
        html { box-sizing: border-box; overflow-y: scroll; }
        *, *:before, *:after { box-sizing: inherit; }
        body { margin: 0; background: #fafafa; }
        .topbar { display:none; }
        .swagger-ui .info { margin:20px 0; }
    </style>
</head>
<body>
<div id="swagger-ui"></div>
<script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js" crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-standalone-preset.js" crossorigin="anonymous"></script>
<script>
window.onload = () => {
  window.ui = SwaggerUIBundle({
    url: "/api/swagger.json",
    dom_id: '#swagger-ui',
    deepLinking: true,
    presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
    plugins: [SwaggerUIBundle.plugins.DownloadUrl],
    layout: "StandaloneLayout",
    defaultModelsExpandDepth: -1,
    docExpansion: "list",
    filter: true,
    tryItOutEnabled: true,
  });
};
</script>
</body>
</html>
"""

REDOC_HTML = """\
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>API 文档 - ReDoc</title>
    <style>body { margin: 0; padding: 0; }</style>
</head>
<body>
<div id="redoc-container"></div>
<script src="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"></script>
<script>
Redoc.init('/api/swagger.json', {
    scrollYOffset: 0,
    hideDownloadButton: false,
    expandResponses: "200",
    nativeScrollbars: true,
}, document.getElementById('redoc-container'));
</script>
</body>
</html>
"""


class SwaggerController(http.Controller):
    """Swagger / OpenAPI 文档控制器"""

    @http.route("/api/swagger.json", type="http", auth="none", methods=["GET"], csrf=False)
    def swagger_json(self, **kwargs):  # noqa
        """生成 OpenAPI 3.0 JSON 文档"""
        spec = _build_openapi_spec()
        return Response(
            json.dumps(spec, ensure_ascii=False, indent=2, default=str),
            status=200,
            content_type="application/json; charset=utf-8",
        )

    @http.route("/api/swagger", type="http", auth="none", methods=["GET"], csrf=False)
    def swagger_ui(self, **kwargs):  # noqa
        """Swagger UI 交互式页面"""
        return Response(
            SWAGGER_UI_HTML,
            status=200,
            content_type="text/html; charset=utf-8",
        )

    @http.route("/api/swagger/redoc", type="http", auth="none", methods=["GET"], csrf=False)
    def swagger_redoc(self, **kwargs):  # noqa
        """ReDoc 文档页面"""
        return Response(
            REDOC_HTML,
            status=200,
            content_type="text/html; charset=utf-8",
        )


# ==================== OpenAPI Spec 生成逻辑 ====================

def _build_openapi_spec():
    """构建 OpenAPI 3.0 规范 JSON"""
    paths = _collect_api_paths()

    return {
        "openapi": "3.0.3",
        "info": {
            "title": "学习平台 REST API",
            "description": "学习平台 & App 管理 & 认证 API 文档",
            "version": "1.0.0",
            "contact": {
                "email": "ckf10000@sina.com",
            },
        },
        "servers": [
            {
                "url": "",
                "description": "当前服务器",
            },
        ],
        "paths": paths,
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "OAuth2.0 Access Token",
                    "description": "通过 /api/auth/token 获取 Access Token",
                },
            },
            "schemas": _define_schemas(),
        },
        "security": [
            {"BearerAuth": []},
        ],
        "tags": _define_tags(),
    }


def _collect_api_paths():
    """从 Odoo 路由表中收集所有 /api/ 前缀的路由"""
    paths = {}

    # 收集 nodb 路由（如 /api/auth/*）
    _collect_from_map(http.root.nodb_routing_map, paths)

    # 收集 db 路由（需要数据库的路由）
    try:
        if request and hasattr(request, 'env') and request.env:
            db_map = request.env['ir.http'].routing_map()
            _collect_from_map(db_map, paths)
    except (Exception,):
        pass

    return dict(sorted(paths.items()))


def _collect_from_map(routing_map, paths):
    """从 werkzeug routing map 中提取路由信息"""
    for rule in routing_map.iter_rules():
        rule_str = rule.rule
        # 只收集 /api/ 前缀的路由
        if not rule_str.startswith('/api/'):
            continue

        # 去掉末尾的斜杠变体（werkzeug 的 strict_slashes）
        if rule_str.endswith('/'):
            continue

        methods = sorted(rule.methods - {'HEAD', 'OPTIONS'})
        if not methods:
            continue

        # 获取端点信息
        endpoint = rule.endpoint
        description = ""
        tag = "api"
        body_params = []
        query_params = []
        response_example = None

        # 尝试从 endpoint 提取元数据
        original_endpoint = _get_original_endpoint(endpoint)
        if original_endpoint:
            description = _extract_description(original_endpoint)
            tag = _infer_tag(original_endpoint)
            body_params = _extract_body_params(original_endpoint)
            query_params = _extract_query_params(original_endpoint)
            response_example = _extract_response_example(original_endpoint)

        routing = _get_routing(endpoint)

        # 构建 OpenAPI path item
        path_key = _convert_path_params(rule_str)

        if path_key not in paths:
            paths[path_key] = {}

        for method in methods:
            operation = {
                "tags": [tag],
                "summary": description.split("\n")[0] if description else rule_str,
                "description": description,
                "operationId": f"{method.lower()}_{_safe_operation_id(rule_str)}",
                "responses": {
                    "200": _build_response(routing, response_example),
                    "401": {"description": "未认证 - Token 无效或已过期"},
                    "403": {"description": "无权限"},
                    "500": {"description": "服务器内部错误"},
                },
            }

            # 请求参数
            params = []
            for p in query_params:
                params.append({
                    "name": p["name"],
                    "in": "query",
                    "required": p.get("required", False),
                    "schema": {"type": p.get("type", "string")},
                    "description": p.get("description", ""),
                })
            if params:
                operation["parameters"] = params

            # 请求体
            if method in ("POST", "PUT", "PATCH") and body_params:
                schema = _build_body_schema(body_params)
                operation["requestBody"] = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": schema,
                        },
                    },
                }

            # 如果是 JSON 类型接口且有认证要求
            if routing.get('type') != 'json' or routing.get('auth') == 'none':
                operation["security"] = []

            paths[path_key][method.lower()] = operation

    return paths


def _get_original_endpoint(endpoint):
    """获取原始（未被装饰器包装的）端点函数"""
    # endpoint 可能是 route_wrapper，其 original_endpoint 属性指向原始方法
    if hasattr(endpoint, 'original_endpoint'):
        return endpoint.original_endpoint
    if hasattr(endpoint, '__wrapped__'):
        return endpoint.__wrapped__
    return endpoint


def _get_routing(endpoint):
    """获取路由配置"""
    if hasattr(endpoint, 'original_routing'):
        return endpoint.original_routing
    if hasattr(endpoint, 'routing'):
        return endpoint.routing
    return {}


def _convert_path_params(rule_str):
    """将 Odoo 路由参数转换为 OpenAPI 风格
    /api/learn/v1/contents/<int:content_id> → /api/learn/v1/contents/{content_id}
    """
    return re.sub(r'<[^:]+:([^>]+)>', r'{\1}', rule_str)  # noqa


def _safe_operation_id(rule_str):
    """生成安全的 operationId"""
    clean = re.sub(r'[<>:]', '_', rule_str)
    clean = re.sub(r'[^a-zA-Z0-9_/]', '', clean)
    return clean.replace('/', '_').strip('_')


def _extract_description(func):
    """从函数 docstring 提取描述"""
    doc = inspect.getdoc(func)
    if not doc:
        return ""
    # 取第一段（在空行之前）
    parts = doc.split('\n\n', 1)
    return parts[0].strip()


# 缓存模块显示名称，避免重复查询 ir.module.module
_module_display_cache = {}


def _get_module_display_name(technical_name):
    """从 ir.module.module 获取模块显示名称，失败则回退到格式化后的技术名"""
    if technical_name in _module_display_cache:
        return _module_display_cache[technical_name]

    try:
        if request and hasattr(request, 'env') and request.env:
            module = request.env['ir.module.module'].sudo().search([
                ('name', '=', technical_name),
            ], limit=1)
            if module and module.shortdesc:
                display = module.shortdesc
                _module_display_cache[technical_name] = display
                return display
    except (Exception,):
        pass

    # 回退：technical_name → 友好格式
    fallback = technical_name.replace('_', ' ').title()
    _module_display_cache[technical_name] = fallback
    return fallback


def _infer_tag(original_endpoint):
    """从端点函数的所属模块动态推断 API 分组标签"""
    if not original_endpoint:
        return "其他"
    module_path = getattr(original_endpoint, '__module__', '')
    # odoo.addons.learn_api.controllers.main → learn_api
    match = re.search(r'odoo\.addons\.(\w+)', module_path)  # noqa
    if match:
        return _get_module_display_name(match.group(1))
    return "其他"


def _extract_body_params(func):
    """尝试从 docstring 提取请求体参数"""
    doc = inspect.getdoc(func)
    if not doc:
        return []

    params = []
    # 查找常见的参数描述模式
    # 模式1: "param_name": 类型,  // 描述
    # 模式2: 在 Request Body 中找到的 JSON 示例
    lines = doc.split('\n')
    in_body = False
    for line in lines:
        stripped = line.strip()
        if any(kw in stripped for kw in ('Request Body', 'request body', '请求体')):
            in_body = True
            continue
        if in_body and stripped.startswith('{'):
            continue
        if in_body and stripped.startswith('}'):
            in_body = False
            continue
        # 只在请求体 JSON 范围内匹配参数，避免混入响应的 JSON 字段
        if in_body:
            match = re.match(r'"(\w+)":\s*(.+?)(?:\s*//\s*(.*))?$', stripped)  # noqa
            if match:
                key = match.group(1)
                value_str = match.group(2).strip().rstrip(',')
                # 跳过嵌套对象的 key（如 "data": {、"user": {）
                if value_str in ('{', '[', '}', ']'):
                    continue
                desc = match.group(3) or ""
                ptype = _infer_type(value_str)
                params.append({
                    "name": key,
                    "type": ptype,
                    "required": "可选" not in desc,
                    "description": desc,
                })

    # 如果没有从 JSON 示例提取到参数，尝试从纯文本提取
    if not params:
        for line in lines:
            # 匹配: param_name (类型): 描述
            match = re.match(r'(\w+)\s*(?:\((\w+)\))?\s*[:：]\s*(.+)', line.strip())  # noqa
            if match and not match.group(1).startswith(('Response', '响应')):
                name = match.group(1)
                ptype = match.group(2) or "string"
                desc = match.group(3)
                if name not in ('Request', 'Body', 'JSON', 'response', 'data'):
                    params.append({
                        "name": name,
                        "type": ptype,
                        "required": True,
                        "description": desc,
                    })

    return params


def _extract_query_params(func):
    """尝试从 docstring 提取查询参数"""
    doc = inspect.getdoc(func)
    if not doc:
        return []

    params = []
    lines = doc.split('\n')
    for line in lines:
        stripped = line.strip()
        # 匹配: param_name (类型, 可选): 描述
        match = re.match(r'(\w+)\s*\((\w+)(?:,\s*可选)?\)\s*[:：]\s*(.+)', stripped)  # noqa
        if match:
            params.append({
                "name": match.group(1),
                "type": match.group(2),
                "required": "可选" not in stripped,
                "description": match.group(3),
            })
    return params


def _extract_response_example(func):
    """尝试从 docstring 提取响应示例"""
    doc = inspect.getdoc(func)
    if not doc:
        return None

    # 查找 Response: 后面的 JSON 示例
    lines = doc.split('\n')
    in_response = False
    json_lines = []
    brace_count = 0

    for line in lines:
        if 'Response' in line or 'response' in line.lower():
            # 检查是否是 Response: 或 Response Body:
            if re.match(r'\s*Response\s*[:：]?\s*$', line) or 'Response Body' in line:
                in_response = True
                continue
        if in_response and '{' in line:
            json_lines.append(line)
            brace_count += line.count('{') - line.count('}')
            if brace_count == 0 and len(json_lines) > 1:
                break
        elif in_response and json_lines:
            json_lines.append(line)
            brace_count += line.count('{') - line.count('}')
            if brace_count == 0:
                break

    if json_lines:
        return '\n'.join(json_lines)
    return None


def _infer_type(value_str):
    """从示例值推断 JSON 类型"""
    value_str = value_str.strip().rstrip(',')
    if value_str in ('true', 'false'):
        return "boolean"
    if value_str.startswith('"') and value_str.endswith('"'):
        return "string"
    if value_str.isdigit():
        return "integer"
    if re.match(r'^\d+\.\d+$', value_str):
        return "number"
    if value_str.startswith('['):
        return "array"
    if value_str.startswith('{'):
        return "object"
    return "string"


def _build_body_schema(params):
    """从参数列表构建请求体 JSON Schema"""
    properties = {}
    required = []
    for p in params:
        prop = {"type": p["type"], "description": p.get("description", "")}
        properties[p["name"]] = prop
        if p.get("required"):
            required.append(p["name"])
    schema = {
        "type": "object",
        "properties": properties,
    }
    if required:
        schema["required"] = required
    return schema


def _build_response(routing, example):
    """构建响应 schema"""
    resp = {"description": "成功"}
    if routing.get('type') == 'json':
        schema = {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "message": {"type": "string"},
                "data": {"type": "object"},
            },
        }
        resp["content"] = {
            "application/json": {
                "schema": schema,
            },
        }
        if example:
            resp["content"]["application/json"]["example"] = _safe_json_parse(example)
    return resp


def _safe_json_parse(text):
    """安全尝试解析 JSON 示例"""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None


def _define_tags():
    """动态生成标签列表（基于实际已扫描到的 API 模块）"""
    tags = []
    for name in sorted(_module_display_cache.values()):
        tags.append({"name": name, "description": name})
    if "其他" not in _module_display_cache.values():
        tags.append({"name": "其他", "description": "其他接口"})
    return tags


def _define_schemas():
    """定义公共 Schema"""
    return {
        "Error": {
            "type": "object",
            "properties": {
                "success": {"type": "boolean", "example": False},
                "message": {"type": "string"},
                "error": {"type": "string"},
            },
        },
        "AuthRequest": {
            "type": "object",
            "required": ["login", "password"],
            "properties": {
                "login": {"type": "string", "description": "用户名或邮箱"},
                "password": {"type": "string", "description": "密码"},
                "client_id": {"type": "string", "description": "OAuth 客户端 ID"},
            },
        },
        "AuthResponse": {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "data": {
                    "type": "object",
                    "properties": {
                        "access_token": {"type": "string"},
                        "refresh_token": {"type": "string"},
                        "token_type": {"type": "string", "example": "Bearer"},
                        "expires_in": {"type": "integer"},
                        "user": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer"},
                                "login": {"type": "string"},
                                "name": {"type": "string"},
                                "email": {"type": "string"},
                            },
                        },
                    },
                },
            },
        },
    }
