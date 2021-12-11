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
    def get_chapters(self, url: str) -> list:
        '''
        Retrieves the chapter links of the given manga URL.

        Args:
            url (str): The URL of the manga page.

        Returns:
            list: A list of URLs of each chapter of a manga.
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
