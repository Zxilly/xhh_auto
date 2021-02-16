#!/usr/bin/python3

'''
# @Author       : Chr_
# @Date         : 2020-07-14 16:36:33
# @LastEditors  : Chr_
# @LastEditTime : 2020-09-05 00:14:20
# @Description  : 启动入口
'''

import os
import sys
import time
import traceback

print(r'''
██╗  ██╗██╗  ██╗██╗  ██╗     █████╗ ██╗   ██╗████████╗ ██████╗ 
╚██╗██╔╝██║  ██║██║  ██║    ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗
 ╚███╔╝ ███████║███████║    ███████║██║   ██║   ██║   ██║   ██║
 ██╔██╗ ██╔══██║██╔══██║    ██╔══██║██║   ██║   ██║   ██║   ██║
██╔╝ ██╗██║  ██║██║  ██║    ██║  ██║╚██████╔╝   ██║   ╚██████╔╝
╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝    ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝ 
                                                       By Chr_
''')


try:
    from utils import cliwait
    from utils.config import load_config
    from utils.version import check_script_update, check_pyxiaoheihe_version
    from utils.version import SCRIPT_VERSION, MINI_CORE_VERSION
    from utils.log import get_logger
    from utils.ftqq import send_to_ftqq
    from utils.email import send_to_email

    from pyxiaoheihe import HeyBoxClient
    from pyxiaoheihe.static import PYXIAOHEIHE_VERSION, RelationType, ReportType
    from pyxiaoheihe.error import UnknownError, HeyboxException, TokenError, AccountLimited
    from pyxiaoheihe.utils import user_relation_filter
except ImportError as e:
    print(e)
    print('导入模块出错,请执行 pip install -r requirements.txt 安装所需的依赖库')
    print('或者尝试升级核心 pip install pyxiaoheihe --upgrade')
    cliwait()
    exit()


logger = get_logger('Run')


