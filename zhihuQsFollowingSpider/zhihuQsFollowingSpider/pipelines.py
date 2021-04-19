# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import pymysql, json, time

class ZhihuqsfollowingspiderPipeline(object):
    def __init__(self):
        self.db = pymysql.connect('localhost','root','root1234','zhihuquestions')
        self.cur = self.db.cursor()
        # self.exists_1 = False
        self.exists_2 = False

    def create_table(self, tablename, keys):
        if tablename != "general_table":
            sql = """create table if not exists {} (no int not null auto_increment, time timestamp, id varchar(50), title text, follows int, views int, answers int, link text, primary key(no)); """.format(tablename)
        else:
            sql = """create table if not exists general_table (no int not null auto_increment, id varchar(50), title text, link text, updatetime timestamp, follows int, views int, answers int,  primary key(no)); """

        # sql = """create table if not exists %s (no int not null auto_increment, {}, primary key(no));"""%tablename
        # inside = ' longtext not null,'.join(keys) +  ' longtext not null'
        # sql = sql.format(inside)
        # print('-------------------------')
        # print(sql)
        self.cur.execute(sql)
        self.cur.connection.commit()

    def insert_values(self, tablename, keys, values):
        sql = "insert into %s({})"%tablename
        sql = sql.format(', '.join(keys))
        sql += """ values{};""".format(values)
        # print(sql)
        self.cur.execute(sql)
        self.cur.connection.commit()

    def update_main_table(self, keys, values, item):
        sql = 'select id from general_table where id="%s";'%item['ID']
        self.cur.execute(sql)
        res = self.cur.fetchall()
        if res:
            sql = 'update general_table set updatetime="{}", views="{}", follows="{}",answers="{}" where id="{}";'.format(item['time'],
                           item['views'],
                           item['follows'],
                           item['answers'],
                           item['ID'])
            print(sql)
            self.cur.execute(sql)
            self.cur.connection.commit()
        else:
            self.insert_values('general_table', keys, values)

    def process_item(self, item, spider):
        detail = item.get('detail')
        print('处理【%s】数据'%detail['title'])
        keys_in_item = list(detail.keys())
        keys_in_item = ['`'+_+'`' for _ in keys_in_item]
        tablename = 'zhihu' + detail['ID']
        keys_needed_for_gtable = ['ID', 'Title', 'link', 'updatetime', 'follows', 'views', 'answers']
        self.create_table(tablename, keys_in_item)
        if not self.exists_2:
            self.create_table('general_table', keys_needed_for_gtable)
            self.exists_2 = True
        values = list(detail.values())
        values = ["'"+str(_)+"'" for _ in values]
        values = ', '.join(values)
        values = '(' + values +')'
        self.insert_values(tablename, keys_in_item, values)
        g_values = [detail['ID'],
                    detail['title'],
                    detail['link'],
                    detail['time'],
                    detail['follows'],
                    detail['views'],
                    detail['answers']]
        g_values = ["'"+str(_)+"'" for _ in g_values]
        g_values = ', '.join(g_values)
        g_values = '(' + g_values +')'
        self.update_main_table(keys_needed_for_gtable, g_values, detail)
        return item

    def close_spider(self,spider):
        self.db.close()

# class ZhihuqsfollowingspiderPipeline2(object):
#     def __init__(self):
#         self.now = time.strftime('%Y%m%d %H%M%S', time.localtime())
#         self.file = open('all_questions_data%s.json'%self.now,'w',encoding='utf-8')
#         self.container = {}
#         self.container['details'] = {}
#         self.container['general'] = {}
#
#     def process_item(self, item, spider):
#         info = item.get('detail')
#         id = info['ID']
#         if self.container['details'].get(id):
#             temp = [self.container['details'].get(id)]
#             temp.append(info)
#             self.container['details'][id] = temp
#         else:
#             self.container['details'].update({id:info})
#         self.container['general'].update({id:info})
#         return item
#
#     def close_spider(self):
#         data = json.dumps(self.container)
#         file.write(data)
#         file.close()
