# -*- coding: utf-8 -*-
from odoo import models, fields  

class AfEmbedPoint(models.Model):  
    _name = 'af.embed.point'  # 模型名称，通常使用小写和下划线  
    _description = '嵌入点记录'  # 模型描述  
  
    user_id = fields.Many2one('loan.user', string='用户', required=True)  # 用户ID，关联到T_user模型  
    point_code = fields.Char(string='点代码', size=255)  # 可空的点代码  
    equip_id = fields.Char(string='设备ID', size=255)  # 可空的设备ID  
    install_time = fields.Integer(string='安装时间')  # 安装时间，使用int类型  
    active = fields.Boolean(default=True)
class AfDailyReport(models.Model):  
    _name = 'af.daily.report'  
    _description = '从appsflyer上的日常报告'  
    
    # id = fields.BigInteger(string='ID', readonly=True)  
    report_date = fields.Char(string='报告日期', )  
    agency = fields.Char(string='合作伙伴', )  
    media_source = fields.Char(string='渠道信息', )  
    campaign = fields.Text(string='Campaign')  
    impressions = fields.Integer(string='Impressions')  
    clicks = fields.Integer(string='Clicks')  
    ctr = fields.Float(string='CTR')  
    installs = fields.Integer(string='Installs')  
    conversion_rate = fields.Float(string='Conversion Rate')  
    sessions = fields.Integer(string='Sessions')  
    loyal_users = fields.Integer(string='Loyal Users')  
    loyal_users_installs = fields.Integer(string='忠实用户/安装')  
    total_cost = fields.Float(string='总成本')  
    average = fields.Float(string='平均eCPI')  
    # create_time = fields.Datetime(string='创建时间', default=fields.Datetime.now)  
    # update_time = fields.Datetime(string='更新时间', default=fields.Datetime.now, onupdate=fields.Datetime.now)
    active = fields.Boolean(default=True)
class AfEventTrackAccessSuccessLog(models.Model):  
    _name = 'af.event.track.access.success.log'  
    _description = 'af埋点成功访问日志'  
    
    # id = fields.BigInteger(string='ID', readonly=True)  
    user_id = fields.Many2one('loan.user', string='用户ID')  # Assuming loan.user represents users  
    appsflyer_id = fields.Char(string='Appsflyer ID', size=255)  
    order_id = fields.Char(string='订单ID', size=255)  
    device_id = fields.Char(string='设备ID', size=255)  
    event_name = fields.Char(string='事件名称', size=100)  
    event_value = fields.Char(string='事件值', size=255)  
    af_result = fields.Char(string='AF结果', size=255)  
    error = fields.Char(string='错误信息', size=255)  
    # create_time = fields.Datetime(string='创建时间', default=fields.Datetime.now)  
    app_name = fields.Char(string='应用名称', size=100) 
    active = fields.Boolean(default=True)
class AfEventTrackLog(models.Model):  
    _name = 'af.event.track.log'  
    _description = 'af埋点日志'  
    
    # id = fields.BigInteger(string='ID', readonly=True)  
    user_id = fields.Many2one('loan.user', string='用户ID')  
    event_name = fields.Char(string='事件名称', size=100)  
    event_value = fields.Char(string='事件值', size=255)  
    af_result = fields.Char(string='AF结果', size=255)  
    error = fields.Char(string='错误信息', size=255)  
    # create_time = fields.Datetime(string='创建时间', default=fields.Datetime.now)  
    app_name = fields.Char(string='应用名称', size=100)    
    active = fields.Boolean(default=True)
class AfEventTrackOpLog(models.Model):  
    _name = 'af.event.track.op.log'  
    _description = 'af埋点操作日志'  
    
    # id = fields.BigInteger(string='ID', readonly=True)  
    user_id = fields.Many2one('loan.user', string='用户ID')  
    appsflyer_id = fields.Char(string='Appsflyer ID', size=255)  
    order_id = fields.Char(string='订单ID', size=255)  
    device_id = fields.Char(string='设备ID', size=255)  
    event_name = fields.Char(string='事件名称', size=100)  
    event_value = fields.Char(string='事件值', size=255)  
    af_result = fields.Char(string='AF结果', size=255)  
    error = fields.Char(string='错误信息', size=255)  
    # create_time = fields.Datetime(string='创建时间', default=fields.Datetime.now)  
    app_name = fields.Char(string='应用名称', size=100)    
    active = fields.Boolean(default=True)
