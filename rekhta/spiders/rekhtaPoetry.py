import json

from scrapy import Request, FormRequest
from scrapy.spiders import CrawlSpider, Spider, Rule
from scrapy.linkextractors import LinkExtractor
from w3lib.url import add_or_replace_parameter
from copy import deepcopy
import re

from rekhta.items import RekhtaItem

count = 1

class RekhtaMixin:
    allowed_domain = ['https://www.rekhta.org/']


class YNewsParserSpider(RekhtaMixin, Spider):
    allowed_domain = RekhtaMixin.allowed_domain

    name = 'rekhta-parse'

    def product_news(self, response):
        product = RekhtaItem()
        product['news'] = {}

        # product['date'] = ""

        return self.extract_requests(self.detail_requests(response), product)

    def product_desc(self, response):
       # 
       data = response.css('div.c span::text').extract()
       return data
       #return [re.sub(r"[^a-zA-Z0-9]+", ' ', k) for k in a.split("\n")]


    #    final_result = []
    #    for d in data: 
    #        final_result = d.split(".")
    #    return data

    def author_title(self, resposne):
        return response.css('.authorAddFavorite a::text').extract_first()

    def product_title(self, response):
        return response.css('.poemPageContentHeader h1::text').extract_first()
    
    def product_detail_title(self, response):
            return response.css('h1.entry-title::text').extract_first()
    
    def product_Date(self, response):
        date = response.css(".entry-content::text").extract_first()
        return re.sub('[^A-Za-z0-9]+', '', date)


    def detail_requests(self, response):
        news_link = response.css('.contentListItems a:nth-child(2)::attr(href)').extract()

        # news_link = response.css('script::text').re_first(r'ContentSlug(.+),"TypeSlug"')
        #news_link = response.css(".contentListItems a:nth-child(1)::attr(href)").extract()

        requests = []

        for color in news_link:
            # url = add_or_replace_parameter(response.url, "color", color)
            # if color !== 'javascript:void(0);'
            requests += [Request(url=color, callback=self.parse_news, dont_filter=True)]

        # For handling those requests which doesn't has color_requests
        return requests
    
    
    def parse_news(self, response):
        product = response.meta['product']
        requests = response.meta['requests']

        product['title'] = response.css(".poemPageContentHeader h1::text").extract_first()
        product['poet'] = response.css("a.ghazalAuthor::text").extract_first()
        product['nazam-roman'] = response.css(".pMC:nth-child(2) span::text").extract()

        # product['news'].update(self.product_sku(response))

        # return self.extract_requests(requests, product)
        urdu_url = response.css('link[rel="alternate"]::attr(href)').extract_first()

        yield Request(url=urdu_url, callback=self.parse_urdu_news, dont_filter=True)


    def parse_urdu_news(self, response):
        product = response.meta['product']
        requests = response.meta['requests']

        product['nazam-urdu'] = response.css(".pMC span::text").extract()
        return self.extract_requests(requests, product)
        # product['nazam-urdu'] = 

    def product_sku(self, response):
        global count
        sku = {}

        sku['news_detail'] = self.product_desc(response)
        sku['title'] = self.product_detail_title(response)
        sku['author'] = self.author_title(resposne)
        sku['date'] = self.product_Date(response)
        sku_id = count
        count = count + 1
        return {sku_id: sku}
    
    @staticmethod
    def extract_requests(requests, product):
        if requests:
            request = requests.pop()
            request.meta['product'] = product
            request.meta['requests'] = requests
            yield request
        else:
            yield product




class RekhtaCralwer(RekhtaMixin, CrawlSpider):
    name = 'rekhta'
    items_per_page = 100
    start_url =  'https://www.rekhta.org/poets'

    spider_parser = YNewsParserSpider()

    allowed_domain = RekhtaMixin.allowed_domain

    


    # rules = (
    #     Rule(LinkExtractor(restrict_css='.pagination.clearfix'), callback=spider_parser.product_news),
    # )

    def start_requests(self): 
        yield Request(url=self.start_url, callback=self.parse_listing, dont_filter=True)

    def parse_listing(self, response):
        urls = response.css('.poetIndexIndexing a::attr("href")').extract()
        for url in urls:
            url = self.start_url + url
            yield Request(url=url, callback=self.parse_pagination, dont_filter=True)

    def parse_pagination(self, response):
        common_meta = {}
        common_meta['trail'] = [response.url]
        
        pages = response.css('.contentLoadMore div::attr("data-url")').extract()

        # page_links = response.css('script::text').re_first(r'ContentSlug":"(.+)"')
        # partitions = page_links.partition(':')
        # my_links = []
        # for i in range(0,pages):
        #     # if partitions[1].equals('ContentSlug'): 
        #     #     my_links.append(partition[i + 1])
        #     my_links.append(partitions[1])
        #     partitions = partitions[1].partition(':')
        
        # print('mylinks', my_links);
        
        
        for page in pages:
            meta = deepcopy(common_meta)
            page = self.start_url + page
            yield Request(url=page, callback=self.poet_listing, meta=meta)

    def poet_listing(self, response): 
        poet_links = response.css('.poetListingContent a:nth-child(1)::attr("href")').extract()

        for poet in poets:
            poet = self.start_url + poet
            yield Request(url=poet, callback=self.poet_page)
    
    def poet_page(self, response):
        poet_data = response.css('.searchCategory a::attr("href")').extract()[1:]

        for poet in poet_data:
            poet = self.start_url + poet
            yield Request(url=poet, callback=self.spider_parser.product_news)
    

    
        
    def parse(self, response):
        response.meta['trail'] = response.meta.get('trail', [])
        response.meta['trail'] += [response.url]

        for request in super().parse(response):
            request.meta['trail'] = response.meta['trail']
            yield request


# response.css('script::text').re(r'ContentSlug":"(.+)"')
#  callback=self.spider_parser.product_news