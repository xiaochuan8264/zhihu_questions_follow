import scrapy, pickle, json, time
from zhihuQsFollowingSpider.items import ZhihuqsfollowingspiderItem

class zhihuQuestionSpider(scrapy.Spider):
    name = 'questionSpider'

    def __init__(self, file=None):
        with open(file, 'r', encoding='utf-8') as f:
            questions = json.load(f)
        self.questions = questions
        # self.ids = list(self.questions.keys())
        # self.values = list(self.questions.values())

    def start_requests(self):
        for key, value in self.questions.items():
            self.id = key
            self.title = value['title']
            self.link = value['link']
            yield scrapy.Request(url=self.link, callback=self.get_detail)

    def get_detail(self, response):
        # 一定是这里出错了
        item = ZhihuqsfollowingspiderItem()
        try:
            now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            self.title = response.xpath('//div/h1/text()').get()
            self.link = response.url
            self.id = self.link.split('/')[-1]
            print('\n爬取到问题【%s】%s\n'%(self.title, self.link))
            follows_n_views = response.xpath('//div[@class="QuestionFollowStatus"]//strong//text()').getall()
            follows = follows_n_views[0].replace(',','')
            views = follows_n_views[1].replace(',','')
            answers = response.xpath('//div[@class="Question-mainColumn"]//div[@class="Card AnswersNavWrapper"]//h4[@class="List-headerText"]//text()').getall()
            if answers:
                answers = answers[0]
            else:
                try:
                    answers = response.xpath('//div[@class="Question-mainColumn"]//div[@class="Card ViewAll"]/@data-za-extra-module').extract()
                    answers = json.loads(answers)['card']['content']['item_number']
                except Exception as e:
                    answers = 0
                    print('也许没人回答吧....')
            item['detail'] = {'time':now,
                              'ID':self.id,
                              'title':self.title,
                              'follows':follows,
                              'views':views,
                              'answers':answers,
                              'link':self.link}
        except Exception as e:
            print('\n\nsomething went wrong\n\n')
            item['detail'] = {'time':now,
                              'ID':self.id,
                              'title':self.title,
                              'follows':0,
                              'views':0,
                              'answers':0,
                              'link':self.link}
        finally:
            yield item