def main():
    '''
    示例程序,可以根据需要自行修改
    '''

    # 动态点赞数量
    EVENT = 20

    start_time = time.time()
    total = 0
    success = 0
    accounts = CFG['accounts']
    hbxcfg = CFG['heybox']
    mcfg = CFG['main']

    if not accounts:
        raise ValueError('未定义有效账号信息')

    ac = len(accounts)
    logger.info(f'成功读取[{ac}]个账号')
    data = []
    for i, account in enumerate(accounts, 1):
        try:
            limited = False
            logger.info(str(f'==[{i}/{ac}]').ljust(40, '='))
            data.append(f'#### {str(f"==[{i}/{ac}]").ljust(30, "=")}')
            hbc = HeyBoxClient(account, hbxcfg, mcfg['debug'])

            # 读取每日任务详情
            qd, fxxw, fxpl, dz = hbc.get_daily_task()
            # qd, fxxw, fxpl, dz = False, False, False, False

            logger.info(f'任务[签到{qd}|分享{fxxw}{fxpl}|点赞{dz}]')
            if not qd:
                hbc.logger.info('签到……')
                hbc.sign()

            try:
                if not dz or not fxxw or not fxpl:
                    hbc.logger.info('获取首页新闻列表……')
                    idlist = hbc.get_news_id(6, -1)
                    hbc.logger.info(f'获取[{len(idlist)}]条内容')
                    if not fxxw or not fxpl:
                        hbc.logger.info('分享新闻……')
                        linkid = idlist[0]
                        hbc.get_news_content(linkid, 1)
                        hbc.get_comments(linkid, 1, i, False)
                        hbc.share_news(linkid, 1)
                        hbc.random_sleep(0, 1)
                        hbc.share_comment()
                        hbc.random_sleep(0, 1)
                    if not dz:
                        for i, linkid in enumerate(idlist, 1):
                            # 伪装正常流量
                            hbc.logger.info(f'模拟浏览新闻{linkid}')
                            hbc.get_news_content(linkid)
                            hbc.get_comments(linkid, 1, i, False)
                            hbc.like_news(linkid, i, True)
                            hbc.random_sleep(1, 5)
                else:
                    hbc.logger.info('已完成点赞和分享任务,跳过')

                # xhh_auto 互助计划,如果想要退出可以在配置文件中关闭
                if mcfg['join_xhhauto']:
                    hbc.logger.info('感谢加入Xhh_Auto互助计划')
                    rs = hbc.get_user_relation(20400942)
                    if rs == RelationType.NoRelation:
                        hbc.follow_user(20400942)
                    ulist = hbc.get_user_fans(20400942)
                    target = user_relation_filter(
                        ulist, RelationType.NoRelation)
                    if target:
                        for i in target[:2]:
                            hbc.follow_user(i, True)
                            hbc.random_sleep(0, 2)

                ulist = hbc.get_new_fans()
                if ulist:
                    for i in ulist:
                        hbc.follow_user(i, True)
                        hbc.random_sleep(0, 5)
                    hbc.logger.info(f'关注了[{len(ulist)}]个新粉丝')
                else:
                    hbc.logger.info('没有新粉丝')
                    if not mcfg['join_xhhauto']:
                        hbc.logger.info('[!] 试试加入xhh_auto互助计划?')

                eventlist = hbc.get_subscrib_events(EVENT, True)
                hbc.logger.info(f'获取[{len(eventlist)}]条动态')
                if eventlist:
                    for linkid, ftype, _ in eventlist:
                        hbc.logger.info(f'点赞动态 {linkid}')
                        hbc.like_event(linkid, ftype, True)
                        hbc.random_sleep(0, 1)
                else:
                    hbc.logger.info('没有新动态')

            except AccountLimited:
                hbc.logger.info('当前账号点赞或关注已受限, 终止任务')
                limited = True

            logger.info('-' * 40)

            logger.info('生成统计数据')
            uname, uid, coin, level, sign = hbc.get_my_data()

            logger.info(f'昵称[{uname}] @{uid} {"[受限]" if limited else ""}')
            logger.info(
                f'等级[{level[0]}级]==>{int((level[1]*100)/level[2])}%==>[{level[0]+1}级]')
            logger.info(f'盒币[{coin}]签到[{sign}]天')
            logger.info(
                f'等级[{level[0]}级]==>{int((level[1]*100)/level[2])}%==>[{level[0]+1}级]')

            follow, fan, awd = hbc.get_user_profile()
            logger.info(f'关注[{follow}]粉丝[{fan}]获赞[{awd}]')

            qd, fxxw, fxpl, dz = hbc.get_daily_task()
            finish = qd and fxxw and fxpl and dz

            logger.info(f'签到[{qd}]分享[{fxxw}{fxpl}]点赞[{dz}]')

            data.append(f'#### {uname} @{uid} {"[受限]" if limited else ""}\n'
                        f'#### 盒币[{coin}]签到[{sign}]天\n'
                        f'#### 等级[{level[0]}级]==>{int((level[1]*100)/level[2])}%==>[{level[0]+1}级]\n'
                        f'#### 关注[{follow}]粉丝[{fan}]获赞[{awd}]\n'
                        f'#### 签到[{qd}]分享[{fxxw}{fxpl}]点赞[{dz}]\n'
                        f'#### 状态[{"全部完成" if finish else "**有任务未完成**"}]')

            hbc.data_report(ReportType.Quit, None)  # 模拟客户端关闭消息

            success += 1
        except TokenError as e:
            logger.error(f'第[{i}]个账号信息有问题,请检查:[{e}]')
            data.append(f'#### 账号信息有问题,请检查:[{e}]')
        except UnknownError as e:
            logger.error(f'第[{i}]个账号遇到了未知错误:[{e}]')
            data.append(f'#### 遇到了未知错误:[{e}]')
        except HeyboxException as e:
            logger.error(f'第[{i}]个账号遇到了未知错误:[{e}]')
            data.append(f'#### 遇到了未知错误:[{e}]')
        finally:
            total += 1

    logger.info('=' * 40)
    if success < total:
        logger.warning(f'[{total-success}]个任务执行出错')
        data.append(f'#### {"=" * 30 }\n'
                    f'#### **[{total-success}]个任务执行出错**')
    logger.info(f'脚本版本:[{SCRIPT_VERSION}],核心版本:[{PYXIAOHEIHE_VERSION}]')
    data.append(f'#### {"=" * 30 }\n'
                f'#### 脚本版本:[{SCRIPT_VERSION}],核心版本:[{PYXIAOHEIHE_VERSION}]')

    end_time = time.time()
    logger.info(f'脚本耗时:[{round(end_time-start_time,4)}]s')
    data.append(f'#### 任务耗时:[{round(end_time-start_time,4)}]s')

    message = '\n'.join(data)

    title = '小黑盒自动脚本'
    if mcfg['check_update']:
        logger.info('检查脚本更新……')
        result = check_script_update()
        if result:
            latest_version, detail, download_url = result
            logger.info(f'-->脚本有更新<--'
                        f'最新版本[{latest_version}]'
                        f'更新内容[{detail}]'
                        f'下载地址[{download_url}]')
            data.append('')
            data.append = (f'### 脚本有更新\n'
                           f'#### 最新版本[{latest_version}]\n'
                           f'#### 下载地址:[GitHub]({download_url})\n'
                           f'#### 更新内容\n'
                           f'{detail}\n'
                           f'> 如果碰到问题欢迎加群**916945024**')
            title += '【有更新】'
        else:
            logger.info(f'脚本已是最新,当前版本{SCRIPT_VERSION}')
    else:
        logger.info('检查脚本更新已禁用,当前版本{SCRIPT_VERSION}')

    logger.info('推送统计信息……')
    message_push(title, message, success != total)
    logger.info('脚本执行完毕')


