import logging
import requests
import hashlib

_logger = logging.getLogger(__name__)


class SFPayService(object):
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
        最后将 MD5 加密后的字符串转成大写
        """
        strings = []
        api_key = params.pop("key")
        for key, value in params.items():
            if value or value == 0:
                strings.append(f"{key}={value}")
        strings.sort()
        strings.append(f"key={api_key}")
        return hashlib.md5("&".join(strings).encode("utf-8")).hexdigest().upper()

    def create_pay_order(self, params):
        """
        代收接口
        :params: {
            'merchantNo: '商户号'  # 分配给各合作商户的唯一识别码
            'key': '密钥'  # 分配给各合作商户的唯一识别码
            'orderNo': '商户订单号'    # 本系统支付记录的唯一识别码
            'amount': '金额'      # 支付订单的金额, 两位小数。金额值需大于0, 小数部分为.00, 测试金额最低100
            'type': '支付类型'    # 支付类型, 8-UPI
            'notifyUrl': '回调地址'  # 支付成功后, 通知商户的回调地址
            'userName': '客户姓名'  # 贷款用户姓名
            'timestamp': '请求时间'  # yyyy-MM-dd HH:mm:ss, 请求时间，以印度标准时间 (GMT+5:30)为准,误差不允许超过5分钟
        } 
        接口返回：
        {
            "code":0,
            "message":null,
            "sign":"DDD120E2912165D2CD42C2F4C7C139B5",
            "amount":"1004.00", # 交易金额
            "version":null,
            "merchantNo":"f3c2d1f505d4dfe12439451b37cb9c46", # 商户号
            "orderNo":"test1512627566666108929", # 商户订单号
            "platformOrderNo":"20220409110450111576", # 平台订单号
            "url":"http://127.0.0.1:8080?payOrderNo=20220409110450111576&sign=35DAC203BF1D6137C5E7E0DCDA56100B" # 支付链接
        }
        """
        url = "https://api.mwxpa.com/api/indiapApi/pay/v2/apiPay"
        params_baisc = {
            'type': 8
        }
        params.update(params_baisc)
        params["sign"] = self._sign(params)
        headers = {"Content-Type": "application/json; charset=utf-8"}
        try:
            res = requests.post(url, json=params, headers=headers).json()
            _logger.info(f"[sf_pay]create_pay_order res: {res}, params: {params}")
            return res
        except Exception as e:
            _logger.error(f"[sf_pay]create_pay_order error: {e}, params: {params}")
            return {"code": 999, "message": f"请求失败, 原因：{e}"}

    def create_transfer_order(self, params):
        """
        代付接口
        :params: {
            'merchantNo: '商户号'  # 分配给各合作商户的唯一识别码
            'key': '密钥'  # 分配给各合作商户的唯一识别码
            'orderNo': '商户订单号'    # 本系统支付记录的唯一识别码
            'amount': '金额'      # 字符串传递,用户支付订单的金额,必须为整数。金额值需大于0,测试金额最低50
            'type': '支付类型'    # 支付类型, 1: 银行卡
            'notifyUrl': '回调地址'  # 支付成功后, 通知商户的回调地址
            'name': '用户账号的真实姓名'  # 贷款用户姓名
            'account': '用户银行卡号',
            'ifscCode': '银行卡对应的ifsc', 字母全大写 ,4个字母+ '0' +6位数字或字母, 例:SBIN0014148
            'timestamp': '请求时间'  # yyyy-MM-dd HH:mm:ss, 请求时间，以印度标准时间 (GMT+5:30)为准,误差不允许超过5分钟
        } 

        接口返回：
        {
            "code":0,
            "message":null,
            "version":null,
            "merchantNo":"f3c2d1f505d4dfe12439451b37cb9c46",
            "amount": "100.00",
            "orderNo":"2024020115495258",
            "platformOrderNo": "2024020115495258",
            "status": 2, # 同步返回订单状态为 2,处理中;（后续通过异步通知或查询最终结果）
            "sign": "C3476440ED44272FBC9435C0DCCFC219"
        }
        """
        url = "https://api.mwxpa.com/api/indiapApi/pay/v2/apiTransfer"
        params_baisc = {
            'type': 1
        }
        params.update(params_baisc)
        params["sign"] = self._sign(params)
        headers = {"Content-Type": "application/json; charset=utf-8"}
        try:
            res = requests.post(url, json=params, headers=headers).json()
            _logger.info(f"[sf_pay]create_transfer_order res: {res}, params: {params}")
            return res
        except Exception as e:
            _logger.error(f"[sf_pay]create_transfer_order error: {e}, params: {params}")
            return {"code": 999, "message": f"请求失败, 原因：{e}"}

    def search_order(self, params):
        """
        查询接口
        :params: {
            'merchantNo: '商户号'  # 分配给各合作商户的唯一识别码
            'key': '密钥'  # 分配给各合作商户的唯一识别码
            'orderNo': '商户订单号'    # 本系统支付记录的唯一识别码
            'timestamp': '请求时间'  # yyyy-MM-dd HH:mm:ss, 请求时间，以印度标准时间 (GMT+5:30)为准,误差不允许超过5分钟
        } 

        接口返回：
        {
            "code":0,
            "message":null,
            "version":null,
            "merchantNo":"f3c2d1f505d4dfe12439451b37cb9c46",
            "amount": "100.00",
            "realAmount": "100.00",
            "orderFee": "0.00",
            "orderNo":"2024020115495258",
            "platformOrderNo": "2024020115495258",
            "status": 2, # 同步返回订单状态为 2,处理中;（后续通过异步通知或查询最终结果）
            "sign": "C3476440ED44272FBC9435C0DCCFC219"
        }
        """
        url = "https://api.mwxpa.com/api/indiapApi/pay/v2/apiQuery"
        params["sign"] = self._sign(params)
        headers = {"Content-Type": "application/json; charset=utf-8"}
        try:
            res = requests.post(url, json=params, headers=headers).json()
            # _logger.info(f"[sf_pay]search_order res: {res}, params: {params}")
            return res
        except Exception as e:
            _logger.error(f"[sf_pay]search_order error: {e}, params: {params}")
            return {"code": 999, "message": f"请求失败, 原因：{e}"}
        
    def create_supplement_order(self, params):
        """
        补单接口
        params: {
            "merchantNo": "商户号",
            "orderNo": "商户订单号",
            "utr": "",
            "timestamp": "时间戳",
        }
        {
            "code": 0, # code 为 0 时，请求成功
            "message": null,
            "sign": "7DE5616E365F70498BA698954DB9F2E7",
            "budanResult": "man", succ:成功 fail:失败 man:需人工 utr_used: utr已被使用
            "budanResultMsg": "需人工复核"
        }
        """
        url = "https://api.mwxpa.com/api/indiapApi/pay/v2/apiBudanService"

        params["sign"] = self._sign(params)
        headers = {"Content-Type": "application/json; charset=utf-8"}
        try:
            res = requests.post(url, json=params, headers=headers).json()
            # _logger.info(params)
            # _logger.info(res)
            return res
        except Exception as e:
            _logger.error(f"[sf_pay]create_supplement_order error: {e}, params: {params}")
            return {"code": 999, "message": f"请求失败, 原因：{e}"}