import datetime
import json
import re

from common.common_modules import SiteRequests, SiteParser
from common.data_structure import Site, DataPayload

SITE_INFO = Site(hostname="natalie.mu", name="Natalie 音楽ナタリー")

def get_data(hd):
    site_parser = SiteParser()
    site_requests = SiteRequests()
    soup = site_parser._parse(site_requests.session.get(hd).text)


    json_raw = soup.find('script', type='application/ld+json')
    json_data = re.sub(r'\\/', '/', bytes(json_raw.string, "utf=8").decode("unicode_escape"))
    data = json.loads(json_data)

    post_title = data[0]["itemListElement"][-1]["item"]["name"]
    post_date = data[1]["datePublished"]
    post_date = datetime.datetime.strptime(post_date, '%Y-%m-%dT%H:%M:%S%z')
    post_date = post_date.replace(tzinfo=None)
    post_date_short = post_date.strftime('%Y%m%d')[2:]

    print(post_title)
    print(post_date)

    content = soup.find('div', class_='NA_article_gallery')

    img_list = []
    for item in content.findAll('img'):
        img_list.append(item['data-src'].split('?')[0])

    dir = [SITE_INFO.name, f"{post_date_short} {post_title}"]

    payload = DataPayload(
        directory_format=dir,
        media=img_list,
        option=None,
    )
    
    from down.directory import DirectoryHandler

    DirectoryHandler().handle_directory(payload)