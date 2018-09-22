import requests
from urllib.parse import urlencode
from requests.exceptions import ConnectionError
from pyquery import PyQuery as pq
from mysql import MySQL
import re
import time
import random
from requests import Session

from common import get_md5

proxy = None


class Spider(object):
    def __init__(self):
        self.keyword = 'python'
        # self.cookie_url = 'http://weixin.sogou.com/weixin?type=2&ie=utf8&s_from=input&_sug_=y&_sug_type_=&query={0}'.format(self.keyword)
        # self.test_url = 'http://weixin.sogou.com/weixin?type=2&ie=utf8&query={}&tsn=1&ft=&et=&interation=&wxid=&usip='.format(self.keyword)
        self.headers = {
            'Cookie': 'ABTEST=8|1537491697|v1; IPLOC=CN3301; SUID=8A00CD733E18960A000000005BA442F1; JSESSIONID=aaaELbWTQ1L2wb49VYFvw; SUID=8A00CD733118960A000000005BA44328; weixinIndexVisited=1; SUV=00CA1DF373CD008A5BA44329E5072984; sct=1; ppinf=5|1537491766|1538701366|dHJ1c3Q6MToxfGNsaWVudGlkOjQ6MjAxN3x1bmlxbmFtZToyOllHfGNydDoxMDoxNTM3NDkxNzY2fHJlZm5pY2s6MjpZR3x1c2VyaWQ6NDQ6bzl0Mmx1UG1pVEc5UzdYai1uNS00dmZESjlaSUB3ZWl4aW4uc29odS5jb218; pprdig=SZP50z_ocFRwyaEzaFydV-HYv-7zERPayFcU4AKiczu0biMhxplP0vHK_c9YDQaC7wSpf6k1pi_KgkugvqfiXFx57nAVREJnCoD2sI6PPqu_RkhU8p_t8K_u0nBORzPL4t56QANrWGeOqqABFIR8--kajPxzjyOrns2gB7Mx1Gk; sgid=18-37096587-AVukQzbMnFYdwGh1fBNzkwE; PHPSESSID=n0hgnp1cq5hb3hde6ag44fo2d0; SUIR=64ED239EEEE89BB9C39C6C78EE77A936; ppmdig=1537498561000000839ca7e11ec83beadd0ca06d0eb18a07; SNUID=5AD01CA2D0D4A689DE848F35D1313467',
            'Host': 'weixin.sogou.com',
            'Upgrade-Insecure-Requests': '1',
            # 'Referer': self.cookie_url,
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
        }
        self.base_url = 'http://weixin.sogou.com/weixin?'
        self.proxy_pool_url = 'http://127.0.0.1:5555/random'
        self.mysql = MySQL()
        self.max_count = 5
        self.session = requests.Session()

    def get_proxy(self):
        try:
            response = requests.get(self.proxy_pool_url)
            if response.status_code == 200:
                return response.text
            return None
        except ConnectionError:
            return None

    def get_html(self, url, count=1):
        # 通过代理ip池
        print('Crawling', url)
        print('Trying Count', count)
        global proxy
        if count >= self.max_count:
            print('Tried Too Many Counts')
            return None
        try:
            if proxy:
                proxies = {
                    'http': 'http://' + proxy,
                    'https': 'https://' + proxy
                }
                response = self.session.get(url, allow_redirects=False, headers=self.headers, proxies=proxies)
                return response.text
            else:
                response = self.session.get(url, allow_redirects=False,  headers=self.headers)
                if response.status_code == 200:
                    return response.text
                if response.status_code == 302:
                    # Need Proxy
                    print('302')
                    proxy = self.get_proxy()
                    if proxy:
                        print('Using Proxy', proxy)
                        return self.get_html(url)
                    else:
                        print('Get Proxy Failed')
                        return None
        except ConnectionError as e:
            print('Error Occurred', e.args)
            proxy = self.get_proxy()
            count += 1
            return self.get_html(url, count)

    # def get_html(url):
    #     # 使用本机ip
    #     try:
    #         response = requests.get(url, allow_redirects=False, headers=headers)
    #         if response.status_code == 200:
    #             return response.text
    #         if response.status_code == 302:
    #             return None
    #     except ConnectionError:
    #         return get_html(url)

    def get_index(self, keyword, page):
        data = {
            'query': keyword,
            'type': 2,
            'page': page
        }
        queries = urlencode(data)
        url = self.base_url + queries
        html = self.get_html(url)
        return html

    def parse_index(self, html):
        doc = pq(html)
        items = doc('.news-box .news-list li .txt-box h3 a').items()
        for item in items:
            yield item.attr('href')
        time.sleep(random.randint(5, 10))

    def get_detail(self, url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.text
            return None
        except ConnectionError:
            return None

    def parse_detail(self, html):
        doc = pq(html)
        url_object_id = get_md5(html)
        title = doc('.rich_media_title').text()
        content = doc('.rich_media_content').text()

        # date = doc('#publish_time').text()
        nickname = doc('#js_name').text()
        wechat = doc('#js_profile_qrcode > div > p:nth-child(3) > span').text()
        try:
            match_date = re.search('var.*?publish_time\s=\s(.*)"', html)
            date = match_date.group(1)[1:11]
            return {
                'url_object_id': url_object_id,
                'title': title,
                'content': content,
                'date': date,
                'nickname': nickname,
                'wechat': wechat
            }
        except AttributeError:
            return {
                'url_object_id': url_object_id,
                'title': title,
                'content': content,
                'nickname': nickname,
                'wechat': wechat
            }

    def main(self):
        for page in range(86, 101):
            self.session.headers.update(self.headers)
            html = self.get_index(self.keyword, page)
            if html:
                article_urls = self.parse_index(html)
                for article_url in article_urls:
                    article_html = self.get_detail(article_url)
                    if article_html:
                        article_data = self.parse_detail(article_html)
                        print(article_data)
                        self.mysql.insert('python_articles', article_data)


if __name__ == '__main__':
    spider = Spider()
    spider.main()