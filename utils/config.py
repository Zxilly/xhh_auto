'''
# @Author       : Chr_
# @Date         : 2020-07-29 14:21:39
# @LastEditors  : Chr_
# @LastEditTime : 2020-09-05 00:12:36
# @Description  : 读取并验证配置
'''

import os

import chardet
import toml

from .log import get_logger, init_logger

logger = get_logger('Setting')

SCRIPT_PATH = f'{os.path.split(os.path.realpath(__file__))[0][:-5]}'

DEFAULT_PATH = f'{SCRIPT_PATH}config.toml'

CFG = {}


def get_script_path() -> str:
    '''
    获取脚本所在路径

    返回:
        str: 脚本所在路径
    '''
    return (SCRIPT_PATH)


def get_config(key: str) -> dict:
    '''
    获取某一项配置

    参数:
        key: 要获取的设置键名
    返回:
        dict: 配置信息字典
    '''
    return (CFG.get(key))


def get_all_config() -> dict:
    '''
    获取全部配置

    返回:
        dict: 配置信息字典
    '''
    return (CFG)


def load_config(path: str = DEFAULT_PATH) -> dict:
    '''
    读取并验证配置

    参数:
        [path]: 配置文件路径,默认为config.toml
    返回:
        dict: 验证过的配置字典
    '''
    global CFG
    try:
        logger.debug('开始读取配置')
        with open(path, 'rb') as f:
            content = f.read()
        detect = chardet.detect(content)
        encode = detect.get('encode', 'utf-8')
        raw_cfg = dict(toml.loads(content.decode(encode)))
        CFG = verify_config(raw_cfg)
        debug = os.environ.get('mode', 'release').lower()
        level = 0 if debug == 'debug' else 20
        init_logger(level)
        logger.debug('配置验证通过')
        return (CFG)

    except FileNotFoundError:
        logger.error(f'[*] 配置文件[{path}]不存在')
        raise FileNotFoundError(f'[*] 配置文件[{path}]不存在')
    except ValueError as e:
        logger.error(f'[*] 配置文件验证失败 [{e}]', exc_info=True)


def verify_config(cfg: dict) -> dict:
    """
    验证配置

    参数:
        cfg: 配置字典
    返回:
        dict: 验证过的配置字典,剔除错误的和不必要的项目
    """
    vcfg = {'main': {'check_update': True, 'debug': False, 'join_xhhauto': True},
            'ftqq': {'enable': False, 'skey': '', 'only_on_error': False},
            'email': {'port': 465, 'server': '', 'password': '', 'user': '',
                      'recvaddr': '', 'sendaddr': '', 'only_on_error': False},
            'heybox': {'channel': 'heybox_yingyongbao', 'os_type': 'Android',
                       'os_version': '9', 'sleep_interval': 1.0, 'auto_report': True},
            'accounts': []}

    main = cfg.get('main', {})
    if main and isinstance(main, dict):
        check_update = bool(main.get('check_update', True))
        debug = bool(main.get('debug', False))
        join_xhhauto = bool(main.get('join_xhhauto', True))
        vcfg['main'] = {'check_update': check_update, 'debug': debug,
                        'join_xhhauto': join_xhhauto}
    else:
        logger.debug('[main]节配置有误或者未配置,将使用默认配置')

    ftqq = cfg.get('ftqq', {})
    if ftqq and isinstance(ftqq, dict):
        enable = bool(ftqq.get('enable', False))
        skey = ftqq.get('skey', "")
        only_on_error = bool(ftqq.get('only_on_error', False))
        if enable and not skey:
            raise ValueError('开启了FTQQ模块,但是未指定SKEY,请检查配置文件')
        vcfg['ftqq'] = {'enable': enable, 'skey': skey,
                        'only_on_error': only_on_error}
    else:
        logger.debug('[ftqq]节配置有误或者未配置,将使用默认配置')

    email = cfg.get('email', {})
    if email and isinstance(email, dict):
        enable = bool(email.get('enable', False))
        try:
            port = int(email.get('port', 0))
        except ValueError:
            port = 465
            logger.warning('[*] [email]节port必须为数字')
        server = email.get('server', '')
        password = email.get('password', '')
        user = email.get('user', '')
        recvaddr = email.get('recvaddr', '')
        sendaddr = email.get('sendaddr', '')
        only_on_error = bool(email.get('only_on_error', False))
        if enable and not (port and server
                           and password and user and recvaddr and sendaddr):
            raise ValueError('开启了email模块,但是配置不完整,请检查配置文件')
        vcfg['email'] = {'enable': enable, 'port': port, 'server': server,
                         'password': password, 'user': user,
                         'recvaddr': recvaddr, 'sendaddr': sendaddr,
                         'only_on_error': only_on_error}
    else:
        logger.debug('[email]节配置有误或者未配置,将使用默认配置')

    heybox = cfg.get('heybox', {})
    if heybox and isinstance(heybox, dict):
        channel = heybox.get('channel', "heybox_yingyongbao")
        try:
            os_type = int(heybox.get('os_type', 1))
            if os_type not in (1, 2):
                raise ValueError
        except ValueError:
            os_type = 1
            logger.warning('[*] [heybox]节os_type只能为1或者2')
        os_version = heybox.get('os_version', "9")
        try:
            sleep = float(heybox.get('sleep_interval', 1))
        except ValueError:
            sleep = 1.0
            logger.warning('[*] [heybox]节sleep_interval必须为数字')
        auto_report = bool(heybox.get('auto_report', False))
        vcfg['heybox'] = {'channel': channel, 'os_type': os_type,
                          'os_version': os_version, 'sleep_interval': sleep,
                          'auto_report': auto_report}
    else:
        logger.debug('[heybox]节配置有误或者未配置,将使用默认配置')

    accounts = cfg.get('accounts', [])
    if accounts and isinstance(accounts, list):
        vcfg['accounts'] = []
        for i, account in enumerate(accounts, 1):
            try:
                heybox_id = int(account['heybox_id'])
                imei = account['imei']
                pkey = account['pkey']
                i_os_type = account.get('os_type') or os_type
                i_channel = account.get('channel') or channel
                i_os_version = account.get('os_version') or os_version

                if heybox_id and imei and pkey:
                    vcfg['accounts'].append({'heybox_id': heybox_id, 'imei': imei,
                                             'pkey': pkey, 'os_type': i_os_type,
                                             'channel': i_channel, 'os_version': i_os_version})
                else:
                    raise ValueError
            except (ValueError, AttributeError):
                logger.warning(f'[*] 第{i}项账号配置有误,已忽略该项')
                logger.debug(f'[*] 配置项为{account}')

    if not vcfg['accounts'] and os.getenv('CI'):
        heybox_id = int(os.getenv('HEYBOX_ID'))
        imei = os.getenv('IMEI')
        pkey = os.getenv('PKEY')
        i_os_type = os.getenv('OS_TYPE') or os_type
        i_channel = os.getenv('CHANNEL') or channel
        i_os_version = os.getenv('OS_VERSION') or os_version

        if heybox_id and imei and pkey:
            vcfg['accounts'].append({'heybox_id': heybox_id, 'imei': imei,
                                     'pkey': pkey, 'os_type': i_os_type,
                                     'channel': i_channel, 'os_version': i_os_version})

    if not vcfg['accounts']:
        logger.error('[*] 不存在有效的账号信息,请检查config.toml')

    return (vcfg)
