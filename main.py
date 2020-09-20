import sys
import contextlib
import aiohttp
from aiohttp import web
import asyncio
import ssl
import certifi
from parser import HTMLNewsParser, HTMLCommentsParser

BASE_URL = "https://news.ycombinator.com"


async def download_news(client, id, url):
    comment_url = "{}/item?id={}".format(BASE_URL, id)
    async with client.get(comment_url) as resp:
        html = await resp.text()
        parser = HTMLCommentsParser()
        parser.feed(html)
        print('*'*40)
        print(url)
        print(id)
        print(parser.comment_list)
        print('*' * 40)


async def download_top_news(client):
    async with client.get(BASE_URL) as resp:
        return await resp.text()


async def main():
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as client:
        html = await download_top_news(client)
        parser = HTMLNewsParser()
        parser.feed(html)

        for item in parser.link_list:
            await download_news(client, item['ID'], item['URL'])


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        sys.exit('Crawler was stopped unexpectedly. Error: {}'.format(e))
