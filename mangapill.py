#!/usr/bin/python3
'''Mangapill
'''
import requests
from bs4 import BeautifulSoup

from scraper import Scraper


class MangapillScraper(Scraper):
    '''A scraper for Mangapill.
    '''
    def get_name(self) -> str:
        return 'mangapill'

    def get_manga_info(self, url) -> list:
        manga_page = requests.get(url).content
        manga_soup = BeautifulSoup(manga_page, 'html.parser')
        info_container = manga_soup.find('body').find(recursive=False, **{'class': 'container'})
        image = info_container.find('img')
        chapters_container = manga_soup.find(**{'id': 'chapters'})
        chapters = chapters_container.find_all('a')
        chapter_links = []
        for chapter in chapters:
            chapter_links.append(
                {
                    'title': chapter.text,
                    'source': 'https://mangapill.com{}{}'.format(
                        '' if chapter.attrs['href'].startswith('/') else '/',
                        chapter.attrs['href']
                    ),
                    'pages': [],
                }
            )
        manga_info = {
            'title': manga_soup.find('h1').text,
            'source': url,
            'props': {
                'cover_source': image.attrs['data-src'],
                'genres': '',
                'description': '',
            },
            'chapters': chapter_links,
        }
        # print(manga_info)
        return manga_info

    def get_chapter_images(self, url: str) -> list:
        chapter_page = requests.get(url).content
        chapter_soup = BeautifulSoup(chapter_page, 'html.parser')
        images_container = chapter_soup.find(**{'class': 'lg:container'})
        images = images_container.find_all('img')
        chapter_images = []
        for image in images:
            chapter_images.append(
                {
                    'saved': False,
                    'source': image.attrs['data-src']
                }
            )
        return chapter_images
