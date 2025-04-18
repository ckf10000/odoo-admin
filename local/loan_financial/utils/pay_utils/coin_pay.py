import logging
import requests
import hashlib

_logger = logging.getLogger(__name__)


class CoinPayService(object):
    domain = "https://api.mwxpa.com/"

    def __init__(self):
        ...

    def _sign(self, params):
        """
        签名
        1.将除了参数 key 值按照 ASCII 升序排序
        2.将除了参数值按照 key=value&key=value…的形式拼接成字符串 stringA
        3.key=value 中 value 为空的不参与拼接， 不进行签名）
        4.将上述字符串使用平台的 key 进行 MD5 加密, MD5(stringA&key=密钥)
        """
        strings = []
        api_key = params.pop("key")
        for key, value in params.items():
            if value or value == 0:
                strings.append(f"{key}={value}")
        strings.sort()
        strings.append(f"key={api_key}")
        return hashlib.md5("&".join(strings).encode("utf-8")).hexdigest()

    def create_pay_order(self, params):
        """
        代收接口
        :params: {
            'type': 0,
            'mchId: '商户号'  # 分配给各合作商户的唯一识别码
            'key': '密钥'  # 分配给各合作商户的唯一识别码
            'productId': '产品号'  # 分配给各合作商户的唯一识别码
            'mchOrderNo': '订单号'    # 本系统支付记录的唯一识别码
            'orderAmount': '金额'      # 订单金额，单位分，不能带小数
            'notifyUrl': '回调地址'  # 支付成功后, 通知商户的回调地址
            'returnUrl': '返回地址'  # 支付成功后, 跳转商户的地址
            'clientIp': '客户端ip'  ,
            'device': '客户端设备信息' # '只能是android、ios、pc',
            'uid': '用户id'  # 用户id,
            'customerName': '客户姓名'  # 客户姓名,
            'tel': '客户电话'  # 客户电话,
            'email': '客户邮箱'  # 客户邮箱,
            'returnType': '返回类型'  # 返回类型, json
            'extra': '附加参数'  # 附加参数
        } 
        接口返回：
        {
            'code': 200, 
            'data': {
                'payOrderId': 'ZF12IeOziPoG', 
                'orderAmount': 100, 
                'payUrl': 'https://xpayvip.com/khxRbU7QLA8uAj', 
                'returnType': 'url'
            }, 
            'message': 'Place an order successfully'
        }
        """
        url = "https://coin-pay.vip/api/pay/create_order"
        params_baisc = {
            'type': 0,
            'productId': 27,
            'clientIp': '127.0.0.1',
            'email': 't-e-s-t@gmail.com',
            'returnType': 'json'
        }
        params.update(params_baisc)
        params["sign"] = self._sign(params)
        headers = {}
        try:
            # _logger.info(f"[coin_pay]create_pay_order params: {params}")
            res = requests.post(url, data=params, headers=headers).json()
            return res
        except Exception as e:
            _logger.error(f"[coin_pay]create_pay_order error: {e}, params: {params}")
            return {"code": 999, "message": f"请求失败, 原因：{e}"}

    def create_transfer_order(self, params):
        """
        代付接口
        :params: {
            'type': 0,
            'mchId: '商户号'  # 分配给各合作商户的唯一识别码
            'key': '密钥'  # 分配给各合作商户的唯一识别码
            'productId': '产品号'  # 分配给各合作商户的唯一识别码
            'mchOrderNo': '订单号'    # 本系统支付记录的唯一识别码
            'accountname': '收款人姓名'  # 贷款用户姓名
            'cardnumber': '收款人银行卡号'  # 贷款用户姓名
            'orderAmount': '金额'      # 订单金额，单位分，不能带小数
            'notifyUrl': '回调地址'  # 支付成功后, 通知商户的回调地址
            'returnUrl': '跳转地址'  # 支付成功后, 跳转商户的回调地址
            'clientIp': '客户端ip'  ,
            'device': '客户端设备信息' # '只能是android、ios、pc',
            'uid': '用户id'  # 用户id,
            'customerName': '客户姓名'  # 客户姓名,
            'tel': '客户电话'  # 客户电话,
            'email': '客户邮箱'  # 客户邮箱,
            'returnType': '返回类型'  # 返回类型, json
            'mode': '模式'  # 模式 印度传入IMPS固定值
            'ifsc': '银行代码'  # 银行代码
            'bankname': '银行名称 wavepay 默认固定'
        } 

        接口返回：
        {
            “code”: 200,
            “message”,”place an order successfully”,
            “data”:{
                    “payOrderId”: “ordeNo123456”,—平台单号
                    “orderAmount”:1000, —订单金额
            }
        }
        """
        url = "https://coin-pay.vip/api/pay/create_order"
        params_baisc = {
            'type': 1,
            'productId': 27
        }
        params.update(params_baisc)
        params["sign"] = self._sign(params)
        headers = {}
        try:
            res = requests.post(url, data=params, headers=headers).json()
            # _logger.info(params)
            # _logger.info(res)
            return res
        except Exception as e:
            _logger.error(f"[sf_pay]create_transfer_order error: {e}, params: {params}")
            return {"code": 999, "message": f"请求失败, 原因：{e}"}

    def search_order(self, params):
        """
        订单查询接口
        params: {
            "mchId": "商户号",
            "key": "商户密钥",
            "payOrderId": "平台订单号",
        }
        """
        url = "https://coin-pay.vip/api/pay/query_order"
        params["sign"] = self._sign(params)
        try:
            res = requests.post(url, data=params).json()
            _logger.info(params)
            _logger.info(res)
            return res
        except Exception as e:
            _logger.error(f"[sf_pay]search_order error: {e}, params: {params}")
            return {"code": 999, "message": f"请求失败, 原因：{e}"}
        

    def create_supplement_order(self, params):
        """
        补单接口
        params: {
            "mchId": "商户号",
            "mchOrderNo": "商户订单号",
            "utr": "",
        }
        {
            "code": 202,
            "message": "未查到此UTR"
        ·}
        """
        url = "https://coin-pay.vip/api/pay/supplement"

        params["sign"] = self._sign(params)
        headers = {}
        try:
            res = requests.post(url, data=params, headers=headers).json()
            # _logger.info(params)
            # _logger.info(res)
            return res
        except Exception as e:
            _logger.error(f"[sf_pay]create_supplement_order error: {e}, params: {params}")
            return {"code": 999, "message": f"请求失败, 原因：{e}"}

    def search_supplement_order(self, params):
        """
        查询补单接口
        params: {
            "mchId": "商户号",
            "utr": "",
        }
        {
            "code": 200,
            "data": {
                "amount": "2500.0",
                "utrAmount": "2500.0"
            },
            "message": "此订单已完成"
        }
        """
        url = "https://coin-pay.vip/api/pay/utr/query"

        params["sign"] = self._sign(params)
        headers = {}
        try:
            res = requests.post(url, data=params, headers=headers).json()
            # _logger.info(params)
            # _logger.info(res)
            return res
        except Exception as e:
            _logger.error(f"[sf_pay]search_supplement_order error: {e}, params: {params}")
            return {"code": 999, "message": f"请求失败, 原因：{e}"}


