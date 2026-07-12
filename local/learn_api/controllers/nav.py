# -*- coding: utf-8 -*-
"""导航 / 首页 / 选择器查询 API"""
from odoo import http
from odoo.http import request

from .common import json_response, error_response, api_verify_auth, encode_image, ALL_TAB, DIM_CHAIN  # noqa


class LearnHomeController(http.Controller):

    @http.route("/api/v1/learn/home_subcategories", type="http", auth="public", methods=["POST"], csrf=False)
    def get_home_subcategories(self, **kw):  # noqa
        """首页聚合：按分类编码返回该分类下的 selector 分组数据

        请求体 (JSON):
        {
            "header": { "clientId": "xxx", "X-Token": "xxx", "X-Timestamp": "...", "X-Nonce": "...", "X-Sign": "..." },
            "body": {
                "category_code": "NINE_YEAR"  // 可选，不传则返回所有分类
            }
        }

        响应:
        {
            "success": true,
            "data": [
                {
                    "category": {"id": 5, "name": "中小学", "code": "NINE_YEAR"},
                    "subcategories": [...]
                }
            ]
        }
        """
        try:
            header, body, user = api_verify_auth(require_token=True)
            category_code = body.get("category_code")
            # 首页特殊编码 → 返回全部分类
            if category_code == ALL_TAB[1]:
                category_code = None
            ctx_lang = user.lang or request.env.context.get('lang', 'zh_CN')

            DimCat = request.env['learn.dim.category'].sudo().with_context(lang=ctx_lang)
            Selector = request.env['learn.selector'].sudo()

            # 确定要查询的分类列表
            if category_code:
                cat = DimCat.search([('code', '=', category_code)], limit=1)
                if not cat:
                    return error_response('分类不存在', status=404)
                cats = cat
            else:
                cats = DimCat.search([('active', '=', True)], order='sequence')

            groups = []
            for c in cats:
                selectors = Selector.search(
                    [('category_id', '=', c.id), ('active', '=', True)],
                    order='sequence'
                )
                # subcategories 按 stage 去重，只取 stage 维度
                items = []
                seen_stages = set()
                for s in selectors:
                    stage_code = s.stage_id.code if s.stage_id else ""
                    if stage_code and stage_code not in seen_stages:
                        seen_stages.add(stage_code)
                        items.append({
                            "id": s.stage_id.id,
                            "name": s.stage_id.name,
                            "code": stage_code,
                            "sequence": s.sequence,
                        })

                groups.append({
                    "category": {"id": c.id, "name": c.name, "code": c.code},
                    "subcategories": items,
                })

            return json_response(data=groups)

        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))


