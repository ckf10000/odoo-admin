import logging
from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class UserAppInfo(models.Model):
    """
    class T_user_app_info_data {

        int id;//int, key, ODOO standard

        String orderId;//int, not null, key of T_bill 的id

        /**
        * app名称
        */
        public String appName;
        /**
        * app包名
        */
        public String packageName;
        /**
        * 首次安装时间(原数据varchar) 13位时间戳
        */
        public long firstInstallTime;
        /**
        * 最近一次更新时间（原数据varchar) 13位时间戳
        */
        public long lastUpdateTime;
        /**
        * app类型(是否系统安装）
        */
        public int appType;
        public int versionCode;
        public String versionName;
    }
    """
    _name = 'risk.app.info'
    _description = 'User App Info'
    _inherit = ['loan.basic.model']
    _table = 'T_user_app_info_data'

    order_ids = fields.Char(string='bill id', index=True)
    app_name = fields.Char(string='app name')
    package_name = fields.Char(string='package name')
    first_install_time = fields.Integer(string='first install time')
    last_update_time = fields.Integer(string='last update time')
    app_type = fields.Integer(string='app type')
    version_code = fields.Integer(string='version code')
    version_name = fields.Char(string='version name')


class UserCallData(models.Model):
    """
    class T_user_call_data {

        int id;//int, key, ODOO standard

        String orderId;//int, not null, key of T_bill 的id

        /**
        * 通话姓名
        */
        public String name;
        /**
        * 通话号码
        */
        public String phone;
        /**
        * 通话时长
        */
        public String duration;
        /**
        * 通话创建时间
        */
        public long callTime;
        /**
        * 通话类型  1-接入,2-打出,3-未接
        */
        public int type;
    }
    """
    _name = 'risk.call.data'
    _description = 'User Call Data'
    _inherit = ['loan.basic.model']
    _table = 'T_user_call_data'

    order_ids = fields.Char(string='bill id', index=True)
    name = fields.Char(string='name')
    phone = fields.Char(string='phone')
    duration = fields.Char(string='duration')
    call_time = fields.Integer(string='call time')
    type = fields.Integer(string='type')


class UserCallData(models.Model):
    _name = 'risk.contact.data'
    _description = 'User Contact Data'
    _inherit = ['loan.basic.model']
    _table = 'T_user_contact_data'

    order_ids = fields.Char(string='bill id', index=True)
    name = fields.Char(string='name')
    mobile = fields.Char(string='mobile')
    updated_time = fields.Char(string='updated time')
    starred = fields.Integer(string='starred')
    times_contacted = fields.Integer(string='times contacted')
    last_time_contacted = fields.Integer(string='last time contacted')


