import logging
from odoo import models
from .oss_stream import OssStream

_logger = logging.getLogger(__name__)


class IrBinary(models.AbstractModel):

    _inherit = "ir.binary"

    def _record_to_stream(self, record, field_name):
        oss_attachment = None
        if record._name == "ir.attachment" and record.oss_url:
            oss_attachment = record
        else:
            field_def = record._fields[field_name]
            if field_def.attachment and not field_def.compute and not field_def.related:
                field_attachment = (
                    self.env["ir.attachment"]
                    .sudo()
                    .search(
                        domain=[
                            ("res_model", "=", record._name),
                            ("res_id", "=", record.id),
                            ("res_field", "=", field_name),
                        ],
                        limit=1,
                    )
                )
                if field_attachment.oss_url:
                    oss_attachment = field_attachment
        if oss_attachment:
            return OssStream.from_oss_attachment(oss_attachment)
        return super()._record_to_stream(record, field_name)