class AfEventTrackRegistLog(models.Model):  
    _name = 'af.event.track.regist.log'  # Odoo模型名，采用小写和下划线  
    _description = 'AF注册日志'  # 模型描述  

    # id = fields.BigInteger(string='ID', readonly=True)  # 自动处理ID  
    user_id = fields.Many2one('loan.user', string='用户', required=True)  # 关联用户ID  
    appsflyer_id = fields.Char(string='Appsflyer ID', size=255)  # 可为空  
    device_id = fields.Char(string='设备ID', size=255)  # 可为空  
    event_name = fields.Char(string='事件名称', size=100)  # 可为空  
    event_value = fields.Char(string='事件值', size=255)  # 可为空  
    af_result = fields.Char(string='AF结果', size=255)  # 可为空  
    error = fields.Char(string='错误信息', size=255)  # 可为空  
    # create_time = fields.Datetime(string='创建时间', default=fields.Datetime.now)  # 默认当前时间  
    app_name = fields.Char(string='应用名称', size=100)  # 可为空   
    active = fields.Boolean(default=True)
class AfEventsCallbackAccessSuccessS2S(models.Model):  
    _name = 'af.events.callback.access.success.s2s'  # Odoo模型名，采用小写和下划线  
    _description = 'AF事件回调成功日志（S2S）'  # 模型描述  

    # id = fields.BigInteger(string='ID', readonly=True)  # 自动处理ID  
    user_id = fields.Many2one('loan.user', string='用户')  # 关联用户ID  
    order_id = fields.Char(string='订单ID', size=64)  # 可为空  
    app_version = fields.Char(string='应用版本', size=64)  # 可为空  
    app_name = fields.Char(string='应用名称', size=64)  # 可为空  
    install_time_selected_timezone = fields.Datetime(string='安装时间（选定时区）')  # 可为空  
    install_time = fields.Char(string='安装时间', size=64)  # 可为空  
    campaign_type = fields.Char(string='活动类型', size=64)  # 可为空  
    af_adset = fields.Char(string='广告集', size=255)  # 可为空  
    af_adset_id = fields.Char(string='广告集ID', size=255)  # 可为空  
    appsflyer_id = fields.Char(string='Appsflyer ID', size=64)  # 可为空  
    media_source = fields.Char(string='媒体来源', size=255)  # 可为空  
    campaign = fields.Char(string='活动', size=255)  # 可为空  
    event_value = fields.Char(string='事件值', size=1000)  # 可为空  
    event_time = fields.Datetime(string='事件时间', required=True)  # 必填字段  
    app_id = fields.Char(string='应用ID', size=64)  # 可为空  
    event_name = fields.Char(string='事件名称', size=64)  # 可为空  
    advertising_id = fields.Char(string='广告ID', size=64)  # 可为空  
    af_channel = fields.Char(string='渠道', size=64)  # 可为空  
    af_ad = fields.Char(string='广告', size=255)  # 可为空  
    af_ad_id = fields.Char(string='广告ID', size=64)  # 可为空  
    af_c_id = fields.Char(string='广告客户ID', size=255)  # 可为空  
    af_ad_type = fields.Char(string='广告类型', size=128)  # 可为空  
    idfv = fields.Char(string='IDFV', size=64)  # 可为空  
    customer_user_id = fields.Char(string='客户用户ID', size=64)  # 可为空  
    custom_data = fields.Char(string='自定义数据', size=128)  # 可为空  
    idfa = fields.Char(string='IDFA', size=64)  # 可为空  
    af_prt = fields.Char(string='广告渠道', size=255)  # 可为空  
    # create_time = fields.Datetime(string='创建时间', default=fields.Datetime.now)  # 默认当前时间       
    active = fields.Boolean(default=True)
