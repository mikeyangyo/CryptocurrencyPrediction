import requests
import datetime
import string
import lxml.html
import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

def getMarkets():
    # download content of cryptocurrencies at tradingview.com
    r = requests.get('https://www.tradingview.com/markets/')

    # check if the content is valid or not
    if r.status_code != requests.codes.ok:
        return None
    
    # use bs4 to reveal the content with html
    soup = BeautifulSoup(r.text, 'html.parser')

    #find idea title by css class
    marketURLs = soup.select('h3.tv-site-widget__title.js-hotlists-dropdown > a')

    markets = []
    for marketURL in marketURLs:
        targetURL = str(marketURL.get('href'))
        splitlist = targetURL.split('/')
        targetmarket = splitlist[2]
        markets.append(targetmarket)
    return markets

def getAllPostsInMarket(startURL, Date = None):
    curURL = startURL
    curPage = 1
    allURLs = []
    allPosts = []

    totalPage = getTotalPageNumber(startURL)
    print 'processing page 1...'
    curURL = requests.compat.urljoin(curURL, '?sort=recent')
    print curURL
    URLs, postInfos, continueFinding = getAllPostsInPage(curURL, Date)
    
    if continueFinding == False:
        print 'No post can be crawl'
        return None

    allURLs.append(URLs)
    allPosts.append(postInfos)

    for i in range(2, totalPage + 1):
        pagePostfix = 'page-' + str(i)
        print 'processing ', pagePostfix, '...'
        absoluteNextPageURL = requests.compat.urljoin(startURL, pagePostfix)
        curURL = absoluteNextPageURL
        curURL = requests.compat.urljoin(curURL, '?sort=recent')
        print curURL
        URLs, postInfos, continueFinding = getAllPostsInPage(curURL, Date)
        
        if URLs in allURLs:
            print 'Error: the URL was duplicated'
            break
        
        if postInfos == None and continueFinding == False:
            print 'No post can be crawl'
            break

        allURLs.append(URLs)
        allPosts.append(postInfos)

    print allPosts

def getAllPostsInPage(startURL, Date = None):    
    # download content of cryptocurrencies at tradingview.com
    r = requests.get(startURL)

    # check if the content is valid or not
    if r.status_code != requests.codes.ok:
        return None
    
    # use bs4 to reveal the content with html
    soup = BeautifulSoup(r.text, 'html.parser')

    #find idea title by css class
    ideaURLs = soup.select('div.tv-site-widget.tv-widget-idea.js-widget-idea > div.tv-site-widget__body.tv-widget-idea.js-feed__item-minimizable-area.js-widget-body > a.tv-widget-idea__title.js-widget-idea__popup')

    URLs = []
    postInfos = []
    continueFinding = True
    for ideaURL in ideaURLs:
        url = ideaURL.get('href')
        absoluteURL = requests.compat.urljoin(startURL, url)
        URLs.append(absoluteURL)
        print absoluteURL
        postInfo, continueFinding = getPostInfo(absoluteURL, Date)
        print postInfo

        if postInfo != None:
            postInfos.append(postInfo)
        print '=================================================================='
    
    if len(postInfos) == 0:
        return URLs, None, continueFinding
    return URLs, postInfos, continueFinding

def getTotalPageNumber(startURL):
    # download content of cryptocurrencies at tradingview.com
    r = requests.get(startURL)

    # check if the content is valid or not
    if r.status_code != requests.codes.ok:
        return None
    
    # use bs4 to reveal the content with html
    soup = BeautifulSoup(r.text, 'html.parser')

    # find page urls by css class
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
    if r.status_code != requests.codes.ok:
        return None
    
    # use bs4 to reveal the content with html
    soup = BeautifulSoup(r.text, 'html.parser')

    # find post title by css class
    title = str(soup.select('h1.tv-chart-view__title-name.js-chart-view__name.apply-overflow-tooltip')[0].getText().rstrip())
    # find author name by css class
    author = str(soup.select('span.tv-chart-view__title-user-name')[0].getText().rstrip())
    # find time posted by css class
    seconds = int(float(soup.select('span.tv-chart-view__title-time')[0].get('data-timestamp')))
    timestamp = datetime.datetime.fromtimestamp(seconds)

    if Date != None:
        print timestamp.date(), Date.date()
        if timestamp.date() < Date.date():
            continueFinding = False
            return None, continueFinding
        elif timestamp.date() > Date.date():
            return None, continueFinding

    # scroll the page to buttom
    browser = webdriver.Chrome()
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

    #find comment info
    allComments = soup.select('div.tv-chart-comment__wrap')
    for comment in allComments:
        print getCommentInfo(comment)
    
    browser.close()
    return {'title':title, 'author':author, 'timestamp':str(timestamp)}, continueFinding

def getCommentInfo(tagString):
    # get author name of comment
    author = str(tagString.select('span.tv-chart-comment__user-name')[0].getText().strip())
    
    # get comment time posted
    seconds = int(float(tagString.select('span.tv-chart-comment__time')[0].get('data-timestamp')))
    timestamp = str(datetime.datetime.fromtimestamp(seconds))
    
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
            toWhom = content[1:toWhomEndIndex]
            content = content[toWhomEndIndex + 1:]
    
    # get agree number
    agreeNumTag = tagString.select('span.tv-chart-comment__rating.js-chart-comment__agree.apply-common-tooltip.tv-chart-comment__rating--positive.tv-chart-comment__rating--button')
    agreeNum = 0
    if len(agreeNumTag) != 0:
        agreeNum = int(agreeNumTag[0].getText().rstrip())

    return {'author': author, 'timestamp': timestamp, 'content': content, '# of agree': agreeNum, 'toWhom': toWhom}