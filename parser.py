#!/usr/bin/env python3

import requests
import sys
import io
import cgitb
import json
from scrapy.selector import Selector

cgitb.enable(display=1)

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome 51.0.2704.84 Safari/537.36"
}


def get_content(url):

    # rule_meta = "string(//script[contains(@data-vue-meta, 'true') and contains(., 'NewsArticle')])"
    # body = 'body({\"customContents\":[{\"row\":4,\"type\":\"ad\"},{\"row\":8,\"type\":\"newsletter\"},{\"row\":10,\"type\":\"more-on-this\"},{\"row\":13,\"type\":\"ad2\"},{\"row\":6,\"type\":\"outstream-1\"}]})'
    rule_meta = "string(//script[contains(@data-vue-meta, 'true') and contains(., 'News')])"
    body = 'body({"customContents":[{"row":4,"type":"ad"},{"row":8,"type":"newsletter"},{"row":9,"type":"reading-50-percent-completion-tracker"},{"row":10,"type":"more-on-this"},{"row":13,"type":"ad2"},{"row":6,"type":"outstream-1"},{"row":9999,"type":"reading-100-percent-completion-tracker"}]})'

    script_target = 'window.__APOLLO_STATE__'
    end_target = '}}}</script>'
    root_query = ''
    title = ''
    pubdate = ''
    media = ''
    raw_string = ''

    request = requests.get(url, headers=headers)
    web_page = request.content.decode('utf-8')
    headers_response = request.headers
    meta_obj = Selector(text=web_page).xpath(rule_meta).extract()

    if len(meta_obj) == 1:
        json_meta = json.loads(meta_obj[0])
        if 'headline' in json_meta:
            title = json_meta['headline']
        if 'datePublished' in json_meta:
            pubdate = json_meta['datePublished']
        if 'image' in json_meta and 'url' in json_meta['image']:
            media = json_meta['image']['url']

    # Get first and last <script> positions
    script_pos = web_page.find(script_target)
    script_end = web_page.find(end_target)

    # Cut and save script from full html content
    text_for_json = web_page[script_pos + 24: script_end + 3]

    # Get script as JSON object
    json_value = json.loads(text_for_json)
    # print(json_value['contentService'])

    # Get unical article id for news
    for key in json_value['contentService']['ROOT_QUERY'].keys():
        if 'content(' in key:
            root_query = json_value['contentService']['ROOT_QUERY'][str(key)]['id']

    json_len = len(json_value['contentService'][root_query][body]['json'])

    for item in headers_response:
        if 'content-length' in item or 'Content-Length' in item \
                or 'Content-Encoding' in item or 'content-encoding' in item \
                or 'Transfer-Encoding' in item or 'transfer-encoding' in item:
            continue
        else:
            print('{}: {}'.format(item, headers_response[item]))
    print('Content-Type: text/html; charset=utf-8')
    print()
    print('<!DOCTYPE html>')
    print("<html>")
    print("<head>")
    print("<meta http-equilv=\"Content-Type\" content=\"text/html; charset=utf-8\"/>")
    print("<title>{}</title>".format(title))

    if media != '':
        print("<meta property=\"og:image\" content=\"{}\"/>".format(media))

    if pubdate != '':
        print("<meta property=\"article:published_time\" content=\"{}\"/>".format(pubdate))

    print("</head>")
    print("<body>")
    print("<address>Current URL for request: {}</address>".format(url))

    title_content = json_value['contentService'][root_query]['headline']

    print("<section class=\"article-title\">")
    print("<h3>{}</h3>".format(title_content))
    print("</section>")
    if pubdate != '':
        print("<div class=\'node-submitted\'>{}</div>".format(pubdate))
    print("<section class=\"article-content\">")

    for x in range(0, json_len):

        if json_value['contentService'][root_query][body]['json'][x]['type'] == 'p':
            children_len = len(json_value['contentService'][root_query][body]['json'][x]['children'])

            for f in range(0, children_len):

                if json_value['contentService'][root_query][body]['json'][x]['children'][f]['type'] == 'text' \
                        and 'data' in json_value['contentService'][root_query][body]['json'][x]['children'][f]:
                    raw_string += json_value['contentService'][root_query][body]['json'][x]['children'][f]['data']

                elif json_value['contentService'][root_query][body]['json'][x]['children'][f]['type'] == 'a' \
                        and 'attribs' in json_value['contentService'][root_query][body]['json'][x]['children'][f]:
                    raw_string += '<a href="{}">{}</a>'.format(json_value['contentService'][root_query][body]['json'][x]['children'][f]['attribs']['href'],
                                                               json_value['contentService'][root_query][body]['json'][x]['children'][f]['children'][0]['data'])

                elif json_value['contentService'][root_query][body]['json'][x]['children'][f]['type'] == 'em':
                    raw_string += '<em>{}</em>'.format(json_value['contentService'][root_query][body]['json'][x]['children'][f]['children'][0]['data'])

            if len(raw_string) >= 1:
                print("<p>{}</p>".format(raw_string))
            raw_string = ''

    print("</section>")
    print("</body>")
    print("</html>")


def main():

    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="UTF-8")

        input_url = " ".join(sys.argv[1:])

        if 'scmp.com' in input_url:
            get_content(input_url)
        else:
            print("Incorrect input URL")
            sys.exit()
    except Exception as e:
        print('Status: 400')


if __name__ == '__main__':
    main()
