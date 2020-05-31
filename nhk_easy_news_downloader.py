#!/usr/bin/python3
# coding=utf-8
import json
import os
import sys
import subprocess

import requests
from bs4 import BeautifulSoup


def news_download(out_folder: str):
    """
    通过 NHK 的 API 获取新闻列表
    :param out_folder: 储存目录
    """
    r = requests.get('http://www3.nhk.or.jp/news/easy/news-list.json')
    r.encoding = 'utf-8-sig'
    o = json.loads(r.text)
    for k, v in o[0].items():
        for d in v:
            parse_news(d, out_folder)


def parse_news(news: dict, out_folder: str):
    """
    下载新闻
    :param news: api 里新闻的明细信息
    :param out_folder: 储存目录
    """
    news_id = news['news_id']
    news_time = news['news_prearranged_time'].replace(':', '-')
    title = news['title']
    news_uri = str.format('http://www3.nhk.or.jp/news/easy/{0}/{1}.html', str(news_id), str(news_id))
    news_file = os.path.join(out_folder, '_'.join([news_time, news_id, title]),
                             str.format("{0}.html", news_id)).replace(' ', '_')
    has_news_web_image = news['has_news_web_image']
    has_news_easy_image = news['has_news_easy_image']
    has_news_easy_voice = news['has_news_easy_voice']

    # 以文件名送判重
    if not os.path.exists(news_file):
        os.makedirs(os.path.dirname(news_file))
        r = requests.get(news_uri)
        r.encoding = 'utf-8'

        soup = BeautifulSoup(r.text, 'html.parser')
        title = soup.find('h1', attrs={'class': 'article-main__title'})
        article = soup.find('div', attrs={'id': 'js-article-body'})

        for a in article.findAll('a'):
            a.unwrap()

        # 音频
        voice_file = None
        if has_news_easy_voice:
            voice_file = news['news_easy_voice_uri']
            voice_uri = str.format('https://nhks-vh.akamaihd.net/i/news/easy/{0}/master.m3u8', voice_file)
            voice_path = os.path.join(os.path.dirname(news_file), voice_file)
            subprocess.call(['ffmpeg', '-i', voice_uri, '-codec', 'copy', voice_path, '-loglevel', 'warning'])

        # 图片
        img_uri = None
        if has_news_easy_image:
            img_uri = str.format('http://www3.nhk.or.jp/news/easy/{0}/{1}', news_id, news['news_easy_image_uri'])
        elif has_news_web_image:
            img_uri = news['news_web_image_uri']
        if img_uri is not None:
            with open(os.path.join(os.path.dirname(news_file), str.format('{0}.jpg', news_id)), 'wb') as f:
                f.write(requests.get(img_uri).content)

        # 文本
        with open(news_file, "w") as f:
            print("<!DOCTYPE html>", file=f)
            print("<html lang='ja'>", file=f)
            print("<head><meta charset='utf-8'></head>", file=f)
            print("<style>p { font-size: 100%; line-height: 3.2; padding-bottom: 20px; }</style>", file=f)
            print("<body>", file=f)
            print(title, file=f)
            if img_uri is not None:
                print("<img src='" + news_id + ".jpg'><br>", file=f)
            if voice_file is not None:
                print("<audio controls><source src='" + voice_file + "' type='audio/mpeg'></audio>", file=f)
            print(article, file=f)
            print("</body>", file=f)
            print("</html>", file=f)


if __name__ == "__main__":
    news_download(sys.argv[1])
