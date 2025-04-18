# -*- coding: utf-8 -*-
import urllib
import logging
from odoo import http
from odoo.http import request
import subprocess
import tempfile
import os
from lxml import etree

_logger = logging.getLogger(__name__)


class LoanFinancial(http.Controller):

    @http.route('/download_order_voucher', type='http', auth="user")
    def download_voucher(self, res_id, res_model, view_id):
        # 此方法只用于下载凭证
        order = request.env[res_model].browse(int(res_id))

        # 渲染form视图
        html_content = request.env['ir.qweb']._render(view_id, {'object': order})
        # 将XML内容转换为标准HTML格式
        # 定义字段值
        data = {
            'order_loan_amount': order.order_loan_amount,
            'pay_voucher': order.pay_voucher,
            'pay_complete_time': order.pay_complete_time,
            'financial_user_id': order.financial_user_id.display_name,
            'order_bank_account_no': order.order_bank_account_no,
            'payment_way_id': order.payment_way_id.way_name,
        }
        
        html_content = self._convert_xml_to_html(html_content, data)
        # 将HTML内容写入临时文件
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.html') as tmp:
            tmp.write(html_content)
            tmp.seek(0)
            html_file_path = tmp.name
            # 读取并打印临时文件的内容
        # 使用wkhtmltoimage生成图片
        image_path = html_file_path.replace('.html', '.png')
        try:
            subprocess.run(['wkhtmltoimage', html_file_path, image_path], check=True)
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Error running wkhtmltoimage: {e}")
        # 读取图片并提供下载
        with open(image_path, 'rb') as img_file:
            image_data = img_file.read()
            filename = 'payment.png'
            encoded_filename = 'attachment; filename*=UTF-8\'\'' + urllib.parse.quote(filename.encode('utf-8'))
            response = request.make_response(image_data, [('Content-Type', 'image/png'), ('Content-Disposition', encoded_filename)])

        # 清理临时文件
        os.remove(tmp.name)
        os.remove(image_path)

        return response
    
    @http.route('/download_order_refund_voucher', type='http', auth="user")
    def download_order_refund_voucher(self, res_id, res_model, view_id):
        # 此方法只用于下载凭证
        record = request.env[res_model].browse(int(res_id))

        # 渲染form视图
        html_content = request.env['ir.qweb']._render(view_id, {'object': record})
        # 将XML内容转换为标准HTML格式
        # 定义字段值
        data = {
            'refund_amount': record.refund_amount,
            'refund_voucher': record.refund_voucher,
            'refund_complete_time': record.refund_complete_time,
            'loan_user_name': record.loan_user_name,
            'bank_account_no': record.bank_account_no,
            'payment_way_id': record.payment_way_id.way_name,
        }
        
        html_content = self._convert_xml_to_html(html_content, data)
        # 将HTML内容写入临时文件
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.html') as tmp:
            tmp.write(html_content)
            tmp.seek(0)
            html_file_path = tmp.name
            # 读取并打印临时文件的内容
        # 使用wkhtmltoimage生成图片
        image_path = html_file_path.replace('.html', '.png')
        try:
            subprocess.run(['wkhtmltoimage', html_file_path, image_path], check=True)
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Error running wkhtmltoimage: {e}")
        # 读取图片并提供下载
        with open(image_path, 'rb') as img_file:
            image_data = img_file.read()
            filename = 'refund.png'
            encoded_filename = 'attachment; filename*=UTF-8\'\'' + urllib.parse.quote(filename.encode('utf-8'))
            response = request.make_response(image_data, [('Content-Type', 'image/png'), ('Content-Disposition', encoded_filename)])

        # 清理临时文件
        os.remove(tmp.name)
        os.remove(image_path)

        return response

    def _convert_xml_to_html(self,xml_content, data):
        # 将XML内容转换为标准HTML格式
        # 解析 XML
        root = etree.fromstring(xml_content.encode('utf-8'))

        # 构建 HTML 结构
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Wizard Form</title>
            <style>
                form {{ display: block; }}
                sheet, group {{ display: block; }}
                field {{ display: block; margin-bottom: 10px; padding: 10px; border: 1px solid #ccc; }}
            </style>
        </head>
        <body>
            {self._render_xml_element(root, data)}
        </body>
        </html>
        """
        return html_content

    def _render_xml_element(self, element, data):
        # 递归渲染 XML 元素
        tag_map = {
            'form': 'form',
            'sheet': 'div',
            'group': 'div',
            'field': 'div'
        }

        if element.tag in tag_map:
            tag_name = tag_map[element.tag]
        else:
            tag_name = 'div'

        attributes = ' '.join([f'{attr}="{value}"' for attr, value in element.attrib.items()])
        inner_html = ''.join([self._render_xml_element(child, data) for child in element])

        if element.tag == 'field':
            field_name = element.get('name')
            field_value = data.get(field_name, '')
            return f'<{tag_name} {attributes}>{element.attrib.get("string","")}  {field_value}</{tag_name}>'

        return f'<{tag_name} {attributes}>{inner_html}</{tag_name}>'