class AfEventsCallbackOpInfo(models.Model):  
    _name = 'af.events.callback.op.info'  # Odoo模型名  
    _description = 'AF事件回调操作信息'  # 模型描述  

    # id = fields.BigInteger(string='ID', readonly=True)  # Odoo会自动管理ID  
    user_id = fields.Many2one('loan.user', string='用户')  # 关联用户ID  
    order_id = fields.Char(string='订单ID', size=64)  # 订单ID  
    app_version = fields.Char(string='应用版本', size=64)  # 应用版本  
    app_name = fields.Char(string='应用名称', size=64)  # 应用名称  
    install_time_selected_timezone = fields.Datetime(string='安装时间（选定时区）')  # 可为空  
    install_time = fields.Char(string='安装时间', size=64)  # 安装时间  
    campaign_type = fields.Char(string='活动类型', size=64)  # 活动类型  
    af_adset_id = fields.Char(string='广告集ID', size=255)  # 广告集ID  
    appsflyer_id = fields.Char(string='Appsflyer ID', size=64)  # Appsflyer ID  
    media_source = fields.Char(string='媒体来源', size=255)  # 媒体来源  
    campaign = fields.Text(string='活动', size=500)  # 活动信息，使用Text以支持更长的内容  
    event_value = fields.Text(string='事件值', size=512)  # 事件值，使用Text以支持更长的内容  
    event_time = fields.Datetime(string='事件时间', required=True)  # 必填事件时间  
    af_ad = fields.Char(string='广告', size=255)  # 广告信息  
    af_channel = fields.Char(string='渠道', size=64)  # 渠道  
    app_id = fields.Char(string='应用ID', size=64)  # 应用ID  
    event_name = fields.Char(string='事件名称', size=64)  # 事件名称  
    advertising_id = fields.Char(string='广告ID', size=64)  # 广告ID  
    af_ad_id = fields.Char(string='广告ID（单独）', size=64)  # 单独广告ID  
    idfv = fields.Char(string='IDFV', size=64)  # IDFV  
    customer_user_id = fields.Char(string='客户用户ID', size=64)  # 客户用户ID  
    custom_data = fields.Char(string='自定义数据', size=128)  # 自定义数据  
    idfa = fields.Char(string='IDFA', size=64)  # IDFA  
    af_ad_type = fields.Char(string='广告类型', size=128)  # 广告类型  
    # create_time = fields.Datetime(string='创建时间', default=fields.Datetime.now)  # 创建时间   
    active = fields.Boolean(default=True)
class AfEventsCallbackOpInfoS2S(models.Model):  
    _name = 'af.events.callback.op.info.s2s'  # Odoo模型名  
    _description = 'AF事件回调操作信息（S2S）'  # 模型描述  

    # id = fields.BigInteger(string='ID', readonly=True)  # Odoo会自动管理ID  
    user_id = fields.Many2one('loan.user', string='用户')  # 关联用户ID  
    order_id = fields.Char(string='订单ID', size=64)  # 订单ID  
    app_version = fields.Char(string='应用版本', size=64)  # 应用版本  
    app_name = fields.Char(string='应用名称', size=64)  # 应用名称  
    install_time_selected_timezone = fields.Datetime(string='安装时间（选定时区）')  # 可为空  
    install_time = fields.Char(string='安装时间', size=64)  # 安装时间  
    campaign_type = fields.Char(string='活动类型', size=64)  # 活动类型  
    af_adset_id = fields.Char(string='广告集ID', size=255)  # 广告集ID  
    appsflyer_id = fields.Char(string='Appsflyer ID', size=64)  # Appsflyer ID  
    media_source = fields.Char(string='媒体来源', size=255)  # 媒体来源  
    campaign = fields.Char(string='活动', size=255)  # 活动信息  
    event_value = fields.Text(string='事件值', size=1000)  # 事件值，使用Text以支持更长的内容  
    event_time = fields.Datetime(string='事件时间', required=True)  # 必填事件时间  
    af_ad = fields.Char(string='广告', size=255)  # 广告信息  
    af_channel = fields.Char(string='渠道', size=64)  # 渠道  
    app_id = fields.Char(string='应用ID', size=64)  # 应用ID  
    event_name = fields.Char(string='事件名称', size=64)  # 事件名称  
    advertising_id = fields.Char(string='广告ID', size=64)  # 广告ID  
    af_ad_id = fields.Char(string='广告ID（单独）', size=64)  # 单独广告ID  
    idfv = fields.Char(string='IDFV', size=64)  # IDFV  
    customer_user_id = fields.Char(string='客户用户ID', size=64)  # 客户用户ID  
    custom_data = fields.Char(string='自定义数据', size=128)  # 自定义数据  
    idfa = fields.Char(string='IDFA', size=64)  # IDFA  
    af_ad_type = fields.Char(string='广告类型', size=64)  # 广告类型  
    af_prt = fields.Char(string='广告渠道', size=255)  # 广告渠道  
    # create_time = fields.Datetime(string='创建时间', default=fields.Datetime.now)  # 创建时间 
    active = fields.Boolean(default=True)
