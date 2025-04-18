import time
import random

def generate_order_no(suffix=''):
    """
    生成18位的唯一订单号
    :param prefix: 后缀，系统编码(分布式不重复)
    :return: 唯一订单号字符串
    """
    # 当前时间戳，精确到毫秒 13位
    timestamp = str(int(time.time() * 1000))
    # 随机数部分，这里取4位，可根据需要调整
    random_part = str(random.randint(1000, 9999))
    # 拼接字符串
    combined = timestamp[-12:] + suffix + random_part
    # 确保总长度不超过18位
    order_id = combined[:18]
    return order_id