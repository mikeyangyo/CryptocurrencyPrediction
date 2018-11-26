import requests
import datetime
import string
import lxml.html
import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from utils import CRYPOTOCURRENCIES_ABBREV, MONEY_ABBREV, write_in_log, execute_sql
from pymysql import ProgrammingError
from accounts import *

def getAllPostsInMarket(startURL, Date = None, **kwargs):
    curURL = startURL
    allURLs = []
    allPosts = []

    totalPage = getTotalPageNumber(startURL, **kwargs)
    print('processing page 1...')
    if kwargs['crawl_status'] == 'alluser':
        print(curURL)
        URLs, postInfos, continueFinding = getAllPostsInPage(curURL, Date)
    else:
        curURL = requests.compat.urljoin(curURL, '/?sort=recent')
        print(curURL)
        URLs, postInfos, continueFinding = getAllPostsInPage(curURL, Date)
    
    if continueFinding == False:
        print('No post can be crawl')
        return None

    allURLs.append(URLs)
    allPosts.append(postInfos)

    for i in range(2, totalPage + 1):
        pagePostfix = 'page-' + str(i)
        print('processing ', pagePostfix, '...')
        absoluteNextPageURL = requests.compat.urljoin(startURL, pagePostfix)
        curURL = absoluteNextPageURL
        curURL = absoluteNextPageURL + '/?sort=recent'
        URLs, postInfos, continueFinding = getAllPostsInPage(curURL, Date)
        
        if URLs in allURLs:
            print('Error: the URL was duplicated')
            break
        
        if postInfos == None and continueFinding == False:
            print('No post can be crawl')
            break

        allURLs.append(URLs)
        allPosts.append(postInfos)
        print(allPosts)

    print(allPosts)

def getAllPostsInPage(startURL, Date = None):    
    # download content of cryptocurrencies at tradingview.com
    r = requests.get(startURL)

    # check if the content is valid or not
    if r.status_code != requests.codes['ok']:
        return None
    
    # use bs4 to reveal the content with html
    soup = BeautifulSoup(r.text, 'html.parser')

    #find idea title by css class
    ideaURLs = soup.select('div.tv-widget-idea > div.tv-widget-idea__title-row > a.tv-widget-idea__title')
    URLs = []
    postInfos = []
    continueFinding = True
    for ideaURL in ideaURLs:
        url = ideaURL.get('href')
        absoluteURL = requests.compat.urljoin(startURL, url)
        URLs.append(absoluteURL)
        print(absoluteURL)
        postInfo, continueFinding = getPostInfo(absoluteURL, Date)
        print(postInfo)

        if postInfo != None:
            postInfos.append(postInfo)
        print('==================================================================')
    
    if len(postInfos) == 0:
        return URLs, None, continueFinding
    return URLs, postInfos, continueFinding

def getTotalPageNumber(startURL, **kwargs):
    # download content of cryptocurrencies at tradingview.com
    r = requests.get(startURL)

    # check if the content is valid or not
    if r.status_code != requests.codes['ok']:
        return None
    
    # use bs4 to reveal the content with html
    soup = BeautifulSoup(r.text, 'html.parser')

    # find page urls by css class
    if 'crawl_status' in kwargs.keys() and kwargs['crawl_status'] != 'alluser':
        PageURLs = soup.select('a.tv-feed-pagination__page')
    else:
        PageURLs = soup.select('a.tv-load-more__page')
    lastPageURL = PageURLs[len(PageURLs) - 1].get('href')
    startIndex = lastPageURL.find('page-')

    # find the page number in url
    totalPageNumber = lastPageURL[startIndex + 5:]
    totalPageNumber = list(totalPageNumber)
    totalPageNumber[len(totalPageNumber) - 1] = ''
    totalPageNumber = ''.join(totalPageNumber)

    return int(totalPageNumber)