class AfEventsCallbackRecord(models.Model):  
    _name = 'af.events.callback.record'  # Odoo模型名  
    _description = 'AF事件回调记录'  # 模型描述  

    # id = fields.BigInteger(string='ID', readonly=True)  # Odoo自动管理ID  
    user_id = fields.Many2one('loan.user', string='用户')  # 关联用户，用于文件和用户关联  
    device_category = fields.Char(string='设备类别', size=100)  # 设备类别  
    bundle_id = fields.Char(string='Bundle ID', size=100)  # Bundle ID  
    event_source = fields.Char(string='事件来源', size=100)  # 事件来源  
    app_version = fields.Char(string='应用版本', size=100)  # 应用版本  
    city = fields.Char(string='城市', size=100)  # 城市  
    device_model = fields.Char(string='设备型号', size=100)  # 设备型号  
    af_c_id = fields.Char(string='AF C ID', size=100)  # AF C ID  
    attributed_touch_time_selected_timezone = fields.Datetime(string='归因触摸时间（选定时区）')  # 可为空  
    selected_currency = fields.Char(string='选择的货币', size=100)  # 选择的货币  
    app_name = fields.Char(string='应用名称', size=100)  # 应用名称  
    install_time_selected_timezone = fields.Datetime(string='安装时间（选定时区）')  # 可为空  
    postal_code = fields.Char(string='邮政编码', size=100)  # 邮政编码  
    wifi = fields.Char(string='Wi-Fi状态', size=100)  # Wi-Fi状态  
    install_time = fields.Char(string='安装时间', size=100)  # 安装时间  
    attributed_touch_type = fields.Char(string='归因触摸类型', size=100)  # 归因触摸类型  
    af_attribution_lookback = fields.Char(string='AF归因回溯', size=100)  # AF归因回溯  
    campaign_type = fields.Char(string='活动类型', size=100)  # 活动类型  
    af_adset_id = fields.Char(string='广告集ID', size=100)  # 广告集ID  
    device_download_time_selected_timezone = fields.Datetime(string='下载时间（选定时区）')  # 可为空  
    conversion_type = fields.Char(string='转化类型', size=100)  # 转化类型  
    api_version = fields.Char(string='API版本', size=100)  # API版本  
    attributed_touch_time = fields.Char(string='归因触摸时间', size=100)  # 归因触摸时间  
    is_retargeting = fields.Char(string='是否再营销', size=100)  # 是否再营销  
    country_code = fields.Char(string='国家代码', size=100)  # 国家代码  
    match_type = fields.Char(string='匹配类型', size=100)  # 匹配类型  
    appsflyer_id = fields.Char(string='Appsflyer ID', size=100)  # Appsflyer ID  
    dma = fields.Char(string='DMA', size=100)  # DMA  
    af_prt = fields.Char(string='AF PRT', size=100)  # AF PRT  
    event_revenue_currency = fields.Char(string='事件收入货币', size=100)  # 事件收入货币  
    media_source = fields.Char(string='媒体来源', size=100)  # 媒体来源  
    campaign = fields.Char(string='活动', size=500)  # 活动  
    region = fields.Char(string='地区', size=100)  # 地区  
    event_value = fields.Char(string='事件值', size=1000)  # 事件值  
    ip = fields.Char(string='IP地址', size=100)  # IP地址  
    event_time = fields.Datetime(string='事件时间', required=True)  # 必填事件时间  
    af_adset = fields.Char(string='广告组', size=100)  # 广告组  
    af_ad = fields.Char(string='广告', size=255)  # 广告  
    state = fields.Char(string='状态', size=100)    
    network_account_id = fields.Char(string='Network Account ID', size=100)  # 媒介账户ID  
    device_type = fields.Char(string='Device Type', size=100)  # 设备类型  
    af_channel = fields.Char(string='AF Channel', size=100)  # AF渠道  
    device_download_time = fields.Char(string='Device Download Time', size=100)  # 设备下载时间  
    language = fields.Char(string='Language', size=100)  # 语言  
    app_id = fields.Char(string='App ID', size=100)  # 应用ID  
    event_name = fields.Char(string='Event Name', size=100)  # 事件名称  
    advertising_id = fields.Char(string='Advertising ID', size=100)  # 广告ID  
    os_version = fields.Char(string='OS Version', size=100)  # 操作系统版本  
    platform = fields.Char(string='Platform', size=100)  # 平台  
    selected_timezone = fields.Char(string='Selected Timezone', size=100)  # 选定时区  
    af_ad_id = fields.Char(string='AF Ad ID', size=100)  # AF广告ID  
    user_agent = fields.Text(string='User Agent')  # 用户代理  
    is_primary_attribution = fields.Char(string='Is Primary Attribution', size=100)  # 是否为主要归因  
    sdk_version = fields.Char(string='SDK Version', size=100)  # SDK版本  
    event_time_selected_timezone = fields.Datetime(string='Event Time (Selected Timezone)')  # 事件时间（选定时区）  
    create_time = fields.Datetime(string='Creation Time', default=fields.Datetime.now)  # 创建时间  
    idfv = fields.Char(string='IDFV', size=100)  # IDFV  
    af_sub1 = fields.Char(string='AF Sub 1', size=100)  # AF子变量1  
    customer_user_id = fields.Char(string='Customer User ID', size=100)  # 客户用户ID  
    is_lat = fields.Char(string='Is LAT', size=100)  # 是否LAT  
    contributor_2_af_prt = fields.Char(string='Contributor 2 AF PRT', size=100)  # 贡献者2 AF PRT  
    gp_broadcast_referrer = fields.Char(string='GP Broadcast Referrer', size=100)  # GP广播来源  
    contributor_2_touch_time = fields.Char(string='Contributor 2 Touch Time', size=100)  # 贡献者2触摸时间  
    contributor_3_touch_type = fields.Char(string='Contributor 3 Touch Type', size=100)  # 贡献者3触摸类型  
    af_cost_value = fields.Char(string='AF Cost Value', size=100)  # AF成本值  
    contributor_1_match_type = fields.Char(string='Contributor 1 Match Type', size=100)  # 贡献者1匹配类型  
    contributor_3_af_prt = fields.Char(string='Contributor 3 AF PRT', size=100)  # 贡献者3 AF PRT  
    custom_data = fields.Char(string='Custom Data', size=255)  # 自定义数据  
    contributor_2_touch_type = fields.Char(string='Contributor 2 Touch Type', size=100)  # 贡献者2触摸类型  
    gp_install_begin = fields.Char(string='GP Install Begin', size=100)  # GP安装开始  
    amazon_aid = fields.Char(string='Amazon AID', size=100)  # Amazon AID  
    gp_referrer = fields.Text(string='GP Referrer')  # GP来源  
    af_cost_model = fields.Char(string='AF Cost Model', size=100)  # AF成本模型  
    operator = fields.Char(string='Operator', size=100)  # 运营商  
    keyword_match_type = fields.Char(string='Keyword Match Type', size=100)  # 关键词匹配类型   
    contributor_3_match_type = fields.Char(string='贡献者3匹配类型', size=100)  # 贡献者3匹配类型  
    contributor_3_touch_time = fields.Char(string='贡献者3触摸时间', size=100)  # 贡献者3触摸时间 
    active = fields.Boolean(default=True)
