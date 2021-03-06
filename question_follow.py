from selenium import webdriver
from selenium.common.exceptions import *
from selenium.webdriver.chrome.options import Options
import requests as rq
import random, pickle, os, time, re, json, pymysql
from bs4 import BeautifulSoup as bf
from selenium.webdriver.common.keys import Keys
import pandas as pd
import numpy as np

def chrome_prep():
    # os.popen('chrome.exe --remote-debugging-port=9222 --user-data-dir="G:\04_Py_Projects\__Developing__\06_zhihu_question_following\data_buff"')
    os.popen('start_chrome.bat')

def start():
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")  #  前面设置的端口号
    driver = webdriver.Chrome(options=chrome_options)  # executable执行webdriver驱动的文件
    return driver

def chrome_prep_and_takeover():
    # 打开浏览器并接管
    chrome_prep()
    driver = start()
    return driver

def login(driver):
    # 改为自己登陆最好，半手动模式
    # 如果用密码登录
    login_buttons = driver.find_elements_by_class_name('SignFlow-tab')
    for each in login_buttons:
        if each.text == '密码登录':
            login = each
            login.click()
    time.sleep(1)
    login_info = {'account':'accountinfo',
                   'password':'passwordinfo'}
    username = driver.find_element_by_name('username')
    username.send_keys(login_info['account'])
    password = driver.find_element_by_name('password')
    password.send_keys(login_info['password'])
    login_button = driver.find_element_by_class_name('SignFlow-submitButton')
    login_button.click()

def load_or_login(driver):
    # 接管浏览器的话缓存是可以保存的，所以完全可以手动登录
    choice = input('choice:')
    if choice == 'load':
        with open('account_cookies.pl', 'rb') as f:
            cookies = pickle.load(f)
        driver.delete_all_cookies()
        for i in cookies:
            driver.add_cookie(i)
        input('pleas refresh to verify if cookies are loaded successfully')
    elif choice == 'login':
        login(driver)
        save_cookies(driver)

def save_cookies(driver):
    cookies = driver.get_cookies()
    with open('account_cookies.pl','wb') as f:
        pickle.dump(cookies, f)

def scroll(driver):
    #下拉到最底部
    js = "return action=document.body.scrollHeight"
    height = driver.execute_script(js)
    driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
    time.sleep(3)
    t1 = int(time.time())
    status = True
    num = 0
    while status:
	    # 获取当前时间戳（秒）
        t2 = int(time.time())
        # 判断时间初始时间戳和当前时间戳相差是否大于30秒，小于30秒则下拉滚动条
        if t2-t1 < 10:
            new_height = driver.execute_script(js)
            if new_height > height :
                time.sleep(1)
                driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
                # 重置初始页面高度
                height = new_height
                # 重置初始时间戳，重新计时
                t1 = int(time.time())
        elif num < 3:  # 当超过30秒页面高度仍然没有更新时，进入重试逻辑，重试3次，每次等待30秒
            time.sleep(3)
            num = num+1
        else:    # 超时并超过重试次数，程序结束跳出循环，并认为页面已经加载完毕！
            print("滚动条已经处于页面最下方！")
            status = False
            # 滚动条调整至页面顶部
            driver.execute_script('window.scrollTo(0, 0)')
            break

def collect_random_questions(driver):
    # 收集提问 一般是最新提问
    page = driver.page_source
    soup = bf(page,'lxml')
    targets = soup.findAll(class_='QuestionItem-title')
    questions = {}
    for t in targets:
        title = t.a.get_text()
        link = 'https://www.zhihu.com' + t.a['href']
        number = t.a['href'].split('/')[-1]
        questions[number] = {'title':title, 'link':link}
    now = time.strftime('%Y%m%d%H%M%S', time.localtime())
    filename = now + '来答问题.json'
    with open(filename,'w',encoding='utf-8') as f:
        json.dump(questions, f)
    return (questions,filename)

def collect_specific_questions(driver):
    pass