def getPostInfo(startURL, Date = None):
    continueFinding = True
    # download content of cryptocurrencies at tradingview.com
    r = requests.get(startURL)

    # check if the content is valid or not
    if r.status_code != requests.codes['ok']:
        return None
    
    # use bs4 to reveal the content with html
    soup = BeautifulSoup(r.text, 'html.parser')

    # find post title by css class
    title = str(soup.select('h1.tv-chart-view__title-name')[0].getText().rstrip())
    # find cryptocurrencies type of post
    cryptoTypeList = str(soup.select('a.tv-chart-view__symbol-link')[0].getText()).split('/')
    cryptoTypes = []
    for i in cryptoTypeList:
        i = i.strip()
        if i in CRYPOTOCURRENCIES_ABBREV.keys() and i not in MONEY_ABBREV.keys():
            cryptoTypes.append(CRYPOTOCURRENCIES_ABBREV[i])
    # find label of post
    labelList = soup.select('span.tv-chart-view__title-icons.js-chart-view__title-icons > span')
    label = None
    if len(labelList) != 0:
        label = str(labelList[0].getText())
    # find author name by css class
    author = str(soup.select('span.tv-chart-view__title-user-name')[0].getText().rstrip())
    # find time posted by css class
    seconds = int(float(soup.select('span.tv-chart-view__title-time')[0].get('data-timestamp')))
    timestamp = datetime.datetime.fromtimestamp(seconds)
    if Date != None:
        if timestamp.date() < Date.date():
            continueFinding = False
            return None, continueFinding
        elif timestamp.date() > Date.date():
            return None, continueFinding

    # scroll the page to buttom
    browser = webdriver.Chrome('./chromedriver')
    browser.get(startURL)
    time.sleep(1)
    elem = browser.find_element_by_tag_name('body')

    lastHeight = browser.execute_script("return document.body.scrollHeight")
    while True:
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.2)
        newHeight = browser.execute_script("return document.body.scrollHeight")
        if newHeight == lastHeight:
            break
        lastHeight = newHeight

    soup = BeautifulSoup(browser.page_source, 'html.parser')

    # check author existence
    sql = 'select id from {schema}.{table} where user_name = "{user_name}"'.format(schema=SCHEMA, table=table_name_set['comment'], user_name=author)
    result, msgs, _ = execute_sql(db_info_tradingview, 'select', sql)
    write_in_log(LOG_FILE, msgs)
    if not result:
        sql = 'insert into {schema}.{table}(user_name, accuracy_so_far) values ("{user_name}", null)'.format(schema = SCHEMA, table = table_name_set['user'], user_name = author)
        result, msgs, _ = execute_sql(db_info_tradingview, 'insert', sql)
        write_in_log(LOG_FILE, msgs)
    else:
        author_id = list(result)[0]

    # check this idea existence
    if len(cryptoTypes) > 0:
        sql = 'select id from {schema}.{table} where author = "{user_name}", tile = "{title}", crypto_type = "{type}", label = "{label}", created_time = "{timestamp}", idea_content = null'.format(
            schema=SCHEMA,
            table=table_name_set['idea'],
            user_name=author,
            title=title,
            type=cryptoTypes[0],
            label=label,
            timestamp=timestamp.strftime("%Y%m%d%H%M%s"))

        result, msgs, _ = execute_sql(db_info_tradingview, 'select', sql)
        write_in_log(LOG_FILE, msgs)
        if not result:
            sql = 'insert into {schema}.{table}(author, title, crypto_type, label, created_time, idea_content) values ("{user_id}", "{title}", "{type}", "{label}", "{timestamp}", null)'.format(
                schema = SCHEMA,
                table = table_name_set['comment'],
                user_id = author_id,
                title=title,
                type=cryptoTypes[0],
                label=label,
                timestamp=timestamp.strftime("%Y%m%d%H%M%s"))
            result, msgs, successed = execute_sql(db_info_tradingview, 'insert', sql)
            write_in_log(LOG_FILE, msgs)

            idea_id = None
            if successed:
                # get id created recently
                sql = 'select id from {schema}.{table} order by id desc limit 1'.format(
                    schema=SCHEMA,
                    table=table_name_set['idea']
                )
                result, msgs, _ = execute_sql(db_info_tradingview, 'select', sql)
                write_in_log(LOG_FILE, msgs)
                idea_id = list(result)[0]

                #find comment info
                allCommentList = soup.select('div.tv-chart-comment__wrap')
                allComments = []
                for commentList in allCommentList:
                    comments = getCommentInfo(commentList, idea_id=idea_id)
                    allComments.append(comments)
            else:
                raise ProgrammingError
        
    browser.close()
    return {'title':title, 'label': label, 'crypto type': cryptoTypes, 'author': author, 'timestamp': timestamp, 'allcomments':allComments}, continueFinding