class AfEventsCallbackRegistS2S(models.Model):  
    _name = 'af.events.callback.regist.s2s'  
    _description = 'App Marketing Events Callback Registration S2S'  

    # id = fields.Auto()  # 主键  
    user_id = fields.Many2one('loan.user', string='User')  # 用户ID，关联Odoo中用户模型  
    order_id = fields.Char(string='Order ID', size=64)  # 订单ID  
    app_version = fields.Char(string='App Version', size=64)  # 应用版本  
    app_name = fields.Char(string='App Name', size=64)  # 应用名称  
    install_time_selected_timezone = fields.Datetime(string='Install Time (Selected Timezone)')  # 安装时间（选定时区）  
    install_time = fields.Char(string='Install Time', size=64)  # 安装时间  
    campaign_type = fields.Char(string='Campaign Type', size=64)  # 活动类型  
    af_adset = fields.Char(string='AF Ad Set', size=255)  # AF广告组  
    af_adset_id = fields.Char(string='AF Ad Set ID', size=255)  # AF广告组ID  
    appsflyer_id = fields.Char(string='Appsflyer ID', size=64)  # Appsflyer ID  
    media_source = fields.Char(string='Media Source', size=255)  # 媒体来源  
    campaign = fields.Char(string='Campaign', size=255)  # 活动名称  
    event_value = fields.Char(string='Event Value', size=512)  # 事件值  
    event_time = fields.Datetime(string='Event Time', required=True)  # 事件时间  
    app_id = fields.Char(string='App ID', size=64)  # 应用ID  
    event_name = fields.Char(string='Event Name', size=64)  # 事件名称  
    advertising_id = fields.Char(string='Advertising ID', size=64)  # 广告ID  
    af_channel = fields.Char(string='AF Channel', size=64)  # AF渠道  
    af_ad = fields.Char(string='AF Ad', size=255)  # AF广告  
    af_ad_id = fields.Char(string='AF Ad ID', size=64)  # AF广告ID  
    af_c_id = fields.Char(string='AF Campaign ID', size=255)  # AF活动ID  
    af_ad_type = fields.Char(string='AF Ad Type', size=128)  # AF广告类型  
    idfv = fields.Char(string='IDFV', size=64)  # IDFV  
    customer_user_id = fields.Char(string='Customer User ID', size=64)  # 客户用户ID  
    custom_data = fields.Char(string='Custom Data', size=128)  # 自定义数据  
    idfa = fields.Char(string='IDFA', size=64)  # IDFA  
    af_prt = fields.Char(string='AF PRT', size=255)  # AF PRT  
    # create_time = fields.Datetime(string='Create Time', default=fields.Datetime.now)  # 创建时间   
    active = fields.Boolean(default=True)
