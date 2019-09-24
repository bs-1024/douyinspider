# -*- coding: utf-8 -*-
import os
import time
from multiprocessing.dummy import Pool
import requests
from queue import Queue
from lxml import etree


class DouyinSpider(object):
    def __init__(self):
        self.temp_url = 'http://douyin.bm8.com.cn/'
        self.headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1"
        }
        self.queue = Queue()
        self.pool = Pool(5)
        self.is_running = True
        self.total_requests_num = 0
        self.total_response_num = 0

    @staticmethod
    def file_path():
        base_dir = os.path.dirname(os.path.abspath(__file__))
        _path = os.path.join(base_dir, "music")
        if not os.path.exists(_path):
            os.mkdir(_path)
        return _path

    def get_url_list(self):
        # for i in range(1, 10):
        #     self.queue.put(self.temp_url.format(i))
        self.queue.put(self.temp_url)
        print("get_url_list")
        self.total_requests_num += 1

    def parse_url(self, url):
        print("parse_url")
        return requests.get(url, headers=self.headers).content.decode()

    def get_content_list(self, html_str):
        html = etree.HTML(html_str)
        li_list = html.xpath("//div[@class='pull-left']/ul/li")
        music_list = []
        print("get_content_list")
        for li in li_list:
            item = {}
            item["title"] = li.xpath("./a/span/text()")[0]
            print(item['title'])
            detail_url = li.xpath("./a/@onclick")[0][6:-1].split(",")[-1]
            resp = requests.get(eval(detail_url), headers=self.headers)
            print(resp.status_code)
            html = etree.HTML(resp.content.decode())
            try:
                video_src = html.xpath("//video/@src")[0]
                if video_src is None:
                    continue
                print(video_src)
            except Exception:
                continue
            resp = requests.get(video_src, headers=self.headers)
            item['content'] = resp.content
            music_list.append(item)
        print("ok_list")
        return music_list

    def download_music(self, music_list):
        for item in music_list:
            _full_name = os.path.join(self.file_path(), item['title'])
            with open(_full_name + '.mp4', "wb") as f:
                f.write(item['content'])
                print("ok")

    def exetute_requests_item_save(self):
        # 1.url列表
        url = self.queue.get()
        # 2.发送请求，获取响应
        html_str = self.parse_url(url)
        # 3.处理数据
        # 3.1首页数据，取a链接
        # 3.2跳转页面，发送请求，获取数据
        music_list = self.get_content_list(html_str)
        # 4.保存
        self.download_music(music_list)
        self.total_response_num += 1

    def _callback(self, temp):
        if self.is_running:
            self.pool.apply_async(self.exetute_requests_item_save, callback=self._callback)

    def run(self):
        self.get_url_list()

        for i in range(2):  # 控制并发
            self.pool.apply_async(self.exetute_requests_item_save, callback=self._callback)

        while True:  # 防止主线程结束
            time.sleep(0.0001)  # 避免cpu空转，浪费资源
            if self.total_response_num >= self.total_requests_num:
                self.is_running = False
                break

        self.pool.close()  # 关闭线程池，防止新的线程开启
        # self.pool.join() #等待所有的子线程结束


if __name__ == '__main__':
    douyin = DouyinSpider()
    douyin.run()
