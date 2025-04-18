import logging
import os
import requests
from odoo import models, fields, api
import oss2

_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    is_oss_file = fields.Boolean(string='是否OSS文件', compute="_compute_is_oss_file", store=True)
    oss_url = fields.Char(string='OSS URL', compute='_compute_oss_url')

    def _get_datas_related_values(self, data, mimetype):
        checksum = self._compute_checksum(data)
        try:
            index_content = self._index(data, mimetype, checksum=checksum)
        except TypeError:
            index_content = self._index(data, mimetype)
        values = {
            'file_size': len(data),
            'checksum': checksum,
            'index_content': index_content,
            'store_fname': False,
            'db_datas': data,
        }
        if data and self._storage() != 'db':
            values['store_fname'] = self._file_write(data, values['checksum'], mimetype)
            values['db_datas'] = False
        return values

    @api.depends('write_date')
    def _compute_is_oss_file(self):
        for record in self:
            record.is_oss_file = record._get_file_data_from_oss()

    @api.depends('store_fname')
    def _compute_oss_url(self):
        oss_client = self._get_oss_client()

        for record in self:
            if record.is_oss_file:
                record.oss_url = oss_client.sign_url('GET', record.store_fname, 3600, slash_safe=True)
            else:
                record.oss_url = False

    @api.model
    def _get_oss_client(self):
        config = self.env['ir.config_parameter']
        accessKeyId = config.get_param('oss.access_key', '')
        accessKeySecret = config.get_param('oss.secret_key', '')
        endpoint = config.get_param('oss.endpoint', '')
        bucket_name = config.get_param('oss.bucket', '')
        if not accessKeyId:
            return None
        # 使用代码嵌入的RAM用户的访问密钥配置访问凭证。
        auth = oss2.Auth(accessKeyId, accessKeySecret)
        bucket = oss2.Bucket(auth, endpoint, bucket_name)
        return bucket

    @api.model
    def _is_file_from_oss(self, fname):
        full_path = self._full_path(fname)
        if not os.path.isfile(full_path):
            return True
        return False

    def _get_file_data_from_oss(self):
        """
        从阿里云获取文件元数据，用于判断是否存储在阿里云上
        """
        oss_client = self._get_oss_client()
        try:
            res = oss_client.get_object_meta(self.store_fname)
            return res
        except Exception as e:
            return False

    @api.model
    def _file_read(self, fname):
        if self._is_file_from_oss(fname):
            return self._file_read_from_oss(fname)
        else:
            return super()._file_read(fname)
        
    @api.model
    def _file_read_from_oss(self, fname):
        """
        从阿里云读取文件
        """
        url = self.oss_url
        if not url:
            return b''
        res = requests.get(url)
        return res.content

    @api.model
    def _file_write(self, bin_value, checksum, mimetype):
        """
        @desc 重写，上传到阿里云
        @return 阿里云返回的文件url
        web.assets_web.min.css
        web.assets_web.min.js
        """
        if mimetype in ["text/css", "application/javascript", "application/octet-stream"]:
            fname = super()._file_write(bin_value, checksum)
            return fname
            
        oss_client = self._get_oss_client()
        fname, _ = self._get_path(bin_value, checksum)
        # res = oss_client.put_object(fname, bin_value)
        return fname

    @api.model
    def _file_delete(self, fname):
        if self._is_file_from_oss(fname):
            ...
        else:
            super()._file_delete(fname)

    


