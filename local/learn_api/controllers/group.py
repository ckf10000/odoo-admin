# -*- coding: utf-8 -*-
"""内容组详情 API"""
from odoo import http
from odoo.http import request

from .common import json_response, error_response, api_verify_auth, encode_image  # noqa


class LearnGroupController(http.Controller):

    @http.route("/api/v1/learn/group/<int:group_id>/sections", type="http", auth="public", methods=["POST"], csrf=False)
    def get_group_sections(self, group_id, **kw):  # noqa
        """获取内容组下所有章节及其条目

        Request Body:
        { "header": {...}, "body": {} }

        Response:
        {
            "success": true,
            "data": {
                "group": {"id": 1, "name": "Unit 1 单元测试"},
                "sections": [
                    {
                        "id": 10, "name": "第一部分：单词默写", "sequence": 10,
                        "content_type": "word_dictation", "score": 20.0,
                        "lines": [
                            {"id": 1, "sequence": 10, "content_type": "word_dictation",
                             "score": 2.0, "word": {"id": 5, "name": "apple", ...}},
                            ...
                        ]
                    },
                    {
                        "id": 20, "name": "第二部分：单选题", "sequence": 20,
                        "content_type": "single_choice", "score": 30.0,
                        "lines": [
                            {"id": 6, "sequence": 10, "content_type": "single_choice",
                             "score": 6.0, "question": {"id": 3, "stem": "1+1=?", ...}},
                            ...
                        ]
                    }
                ]
            }
        }
        """
        try:
            header, body, user = api_verify_auth(require_token=True)  # noqa
            ctx_lang = user.lang or request.env.context.get('lang', 'zh_CN')

            Group = request.env['learn.group'].sudo().with_context(lang=ctx_lang)
            group = Group.browse(group_id)
            if not group.exists():
                return error_response("内容组不存在", status=404)

            sections_data = []
            for section in group.section_ids.sorted('sequence'):
                sec = {
                    "id": section.id,
                    "name": section.name,
                    "sequence": section.sequence,
                    "content_type": section.content_type,
                    "score": section.score,
                    "lines": [],
                }
                for line in section.line_ids.sorted('sequence'):
                    item = {
                        "id": line.id, "sequence": line.sequence,
                        "content_type": section.content_type,
                        "score": line.score,
                    }
                    # 根据 res_model 填充数据
                    if line.res_model == 'learn.phrase' and line.phrase_id:
                        p = line.phrase_id
                        item["phrase"] = {
                            "id": p.id, "name": p.name,
                            "phrase_type": p.phrase_type,
                            "ref_model": p.ref_model,
                        }
                        # 展开 phrase 的原子数据
                        if p.ref_model == 'learn.word' and p.word_id:
                            w = p.word_id
                            item["word"] = {  # noqa
                                "id": w.id, "name": w.name, "phonetic": w.phonetic,
                                "meaning": w.meaning, "meaning_en": w.meaning_en or "",
                                "example_sentence": w.example_sentence or "",
                                "phrases": w.phrases or "", "difficulty": w.difficulty,
                                "pos": [{"id": pos.id, "name": pos.name, "code": pos.code} for pos in w.pos_ids],
                            }
                        elif p.ref_model == 'learn.character' and p.character_id:
                            ch = p.character_id
                            item["character"] = {
                                "id": ch.id, "name": ch.name,
                                "pinyin": ch.pinyin or "", "strokes": ch.strokes or 0,
                                "radical": ch.radical or "", "meaning": ch.meaning or "",
                                "phrases": ch.phrases or "", "difficulty": ch.difficulty,
                            }
                    elif line.res_model == 'learn.word' and line.word_id:
                        w = line.word_id
                        item["word"] = {
                            "id": w.id, "name": w.name, "phonetic": w.phonetic,
                            "meaning": w.meaning, "part_of_speech": w.part_of_speech,
                            "difficulty": w.difficulty,
                        }
                    elif line.res_model == 'learn.character' and line.character_id:
                        ch = line.character_id
                        item["character"] = {
                            "id": ch.id, "name": ch.name,
                            "pinyin": ch.pinyin or "", "strokes": ch.strokes or 0,
                            "radical": ch.radical or "", "meaning": ch.meaning or "",
                            "phrases": ch.phrases or "", "difficulty": ch.difficulty,
                        }
                    elif line.res_model == 'learn.question' and line.question_id:
                        q = line.question_id
                        item["question"] = {
                            "id": q.id, "question_type": q.question_type,
                            "stem": q.stem,
                            "stem_image": encode_image(q.stem_image) if q.stem_image else None,
                            "options": {
                                "A": q.option_a, "B": q.option_b, "C": q.option_c,
                                "D": q.option_d, "E": q.option_e, "F": q.option_f,
                            } if q.question_type in ("single_choice", "multi_choice") else None,
                            "score": q.score, "difficulty": q.difficulty,
                        }
                    elif line.res_model == 'learn.media' and line.media_id:
                        m = line.media_id
                        item["media"] = {
                            "id": m.id, "name": m.name, "media_type": m.media_type,
                            "url": m.url, "file_name": m.file_name, "duration": m.duration,
                        }
                    elif line.res_model == 'learn.article' and line.article_id:
                        a = line.article_id
                        item["article"] = {
                            "id": a.id, "name": a.name, "article_type": a.article_type,
                            "content": a.content, "tags": a.tags,
                        }
                    sec["lines"].append(item)
                sections_data.append(sec)

            return json_response(data={
                "group": {"id": group.id, "name": group.name},
                "sections": sections_data,
            })
        except ValueError as e:
            return error_response(str(e), status=401)
        except Exception as e:
            return error_response(str(e))
