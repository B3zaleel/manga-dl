#!/usr/bin/python3
'''Scraper
'''
from abc import ABC, abstractmethod


class Scraper(ABC):
    '''An abstract class for all scrapers.
    '''
    @abstractmethod
    def get_name(self) -> str:
        '''Retrieves the name of this scraper.
        '''
        pass

    @abstractmethod
    def get_manga_info(self, url: str) -> dict:
        '''
        Retrieves information about a Manga from the given manga URL.

        Args:
            url (str): The URL of the manga page.

        Returns:
            dict: Information about a manga.
        '''
        pass

    @abstractmethod
    def get_chapter_images(self, url: str) -> list:
        '''
        Retrieves the chapter image sources of the given chapter URL.

        Args:
            url (str): The URL of the chapter page.

        Returns:
            list: A list of URLs of each image source for a chapter.
        '''
        pass
