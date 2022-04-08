#!/usr/bin/python3
'''Manga Downloader.
'''
import cmd
import os
import asyncio
import shlex
import shutil
import json
import threading

import io_helper
from scraper import Scraper
from mangapill import MangapillScraper


class MangaDLConsole(cmd.Cmd):
    '''
    '''
    prompt = "\033[32m$ \033[0m"
    '''The console's prompt.
    '''
    scraper: Scraper = None
    '''The current scraper.
    '''
    scrapers = {
        'mangapill': MangapillScraper,
    }
    '''
    '''
    cwd = './'
    '''The current working directory.
    '''
    manga: str = ''
    '''The current manga.
    '''
    mangas = []
    '''
    '''
    book_format = 'cbz'

    def emptyline(self) -> bool:
        '''
        '''
        return False

    def do_quit(self, line: str):
        '''Quits the console.
        '''
        exit(0)

    # region Scrapers
    def do_get_scraper(self, line: str):
        '''Prints the current scraper.
        '''
        if (type(self.scraper) is not Scraper) and (isinstance(self.scraper, Scraper)):
            print('{}'.format(self.scraper.get_name()))
        else:
            print('\033[31mError:\033[0m Valid scraper hasn\'t been set')

    def do_set_scraper(self, line: str):
        '''Sets the current scraper.
        '''
        args = shlex.split(line)
        error = ''
        if len(args) > 0:
            if (args[0] in self.scrapers.keys()):
                self.scraper = self.scrapers[args[0]]()
            else:
                error = 'no scraper named "{}"'.format(args[0])
        else:
            error = 'too few arguments'
        if len(error) > 0:
            print('\033[31mError:\033[0m {}'.format(error))

    def do_list_scrapers(self, line: str):
        '''Lists all available scrapers.
        '''
        i = 1
        for scraper_name in self.scrapers.keys():
            print('+ {}'.format(scraper_name))
            i += 1
    # endregion

    # region directory info
    def do_get_wd(self, line: str):
        '''Prints the current working directory.
        '''
        print(self.cwd)

    def do_set_wd(self, line: str):
        '''Changes the current working directory.
        '''
        args = shlex.split(line)
        error = ''
        if len(args) > 0:
            if (os.path.isdir(args[0])):
                self.cwd = args[0]
            else:
                error = 'no such directory "{}"'.format(args[0])
        else:
            error = 'too few arguments'
        if len(error) > 0:
            print('\033[31mError:\033[0m {}'.format(error))
    # endregion

    # region manga
    def do_add_manga(self, line: str):
        '''Adds a new manga.\nUsage: add_manga url
        '''
        args = shlex.split(line)
        error = ''
        if self.scraper is None:
            error = 'Scraper not set.'
        elif len(args) >= 1:
            url = args[0]
            for manga in self.mangas:
                if manga['source'] == url:
                    return
            manga_info = self.scraper.get_manga_info(url)
            self.mangas.append(manga_info)
        else:
            error = 'too few arguments'
        if len(error) > 0:
            print('\033[31mError:\033[0m {}'.format(error))

    def do_get_manga(self, line: str):
        '''Prints the selected manga.\nUsage: get_manga
        '''
        print(self.manga)

    def do_set_manga(self, line: str):
        '''Selects a new manga.\nUsage: set_manga <manga name>
        '''
        error = 'no manga named "{}"'.format(line)
        for manga in self.mangas:
            if manga['title'] == line:
                self.manga = line
                error = ''
        if len(error) > 0:
            print('\033[31mError:\033[0m {}'.format(error))

    # def do_update_manga(self, line: str):
    #     pass

    def do_delete_manga(self, line: str):
        '''Deletes a manga.\nUsage: delete_manga <manga name>
        '''
        error = 'no manga named "{}"'.format(line)
        i = 0
        for manga in self.mangas:
            if manga['title'] == line:
                self.mangas.pop(i)
                error = ''
            i += 1
        if len(error) > 0:
            print('\033[31mError:\033[0m {}'.format(error))

    def download_chapters_task(self, cwd, scraper_id, manga_title, chapters):
        scraper = self.scrapers[scraper_id]()
        for chapter in chapters:
            try:
                chapter_folder = '{}{}{}{}{}'.format(
                    cwd,
                    '' if cwd.endswith(os.path.sep) else os.path.sep,
                    manga_title,
                    os.path.sep,
                    chapter['title']
                )
                if os.path.isfile('{}.cbz'.format(chapter_folder)):
                    # print('\033[32m{} is complete\033[0m'.format(chapter['title']))
                    continue
                chapter['pages'] = scraper.get_chapter_images(chapter['source'])
                page_sources = list(map(lambda x: x['source'], chapter['pages']))
                failed_downloads = io_helper.download_files(page_sources, chapter_folder)
                for page in chapter['pages']:
                    page['saved'] = page['source'] not in failed_downloads
                if len(failed_downloads) == 0:
                    io_helper.compress_folder_as_cbz(chapter_folder)
                    shutil.rmtree(chapter_folder)
                    # print('\033[32m{} is complete\033[0m'.format(chapter['title']))
                # else:
                #     print('\033[33m{} is incomplete\033[0m'.format(chapter['title']))
            except Exception as ex:
                # log error
                continue

    def do_download_chapters(self, line: str):
        '''Downloads chapters of the current manga.
        Usage: download_chapters [all|chapter_title ...]
        '''
        manga_info = None
        for manga in self.mangas:
            if manga['title'] == self.manga:
                manga_info = manga
        if manga_info is not None:
            chapters = []
            if line == 'all':
                chapters.extend(manga_info['chapters'])
            else:
                arg0 = list(map(lambda x: x.strip(), shlex.split(line)))
                for chapter in manga_info['chapters']:
                    if chapter['title'] in arg0:
                        chapters.append(chapter)
            dl_args = (
                self.cwd,
                self.scraper.get_name(),
                self.manga,
                chapters,
            )
            dl_thread = threading.Thread(
                group=None,
                target=self.download_chapters_task,
                args=dl_args
            )
            dl_thread.setDaemon(True)
            dl_thread.start()
            print('Downloading...')

    # def do_list_chapters(self, line: str):
    #     error = 'no manga named "{}"'.format(line)
    #     for manga in self.mangas:
    #         if manga['title'] == line:
    #             chapters = manga['chapters']
    #             error = ''
    #     if len(error) > 0:
    #         print('\033[31mError:\033[0m {}'.format(error))

    def do_list_mangas(self, line: str):
        '''Lists all available Mangas.\nUsage: list_mangas
        '''
        for manga in self.mangas:
            print('{}Title: {}'.format(
                '\033[33m*\033[0m ' if self.manga == manga['title'] else ' ',
                manga['title'])
            )
            print('\tCover Source: {}'.format(manga['props']['cover_source']))
            print('\tChapters Count: {}'.format(len(manga['chapters'])))
    # endregion

    # region IO
    def do_save(self, line: str):
        '''Saves information about the mangas.\nUsage: save
        '''
        file_path = '{}{}manga_info.json'.format(self.cwd, '' if self.cwd.endswith(os.path.sep) else os.path.sep)
        with open(file_path, 'w') as file:
            file.write(json.dumps(self.mangas))
            print('Saved manga_info.json')

    def do_load(self, line: str):
        '''Loads information about the mangas.\nUsage: load
        '''
        file_path = '{}{}manga_info.json'.format(self.cwd, '' if self.cwd.endswith(os.path.sep) else os.path.sep)
        if os.path.isfile(file_path):
            with open(file_path, 'r') as file:
                content = ''.join(file.readlines())
                self.mangas = json.loads(content)
                print('Loaded manga_info.json')
        else:
            print('\033[31mError:\033[0m manga_info.json doesn\'t exist in {}'.format(os.path.abspath(self.cwd)))
    # endregion


if __name__ == '__main__':
    asyncio.run(MangaDLConsole().cmdloop())
