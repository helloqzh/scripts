#!/usr/bin/env python3
# coding=utf-8

import json
import logging
import os
import smtplib
import socket
from email.mime.text import MIMEText

from aliyunsdkalidns.request.v20150109.DescribeDomainRecordsRequest import DescribeDomainRecordsRequest
from aliyunsdkalidns.request.v20150109.UpdateDomainRecordRequest import UpdateDomainRecordRequest
from aliyunsdkcore.client import AcsClient
from dotenv import load_dotenv


def get_ip() -> str:
    """
    获取外网 IP
    :return: 当前的外网 IP
    """
    sock = socket.create_connection(('ns1.dnspod.net', 6666))
    ip = sock.recv(16)
    sock.close()
    return str(ip, encoding="UTF-8")


def refresh_domain_records():
    """
    更新域名 DNS
    """
    try:
        ip = get_ip()
        client = AcsClient(ALI_AK, ALI_SECRET, ALI_REGION_ID)
        req_get_records = DescribeDomainRecordsRequest()
        req_get_records.set_accept_format('json')
        req_get_records.set_DomainName(ALI_DOMAIN)
        response = json.loads(client.do_action_with_exception(req_get_records))
        msg = ""
        for record in response["DomainRecords"]["Record"]:
            recode_ip = record["Value"]
            if recode_ip != ip:
                req_set_record = UpdateDomainRecordRequest()
                req_set_record.set_RecordId(record["RecordId"])
                req_set_record.set_RR(record["RR"])
                req_set_record.set_Type(record["Type"])
                req_set_record.set_TTL(record["TTL"])
                req_set_record.set_Value(ip)
                req_set_record.set_accept_format('json')
                client.do_action_with_exception(req_set_record)
                info = str.format("{0}.{1} {2} --> {3}", record["RR"], ALI_DOMAIN, recode_ip, ip)
                logging.info(info)
                msg += info + "\n"
        if msg != "":
            send_mail(msg)
    except:
        logging.exception("Exception occurred")


def send_mail(content: str) -> bool:
    """
    把当前外网的 IP 通过邮件发出去
    :param content: 邮件内容
    :return: 发送结果
    """
    try:
        msg = MIMEText(content)
        msg['Subject'] = "外网 IP 地址变更通知"
        msg['From'] = SMTP_MAIL_USER
        msg['To'] = ALI_DNS_USER_MAIL
        s = smtplib.SMTP_SSL(SMTP_MAIL_SERVER, SMTP_MAIL_SERVER_PORT)
        s.login(SMTP_MAIL_USER, SMTP_MAIL_PASSWORD)
        s.sendmail(SMTP_MAIL_USER, ALI_DNS_USER_MAIL, msg.as_string())
        s.close()
        return True
    except:
        logging.exception("Exception occurred")
        return False


if __name__ == "__main__":
    # 加载配置文件，详细参照 python-dotenv
    # https://github.com/theskumar/python-dotenv
    load_dotenv(encoding="UTF-8")

    # 邮件发送服务器配置
    SMTP_MAIL_SERVER = os.getenv("SMTP_MAIL_SERVER")
    SMTP_MAIL_SERVER_PORT = os.getenv("SMTP_MAIL_SERVER_PORT")
    SMTP_MAIL_USER = os.getenv("SMTP_MAIL_USER")
    SMTP_MAIL_PASSWORD = os.getenv("SMTP_MAIL_PASSWORD")

    # 阿里云相关 API 配置
    ALI_AK = os.getenv("ALI_AK")
    ALI_SECRET = os.getenv("ALI_SECRET")
    ALI_REGION_ID = os.getenv("ALI_REGION_ID")
    ALI_DOMAIN = os.getenv("ALI_DOMAIN")
    ALI_DNS_USER_MAIL = os.getenv("ALI_DNS_USER_MAIL")

    # 共通配置
    LOG_OUT_DIRECTORY = os.getenv("LOG_OUT_DIRECTORY")

    logging.basicConfig(filename=os.path.join(LOG_OUT_DIRECTORY, "ali_dynamic_dns.log"),
                        filemode="a",
                        format="%(asctime)s %(filename)s(%(lineno)d):%(levelname)s:%(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S",
                        level=logging.INFO)

    refresh_domain_records()