class UserDeviceMoreInfoData(models.Model):
    _name = 'risk.device.more.info.data'
    _description = 'User Device More Info Data'
    _inherit = ['loan.basic.model']
    _table = 'T_user_device_more_info_data'

    order_ids = fields.Char(string='bill id', index=True)
    device_info = fields.Json(string='device info')
    # is_charging = fields.Integer(string='is charging')
    # battery_pct = fields.Integer(string='battery pct')
    # charge_type = fields.Integer(string='charge type')
    # battery_temperature = fields.Integer(string='battery temperature')
    # battery_health = fields.Integer(string='battery health')
    # screen_brightness = fields.Integer(string='screen brightness')

    # andid = fields.Char(string='android id')
    # gaid = fields.Char(string='gaid')
    # network_operator_name = fields.Char(string='network operator name')
    # network_operator = fields.Char(string='network operator')
    # network_type = fields.Char(string='network type')
    # phone_type = fields.Char(string='phone type')
    # mcc = fields.Char(string='mcc')
    # bluetooth_mac = fields.Char(string='bluetooth mac')
    # mnc = fields.Char(string='mnc')
    # locale_iso3_language = fields.Char(string='locale iso3 language')
    # locale_iso3_country = fields.Char(string='locale iso3 country')
    # time_zone_id = fields.Char(string='time zone id')
    # locale_display_language = fields.Char(string='locale display language')
    # cid = fields.Char(string='cid')
    # dns = fields.Char(string='dns')
    # uuid = fields.Char(string='uuid')
    # slot_count = fields.Integer(string='slot count')
    # meid = fields.Char(string='meid')
    # imei1 = fields.Char(string='imei1')
    # imei2 = fields.Char(string='IMEI2')
    # imsi = fields.Char(string='IMSI')
    # mac = fields.Char(string='MAC')
    # language = fields.Char(string='Language')
    # ui_mode_type = fields.Char(string='UI Mode Type')
    # security_patch = fields.Char(string='Security Patch')
    # model = fields.Char(string='Model')
    # release = fields.Char(string='Release')
    # brand = fields.Char(string='Brand')
    # product = fields.Char(string='Product')
    # sdk_version_code = fields.Char(string='SDK Version Code')
    # physical_size = fields.Char(string='Physical Size')
    # cpu_type = fields.Char(string='CPU Type')
    # cpu_min = fields.Char(string='CPU Min')
    # cpu_max = fields.Char(string='CPU Max')

    # cpu_cur = fields.Char(string='CPU Cur')
    # manufacturer_name = fields.Char(string='Manufacturer Name')
    # board = fields.Char(string='Board')
    # serial_number = fields.Char(string='Serial Number')
    # display = fields.Char(string='Display')
    # uid = fields.Char(string='UID')
    # bootloader = fields.Char(string='Bootloader')
    # finger_print = fields.Char(string='Finger Print')
    # host = fields.Char(string='Host')
    # hardware = fields.Char(string='Hardware')
    # device = fields.Char(string='Device')
    # user = fields.Char(string='User')
    # radio_version = fields.Char(string='Radio Version')
    # tags = fields.Char(string='Tags')
    # time = fields.Char(string='Time')
    # type = fields.Char(string='Type')
    # base_os = fields.Char(string='Base OS')
    # baseband_ver = fields.Char(string='Baseband Ver')
    # resolution = fields.Char(string='Resolution')
    # screen_density = fields.Char(string='Screen Density')
    # screen_density_dpi = fields.Char(string='Screen Density DPI')
    # cpu_abi = fields.Char(string='CPU ABI')
    # cpu_abi2 = fields.Char(string='CPU ABI2')
    # abis = fields.Char(string='ABIs')
    # tablet = fields.Integer(string='Tablet')

    # audio_external = fields.Integer(string='Audio External')
    # audio_internal = fields.Integer(string='Audio Internal')
    # contact_group = fields.Integer(string='Contact Group')
    # download_files = fields.Integer(string='Download Files')
    # images_external = fields.Integer(string='Images External')
    # images_internal = fields.Integer(string='Images Internal')
    # video_external = fields.Integer(string='Video External')
    # video_internal = fields.Integer(string='Video Internal')
    # wifi_enabled = fields.Boolean(string='Wifi Enabled')
    # ip = fields.Char(string='IP')
    # current_wifi = fields.Char(string='Current Wifi')
    # configured_wifi = fields.Char(string='Configured Wifi')
    # root = fields.Integer(string='Root')
    # simulator = fields.Integer(string='Simulator')
    # keyboard = fields.Integer(string='Keyboard')
    # ringer_mode = fields.Integer(string='Ringer Mode')
    # dbm = fields.Char(string='DBM')
    # last_boot_time = fields.Integer(string='Last Boot Time')
    # http_proxy_host_port = fields.Char(string='HTTP Proxy Host Port')
    # vpn_address = fields.Char(string='VPN Address')
    # is_using_proxy_port = fields.Integer(string='Is Using Proxy Port')
    # is_using_vpn = fields.Integer(string='Is Using VPN')
    # is_usb_debug = fields.Integer(string='Is USB Debug')
    # is_mock_location = fields.Integer(string='Is Mock Location')
    # is_airplane_mode = fields.Integer(string='Is Airplane Mode')
    # elapsed_realtime = fields.Integer(string='Elapsed Realtime')
    # networking_roaming = fields.Char(string='Networking Roaming')
    # camera_num = fields.Integer(string='Camera Number')

    # internal_storage_total = fields.Integer(string='Internal Storage Total')
    # internal_storage_usable = fields.Integer(string='Internal Storage Usable')
    # memory_card_size = fields.Integer(string='Memory Card Size')
    # memory_card_size_use = fields.Integer(string='Memory Card Size Use')
    # ram_total_size = fields.Integer(string='RAM Total Size')
    # ram_usable_size = fields.Integer(string='RAM Usable Size')


class UserLbsData(models.Model):
    _name = 'risk.lbs.data'
    _description = 'User Lbs Data'
    _inherit = ['loan.basic.model']
    _table = 'T_user_lbs_data'

    order_ids = fields.Char(string='bill id', index=True)
    action = fields.Char(string='Action')
    code = fields.Char(string='Code')
    lat = fields.Char(string='Latitude')
    lon = fields.Char(string='Longitude')
    map = fields.Char(string='Map')


class UserSmsData(models.Model):
    _name = 'risk.sms.data'
    _description = 'User sms Data'
    _inherit = ['loan.basic.model']
    _table = 'T_user_sms_data'

    order_ids = fields.Char(string='bill id', index=True)
    content = fields.Char(string='Content')
    phone = fields.Char(string='Phone')
    type = fields.Char(string='Type')
    time = fields.Char(string='Time')
    read = fields.Char(string='Read')
    seen = fields.Char(string='Seen')
    status = fields.Char(string='Status')
    person = fields.Char(string='Person')




