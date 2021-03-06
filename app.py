#!/usr/bin/python3
'''Manga Downloader.
'''
import cmd
import os
import re
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
                    chapter['isCompleted'] = True
                    chapter['pages'] = []
                    # print('\033[32m{} is complete\033[0m'.format(chapter['title']))
                    continue
                chapter['pages'] = scraper.get_chapter_images(chapter['source'])
                page_sources = list(map(lambda x: x['source'], chapter['pages']))
                chapter['isCompleted'] = False
                failed_downloads = 0
                for url, done in io_helper.download_files(page_sources, chapter_folder):
                    failed_downloads += 0 if done else 1
                    idx = page_sources.index(url)
                    chapter['pages'][idx]['saved'] = done
                if failed_downloads == 0:
                    io_helper.compress_folder_as_cbz(chapter_folder)
                    shutil.rmtree(chapter_folder)
                    chapter['isCompleted'] = True
                    chapter['pages'] = []
                    # print('\033[32m{} is complete\033[0m'.format(chapter['title']))
                else:
                    chapter['isCompleted'] = False
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

    def do_list_chapters(self, line: str):
        '''Lists the chapters of the current manga or a given manga.
    Usage: list_chapters [manga_title[|.] [start][-end]]
        '''
        args = shlex.split(line)
        manga_title = args[0] if len(args) else self.manga
        msg = 'no manga named "{}"'.format(manga_title)
        chapters = []
        start, end = (0, 0)
        if manga_title == '.':
            manga_title = self.manga
        for manga in self.mangas:
            if manga['title'] == manga_title:
                chapters = manga['chapters']
                msg = ''
                break
        if msg:
            print('\033[31mError:\033[0m {}'.format(msg))
            return
        if len(chapters) > 0:
            start = 0
            end = len(chapters)
        else:
            msg = 'There are no chapters'
            print('\033[33mInfo:\033[0m {}'.format(msg))
            return
        if len(args) > 1:
            chapters_range = args[1].strip()
            range_match = re.fullmatch(r'(?P<start>\d+)?(?:-(?P<end>\d+))?', chapters_range)
            if range_match:
                if range_match.group('end'):
                    end_val = int(range_match.group('end'))
                    if end_val <= end and end_val >= 0:
                        end = end_val
                if range_match.group('start'):
                    start_val = int(range_match.group('start'))
                    if start_val >= end:
                        msg = 'Start must be less than end'
                        print('\033[31mError:\033[0m {}'.format(msg))
                        return
                    if start_val < end and start_val >= 0:
                        start = start_val
            else:
                msg = 'Invalid option: {}'.format(args[1])
                print('\033[31mError:\033[0m {}'.format(msg))
                return
        for chapter in chapters[start:end]:
            pages_count = len(chapter['pages'])
            pages_saved = len(list(filter(lambda x: x['saved'], chapter['pages'])))
            status = 'Unknown'
            if chapter.get('isCompleted', False):
                status = '\033[92mCompleted\033[0m'
            if pages_count > 0:
                if pages_saved < pages_count:
                    status = '\033[93m{}%\033[0m'.format(int((pages_saved / pages_count) * 100))
                elif pages_saved == pages_count:
                    status = '\033[92mCompleted\033[0m'
            print('Title : {}'.format(chapter['title']))
            print('Status: {}'.format(status))

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