class AfInAppEventsReport(models.Model):  
    _name = 'af.in.app.events.report'  
    _description = 'In-App Events Report from Appsflyer'  

    # id = fields.Auto()  # 自动生成的主键  
    attributed_touch_type = fields.Char(string='Attributed Touch Type', size=50, default='')  # 归因触摸类型  
    attributed_touch_time = fields.Char(string='Attributed Touch Time', size=20, default='')  # 归因触摸时间  
    install_time = fields.Char(string='Install Time', size=20, default='', help='用户安装时间')  # 用户安装时间  
    event_time = fields.Char(string='Event Time', size=20, default='', help='事件时间')  # 事件时间  
    event_name = fields.Char(string='Event Name', size=50, default='', help='事件名称')  # 事件名称  
    success_time = fields.Char(string='Success Time', size=20, default='')  # 成功时间  
    user_id = fields.Many2one('loan.user', string='User', required=True)  # 用户ID，关联Odoo用户  
    device_id = fields.Char(string='Device ID', size=200, default='')  # 设备ID  
    partner = fields.Char(string='Partner', size=100, default='', help='合作伙伴')  # 合作伙伴  
    media_source = fields.Char(string='Media Source', size=50, default='', help='渠道信息')  # 渠道信息  
    channel = fields.Char(string='Channel', size=100, default='', help='渠道')  # 渠道  
    campaign = fields.Char(string='Campaign', size=500, default='')  # 活动  
    campaign_id = fields.Char(string='Campaign ID', size=50, default='')  # 活动ID  
    country_code = fields.Char(string='Country Code', size=100, default='', help='国家')  # 国家  
    state = fields.Char(string='State', size=100, default='', help='地域')  # 地域  
    city = fields.Char(string='City', size=100, default='', help='城市')  # 城市  
    postal_code = fields.Char(string='Postal Code', size=100, default='', help='邮编')  # 邮编  
    ip = fields.Char(string='IP Address', size=50, default='', help='IP地址')  # IP地址  
    wifi = fields.Char(string='Network Type', size=100, default='', help='网络')  # 网络类型  
    operator = fields.Char(string='Operator', size=128, default='', help='运营商')  # 运营商  
    carrier = fields.Char(string='Carrier', size=100, default='', help='载体')  # 载体  
    appsflyer_id = fields.Char(string='Appsflyer ID', size=50, default='')  # Appsflyer ID  
    advertising_id = fields.Char(string='Advertising ID', size=50, default='0', help='advertising id')  # 广告ID  
    device_type = fields.Char(string='Device Type', size=100, default='')  # 设备类型  
    app_version = fields.Char(string='App Version', size=50, default='', help='软件版本')  # 软件版本  
    app_id = fields.Char(string='App ID', size=50, default='', help='App ID值')  # app ID值  
    # create_time = fields.Datetime(string='Create Time', default=fields.Datetime.now)  # 创建时间  
    # update_time = fields.Datetime(string='Update Time', default=fields.Datetime.now, required=True)  # 更新时间  
    active = fields.Boolean(default=True)
