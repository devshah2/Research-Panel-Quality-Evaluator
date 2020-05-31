from __future__ import absolute_import, division, print_function, unicode_literals
from progress.bar import IncrementalBar
from bs4 import BeautifulSoup

import threading
import arrow
import bibtexparser
import codecs
import hashlib
import pprint
import random
import re
import requests
import sys
import time

_GOOGLEID = hashlib.md5(str(random.random()).encode('utf-8')).hexdigest()[:16]
_COOKIES = {'GSP': 'ID={0}:CF=4'.format(_GOOGLEID)}
_HEADERS = {
    'accept-language': 'en-US,en',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/41.0.2272.76 Chrome/41.0.2272.76 Safari/537.36',
    'accept': 'text/html,application/xhtml+xml,application/xml'
    }
_HOST = 'https://scholar.google.com'
_AUTHSEARCH = '/citations?view_op=search_authors&hl=en&mauthors={0}'
_CITATIONAUTH = '/citations?user={0}&hl=en'
_CITATIONPUB = '/citations?view_op=view_citation&citation_for_view={0}'
_KEYWORDSEARCH = '/citations?view_op=search_authors&hl=en&mauthors=label:{0}'
_PUBSEARCH = '/scholar?q={0}'
_SCHOLARPUB = '/scholar?oi=bibs&hl=en&cites={0}'

_CITATIONAUTHRE = r'user=([\w-]*)'
_CITATIONPUBRE = r'citation_for_view=([\w-]*:[\w-]*)'
_SCHOLARCITERE = r'gs_ocit\(event,\'([\w-]*)\''
_SCHOLARPUBRE = r'cites=([\w-]*)'
_EMAILAUTHORRE = r'Verified email at '

_SESSION = requests.Session()
_PAGESIZE = 100


def _handle_captcha(url):
    # TODO: PROBLEMS HERE! NEEDS ATTENTION
    # Get the captcha image
    captcha_url = _HOST + '/sorry/image?id={0}'.format(g_id)
    captcha = _SESSION.get(captcha_url, headers=_HEADERS)
    # Upload to remote host and display to user for human verification
    img_upload = requests.post('http://postimage.org/',
        files={'upload[]': ('scholarly_captcha.jpg', captcha.text)})
    print(img_upload.text)
    img_url_soup = BeautifulSoup(img_upload.text, 'html.parser')
    img_url = img_url_soup.find_all(alt='scholarly_captcha')[0].get('src')
    print('CAPTCHA image URL: {0}'.format(img_url))
    # Need to check Python version for input
    if sys.version[0]=="3":
        g_response = input('Enter CAPTCHA: ')
    else:
        g_response = raw_input('Enter CAPTCHA: ')
    # Once we get a response, follow through and load the new page.
    url_response = _HOST+'/sorry/CaptchaRedirect?continue={0}&id={1}&captcha={2}&submit=Submit'.format(dest_url, g_id, g_response)
    resp_captcha = _SESSION.get(url_response, headers=_HEADERS, cookies=_COOKIES)
    print('Forwarded to {0}'.format(resp_captcha.url))
    return resp_captcha.url


def _get_page(pagerequest):
    """Return the data for a page on scholar.google.com"""
    # Note that we include a sleep to avoid overloading the scholar server
    time.sleep(5+random.uniform(0, 5))
    resp = _SESSION.get(pagerequest, headers=_HEADERS, cookies=_COOKIES)
    if resp.status_code == 200:
        # print(resp.text)
        return resp.text
    if resp.status_code == 503:
        # Inelegant way of dealing with the G captcha
        raise Exception('Error: {0} {1}'.format(resp.status_code, resp.reason))
        # TODO: Need to fix captcha handling
        # dest_url = requests.utils.quote(_SCHOLARHOST+pagerequest)
        # soup = BeautifulSoup(resp.text, 'html.parser')
        # captcha_url = soup.find('img').get('src')
        # resp = _handle_gcaptcha(captcha_url)
        # return _get_page(re.findall(r'https:\/\/(?:.*?)(\/.*)', resp)[0])
    else:
        raise Exception('Error: {0} {1}'.format(resp.status_code, resp.reason))


def _get_soup(pagerequest):
    # print(pagerequest)
    # print("\n\n")
    """Return the BeautifulSoup for a page on scholar.google.com"""
    html = _get_page(pagerequest)
    html = html.replace(u'\xa0', u' ')
    return BeautifulSoup(html, 'html.parser')

def _search_citation_soup(soup):
    """Generator that returns Author objects from the author search page"""
    while True:
        for row in soup.find_all('div', 'gsc_1usr'):
            # print(row)
            yield Author(row)
        next_button = soup.find(class_='gs_btnPR gs_in_ib gs_btn_half gs_btn_lsb gs_btn_srt gsc_pgn_pnx')
        if next_button and 'disabled' not in next_button.attrs:
            url = next_button['onclick'][17:-1]
            url = codecs.getdecoder("unicode_escape")(url)[0]
            soup = _get_soup(_HOST+url)
        else:
            break

def _find_tag_class_name(__data, tag, text):
    elements = __data.find_all(tag)
    for element in elements:
        if 'class' in element.attrs and text in element.attrs['class'][0]:
            return element.attrs['class'][0]


class Author(object):
    """Returns an object for a single author"""
    def __init__(self, __data):
        # print(__data)
        if isinstance(__data, str):
            self.id = __data
        else:
            self.name = __data.find('h3', class_=_find_tag_class_name(__data, 'h3', 'name')).text
            # print(self.name)
            self.id = re.findall(_CITATIONAUTHRE, __data('a')[0]['href'])[0]
        self._filled = False

    def fill(self):
        """Populate the Author with information from their profile"""
        url_citations = _CITATIONAUTH.format(self.id)
        url = '{0}&pagesize={1}'.format(url_citations, _PAGESIZE)
        soup = _get_soup(_HOST+url)
        # h-index, i10-index and h-index, i10-index in the last 5 years
        index = soup.find_all('td', class_='gsc_rsb_std')
        if index:
            self.citedby = int(index[0].text)
            self.citedby5y = int(index[1].text)
            self.hindex = int(index[2].text)
            self.hindex5y = int(index[3].text)
            self.i10index = int(index[4].text)
            self.i10index5y = int(index[5].text)
        else:
            self.hindex = self.hindex5y = self.i10index = self.i10index5y = 0
        return self

    def __str__(self):
        return pprint.pformat(self.__dict__)

def search_author(name):
    url = _AUTHSEARCH.format(requests.utils.quote(name))
    soup = _get_soup(_HOST+url)
    return _search_citation_soup(soup)

import time
data=[]
def runXXX(author):
    authorStr=author
    init=time.time()
    search_query = search_author(author)
    try:
        author = next(search_query).fill()

    # print(author)
        global data
        data.append([author.citedby,author.i10index,author.hindex,author.name])
    except Exception as e:
        pass

def run(names):
    threads=[]
    counter=0
    bar = IncrementalBar('Countdown', max = len(names))
    for i in names:
        threads.append(threading.Thread(target=runXXX, args=(i,)))
        threads[counter].start()
        # time.sleep(1)
        counter+=1
        if(counter%5==0 and counter!=0):
            for id in range(len(threads)):
                # print(id)
                threads[id].join()
                bar.next()
            threads=[]
            counter=0
            time.sleep(2)
                
    for id in range(len(threads)):
        # print(id)
        threads[id].join()
init=time.time()