def getCommentInfo(tagString, **kwargs):
    # get author name of comment
    author = str(tagString.select('span.tv-chart-comment__user-name')[0].getText().strip())
    
    # get comment time posted
    seconds = int(float(tagString.select('span.tv-chart-comment__time')[0].get('data-timestamp')))
    timestamp = datetime.datetime.fromtimestamp(seconds)
    # get comment content
    content = ''
    toWhom = None
    commentText = tagString.select('div.tv-chart-comment__text')[0].getText().strip()
    
    if commentText != '':
        html = lxml.html.fromstring(commentText)
        content = lxml.html.tostring(html)
    
        # remove the <p> tag
        content = content[3:len(content)-4].strip()
        
        # check if this comment is a reply or not
        if content[0] == '@':
            toWhomEndIndex = content.find(',')
            toWhom = str(content[1:toWhomEndIndex])
            content = str(content[toWhomEndIndex + 1:])
    
    # get agree number
    agreeNumTag = tagString.select('span.tv-chart-comment__rating.js-chart-comment__agree.apply-common-tooltip.tv-chart-comment__rating--positive.tv-chart-comment__rating--button')
    agreeNum = 0
    if len(agreeNumTag) != 0:
        agreeNum = int(agreeNumTag[0].getText().rstrip())

    # check author existence
    sql = 'select id from {schema}.{table} where user_name = "{user_name}"'.format(schema=SCHEMA, table=table_name_set['comment'], user_name=author)
    result, msgs, _ = execute_sql(db_info_tradingview, 'select', sql)
    write_in_log(LOG_FILE, msgs)
    if not result:
        sql = 'insert into {schema}.{table}(user_name, accuracy_so_far) values ("{user_name}", null)'.format(schema = SCHEMA, table = table_name_set['user'], user_name = user)
        result, msgs, _ = execute_sql(db_info_tradingview, 'insert', sql)
        write_in_log(LOG_FILE, msgs)
    else:
        author_id = list(result)[0]

    # check toWhom existence
    if toWhom:
        sql = 'select id from {schema}.{table} where user_name = "{user_name}"'.format(schema=SCHEMA, table=table_name_set['comment'], user_name=toWhom)
        result, msgs, _ = execute_sql(db_info_tradingview, 'select', sql)
        write_in_log(LOG_FILE, msgs)
        if not result:
            sql = 'insert into {schema}.{table}(user_name, accuracy_so_far) values ("{user_name}", null)'.format(schema = SCHEMA, table = table_name_set['user'], user_name = user)
            result, msgs, _ = execute_sql(db_info_tradingview, 'insert', sql)
            write_in_log(LOG_FILE, msgs)
        else:
            to_whom_id = list(result)[0]

    # check this comment existence
    sql = 'select id from {schema}.{table} where idea = "{idea_id}", author = "{user_name}", comment_content = "{content}", created_time = "{timastamp}", number_of_agree = "{num_of_agree}"'.format(
        schema=SCHEMA,
        table=table_name_set['comment'],
        idea_id=kwargs['idea_id'],
        user_name=author_id,
        content=content,
        timestamp=timestamp.strftime("%Y%m%d%H%M%s"),
        num_of_agree=agreeNum)
    if toWhom:
        sql += ', to_whom = "{user_name}"'.format(user_name=to_whom_id)

    result, msgs, _ = execute_sql(db_info_tradingview, 'select', sql)
    write_in_log(LOG_FILE, msgs)
    if not result:
        sql = 'insert into {schema}.{table}(author, comment_content, created_time, number_of_agree, to_whom) values ("{author_id}", "{content}", "{created_time}", {number_of_agree}, "{to_whom}")'.format(
            schema = SCHEMA,
            table = table_name_set['comment'],
            user_name = author_id,
            comment_content=content,
            created_time=timestamp.strftime("%Y%m%d%H%M%s"),
            number_of_agree=agreeNum,
            to_whom=to_whom_id)
        result, msgs, _ = execute_sql(db_info_tradingview, 'insert', sql)
        write_in_log(LOG_FILE, msgs)

    return {'author': author, 'timestamp': timestamp, 'content': content, '# of agree': agreeNum, 'toWhom': toWhom}