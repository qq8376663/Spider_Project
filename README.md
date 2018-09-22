# Spider_Project
使用代理ip池爬取微信公众号文章

代理池转自https://github.com/Python3WebSpider/ProxyPool

## 如何运行
### 1.获取代理ip
根据需求配置ProxyPool-master\proxypool下的setting文件（url，redis，web接口）

运行ProxyPool-master目录下的run.py文件，即可获取可用的ip
### 2.爬取数据
修改Spider_Project目录下的setting文件（mysql数据库配置）

根据需要修改spider.py中的keyword变量（代表搜索的公众号文章关键字），更换Cookie

配置完后运行spider.py