class AfInstallsReport(models.Model):  
    _name = 'af.installs.report'  
    _description = 'Installs Report from Appsflyer'  

    # id = fields.Auto()  # 自动生成的主键  
    media_source = fields.Char(string='Media Source', size=50, required=True, default='', help='渠道信息')  # 渠道信息  
    install_time = fields.Char(string='Install Time', size=20, default='', help='用户安装时间')  # 用户安装时间  
    city = fields.Char(string='City', size=100, default='', help='城市')  # 城市  
    country_code = fields.Char(string='Country Code', size=100, default='', help='国家')  # 国家  
    ip = fields.Char(string='IP Address', size=50, default='', help='IP地址')  # IP地址  
    operator = fields.Char(string='Operator', size=128, default='', help='运营商')  # 运营商  
    appsflyer_id = fields.Char(string='Appsflyer ID', size=50, default='')  # Appsflyer ID  
    advertising_id = fields.Char(string='Advertising ID', size=50, default='0', help='advertising id')  # 广告ID  
    imei = fields.Char(string='IMEI', size=30, default='', help='硬件IMEI值')  # 硬件IMEI值  
    platform = fields.Char(string='Platform', size=50, default='', help='平台信息')  # 平台信息  
    device_type = fields.Char(string='Device Type', size=100)  # 设备类型  
    os_version = fields.Char(string='OS Version', size=50, default='', help='设备系统类型')  # 设备系统类型  
    app_version = fields.Char(string='App Version', size=50, default='', help='软件版本')  # 软件版本  
    sdk_version = fields.Char(string='SDK Version', size=50, default='', help='SDK版本')  # SDK版本  
    app_id = fields.Char(string='App ID', size=50, default='', help='App ID值')  # App ID值  
    app_name = fields.Char(string='App Name', size=100, default='', help='App名称')  # App名称  
    event_name = fields.Char(string='Event Name', size=100, default='', help='事件名称')  # 事件名称  
    interface_event_name = fields.Char(string='Interface Event Name', size=16, default='', help='接口名称')  # 接口名称  
    is_retargeting = fields.Char(string='Is Retargeting', size=100, default='', help='是否重定向')  # 是否重定向  
    retargeting_conversion_type = fields.Char(string='Retargeting Conversion Type', size=100, default='')  # 重定向转化类型  
    user_agent = fields.Char(string='User Agent', size=500, default='', help='用户代理')  # 用户代理  
    start_time = fields.Char(string='Start Time', size=20, default='', help='数据产生的日期')  # 数据产生的日期  
    source = fields.Char(string='Source', size=20, default='', help='来源: normal或media')  # 来源类型  
    event_time = fields.Char(string='Event Time', size=100, default='', help='事件时间')  # 事件时间  
    event_source = fields.Char(string='Event Source', size=100, default='', help='事件来源')  # 事件来源  
    partner = fields.Char(string='Partner', size=100, default='', help='合作伙伴')  # 合作伙伴  
    channel = fields.Char(string='Channel', size=100, default='', help='渠道')  # 渠道  
    keywords = fields.Char(string='Keywords', size=100, default='', help='关键字')  # 关键字  
    region = fields.Char(string='Region', size=100, default='', help='区域')  # 区域  
    state = fields.Char(string='State', size=100, default='', help='地域')  # 地域  
    postal_code = fields.Char(string='Postal Code', size=100, default='', help='邮编')  # 邮编  
    dma = fields.Char(string='DMA', size=100, default='')  # DMA  
    wifi = fields.Char(string='Network', size=100, default='', help='网络')  # 网络类型  
    carrier = fields.Char(string='Carrier', size=100, default='', help='载体')  # 载体  
    language = fields.Char(string='Language', size=100, default='', help='语言')  # 语言  
    android_id = fields.Char(string='Android ID', size=100, default='')  # Android ID  
    customer_user_id = fields.Char(string='Customer User ID', size=100, default='', help='系统用户ID')  # 系统用户ID  
    # create_time = fields.Datetime(string='Create Time', default=fields.Datetime.now, required=True)  # 创建时间  
    active = fields.Boolean(default=True)
