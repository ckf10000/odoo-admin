import logging
from odoo.http import Stream, request

_logger = logging.getLogger(__name__)


try:
    from werkzeug.utils import send_file as _send_file
except ImportError:
    from odoo.tools._vendor.send_file import send_file as _send_file


class OssStream(Stream):
    oss_attachment = None

    @classmethod
    def from_oss_attachment(cls, attachment):
        attachment.ensure_one()
        if not attachment.oss_url:
            raise ValueError("Attachment is not stored into oss")
        return cls(
            mimetype=attachment.mimetype,
            download_name=attachment.name,
            conditional=True,
            etag=attachment.checksum,
            type="oss",
            size=attachment.file_size,
            last_modified=attachment.write_date,
            data=attachment._file_read_from_oss(attachment.store_fname),
            oss_attachment=attachment,
        )

    def read(self):
        if self.type == "oss":
            return self.data
        return super().read()

    def get_response(self, as_attachment=None, immutable=None, **send_file_kwargs):
        if self.type == "oss":
            return request.redirect(self.oss_attachment.oss_url, code=301, local=False)
        
        return super().get_response(
                as_attachment=as_attachment, immutable=immutable, **send_file_kwargs
            )

        