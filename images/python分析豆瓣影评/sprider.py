import requests
from lxml import etree
import sys
import log
from pyecharts.charts import Bar, WordCloud
from pyecharts import options as opts
import jieba
from collections import Counter
from pyecharts.globals import SymbolType
import re
import random
import time

global logger
logger = log.Logger(sys.path[0]+"\\all.log", level='info')


class sprider():
    def __init__(self):
        # 设置请求头
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko'}
        self.short_comments_file = sys.path[0]+"\\Short_comments_file.txt"
        self.score_file = sys.path[0]+"\\score_file.txt"

    def login(self,session):
        login_url = 'https://accounts.douban.com/j/mobile/login/basic'
        postData = {'ck': '',
                    'name': 'yourname',
                    'password': 'passwd',
                    'remember': 'false',
                    'ticket': ''}
        # 从网上看到，需要先get请求一次才能成功，不然能登录能200，但是不能进行后续的get请求抛403，具体原因不详
        a = session.get(login_url,headers=self.headers)
        b = session.post(login_url, data=postData, headers=self.headers)
        if b.status_code == 200:
            logger.logger.info("登录成功")
        else:
            logger.logger.error("登录失败:"+str(b.status_code)+str(b.text))
            sys.exit(48)

    def get_request(self,url,session):
        # get请求获取短评详情
        request = session.get(url,headers=self.headers)
        if request.status_code == 200:
            # 防止乱码，将编码格式设置为utf-8
            request.encode = 'utf-8'
            return request.text
        else:
            logger.logger.error('current status_code:'+str(request.status_code)+str(request.text))
            sys.exit(44)

    def xpath_analysis(self, text, xpath):
        html = etree.HTML(text)
        # 使用xpath进行短评解析
        result = html.xpath(xpath)
        return result

    def to_file(self, filename, data):
        # 采用追加的方式将内容写入文件
        with open(filename, 'a', encoding='utf-8') as f:
            # xpath获取的data为列表，所以用遍历的方式写入
            logger.logger.info(data)
            for i in data:
                f.write(i+'\n')

    def init_file(self, filename):
        # 初始化文件，直接清空
        with open(filename, 'w') as f:
            f.write('')


class visualization():
    def __init__(self):
        # 初始化文件路径
        self.short_comments_file = sys.path[0]+"\\short_comments_file.txt"
        self.score_file = sys.path[0]+"\\score_file.txt"
        self.path = sys.path[0]

    def analysis_score(self):
        evaluate = {}
        with open(self.score_file, 'r', encoding='utf-8') as f:
            for i in f.readlines():
                i = re.sub(r"[A-Za-z0-9\-\:]", "", i)
                i = i.strip()  # 去掉每行的换行符
                # 如果这个没出现过，就初始化为1
                if i not in evaluate:
                    evaluate[i] = 1
                    logger.logger.debug(evaluate)
                else:
                    # 如果已经出现过了，就在自加1
                    evaluate[i] += 1
                    logger.logger.debug(evaluate)
            logger.logger.info(evaluate)
        bar = Bar()
        eva = []
        count = []
        for k, v in evaluate.items():
            if k != '':
                eva.append(k)
                count.append(v)
        bar.add_xaxis(eva)  # 柱状图x轴
        logger.logger.info('xaxis'+str(eva))
        bar.add_yaxis("评价", count)  # 柱状图y轴
        logger.logger.info('yaxis'+str(count))
        bar.set_global_opts(title_opts=opts.TitleOpts(title="隐秘的角落 豆瓣评分"))
        # 生成可视化图表
        bar.render(self.path+"\\score.html")

    def analysis_short_comment(self):
        cut_words = ""
        for line in open(self.short_comments_file, 'r', encoding='utf-8'):
            line.strip('\n')
            # 正则去掉标点等无效的字符
            line = re.sub(r"[A-Za-z0-9\：\·\—\，\。\“ \”\....]", "", line)
            # cut_all=False为精确模式，cut_all=True为全词模式
            seg_list = jieba.cut(line, cut_all=False)
            cut_words += (" ".join(seg_list))
        all_words = cut_words.split()
        c = Counter()
        for x in all_words:
            if len(x) > 1 and x != '\r\n':
                c[x] += 1
        words = c.most_common(500)  # 输出词频最高的前500词
        logger.logger.debug(words)
        wordcloud = WordCloud()
        wordcloud.add("", words, word_size_range=[5, 100], shape='circle')
        wordcloud.set_global_opts(title_opts=opts.TitleOpts(title="隐秘的角落 短评"))
        wordcloud.render(self.path+"\\short_comment.html")


def run_sprider(sprider):
    # 初始化文件
    sprider.init_file(sprider.short_comments_file)
    sprider.init_file(sprider.score_file)
    # 遍历获取数据
    s = requests.session()
    sprider.login(s)
    for page_start in range(0, 500, 20):  # 范围从0-500，步长为20,页面上总评论数为160000+
        try:
            delay = round(random.uniform(0.1, 4), 1)
            logger.logger.info('i will sleep:'+str(delay)+'s')
            time.sleep(delay)
            URL = 'https://movie.douban.com/subject/33404425/comments?start={}&limit=20&sort=new_score&status=P'.format(
                page_start)
            logger.logger.info('current_request_url:'+URL)
            x = sprider.get_request(URL,s)
            # 短评的xpath路径
            xpath = '//*[@id="comments"]/div[*]/div[2]/p/span/text()'
            short_comment = sprider.xpath_analysis(x, xpath)
            sprider.to_file(sprider.short_comments_file, short_comment)
            # 评分的xpath路径
            xpath2 = '//*[@id="comments"]/div[*]/div[2]/h3/span[2]/span[2]/@title'
            score = sprider.xpath_analysis(x, xpath2)
            sprider.to_file(sprider.score_file, score)
        except Exception as e:
            logger.logger.error(e)
            logger.logger.info('current_page:'+page_start)
            sys.exit(146)


if __name__ == "__main__":
    sprider = sprider()
    run_sprider(sprider)

    c = visualization()
    c.analysis_score()
    c.analysis_short_comment()
