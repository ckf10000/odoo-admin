# -*- coding: utf-8 -*-
"""知识库原子数据模型：音频、视频、文档、图片、题目库"""
from odoo import models, fields, api


class LearnWord(models.Model):
    _name = 'learn.word'
    _description = '单词'
    _order = 'sequence, id'

    name = fields.Char(string='单词', required=True, index=True)
    phonetic = fields.Char(string='音标')
    pos_ids = fields.Many2many(
        'learn.word.pos', 'learn_word_pos_rel', 'word_id', 'pos_id', string='词性',
    )
    meaning = fields.Char(string='中文释义', index=True)
    meaning_en = fields.Text(string='英文释义')
    example_sentence = fields.Text(string='例句')
    phrases = fields.Text(string='关联短语')
    etymology = fields.Text(string='词源解释')

    source_ids = fields.Many2many(
        'learn.content.source', 'learn_word_source_rel', 'word_id', 'source_id', string='来源',
    )
    difficulty = fields.Selection([
        ('easy', '简单'),
        ('medium', '中等'),
        ('hard', '困难'),
    ], string='难度', default='easy')

    sequence = fields.Integer(string='排序', default=10)
    active = fields.Boolean(string='启用', default=True)
    description = fields.Text(string='备注')

    group_line_ids = fields.One2many('learn.group.line', 'word_id', string='所属内容组')

    @api.model_create_multi
    def create(self, vals_list):
        new_vals = []
        existing_records = self.browse()
        for vals in vals_list:
            existing = self.sudo().search([('name', '=', vals.get('name'))], limit=1)
            if existing:
                # 如果已存在，追加新的 source_ids
                new_sources = vals.get('source_ids')
                if new_sources:
                    existing.sudo().write({'source_ids': new_sources})
                existing_records += existing
                continue
            new_vals.append(vals)
        records = super().create(new_vals) if new_vals else self.browse()
        return records + existing_records

    _sql_constraints = [
        ('unique_word', 'UNIQUE(name)', '该单词已存在！'),
    ]


class LearnCharacter(models.Model):
    _name = 'learn.character'
    _description = '生字'
    _order = 'sequence, id'

    name = fields.Char(string='生字', required=True, index=True)
    pinyin = fields.Char(string='拼音')
    strokes = fields.Integer(string='笔画')
    radical = fields.Char(string='部首')
    meaning = fields.Text(string='释义')
    phrases = fields.Text(string='组词')

    source_ids = fields.Many2many(
        'learn.content.source', 'learn_character_source_rel', 'character_id', 'source_id', string='来源',
    )
    difficulty = fields.Selection([
        ('easy', '简单'),
        ('medium', '中等'),
        ('hard', '困难'),
    ], string='难度', default='easy')

    sequence = fields.Integer(string='排序', default=10)
    active = fields.Boolean(string='启用', default=True)
    description = fields.Text(string='备注')

    group_line_ids = fields.One2many('learn.group.line', 'character_id', string='所属内容组')

    @api.model_create_multi
    def create(self, vals_list):
        new_vals = []
        existing_records = self.browse()
        for vals in vals_list:
            existing = self.sudo().search([('name', '=', vals.get('name'))], limit=1)
            if existing:
                new_sources = vals.get('source_ids')
                if new_sources:
                    existing.sudo().write({'source_ids': new_sources})
                existing_records += existing
                continue
            new_vals.append(vals)
        records = super().create(new_vals) if new_vals else self.browse()
        return records + existing_records

    _sql_constraints = [
        ('unique_character', 'UNIQUE(name)', '该生字已存在！'),
    ]


class LearnAudio(models.Model):
    _name = 'learn.audio'
    _description = '音频'
    _order = 'sequence, id'

    name = fields.Char(string='名称', required=True)
    url = fields.Char(string='音频链接')
    file_data = fields.Binary(string='音频文件', attachment=True)
    file_name = fields.Char(string='文件名')
    duration = fields.Integer(string='时长（秒）')
    description = fields.Text(string='描述')
    sequence = fields.Integer(string='排序', default=10)
    active = fields.Boolean(string='启用', default=True)


class LearnVideo(models.Model):
    _name = 'learn.video'
    _description = '视频'
    _order = 'sequence, id'

    name = fields.Char(string='名称', required=True)
    url = fields.Char(string='视频链接')
    file_data = fields.Binary(string='视频文件', attachment=True)
    file_name = fields.Char(string='文件名')
    duration = fields.Integer(string='时长（秒）')
    description = fields.Text(string='描述')
    sequence = fields.Integer(string='排序', default=10)
    active = fields.Boolean(string='启用', default=True)


class LearnDocument(models.Model):
    _name = 'learn.document'
    _description = '文档'
    _order = 'sequence, id'

    name = fields.Char(string='名称', required=True)
    file_data = fields.Binary(string='文件', attachment=True)
    file_name = fields.Char(string='文件名')
    url = fields.Char(string='外链')
    description = fields.Text(string='描述')
    sequence = fields.Integer(string='排序', default=10)
    active = fields.Boolean(string='启用', default=True)


class LearnImage(models.Model):
    _name = 'learn.image'
    _description = '图片'
    _order = 'sequence, id'

    name = fields.Char(string='名称', required=True)
    image_data = fields.Binary(string='图片', attachment=True)
    file_name = fields.Char(string='文件名')
    url = fields.Char(string='外链')
    description = fields.Text(string='描述')
    sequence = fields.Integer(string='排序', default=10)
    active = fields.Boolean(string='启用', default=True)


class LearnQuestionBank(models.Model):
    _name = 'learn.question.bank'
    _description = '题目库'
    _order = 'sequence, id'

    name = fields.Char(string='题目标题')
    question_type = fields.Selection([
        ('single_choice', '单选题'),
        ('multi_choice', '多选题'),
        ('fill_blank', '填空题'),
        ('true_false', '判断题'),
        ('calculation', '计算题'),
        ('essay', '问答题'),
    ], string='题目类型', required=True, default='single_choice')
    stem = fields.Html(string='题干')
    stem_image = fields.Binary(string='题干图片', attachment=True)
    option_a = fields.Char(string='选项 A')
    option_b = fields.Char(string='选项 B')
    option_c = fields.Char(string='选项 C')
    option_d = fields.Char(string='选项 D')
    option_e = fields.Char(string='选项 E')
    option_f = fields.Char(string='选项 F')
    correct_answer = fields.Char(string='正确答案')
    reference_answer = fields.Text(string='参考答案')
    answer_explanation = fields.Html(string='答案解析')
    default_score = fields.Float(string='默认分值', default=5.0)
    difficulty = fields.Selection([
        ('easy', '简单'),
        ('medium', '中等'),
        ('hard', '困难'),
    ], string='难度', default='easy')
    sequence = fields.Integer(string='排序', default=10)
    active = fields.Boolean(string='启用', default=True)
    description = fields.Text(string='备注')
