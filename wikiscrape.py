import jieba
from lxml import html
import requests, re
import time
from collections import Counter
from hanziconv import HanziConv as hc
import datetime
import django
import os

from .models import *


def get_chinese(context):
    filter = re.compile(u'[^\u4E00-\u9FA5]') # non-Chinese unicode range
    context = filter.sub(r'', context) # remove all non-Chinese characters
    return context

class Crawler:

    def __init__(self):
        self.characters = Counter()
        self.words = Counter()
        self.visited = set(u.string for u in URL.objects.all() if u.visited)
        self.found = set(u.string for u in URL.objects.all() if not u.visited)
        self.visited_own = set()
        self.found_own = set()
        if not self.found:
            self.found.add(self.seed_url)
            self.found_own.add(self.seed_url)


    @property
    def seed_url(self):
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
                self.words += Counter(jieba.cut(x, cut_all=False))

            for href in hrefs:
                zhref = 'https://zh.wikipedia.org' + href
                if zhref not in self.visited:
                    self.found.add(zhref)
                    self.found_own.add(zhref)
        except requests.exceptions.ConnectionError as e:
            print(e)
            print('Continuing...')
        except requests.exceptions.ChunkedEncodingError as e:
            print(e)
            print('Continuing...')
        except requests.exceptions.InvalidURL as e:
            print(e)
            print('Continuing...')
        self.visited.add(url)
        self.visited_own.add(url)

    def crawl(self):
        t = time.perf_counter()
        visited_count = 0
        print()
        print('Crawling: safe to stop.')
        while visited_count <= 200000:
            self.process_page()
            visited_count += 1
            print('Visited: {}'.format(visited_count))
        print()
        print('Writing: do not stop!')
        print()
        print('Writing characters')
        for shape, count in self.characters.items():
            char, created = Character.objects.get_or_create(shape=shape, defaults={'count':count})
            if not created:
                char.count += count
                char.save()
        print()
        print('Writing words')
        for string, count in self.words.items():
            s, created = Word.objects.get_or_create(string=string, defaults={'count':count})
            if not created:
                s.count += count
                s.save()
        print()
        print('Writing urls')
        for url in self.found_own:
            URL.objects.get_or_create(string=url, defaults={'visited': False})

        for url in self.visited_own:
            u = URL.objects.get(string=url)
            u.visited = True
            u.save()
        print()



def test():
    sample = '组织之宗旨在于通过教育、科学及文化来促进各国之间合作，对和平与安全作出贡献，以增进对正义、法治及联合国宪章所确认之世界人民不分种族、性别、语言或宗教均享人权与基本自由之普遍尊重[2]。联合国教育、科学与文化组织接续国际联盟的国际智力合作委员会。'
    o = get_chinese(sample)

    input_text = '王小明在北京的清华大学读书。'

    print(', '.join(jieba.cut(input_text, cut_all=False)))
    print(', '.join(jieba.cut(o, cut_all=False))) # cut all true returns breakdowns of words in words and the words

    for c in jieba.cut(o, cut_all=False):
        print(c)

def go():
    cs = []
    for i in range(4):

        print('Crawlers ran this go:{}'.format(len(cs)))
        print('Characters found:{}'.format(Character.objects.all().count()))
        print('Words found:{}'.format(Word.objects.all().count()))
        print('URLs Visited:{}'.format(URL.objects.filter(visited=True).count()))
        print('URLs Found:{}'.format(URL.objects.filter(visited=False).count()))
        c = Crawler()
        c.crawl()
        cs.append(c)


if __name__ == '__main__':
    print('main')

