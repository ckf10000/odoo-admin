# -*- coding: utf-8 -*-
"""OSS 对象存储配置 — 统一管理文件上传/下载（支持阿里云 OSS + MinIO/S3）"""
import base64
import logging
import time
import oss2
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AppOssConfig(models.Model):
    _name = "app.oss.config"
    _description = "OSS 配置"
    _sql_constraints = [
        ("unique_code", "UNIQUE(code)", "配置编码必须唯一！"),
    ]

    name = fields.Char(string="配置名称", required=True)
    code = fields.Char(string="配置编码", required=True, help="唯一标识，如：production, staging")
    active = fields.Boolean(string="启用", default=True)

    # ---- OSS 连接参数 ----
    provider = fields.Selection(
        selection=[("aliyun", "阿里云 OSS"), ("minio", "MinIO / S3 兼容")],
        string="存储类型", required=True, default="minio",
    )
    endpoint = fields.Char(string="Endpoint", required=True, help="如：oss-cn-hangzhou.aliyuncs.com 或 192.168.1.1:9000")
    bucket_name = fields.Char(string="Bucket 名称", required=True)
    access_key_id = fields.Char(string="AccessKey ID", required=True)
    access_key_secret = fields.Char(string="AccessKey Secret", required=True)

    # ---- 上传策略 ----
    base_path = fields.Char(
        string="基础路径", default="app-manage/",
        help="OSS 中文件存储的基础目录，如：app-manage/",
    )
    custom_domain = fields.Char(
        string="自定义域名",
        help="如绑定了 CDN 自定义域名，填写后生成的 URL 将使用此域名",
    )

    # ---- 统计 ----
    last_upload_time = fields.Datetime(string="最近上传时间", readonly=True)

    def _get_bucket(self):
        """获取 OSS Bucket 对象"""
        self.ensure_one()
        auth = oss2.Auth(self.access_key_id, self.access_key_secret)
        bucket = oss2.Bucket(auth, self.endpoint, self.bucket_name)
        return bucket

    def _get_s3_client(self):
        """获取 boto3 S3 客户端（用于 MinIO/S3 兼容存储，支持 AWS V4 签名）"""
        self.ensure_one()
        import boto3
        from botocore.config import Config

        endpoint = self.endpoint
        if not endpoint.startswith("http"):
            endpoint = f"http://{endpoint}"

        client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.access_key_secret,
            region_name="us-east-1",
            config=Config(signature_version="s3v4"),
        )
        return client

    def action_test_connection(self):
        """测试 OSS 连接"""
        self.ensure_one()
        try:
            if self.provider == "minio":
                client = self._get_s3_client()
                client.head_bucket(Bucket=self.bucket_name)
            else:
                bucket = self._get_bucket()
                bucket.get_bucket_info()
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "连接成功",
                    "message": f"成功连接到 OSS Bucket: {self.bucket_name}",
                    "type": "success",
                    "sticky": False,
                },
            }
        except Exception as e:
            raise UserError(f"OSS 连接失败: {e}")

    @api.model
    def get_active_config(self):
        """获取当前启用的 OSS 配置（单例模式，一般只有一个）"""
        config = self.sudo().search([("active", "=", True)], limit=1)
        if not config:
            _logger.warning("没有启用的 OSS 配置")
            return None
        return config

    @api.model
    def upload_file(self, file_data, filename, sub_path=""):
        """
        上传文件到 OSS 并返回下载 URL。

        :param file_data: bytes 或 base64 字符串
        :param filename: 文件名
        :param sub_path: 子目录（如 releases/plugins/resources/）
        :return: 下载 URL 字符串
        """
        config = self.get_active_config()
        if not config:
            _logger.warning("OSS 未配置，跳过上传")
            return None

        try:
            # 解码 base64
            if isinstance(file_data, str):
                file_data = base64.b64decode(file_data)

            # 构建 OSS 路径
            base = config.base_path.rstrip("/")
            if sub_path:
                sub_path = sub_path.strip("/")
            timestamp = str(int(time.time() * 1000))
            oss_key = f"{base}/{sub_path}/{timestamp}_{filename}" if sub_path else f"{base}/{timestamp}_{filename}"

            # 上传
            if config.provider == "minio":
                client = config._get_s3_client()
                import io
                client.upload_fileobj(io.BytesIO(file_data), config.bucket_name, oss_key)
            else:
                bucket = config._get_bucket()
                result = bucket.put_object(oss_key, file_data)
                if result.status != 200:
                    _logger.error("OSS 上传失败: status=%s", result.status)
                    return None

            # 更新最后上传时间
            config.sudo().write({"last_upload_time": fields.Datetime.now()})

            # 生成永久下载 URL（公共读 + 自定义域名优先）
            if config.custom_domain:
                url = f"https://{config.custom_domain}/{oss_key}"
            else:
                endpoint = config.endpoint.rstrip("/")
                # endpoint 已经是 http(s)://host:port，直接拼接 bucket
                if endpoint.startswith(("http://", "https://")):
                    # 阿里云 OSS：去掉 http://，格式为 bucket.endpoint
                    if "aliyuncs.com" in endpoint:
                        host = endpoint.replace("https://", "").replace("http://", "")
                        url = f"https://{config.bucket_name}.{host}/{oss_key}"
                    else:
                        # MinIO 或自托管：直接 endpoint + bucket
                        url = f"{endpoint}/{config.bucket_name}/{oss_key}"
                else:
                    # 默认按阿里云格式拼接
                    url = f"https://{config.bucket_name}.{endpoint}/{oss_key}"

            _logger.info("OSS 上传成功: %s → %s", filename, url)
            return url

        except Exception as e:
            _logger.exception("OSS 上传失败: %s", e)
            return None


class OssUploadMixin(models.AbstractModel):
    """OSS 上传 Mixin — 给需要上传文件的模型混入"""
    _name = "oss.upload.mixin"
    _description = "OSS 上传混入"

    oss_config_id = fields.Many2one(
        "app.oss.config", string="OSS 配置",
        help="留空则使用默认启用的配置",
    )

    def _upload_to_oss(self, binary_field, filename_field, url_field, sub_path):
        """
        将 Binary 字段的文件上传到 OSS，回填 URL 字段。
        """
        self.ensure_one()
        file_data = self[binary_field]
        if not file_data:
            return

        filename = self[filename_field] or "file.bin"
        url = self.env["app.oss.config"].upload_file(file_data, filename, sub_path)
        if url:
            self[url_field] = url
