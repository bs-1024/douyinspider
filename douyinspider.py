# -*- coding: utf-8 -*-
import requests
import os
from lxml import etree
from queue import Queue
import threading


class DouyinSpider(object):
    def __init__(self):
        self.temp_url = "http://douyin.bm8.com.cn/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1"
        }
        self.url_queue = Queue()
        self.html_queue = Queue()
        self.content_list_queue = Queue()

    @staticmethod
    def file_path():
        base_dir = os.path.dirname(os.path.abspath(__file__))
        _path = os.path.join(base_dir, "music")
        if not os.path.exists(_path):
            os.mkdir(_path)
        return _path

    def get_url_list(self):
        self.url_queue.put(self.temp_url)
        # for i in range(1, 14):
        #     self.url_queue.put(self.temp_url.format(i))

    def parse_url(self):
        while True:
            url = self.url_queue.get()
            resp = requests.get(url, headers=self.headers)
            if resp.status_code != 200:
                self.url_queue.put(url)
            else:
                self.html_queue.put(resp.content.decode())
            self.url_queue.task_done()

    def get_content_list(self):
        while True:
            html_str = self.html_queue.get()
            html = etree.HTML(html_str)
            li_list = html.xpath("//div[@class='pull-left']/ul/li")
            music_list = []
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
            self.content_list_queue.put(music_list)
            self.html_queue.task_done()

    def download_music(self):
        while True:
            music_list = self.content_list_queue.get()
            for item in music_list:
                _full_name = os.path.join(self.file_path(), item['title'])
                with open(_full_name + '.mp4', "wb") as f:
                    f.write(item['content'])
                    print("ok")
            self.content_list_queue.task_done()

    def run(self):
        thread_list = []
        # 1.url列表
        t_url = threading.Thread(target=self.get_url_list)
        thread_list.append(t_url)
        # 2.发送请求，获取响应
        for i in range(10):
            t_parse = threading.Thread(target=self.parse_url)
            thread_list.append(t_parse)

        # 3.处理数据
        t_content = threading.Thread(target=self.get_content_list)
        thread_list.append(t_content)
        # 4.保存数据
        t_download = threading.Thread(target=self.download_music)
        thread_list.append(t_download)

        for t in thread_list:
            t.setDaemon(True)
            t.start()

        for q in [self.url_queue, self.html_queue, self.content_list_queue]:
            q.join()


if __name__ == '__main__':
    douyin = DouyinSpider()
    douyin.run()



















