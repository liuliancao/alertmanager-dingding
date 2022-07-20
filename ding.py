#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Date: Fri Jul 15 17:08:07 2022
# Author: liuliancao <liuliancao@gmail.com>
"""
Description: dingding talk.

open api overview
https://open.dingtalk.com/document/isvapp-server/api-overview

api explorer
https://open-dev.dingtalk.com/apiExplorer

ding msg format
https://open.dingtalk.com/document/group/message-types-and-data-format
"""
import re
import sys
import json
import requests
from urllib.parse import quote
import logging
from logging.handlers import TimedRotatingFileHandler

from flask import Flask
from flask import request

from alibabacloud_dingtalk.oauth2_1_0.client import Client as dingtalkoauth2_1_0Client
from alibabacloud_dingtalk.robot_1_0.client import Client as dingtalkrobot_1_0Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dingtalk.oauth2_1_0 import models as dingtalkoauth_2__1__0_models
from alibabacloud_tea_util.client import Client as UtilClient
from alibabacloud_dingtalk.robot_1_0 import models as dingtalkrobot__1__0_models
from alibabacloud_tea_util import models as util_models

app = Flask(__name__)
logger = logging.getLogger('ding')
logger.setLevel(logging.DEBUG)
fileHandler = TimedRotatingFileHandler("ding.log", when='D', encoding="utf-8")
fileHandler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)