class AfRequestLog(models.Model):  
    _name = 'af.request.log'  
    _description = 'AF Request Log'  
    _order = 'create_time desc'  # 默认按照创建时间降序排列  

    # id = fields.Auto()  # 自动生成的主键  
    report_type = fields.Char(string='Report Type', size=50, required=True, default='', help='AF 报告类型')  
    app_id = fields.Char(string='App ID', size=50, required=True, default='', help='AppId名称')  
    start_time = fields.Char(string='Start Time', size=30, required=True)  
    end_time = fields.Char(string='End Time', size=30, required=True)  
    flag = fields.Boolean(string='Success Flag', help='1-成功;0-失败')  # 将 tinyint 转换为 bool  
    remark = fields.Text(string='Remark', default='', help='备注信息')  
    request_cnt = fields.Integer(string='Request Count', default=1)  
    # create_time = fields.Datetime(string='Create Time', default=fields.Datetime.now, required=True)  
    # update_time = fields.Datetime(string='Update Time', default=fields.Datetime.now, required=True, index=True)  
    active = fields.Boolean(default=True)
class AfTrackPoint(models.Model):  
    _name = 'af.track.point'  
    _description = 'AF Track Point'  

    # id = fields.Auto()  # 自动生成的主键  
    user_id = fields.Many2one('loan.user', string='User', help='用户 ID')  # 假设与用户模型关联，也可以根据业务需要调整  
    app_version = fields.Char(string='App Version', size=64)  
    app_name = fields.Char(string='App Name', size=64)  
    appsflyer_id = fields.Char(string='Appsflyer ID', size=128)  
    device_id = fields.Char(string='Device ID', size=64)  
    install_time = fields.Datetime(string='Install Time', help='安装时间')  
    media_source = fields.Char(string='Media Source', size=128)  
    event_time = fields.Datetime(string='Event Time', required=True)  # 事件时间从 datetime 转换  
    # create_time = fields.Datetime(string='Create Time', default=fields.Datetime.now, help='创建时间')             
    active = fields.Boolean(default=True)

class AfTrackPointOrder(models.Model):  
    _name = 'af.track.point.order'  
    _description = 'AF Track Point Order'  
    _order = 'create_time desc'  # 根据创建时间降序排列  

    # id = fields.Auto()  # 自动生成的主键  
    user_id = fields.Many2one('loan.user', string='User', help='用户 ID')  # 假设与用户模型关联  
    order_id = fields.Char(string='Order ID', size=64)  
    app_version = fields.Char(string='App Version', size=64)  
    app_name = fields.Char(string='App Name', size=64)  
    appsflyer_id = fields.Char(string='Appsflyer ID', size=128)  
    device_id = fields.Char(string='Device ID', size=64)  
    install_time = fields.Datetime(string='Install Time', help='安装时间')  
    event_time = fields.Datetime(string='Event Time', required=True)  # 事件时间  
    # create_time = fields.Datetime(string='Create Time', default=fields.Datetime.now, required=True)  # 创建时间  
    active = fields.Boolean(default=True)


class AfTrackPointRegist(models.Model):  
    _name = 'af.track.point.regist'  
    _description = 'AF Track Point Registration'  
    _order = 'create_time desc'  # 根据创建时间降序排列  

    # id = fields.Auto()  # 自动生成的主键  
    user_id = fields.Many2one('loan.user', string='User', help='用户 ID')  # 假设与用户模型关联  
    app_version = fields.Char(string='App Version', size=64)  
    app_name = fields.Char(string='App Name', size=64)  
    appsflyer_id = fields.Char(string='Appsflyer ID', size=128)  
    device_id = fields.Char(string='Device ID', size=64)  
    install_time = fields.Datetime(string='Install Time', help='安装时间')  
    media_source = fields.Char(string='Media Source', size=128)  
    event_time = fields.Datetime(string='Event Time', required=True)  # 事件时间  
    # create_time = fields.Datetime(string='Create Time', default=fields.Datetime.now, required=True)  # 创建时间  
    active = fields.Boolean(default=True)