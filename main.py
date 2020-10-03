import argparse
import asyncio
import logging
import os
import sys
import time
from mimetypes import guess_extension

import aiofiles
import aiohttp

from parser import HTMLNewsParser, HTMLCommentsParser

NEWS_URL = "https://news.ycombinator.com"
COMMENT_URL_TEMPLATE = "https://news.ycombinator.com/item?id={}"
DEFAULT_DIR = "."
DEFAULT_PERIOD = 60


async def get_page(client, url):
    async with client.get(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X x.y; rv:42.0) '
                                                      'Gecko/20100101 Firefox/42.0'}) as resp:
        resp.raise_for_status()
        content = await resp.read()
        return content, resp.headers['content-type']


async def save_content(path, content, content_type):
    path += guess_extension(content_type.partition(';')[0].strip())
    async with aiofiles.open(path, mode='wb') as f:
        await f.write(content)
        await f.close()


async def process_comment_link(client, url, path, num):
    try:
        content, content_type = await get_page(client, url)
        await save_content(os.path.join(path, 'link{}'.format(num)), content, content_type)
    except Exception as ex:
        logging.error('Error while download link {} from comment: {}'.format(url, ex))


async def download_comment_links(client, path, url_list):
    tasks = []
    num = 1
    for comment_url in url_list:
        tasks.append(asyncio.create_task(process_comment_link(client, comment_url, path, num)))
        num += 1
    await asyncio.gather(*tasks, return_exceptions=True)


async def download_news(dir, id, url):
    path = os.path.join(dir, id)

    if not(url.startswith('http://') or url.startswith('https://')):
        url = "{}/{}".format(NEWS_URL, url)

    logging.info('Start downloading {}'.format(url))
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as client:
        try:
            content, content_type = await get_page(client, url)
        except aiohttp.InvalidURL:
            logging.info('Invalid url {}'.format(url))
        except Exception as ex:
            logging.error('Error while download news {} : {}'.format(url, ex))
        else:
            if not os.path.exists(path):
                os.mkdir(path)
            await save_content(os.path.join(path, 'news_content'), content, content_type)

            comment_url = COMMENT_URL_TEMPLATE.format(id)

            try:
                html, _ = await get_page(client, comment_url)

                if html:
                    parser = HTMLCommentsParser()
                    parser.feed(html.decode("utf-8"))

                    logging.info('Start downloading {} links from comments (count = {})'
                                 .format(url, len(parser.url_list)))
                    await download_comment_links(client, path, parser.url_list)
            except aiohttp.ClientResponseError as ex:
                # try to process news on the next iteration
                if ex.status == 503:
                    return -1
                else:
                    logging.error('Error while process comment page {}: {}'.format(comment_url, ex))
            except Exception as ex:
                logging.error('Error while process comment page {}: {}'.format(comment_url, ex))
            return id


async def main(args):
    processed_news = set()

    while True:
        logging.info('Start crawling iteration...')
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as client:
            html, _ = await get_page(client, NEWS_URL)
        # await asyncio.sleep(0.1)
        parser = HTMLNewsParser()
        parser.feed(html.decode("utf-8"))

        tasks = []
        for id, url in parser.news_dict.items():
            if id not in processed_news:
                tasks.append(asyncio.create_task(download_news(args.save_path, id, url)))

        # add processed news id
        processed_news.update(await asyncio.gather(*tasks, return_exceptions=True))
        logging.info('Finish crawling iteration...')

        await asyncio.sleep(args.period)


def parse_args():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--save_path', default=DEFAULT_DIR, type=str,
                        help='directory for saving news')
    parser.add_argument('--period', default=DEFAULT_PERIOD, type=int,
                        help='run cycle every N seconds')
    return parser.parse_args()


if __name__ == '__main__':
    try:
        args = parse_args()

        logging.basicConfig(format='%(asctime)s] %(levelname).1s %(message)s',
                            datefmt='%Y.%m.%d %H:%M:%S', level=logging.INFO)
        logging.info("Crawler started with options: {}".format(args))

        asyncio.run(main(args))
    except KeyboardInterrupt:
        sys.exit('Crawler stopped.')
    except Exception as e:
        logging.info('Crawler stopped unexpectedly. Error: {}'.format(e))
        sys.exit('Crawler stopped unexpectedly. Error: {}'.format(e))
