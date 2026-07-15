# -*- coding: utf-8 -*-
"""迁移脚本：升级时为所有 group 创建默认章节，将无 section 的 line 挂上"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):  # noqa
    _logger.info('Migration 1.1: creating default sections for existing groups')
    # 1. 为所有无 section 的 group 创建默认 section
    cr.execute("""
        INSERT """ + """INTO learn_group_section
            (group_id, name, content_type_id, sequence, create_uid, create_date, write_uid, write_date)
        SELECT g.id, '默认章节', (
            SELECT id FROM learn_content_type WHERE code = 'word_card' LIMIT 1
        ), 10, 1, NOW(), 1, NOW()
        FROM learn_group g
        LEFT JOIN learn_group_section s ON s.group_id = g.id
        WHERE s.id IS NULL
    """)
    _logger.info('Default sections created')