def get_question_status(filename):
    #调用scrapy获得所需信息
    os.chdir('zhihuQsFollowingSpider')
    time.sleep(0.5)
    os.popen('scrapy crawl questionSpider -a file="../%s"'%filename)

def update_questions_status(datelimit=None, viewslimit=None):
    db = pymysql.connect('localhost','root','root1234','zhihuquestions')
    cur = db.cursor()
    sql = "select id, title, link from general_table;"
    cur.execute(sql)
    res = cur.fetchall()
    data = {}
    temp = [data.update({_[0]:{'title':_[1], 'link':_[2]}}) for _ in res]
    filename = 'data_in_mysql.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    get_question_status(filename)

def get_jingdong_products(driver, pagelimit=100):
    """
    首先进入京东自行找一个大的品类
    可以是自己筛选佣金范围后的产品，也可以是搜索后的产品
    """
    def extract_card(card):
        card_info = {}
        one = card.find_element_by_class_name('one')
        rate_and_money = one.text.split('\n')
        commission_rate = rate_and_money[0]
        commission = rate_and_money[1]

        two = card.find_element_by_class_name('two')
        two_detail = two.find_element_by_tag_name('a')
        link = two_detail.get_attribute('href')
        product = two_detail.get_attribute('title')

        three = card.find_element_by_class_name('three')
        price = three.find_element_by_tag_name('span').text

        four = card.find_element_by_class_name('four')
        comments = four.text

        try:
            shop = card.find_element_by_class_name('shop-detail')
            shop = shop.text
        except NoSuchElementException as e:
            shop = 'unknown'
        card_info['product'] = product
        card_info['price'] = price
        card_info['commission'] = commission
        card_info['comments'] = comments
        card_info['commission_rate'] = commission_rate
        card_info['shop'] = shop
        card_info['link'] = link
        return card_info

    def check_page(driver, last_card=None):
        card = driver.find_element_by_class_name('card')
        first_card_info = extract_card(card)
        print(first_card_info, end='>>>>>')
        print(last_card)
        if first_card_info == last_card:
            return True
        else:
            return False

    url = driver.current_url
    pages = driver.find_elements_by_class_name('number')
    numbers = [int(_.text) for _ in pages]
    page = max(numbers)
    if pagelimit >= page:
        pagelimit = page
    try:
        products_info = []
        # 页面刷新有延迟，需要验证是不是还在同一个页面，如果是则等待刷新
        last_card = None
        for each_page in range(pagelimit):
            # 提取页面商品信息
            cards = driver.find_elements_by_class_name('card')
            if len(products_info):
                check = check_page(driver, last_card)
                while check:
                    print('等待刷新界面')
                    check = check_page(driver, last_card)
                    time.sleep(5)
                    driver.refresh()
            mark = 1
            for card in cards:
                card_info = extract_card(card)
                if mark:
                    last_card = card_info.copy()
                    mark = 0
                    # print(last_card)

                products_info.append(card_info.copy())
            #进入下一页
            next_page = driver.find_element_by_class_name('btn-next')
            next_page.send_keys(Keys.ENTER)
            print('\n进入第 %d 页\n'% (each_page + 2))
            time.sleep(5)
        return products_info
    except Exception as e:
        print(e)
    finally:
        return products_info

def save_products(products_info):

    with open('jingdong_products.pl','wb') as f:
        pickle.dump(products_info, f)
    df = pd.DataFrame(products_info)
    df.to_excel('jingdong_products.xlsx')

def test(driver):
    next_page = driver.find_element_by_class_name('btn-next')
    next_page.send_keys(Keys.ENTER)


def integrated_commands():
    # 开启chrome浏览器
    chrome_prep()
    time.sleep(2)
    homepage = "https://www.zhihu.com/"
    # webdriver接管浏览器
    driver = start()
    # 进入知乎
    driver.get(homepage)
    # 加载cookie或登录
    load_or_login(driver)
    # 最新问题下滑到底部
    scroll(driver)
    # 获取到问题
    questions_n_file = collect_random_questions(driver)
    get_question_status(questions_n_file[1])

if "__name__" == "__main__":
    driver = chrome_prep_and_takeover()