class LearnSelectorController(http.Controller):

    @http.route("/api/v1/learn/tab_selector", type="http", auth="public", methods=["POST"], csrf=False)
    def get_tab_selector(self, **kw):  # noqa
        """获取选择器维度树（动态层级：category → stage → class → region → version → year → semester → subject）

        请求体 (JSON):
        {
            "header": { "clientId": "xxx", "X-Timestamp": "...", "X-Nonce": "...", "X-Sign": "..." },
            "body": {
                "category_code": "NINE_YEAR",       // 可选，分类编码
                "sub_category_code": "PRIMARY"       // 可选，阶段编码（需传 category_code）
            }
        }

        - 无参：root = category，最多全量 7 层，同一个前缀路径下，某个维度要么全配、要么全缺，末层永远是 subject
        - 有 category_code：root = stage，该分类下最多 6 层，同一个前缀路径下，某个维度要么全配、要么全缺，末层永远是 subject
        - 有 category_code + sub_category_code：root = class，该阶段下 最多 5 层，同一个前缀路径下，某个维度要么全配、要么全缺，末层永远是 subject
        任一条件下无数据则返回空列表。

        返回 (JSON):
        {
            "success": true,
            "data": {
                "default_condition": [
                    {"id": 20, "name": "一年级", "code": "GRADE_1", "dim_type":"class", "dim_desc":"年级","children": [
                        {"id": 30, "name": "广东", "code": "GD", "dim_type":"rejoin", "dim_desc":"区域", "children": [
                            {
                                "id": 40, "name": "人教版", "code": "PEP", "dim_type":"version",
                                "dim_desc":"版本", "children": [
                                {
                                    "id": 50, "name": "2026", "code": "2026", "dim_type":"year",
                                    "dim_desc":"年份", "children": [
                                    {
                                        "id": 60, "name": "上册", "code": "UP",
                                        "dim_type":"semester", "dim_desc":"学期", "children": [
                                        {
                                            "id": 70, "name": "语文", "code": "CHINESE",
                                            "selector_code": "NINE_YEAR_PRIMARY_GRADE_1_PEP_2026_UP_CHINESE",
                                            "dim_type":"subject", "dim_desc":"科目", "children":[]
                                    ]}
                                ]}
                            ]}
                        ]}
                    ]}
                ],
                "conditions": [
                    {"
                        id": 20, "name": "一年级", "code": "GRADE_1", "sequence": 10,
                        "dim_type":"class", "dim_desc":"年级", "children": [...]
                    },
                    {
                        "id": 30, "name": "二年级", "code": "GRADE_2", "sequence": 20,
                        "dim_type":"class", "dim_desc":"年级", "children": [...]
                    },
                    {
                        "id": 40, "name": "三年级", "code": "GRADE_3", "sequence": 30,
                        "dim_type":"class", "dim_desc":"年级", "children": [...]
                    }
                ]
            }
        }
        """
        try:
            header, body, user = api_verify_auth(require_token=True)

            category_code = body.get("category_code")
            sub_category_code = body.get("sub_category_code", "")
            ctx_lang = user.lang or request.env.context.get('lang', 'zh_CN')

            Selector = request.env['learn.selector'].sudo().with_context(lang=ctx_lang)
            domain = [('active', '=', True)]

            # 确定起始层级 offset 并过滤
            if category_code:
                cat = request.env['learn.dim.category'].sudo().with_context(lang=ctx_lang).search(
                    [('code', '=', category_code)], limit=1
                )
                if not cat:
                    return error_response('分类不存在', status=404)
                domain.append(('category_id', '=', cat.id))
                start_offset = 1  # root = stage

                if sub_category_code:
                    stage = request.env['learn.dim.stage'].sudo().with_context(lang=ctx_lang).search(
                        [('code', '=', sub_category_code)], limit=1
                    )
                    if not stage:
                        return error_response('阶段不存在', status=404)
                    domain.append(('stage_id', '=', stage.id))
                    start_offset = 2  # root = class
            else:
                start_offset = 0  # root = category

            selectors = Selector.search(domain, order='sequence')

            if not selectors:
                return json_response(data={
                    "default_condition": [],
                    "conditions": [],
                })

            # ---------- 递归构建树 ----------
            from collections import OrderedDict

            def build_level(sels, level_idx):
                """从 sels 中按 DIM_CHAIN[level_idx] 维度分组，递归构建子树"""
                if level_idx >= len(DIM_CHAIN) or not sels:
                    return []

                field_name, dim_type, dim_desc = DIM_CHAIN[level_idx]
                groups = OrderedDict()
                s_map = {s.id: s for s in sels}

                for s in sels:
                    if field_name == "region_ids":
                        recs = s.region_ids
                    else:
                        obj = s[field_name]
                        recs = [obj] if obj else []

                    for rec in recs:
                        code = rec.code
                        if code not in groups:
                            groups[code] = {"obj": rec, "sel_ids": set()}
                        groups[code]["sel_ids"].add(s.id)

                # 当前维度所有 selector 均未配置 → 跳过，继续下一个维度
                if not groups:
                    return build_level(sels, level_idx + 1)

                nodes = []
                for code, gdata in groups.items():
                    child_sels = [s_map[sid] for sid in gdata["sel_ids"]]
                    children = build_level(child_sels, level_idx + 1)
                    # 排序用组内 selector 的最小 sequence，而非维度表的 sequence
                    min_sel_seq = min(s.sequence for s in child_sels) if child_sels else gdata["obj"].sequence
                    node = {
                        "id": gdata["obj"].id,
                        "name": gdata["obj"].name,
                        "code": code,
                        "sequence": min_sel_seq,
                        "dim_type": dim_type,
                        "dim_desc": dim_desc,
                        "children": children,
                    }
                    # 最内层 subject 节点携带 selector_code
                    if dim_type == "subject" and child_sels:
                        node["selector_code"] = child_sels[0].code
                    nodes.append(node)

                nodes.sort(key=lambda x: x["sequence"])
                return nodes

            conditions = build_level(selectors, start_offset)

            # ---------- 递归取第一条路径 ----------
            _pick_keys = ("id", "name", "code", "sequence", "dim_type", "dim_desc")

            def _pick_first(node):
                copy = {k: node[k] for k in _pick_keys if k in node}
                if "selector_code" in node:
                    copy["selector_code"] = node["selector_code"]
                copy["children"] = [_pick_first(node["children"][0])] if node["children"] else []
                return copy

            default_condition = [_pick_first(conditions[0])] if conditions else []
            return json_response(data={
                "default_condition": default_condition,
                "conditions": conditions,
            })

        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))


class LearnNavController(http.Controller):

    @http.route("/api/v1/learn/nav_tabs", type="http", auth="public", methods=["POST"], csrf=False)
    def get_nav_tabs(self, **kw):  # noqa
        """获取底部导航 Tab 列表

        请求体 (JSON):
        {
            "header": { "clientId": "xxx", "X-Token": "xxx", "X-Timestamp": "...", "X-Nonce": "...", "X-Sign": "..." },
            "body": {}
        }

        响应:
        {
            "success": true,
            "data": [
                {
                    "id": 0,
                    "code": "all",
                    "name": "全部",
                    "nav_icon": null,
                    "nav_icon_active": null,
                    "is_home": true,
                    "sequence": 0
                },
                {
                    "id": 5,
                    "code": "deyu",
                    "name": "德育",
                    "nav_icon": "base64...",
                    "nav_icon_active": "base64...",
                    "is_home": false,
                    "sequence": 10
                }
            ]
        }
        """
        try:
            header, body, user = api_verify_auth(require_token=True)  # noqa

            tabs = [{
                "id": ALL_TAB[0],
                "code": ALL_TAB[1],
                "name": ALL_TAB[2],
                "nav_icon": None,
                "nav_icon_active": None,
                "sequence": 0,
                "is_home": True,
            }]

            ctx_lang = user.lang or request.env.context.get('lang', 'zh_CN')
            categories = request.env["learn.dim.category"].sudo().with_context(lang=ctx_lang).search([
                ("active", "=", True),
            ], order="sequence, id")

            for cat in categories:
                tabs.append({
                    "id": cat.id,
                    "code": cat.code,
                    "name": cat.name,
                    "nav_icon": encode_image(cat.icon),
                    "nav_icon_active": None,
                    "sequence": cat.sequence,
                    "is_home": False,
                })

            return json_response(data=tabs)

        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))
