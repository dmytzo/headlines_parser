import json
import urllib2

from bs4 import BeautifulSoup


from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from articles_data import ARTICLES_DATA


def get_site_name(url):
    split_by = 'www.' if 'www.' in url else '//'
    return url.split(split_by)[1].split('.')[0]


def more_link_is_exist(article):
    return article.get('more_link') and 'http' in article['more_link']


def print_status(link, article_text):
    print(link)
    print('status - {}'.format('success' if article_text != 'NOT PROCESSED' else 'failed'))


def get_soup(request_type, url):
    if request_type == 'selenium':
        browser.get(url)
        html = browser.page_source
    else:
        html = urllib2.urlopen(url)

    return BeautifulSoup(html, 'lxml')


def get_article_text_multiple_parent_and_child(site, soup):
    article_blocks = soup.find_all(site['parent_selector']['tag'], **site['parent_selector']['attribute'])

    article_text = '' if article_blocks else 'NOT PROCESSED'

    for article_block in article_blocks:
        paragraphs = article_block.find_all(site['selector']['tag'])
        for paragraph in paragraphs:
            article_text += paragraph.text

    return article_text


def get_article_text_multiple(site, soup):
    article_block = soup.select('.{} > {}'.format(site['parent_selector']['attribute'][0][:-1],
                                                  site['selector']['tag']))

    article_text = '' if article_block else 'NOT PROCESSED'

    for paragraph in article_block:
        article_text += paragraph.text

    return article_text


def get_article_text_single(site, soup):
    parent_block = soup.find(site['parent_selector']['tag'], **site['parent_selector']['attribute'])

    article_block = parent_block.find_all(site['selector']['tag'])
    article_text = '' if article_block else 'NOT PROCESSED'
    for paragraph in article_block:
        if not paragraph.find_all('script'):
            article_text += paragraph.text
    return article_text


POSITION_FUNCTIONS = {
    'multiple_parent_and_child': get_article_text_multiple_parent_and_child,
    'multiple': get_article_text_multiple,
    'single': get_article_text_single
}


def parse_articles(data, articles):
    for article in articles:
        article_text = 'NOT PROCESSED'
        if more_link_is_exist(article):
            url = article['more_link']
            site_name = get_site_name(url)

            site = data.get(site_name)
            if site:
                try:
                    soup = get_soup(site['request'], url)
                    article_text = POSITION_FUNCTIONS[site['parent_selector']['position']](site, soup)
                except Exception:
                    pass

            print_status(article['more_link'], article_text)
            del article['more_link']

        article['article_text'] = article_text


# ________START_________
if __name__ == "__main__":
    options = Options()
    options.add_argument('--headless')
    profile = webdriver.FirefoxProfile()
    profile.set_preference("media.volume_scale", "0.0")
    profile.set_preference('permissions.default.image', 2)
    profile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so', 'false')
    browser = webdriver.Firefox(options=options, firefox_profile=profile, executable_path='/usr/local/bin/geckodriver')

    with open('headlines_2018.json') as data_file:
        articles_data = json.load(data_file)

    parse_articles(ARTICLES_DATA, articles_data)

    with open('headlines_2018_1.json', 'w+') as outfile:
        json.dump(articles_data, outfile)

    browser.quit()

    print('done')
