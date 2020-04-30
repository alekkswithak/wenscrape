from lxml import html
import requests, re
import time
from collections import Counter
from hanziconv import HanziConv as hc
import datetime

def get_chinese(context):
    filter = re.compile(u'[^\u4E00-\u9FA5]') # non-Chinese unicode range
    context = filter.sub(r'', context) # remove all non-Chinese characters
    return context


class Crawler:

    def __init__(self):
        self.characters = Counter()
        self.visited = set()
        self.found = set()
        self.found.add(self.go())

    def go(self):
        return 'https://zh.wikipedia.org/wiki/%E8%81%94%E5%90%88%E5%9B%BD%E6%95%99%E8%82%B2%E3%80%81%E7%A7%91%E5%AD%A6%E5%8F%8A%E6%96%87%E5%8C%96%E7%BB%84%E7%BB%87'


    def process_page(self):
        url = self.found.pop()
        try:
            page = requests.get(url)
            tree = html.fromstring(page.content)
            paragraphs = tree.xpath('//div[@class="mw-parser-output"]/p/text()')
            hrefs = tree.xpath("//div[@class='mw-parser-output']/p/a/@href")

            for p in paragraphs:
                w = get_chinese(p)
                x = hc.toSimplified(w)
                self.characters += Counter(x)

            for href in hrefs:
                zhref = 'https://zh.wikipedia.org' + href
                if zhref not in self.visited:
                    self.found.add(zhref)
        except requests.exceptions.ConnectionError as e:
            print(e)
        except requests.exceptions.ChunkedEncodingError as e:
            print(e)
        except requests.exceptions.InvalidURL as e:
            print(e)
        self.visited.add(url)


    def run(self):
        t = time.perf_counter()
        while len(self.found) > 0:
            self.process_page()
            print(self.characters.most_common(42))
            print('visited: '+str(len(self.visited)))
            print('found: ' + str(len(self.found)))
            print('characters found:'+str(len(self.characters)))

            elapsed_seconds = round(time.perf_counter() - t, 2)
            print(str(datetime.timedelta(seconds=elapsed_seconds)))
        print(self.characters)


if __name__ == '__main__':
    c = Crawler()
    c.run()
