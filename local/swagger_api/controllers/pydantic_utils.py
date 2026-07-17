# -*- coding: utf-8 -*-
"""Pydantic 模型 → OpenAPI Schema 转换工具"""
import inspect
import importlib
from typing import get_type_hints, get_origin, get_args, List, Optional

PYDANTIC_TYPE_MAP = {
    "string": "string",
    "integer": "integer",
    "number": "number",
    "boolean": "boolean",
    "array": "array",
    "object": "object",
}


def _py_type_to_openapi(py_type) -> str:
    """Python/Pydantic 类型 → OpenAPI type"""
    origin = get_origin(py_type)
    if origin is not None:
        # Optional[X] / List[X] 等泛型
        if origin is list or origin is List:
            return "array"
        args = get_args(py_type)
        # Optional[X] → X 的类型
        for arg in args:
            if arg is not type(None):
                return _py_type_to_openapi(arg)
    if py_type is str:
        return "string"
    if py_type is int:
        return "integer"
    if py_type is float:
        return "number"
    if py_type is bool:
        return "boolean"
    if py_type is dict:
        return "object"
    if py_type is list or py_type is List:
        return "array"
    return "string"


def pydantic_to_openapi_params(model_class) -> list:
    """将 Pydantic BaseModel 转为 OpenAPI parameters 列表"""
    params = []
    hints = get_type_hints(model_class)
    schema = model_class.model_json_schema()
    props = schema.get("properties", {})  # noqa
    required = set(schema.get("required", []))

    for field_name, field_info in model_class.model_fields.items():
        openapi_type = _py_type_to_openapi(hints.get(field_name, str))
        param = {
            "name": field_name,
            "type": openapi_type,
            "required": field_name in required,
            "description": (field_info.description or ""),
        }
        # 数字范围
        for meta in field_info.metadata:
            if hasattr(meta, 'ge'):
                param["minimum"] = meta.ge
            if hasattr(meta, 'le'):
                param["maximum"] = meta.le
            if hasattr(meta, 'min_length'):
                param["minLength"] = meta.min_length
        params.append(param)
    return params


def _get_module_schemas(func, schema_type):
    """
    自动发现 controller 方法对应的 Pydantic schema 类。

    查找顺序：
    1. 方法上的 _body_schema / _response_schema 属性（显式绑定）
    2. 同模块 controllers/ 目录下的 request_schemas.py / response_schemas.py（自动匹配）

    自动匹配规则：
    - 从 func.__module__ 提取 addon 名（如 learn_api）
    - 加载 {addon}.controllers.{schema_type}_schemas 模块
    - 按方法名驼峰 + Body/Response 后缀查找（如 search → SearchBody, SearchResponse）

    schema_type: "request" 或 "response"
    """
    # 方式1：显式绑定
    attr_name = f'_{schema_type}_schema' if schema_type == 'response' else '_body_schema'
    schema_cls = getattr(func, attr_name, None)
    if schema_cls:
        return schema_cls

    # 方式2：自动匹配
    module_path = func.__module__
    if not module_path.startswith("odoo.addons."):
        return None

    parts = module_path.split(".")
    addon_name = parts[2]  # odoo.addons.learn_api.controllers.search → learn_api
    func_name = func.__name__  # get_content_types

    try:
        mod = importlib.import_module(f"odoo.addons.{addon_name}.controllers.{schema_type}_schemas")
    except ImportError:
        return None

    # 方法名 → 类名：get_content_types → ContentTypes, search → Search, check_login → Login/CheckLogin
    name = func_name
    # 去掉常见前缀
    for prefix in ('get_', 'check_'):
        if name.startswith(prefix):
            name = name[len(prefix):]
            break
    class_name = ''.join(w.capitalize() for w in name.split('_'))

    suffix = 'Response' if schema_type == 'response' else 'Body'
    # 候选列表：LoginBody, CheckLoginBody（兼容带 Check 前缀的命名）
    candidates = [class_name + suffix]
    if not class_name.startswith('Check'):
        candidates.append('Check' + class_name + suffix)

    for cls_name, cls_obj in inspect.getmembers(mod, inspect.isclass):
        if cls_name in candidates and hasattr(cls_obj, 'model_fields'):
            return cls_obj
    return None


def find_body_schema_for_route(func) -> tuple:
    """
    查找 controller 方法对应的 Pydantic body schema。

    返回 (schema_class_or_None, full_json_schema)
    """
    schema_cls = _get_module_schemas(func, 'request')
    if schema_cls:
        return schema_cls, schema_cls.model_json_schema()
    return None, None


def find_response_schema_for_route(func) -> tuple:
    """
    查找 controller 方法对应的 Pydantic response schema。

    返回 (schema_class_or_None, data_field_schema_inline)
    data_field_schema 是已展开的 schema（不包含 $ref，引用类型已 inline 展开）
    """
    schema_cls = _get_module_schemas(func, 'response')
    if schema_cls and hasattr(schema_cls, 'model_json_schema'):
        json_schema = schema_cls.model_json_schema()
        props = json_schema.get("properties", {})
        data_prop = props.get("data")
        if data_prop:
            # 展开 $ref 为内联 schema
            return schema_cls, _inline_refs(data_prop, json_schema)
        return schema_cls, _inline_refs(json_schema, json_schema)
    return None, None


def _inline_refs(schema, root_schema):
    """递归展开 schema 中的 $ref 引用"""
    if not isinstance(schema, dict):
        return schema
    if '$ref' in schema:
        ref = schema['$ref']
        # 形如 "#/$defs/Foo" 或 "#/definitions/Foo"
        if ref.startswith('#/'):
            parts = ref[2:].split('/')
            target = root_schema
            for part in parts:
                target = target.get(part, {}) if isinstance(target, dict) else {}
            return _inline_refs(target, root_schema)
        return schema
    result = {}
    for k, v in schema.items():
        if k == '$defs' or k == 'definitions':
            continue  # 跳过定义字典本身
        if isinstance(v, dict):
            result[k] = _inline_refs(v, root_schema)
        elif isinstance(v, list):
            result[k] = [_inline_refs(item, root_schema) if isinstance(item, dict) else item for item in v]
        else:
            result[k] = v
    return result


def pydantic_response_to_openapi_example(model_class) -> Optional[dict]:
    """从 Pydantic 模型生成 OpenAPI response example"""
    if not model_class:
        return None
    try:
        # 生成一个示例实例
        example = _build_example(model_class)
        return example
    except (Exception,):
        return None


def _build_example(model_class, depth=0):
    """递归构建示例数据"""
    if depth > 3:
        return "..."
    hints = get_type_hints(model_class)
    result = {}
    for field_name, field_info in model_class.model_fields.items():
        py_type = hints.get(field_name, str)
        origin = get_origin(py_type)
        if origin is list or origin is List:
            args = get_args(py_type)
            item_type = args[0] if args else str
            if hasattr(item_type, 'model_fields'):
                result[field_name] = [_build_example(item_type, depth + 1)]
            else:
                result[field_name] = [_type_default(item_type)]
        elif hasattr(py_type, 'model_fields'):
            result[field_name] = _build_example(py_type, depth + 1)
        elif origin is not None:
            # Optional[X]
            for arg in get_args(py_type):
                if arg is not type(None):
                    result[field_name] = _type_default(arg)
                    break
        else:
            result[field_name] = _type_default(py_type)
    return result


def _type_default(py_type):
    """根据类型返回默认示例值"""
    if py_type is str:
        return "string"
    if py_type is int:
        return 0
    if py_type is float:
        return 0.0
    if py_type is bool:
        return True
    if py_type is dict:
        return {}
    return "..."
