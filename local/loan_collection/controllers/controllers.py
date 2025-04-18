import urllib

from odoo import http
from odoo.http import request
import subprocess
import tempfile
import os
from lxml import etree

class FormToImageController(http.Controller):

    @http.route('/wizard/form_to_image', type='http', auth="user")
    def wizard_form_to_image(self, res_id, res_model, view_id):
        # 此方法只用于下载凭证
        # 获取wizard记录
        wizard = request.env[res_model].browse(int(res_id))

        # 渲染wizard的form视图
        html_content = request.env['ir.qweb']._render(view_id, {'object': wizard})
        # 将XML内容转换为标准HTML格式
        # 定义字段值
        if res_model == 'loan.proof':
            data = {
                'amount': wizard.amount,
                'text': wizard.text,
                'loan_time': wizard.loan_time,
                'name': wizard.name,
                'number': wizard.number,
                'loan_mode': wizard.loan_mode,
            }
        else:
            data = {
                'contract_amount': wizard.contract_amount,
                'loan_amount': wizard.loan_amount,
                'borrow_money_date': wizard.borrow_money_date,
                'application_time': wizard.application_time,
                'loan_time': wizard.loan_time,
                'cash_time': wizard.cash_time,
                'loan_number': wizard.loan_number,
                'receivables_number': wizard.receivables_number,
                'payment_way_id': wizard.payment_way_id,
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
            filename = '放款凭证.png'
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
            return f'<{tag_name} {attributes}>{element.attrib["string"]}  {field_value}</{tag_name}>'

        return f'<{tag_name} {attributes}>{inner_html}</{tag_name}>'