def message_push(title: str, message: str, error: bool = False):
    '''
    推送通知
    '''
    ftqq = CFG['ftqq']
    email = CFG['email']
    if ftqq['enable']:
        if (ftqq['only_on_error'] == True and error) or (ftqq['only_on_error'] == False):
            result = send_to_ftqq(title, message, ftqq)
            if result:
                logger.info('FTQQ推送成功')
            else:
                logger.warning('[*] FTQQ推送失败')
    if email['enable']:
        if (email['only_on_error'] == True and error) or (email['only_on_error'] == False):
            result = send_to_email(title, message, email)
            if result:
                logger.info('邮件推送成功')
            else:
                logger.warning('[*] 邮件推送失败')


if __name__ == '__main__':
    try:
        logger.info('载入配置文件')
        CFG = load_config()
    except FileNotFoundError:
        logger.error('[*] 配置文件[config.toml]不存在,请参考[README.md]生成配置')
        cliwait()
    except ValueError:
        logger.error('[*] 尚未配置有效的账户凭据,请添加到[config.toml]中')
        cliwait()
    except Exception as e:
        logger.error(f'[*] 载入配置文件出错,请检查[config.toml] [{e}]')
        cliwait()
        exit()

    try:
        if check_pyxiaoheihe_version():
            main()
        else:
            logger.error(
                f'[*] Pyxiaoheihe版本太低,无法继续运行 [当前{PYXIAOHEIHE_VERSION} < 要求{MINI_CORE_VERSION}]')
            logger.error('[*] 可以使用 pip3 install pyxiaoheihe --upgrade 命令升级')
            cliwait()
    except KeyboardInterrupt:
        logger.info('[*] 手动终止运行')
        cliwait()
    except Exception as e:
        logger.error(f'遇到未知错误 [{e}]', exc_info=True)
        title = '脚本执行遇到未知错误'
        message = (f'#### 脚本版本:[{SCRIPT_VERSION}],核心版本:[{PYXIAOHEIHE_VERSION}]\n'
                   f'#### 系统信息:[{os.name}]\n'
                   f'#### Python版本: [{sys.version}]\n'
                   f'#### {"=" * 30}\n'
                   f'#### 错误信息: {traceback.format_exc()}\n'
                   f'#### {"=" * 30}\n'
                   '#### 联系信息:\n'
                   '* QQ群: 916945024\n'
                   '* TG群: https://t.me/xhh_auto\n'
                   '* 邮箱: chr@chrxw.com\n'
                   '> 如果需要帮助请附带上错误信息')
        message_push(title, message, True)
        cliwait()
