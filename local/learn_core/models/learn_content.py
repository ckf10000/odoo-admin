# -*- coding: utf-8 -*-
from odoo import models, fields, api

"""学习内容模型 - 教材/试卷/练习册/视频"""


class LearnContent(models.Model):
    _name = "learn.content"
    _description = "学习内容"
    _order = "sequence, id"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="标题", required=True, translate=True)
    sequence = fields.Integer(string="排序", default=10)

    # ---- 选择器关联 ----
    selector_id = fields.Many2one(
        "learn.selector", string="所属选择器",
        ondelete="restrict", index=True,
    )

    # ---- 内容类型 ----
    content_type = fields.Selection(
        selection=[
            ("textbook", "教材"),
            ("exam", "试卷"),
            ("workbook", "练习册"),
            ("video", "视频"),
        ],
        string="内容类型",
        required=True,
        default="textbook",
    )

    # ---- 基础信息 ----
    subject = fields.Char(string="科目", help="如：语文、数学、英语")
    grade = fields.Char(string="年级", help="如：一年级、二年级")
    semester = fields.Selection(
        selection=[
            ("spring", "上学期"),
            ("summer", "暑假"),
            ("autumn", "下学期"),
            ("winter", "寒假"),
        ],
        string="学期",
    )
    publisher = fields.Char(string="出版社")
    author = fields.Char(string="作者/编者")
    isbn = fields.Char(string="ISBN")
    edition = fields.Char(string="版本")

    description = fields.Html(string="简介")
    tags = fields.Many2many(
        "learn.tag", string="标签",
        help="用于辅助搜索和归类",
    )

    # ---- 封面 ----
    cover_image = fields.Binary(string="封面图", attachment=True)
    cover_image_filename = fields.Char(string="封面图文件名")

    # ---- 教材/文档类内容 ----
    document_file = fields.Binary(string="文档文件（PDF）", attachment=True)
    document_filename = fields.Char(string="文档文件名")

    # ---- 视频内容 ----
    video_url = fields.Char(string="视频链接", help="支持 YouTube/Bilibili/本地URL")
    video_platform = fields.Selection(
        selection=[
            ("local", "本地"),
            ("youtube", "YouTube"),
            ("bilibili", "Bilibili"),
            ("other", "其他"),
        ],
        string="视频平台",
        default="local",
    )
    video_duration = fields.Float(string="视频时长（分钟）")

    # ---- 试卷/练习册专属字段 ----
    total_score = fields.Float(string="总分", default=100.0)
    pass_score = fields.Float(string="及格分", default=60.0)
    time_limit = fields.Integer(string="时间限制（分钟）", help="0 表示不限时")
    question_count = fields.Integer(
        string="题目数量", compute="_compute_question_count", store=True,
    )
    question_ids = fields.One2many(
        "learn.question", "content_id", string="题目列表",
    )
    word_ids = fields.One2many(
        "learn.word", "content_id", string="单词列表",
    )
    item_ids = fields.One2many(
        "learn.item", "content_id", string="知识点列表",
    )

    # ---- 状态 ----
    state = fields.Selection(
        selection=[
            ("draft", "草稿"),
            ("published", "已发布"),
            ("archived", "已归档"),
        ],
        string="状态",
        default="draft",
        tracking=True,
    )
    is_public = fields.Boolean(string="公开可见", default=True)

    # ---- 统计 ----
    view_count = fields.Integer(string="浏览次数", default=0)
    favorite_count = fields.Integer(
        string="收藏数", compute="_compute_favorite_count", store=True,
    )
    avg_rating = fields.Float(
        string="平均评分", compute="_compute_avg_rating", store=True,
    )

    # ---- 用户隔离字段 ----
    create_uid = fields.Many2one("res.users", string="创建者", default=lambda self: self.env.uid)
    # 多用户隔离通过 record rules 实现，每个用户只能看到自己创建的内容 + 公开内容

    _sql_constraints = []

    @api.depends("question_ids")
    def _compute_question_count(self):
        for record in self:
            record.question_count = len(record.question_ids)

    def _compute_favorite_count(self):
        for record in self:
            record.favorite_count = self.env["learn.favorite"].search_count([
                ("content_id", "=", record.id),
            ])

    def _compute_avg_rating(self):
        for record in self:
            ratings = self.env["learn.rating"].search([
                ("content_id", "=", record.id),
            ])
            if ratings:
                record.avg_rating = sum(r.score for r in ratings) / len(ratings)
            else:
                record.avg_rating = 0.0

    def action_publish(self):
        self.state = "published"

    def action_archive(self):
        self.state = "archived"

    def action_draft(self):
        self.state = "draft"

    def action_view_questions(self):
        """跳转到题目列表"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": f"{self.name} - 题目列表",
            "res_model": "learn.question",
            "view_mode": "tree,form",
            "domain": [("content_id", "=", self.id)],  # noqa
            "context": {"default_content_id": self.id},  # noqa
        }

    def increment_view_count(self):
        """增加浏览次数（供 API 调用）"""
        self.view_count += 1


class LearnTag(models.Model):
    _name = "learn.tag"
    _description = "内容标签"

    name = fields.Char(string="标签名称", required=True)
    color = fields.Integer(string="颜色索引")


class LearnQuestion(models.Model):
    _name = "learn.question"
    _description = "题目"
    _order = "sequence, id"

    name = fields.Char(string="题目标题")
    sequence = fields.Integer(string="排序", default=10)

    content_id = fields.Many2one(
        "learn.content", string="所属内容",
        required=True, ondelete="cascade",
    )

    # ---- 题目类型 ----
    question_type = fields.Selection(
        selection=[
            ("single_choice", "单选题"),
            ("multi_choice", "多选题"),
            ("fill_blank", "填空题"),
            ("calculation", "计算题"),
            ("essay", "问答题"),
            ("true_false", "判断题"),
        ],
        string="题目类型",
        required=True,
        default="single_choice",
    )

    # ---- 题目内容 ----
    stem = fields.Html(string="题干", required=True)
    stem_image = fields.Binary(string="题干图片", attachment=True)

    # ---- 选项（选择题用） ----
    option_a = fields.Char(string="选项 A")
    option_b = fields.Char(string="选项 B")
    option_c = fields.Char(string="选项 C")
    option_d = fields.Char(string="选项 D")
    option_e = fields.Char(string="选项 E")
    option_f = fields.Char(string="选项 F")

    # ---- 答案 ----
    # 选择题：存储正确答案选项，如 "A" / "AB" / "ACD"
    correct_answer = fields.Char(string="正确答案")
    # 填空题/计算题/问答题的参考答案
    reference_answer = fields.Text(string="参考答案")
    # 答案解析
    answer_explanation = fields.Html(string="答案解析")

    # ---- 分值 ----
    score = fields.Float(string="分值", default=5.0)

    # ---- 难度 ----
    difficulty = fields.Selection(
        selection=[
            ("easy", "简单"),
            ("medium", "中等"),
            ("hard", "困难"),
        ],
        string="难度",
        default="medium",
    )

    _sql_constraints = [
        ("unique_sequence_content",
         "UNIQUE(sequence, content_id)",
         "同一内容下题目序号必须唯一！"),
    ]


class LearnItem(models.Model):
    """通用知识点条目 - 统一管理各科目的原子概念

    支持的知识点类型 (item_type):
    - word:      英语单词（音标、词性、例句）
    - character: 语文生字（拼音、部首、笔画数、笔顺）
    - vocabulary:语文词语（近义词、反义词、造句）
    - pinyin:    拼音（声母、韵母、声调）
    - formula:   数学/物理公式（公式表达式、变量说明）
    - term:      通用术语（仅释义）
    """
    _name = "learn.item"
    _description = "知识点条目"
    _order = "sequence, id"

    name = fields.Char(string="条目名称", required=True, translate=True)
    sequence = fields.Integer(string="排序", default=10)

    # ---- 知识点类型 ---- #
    item_type = fields.Selection(
        selection=[
            ("word", "英语单词"),
            ("character", "语文生字"),
            ("vocabulary", "语文词语"),
            ("pinyin", "拼音"),
            ("formula", "公式"),
            ("term", "通用术语"),
        ],
        string="条目类型",
        required=True,
        default="term",
    )

    # ---- 关联 ---- #
    content_id = fields.Many2one(
        "learn.content", string="所属内容",
        required=True, ondelete="cascade", index=True,
    )
    # ======== 通用字段（所有类型共享） ========
    meaning = fields.Text(string="释义", required=True)
    difficulty = fields.Selection(
        selection=[("easy", "简单"), ("medium", "中等"), ("hard", "困难")],
        string="难度", default="medium",
    )
    audio_file = fields.Binary(string="发音音频", attachment=True)
    audio_filename = fields.Char(string="音频文件名")
    image = fields.Binary(string="配图", attachment=True)

    # ======== 英语单词专用 ========
    pronunciation = fields.Char(string="音标")
    part_of_speech = fields.Selection(
        selection=[
            ("noun", "名词"), ("verb", "动词"),
            ("adj", "形容词"), ("adv", "副词"),
            ("pron", "代词"), ("prep", "介词"),
            ("conj", "连词"), ("interj", "感叹词"),
            ("num", "数词"), ("phrase", "短语"),
            ("sentence", "句型"), ("other", "其他"),
        ],
        string="词性",
    )
    example = fields.Text(string="例句")
    example_translation = fields.Text(string="例句翻译")

    # ======== 语文生字专用 ========
    char_pinyin = fields.Char(string="拼音")
    char_radical = fields.Char(string="部首")
    char_strokes = fields.Integer(string="笔画数")
    char_stroke_order = fields.Text(string="笔顺")
    char_structure = fields.Selection(
        selection=[
            ("single", "独体字"),
            ("left_right", "左右结构"),
            ("up_down", "上下结构"),
            ("half_surround", "半包围"),
            ("full_surround", "全包围"),
            ("pin", "品字形"),
        ],
        string="字形结构",
    )

    # ======== 语文词语专用 ========
    vocab_synonyms = fields.Text(string="近义词")
    vocab_antonyms = fields.Text(string="反义词")
    vocab_sentence = fields.Text(string="造句")

    # ======== 拼音专用 ========
    pinyin_initial = fields.Char(string="声母")
    pinyin_final = fields.Char(string="韵母")
    pinyin_tone = fields.Selection(
        selection=[
            ("1", "一声（阴平）"), ("2", "二声（阳平）"),
            ("3", "三声（上声）"), ("4", "四声（去声）"),
            ("0", "轻声"),
        ],
        string="声调",
    )

    # ======== 公式专用 ========
    formula_expression = fields.Text(string="公式表达式")
    formula_variables = fields.Text(string="变量说明")

    _sql_constraints = [
        ("unique_item_content",
         "UNIQUE(name, content_id, item_type)",
         "同一内容下同类型条目不能重复！"),
    ]


class LearnWord(models.Model):
    """保留旧 learn.word 模型，兼容已有数据，后续可迁移到 learn.item"""
    _name = "learn.word"
    _description = "单词/知识点（旧）"
    _order = "sequence, id"

    name = fields.Char(string="单词/术语", required=True)
    sequence = fields.Integer(string="排序", default=10)

    content_id = fields.Many2one(
        "learn.content", string="所属内容",
        required=True, ondelete="cascade", index=True,
    )
    pronunciation = fields.Char(string="音标")
    part_of_speech = fields.Selection(
        selection=[
            ("noun", "名词"), ("verb", "动词"),
            ("adj", "形容词"), ("adv", "副词"),
            ("pron", "代词"), ("prep", "介词"),
            ("conj", "连词"), ("interj", "感叹词"),
            ("num", "数词"), ("phrase", "短语"),
            ("sentence", "句型"), ("other", "其他"),
        ],
        string="词性",
    )
    meaning = fields.Text(string="释义", required=True)
    example = fields.Text(string="例句")
    example_translation = fields.Text(string="例句翻译")
    audio_file = fields.Binary(string="发音音频", attachment=True)
    audio_filename = fields.Char(string="音频文件名")
    image = fields.Binary(string="配图", attachment=True)

    difficulty = fields.Selection(
        selection=[("easy", "简单"), ("medium", "中等"), ("hard", "困难")],
        string="难度", default="medium",
    )

    _sql_constraints = [
        ("unique_word_content",
         "UNIQUE(name, content_id)",
         "同一内容下单词不能重复！"),
    ]