class Ding:
    """Used for dingding message."""

    def __init__(self, config="./ding.json"):
        """Init Ding with ding.json."""
        try:
            with open(config) as f:
                config_json = json.loads(f.read())
                app_key = config_json['appKey']
                app_secret = config_json['appSecret']
                robot_app_key = config_json['robotAppKey']
                robot_app_secret = config_json['robotAppSecret']
                self.robot_code = robot_app_key
                self.single_groups = config_json['single_groups']
                self.webhooks = config_json['webhooks']
                self.alertmanager_url = config_json['alertmanagerURL']
                self.grafana_url = config_json['grafanaURL']
                self.grafana_prefix = config_json['grafanaPrefix']
                self.prometheus_url = config_json['prometheusURL']
                self.prometheus_prefix = config_json['prometheusPrefix']
        except Exception as e:
            print("{file} not exists or json  not illegal! error: {error}".
                  format(file=config, error=str(e)))
            logger.error(
                "{file} not exists or json  not illegal! error: {error}".
                format(file=config, error=str(e)))
            sys.exit(300)
        finally:
            pass

        # get access token
        self.auth_client = self.create_oauth_client()
        get_access_token_request = \
            dingtalkoauth_2__1__0_models.GetAccessTokenRequest(
                app_key=app_key, app_secret=app_secret)
        get_robot_access_token_request = \
            dingtalkoauth_2__1__0_models.GetAccessTokenRequest(
                app_key=robot_app_key, app_secret=robot_app_secret)

        try:
            access_token_ret = self.auth_client.get_access_token(
                get_access_token_request)
            robot_access_token_ret = self.auth_client.get_access_token(
                get_robot_access_token_request)

            self.access_token = access_token_ret.body.access_token
            self.robot_access_token = robot_access_token_ret.body.access_token
        except Exception as err:
            if not UtilClient.empty(err.code) and not UtilClient.empty(
                    err.message):
                # err 中含有 code 和 message 属性，可帮助开发定位问题
                print(err.code, err.message)
                logger.debug('get access token error ', err.code, err.message)
            sys.exit(400)
        finally:
            pass

    @staticmethod
    def create_oauth_client() -> dingtalkoauth2_1_0Client:
        """
        使用 Token 初始化账号Client
        @return: Client
        @throws Exception
        """
        config = open_api_models.Config()
        config.protocol = 'https'
        config.region_id = 'central'
        return dingtalkoauth2_1_0Client(config)

    @staticmethod
    def create_batch_client() -> dingtalkrobot_1_0Client:
        """
        使用 Token 初始化账号Client
        @return: Client
        @throws Exception
        """
        config = open_api_models.Config()
        config.protocol = 'https'
        config.region_id = 'central'
        return dingtalkrobot_1_0Client(config)

    @staticmethod
    def create_batch_group_client() -> dingtalkrobot_1_0Client:
        """
        使用 Token 初始化账号Client
        @return: Client
        @throws Exception
        """
        config = open_api_models.Config()
        config.protocol = 'https'
        config.region_id = 'central'
        return dingtalkrobot_1_0Client(config)

    def get_user_id_by_phone(self, mobile):
        """
        Get user id by phone.

        # /?devType=org&api=dingtalk.oapi.v2.user.getbymobile.
        Doc from https://open-dev.dingtalk.com/apiExplorer
        """
        try:
            url = "https://oapi.dingtalk.com/topapi/v2/user/getbymobile?access_token=" + \
                self.access_token
            params = {"mobile": mobile}
            req = requests.post(url, data=json.dumps(params))
            resp = req.json()

            if resp['errcode']:
                logger.error("call ding getbymobile failed ", resp['errmsg'])
                return 0
            else:
                userid = resp['result']['userid']
                message = "get {mobile}, userid: {userid}".format(
                    mobile=mobile, userid=userid)
                logger.info(message)
                return userid

        except Exception as e:
            logger.error("get user id by phone ", mobile, "failed ", str(e))
            print(str(e))
            return 0
        finally:
            pass

    def send_single_message(self, sender_id='', content='', robot_code=''):
        """Send single message by sender id."""
        if not self.access_token:
            logger.debug(
                "please check your robot app key and robot app secret.")
            sys.exit(500)

        if not robot_code:
            robot_code = self.robot_code
        batch_send_otoheaders = dingtalkrobot__1__0_models.BatchSendOTOHeaders(
        )
        batch_send_otoheaders.x_acs_dingtalk_access_token = \
            self.robot_access_token
        msg_content = content
        batch_send_otorequest = dingtalkrobot__1__0_models.BatchSendOTORequest(
            robot_code=robot_code,
            user_ids=[sender_id],
            msg_key='sampleActionCard6',
            msg_param=json.dumps(msg_content))
        try:
            self.batch_client = self.create_batch_client()
            self.batch_client.batch_send_otowith_options(
                batch_send_otorequest, batch_send_otoheaders,
                util_models.RuntimeOptions())
        except Exception as err:
            if not UtilClient.empty(err.code) and not UtilClient.empty(
                    err.message):
                # err 中含有 code 和 message 属性，可帮助开发定位问题
                pass
            logger.debug('batch send message caught error ', err.code,
                         err.message)
        finally:
            pass

    def send_group_message(self, conversation_id='', content=''):
        if not self.access_token:
            logger.debug(
                "access token is null, please check your app key and app secret."
            )
            sys.exit(500)

        self.batch_group_client = self.create_batch_group_client()
        org_group_send_headers = dingtalkrobot__1__0_models.OrgGroupSendHeaders(
        )
        org_group_send_headers.x_acs_dingtalk_access_token = self.robot_access_token
        msg_content = {"content": content}
        org_group_send_request = dingtalkrobot__1__0_models.OrgGroupSendRequest(
            # msg_param='{"content":"今天吃肘子"}',
            msg_param=json.dumps(msg_content),
            msg_key='sampleText',
            open_conversation_id=conversation_id,
            robot_code=self.robot_code)
        try:
            self.batch_group_client.org_group_send_with_options(
                org_group_send_request, org_group_send_headers,
                util_models.RuntimeOptions())
        except Exception as err:
            if not UtilClient.empty(err.code) and not UtilClient.empty(
                    err.message):
                # err 中含有 code 和 message 属性，可帮助开发定位问题
                pass
            logger.debug('create group message failed, ', err.code,
                         err.message)
        finally:
            pass

    def send_webhook_message(self, webhook, content):
        """Send webhook message."""
        headers = {'Content-Type': 'application/json'}
        req = requests.post(url=webhook,
                            data=json.dumps(content),
                            headers=headers)
        print(req.text)
        logger.info("dingding webhook ", req.text)

    def send_singles(self, single_group, content):
        """Send to single person with group name."""
        singles = self.single_groups.get(single_group, [])
        for single in singles:
            user_id = self.get_user_id_by_phone(mobile=single['mobile'])
            self.send_single_message(sender_id=user_id, content=content)

    def send_group(self, content, name='消息测试群'):
        """Send to dingding group with robot."""
        webhook = self.webhooks.get(name)
        self.send_webhook_message(webhook, content)

    def ding_alert(self, params):
        """Deal with ding ding alert."""
        logger.info("got alert params ", params)
        # send single
        status = params.get('status', 'firing')
        alertname = params['labels'].get('alertname', 'null')
        cats = []
        for key, value in params['labels'].items():
            if not key.startswith('__'):
                cats.append("{key}=\"{value}\"".format(key=key, value=value))
        cats_str = ','.join(cats)

        silenceLink = self.alertmanager_url + '/#silences/new?filter=' + \
            quote('{'+cats_str + '}')
        print('silenceLink ', silenceLink)
        value = ''
        summary = ''
        details = ''
        if params.get('annotations', None):
            summary = params['annotations'].get('summary', 'null')
            details = params['annotations'].get('__value_string__', '')
            values = re.findall(r'value=(\d+\.\d+|\d+)', details)
            if values:
                value = values[0]

        startsAt = params.get('startsAt', '')

        instance = params.get('instance', 'null')
        graphLink = ''

        if 'generatorURL' in params:
            if re.search(self.grafana_prefix, params['generatorURL']):
                # possibly grafana
                graphLink = params['generatorURL'].replace(
                    self.grafana_prefix, self.grafana_url)
            elif re.search(self.prometheus_prefix, params['generatorURL']):
                # possibly prometheus
                graphLink = params['generatorURL'].replace(
                    self.prometheus_prefix, self.prometheus_url)
            else:
                graphLink = params['generatorURL']
        if status == 'firing':
            content = {
                "title":
                "[FIRING] {alertname} \n\n alerts firing".format(
                    alertname=alertname),
                "text":
                "[FIRING][**{alertname}**]({graphLink}) (实例：{instance}) \n\n **alerts firing** \n\n  \n\n 当前值为{value} \n\n **描述信息:** {summary} \n\n **告警时间:** {startsAt} \n\n **告警详情:** {details}"
                .format(alertname=alertname,
                        graphLink=graphLink,
                        instance=instance,
                        value=value,
                        summary=summary,
                        startsAt=startsAt,
                        details=details),
                "btnOrientation":
                "1",
                "buttonTitle1":
                "抑制2h",
                "buttonUrl1":
                "{silenceLink}".format(silenceLink=silenceLink),
                "buttonTitle2":
                "关联图表",
                "buttonUrl2":
                "{graphLink}".format(graphLink=graphLink)
            }
            group_content = {
                "msgtype": "actionCard",
                "actionCard": {
                    "title":
                    "[FIRING] {alertname} \n\n alerts firing".format(
                        alertname=alertname),
                    "text":
                    "[FIRING][**{alertname}**]({graphLink}) (实例：{instance}) \n\n **alerts firing** \n\n  \n\n 当前值为{value} \n\n **描述信息:** {summary} \n\n **告警时间:** {startsAt} \n\n **告警详情:** {details}"
                    .format(alertname=alertname,
                            graphLink=graphLink,
                            instance=instance,
                            value=value,
                            summary=summary,
                            startsAt=startsAt,
                            details=details),
                    "btnOrientation":
                    "1",
                    "btns": [{
                        "title":
                        "抑制2h",
                        "actionURL":
                        "{silenceLink}".format(silenceLink=silenceLink)
                    }, {
                        "title":
                        "关联图表",
                        "actionURL":
                        "{graphLink}".format(graphLink=graphLink)
                    }]
                }
            }

        else:
            endsAt = params.get('endsAt', '')
            content = {
                "title":
                "[RESOLVED] [{alertname}已恢复]({graphLink}) \n\n alerts resolved"
                .format(alertname=alertname, graphLink=graphLink),
                "text":
                "[RESOLVED] [**{alertname}已恢复**]({graphLink}) \n\n **alerts resolved** \n\n (实例：{instance}) \n\n  **当前值为{value}** \n\n **Description:** {summary} \n\n **告警时间:** {startsAt} \n\n **恢复时间:** {endsAt} \n\n **Details:** {details}"
                .format(graphLink=graphLink,
                        instance=instance,
                        value=value,
                        summary=summary,
                        alertname=alertname,
                        startsAt=startsAt,
                        endsAt=endsAt,
                        details=details),
                "btnOrientation":
                "1",
                "buttonTitle2":
                "关联图表",
                "buttonUrl2":
                "{graphLink}".format(graphLink=graphLink)
            }
            group_content = {
                "msgtype": "actionCard",
                "actionCard": {
                    "title":
                    "[RESOLVED] [{alertname}已恢复]({graphLink}) \n\n alerts resolved"
                    .format(alertname=alertname, graphLink=graphLink),
                    "text":
                    "[RESOLVED] [**{alertname}已恢复**]({graphLink}) \n\n **alerts resolved** \n\n (实例：{instance}) \n\n  **当前值为{value}** \n\n **Description:** {summary} \n\n **告警时间:** {startsAt} \n\n **恢复时间:** {endsAt} \n\n **Details:** {details}"
                    .format(graphLink=graphLink,
                            instance=instance,
                            value=value,
                            summary=summary,
                            alertname=alertname,
                            startsAt=startsAt,
                            endsAt=endsAt,
                            details=details),
                    "btnOrientation":
                    "1",
                    "btns": [{
                        "title":
                        "抑制2h",
                        "actionURL":
                        "{silenceLink}".format(silenceLink=silenceLink)
                    }, {
                        "title":
                        "关联图表",
                        "actionURL":
                        "{graphLink}".format(graphLink=graphLink)
                    }]
                }
            }
        try:
            single_ret = self.send_singles(params['labels'].get(
                'alert_group', 'default'),
                                           content=content)
            logger.info("single ret ", single_ret)
        except Exception as e:
            logger.error("single caught exception ", str(e))
        finally:
            pass

        try:
            group_name = params['labels'].get('alert_ding', '消息测试群')
            group_ret = self.send_group(name=group_name, content=group_content)
            logger.info("group ret ", group_ret)
        except Exception as e:
            logger.error("group caught exception ", str(e))
        finally:
            pass


@app.route('/ding', methods=['POST'])
def recieve_ding_alert():
    """Receive ding alert."""
    alert_params_list = json.loads(request.data)
    # prometheus alerts
    ding = Ding()
    if 'alerts' in alert_params_list:
        rets = []
        for alert_params in alert_params_list['alerts']:
            logger.debug("message sent by alertmanager:" +
                         json.dumps(alert_params, ensure_ascii=False))
            rets.append(ding.ding_alert(alert_params))
    else:
        rets = [ding.ding_alert(alert_params_list)]

    return {'message': 'ok', 'code': '200', 'data': rets}


if __name__ == '__main__':
    ding = Ding()
    app.run(host="0.0.0.0", port=5354, debug=True)
