#!/usr/bin/python3
'''IO Helper functions.
'''
import os
import sys
from typing import Tuple, List
import requests
from zipfile import ZipFile


def safeMkDir(dir_path):
    '''Makes all directories in a given path if they don't exist.

    Args:
        dir_path (str): The directory path.
    '''
    prev_wd = os.path.abspath(os.curdir)
    dir_parts = dir_path.split(os.path.sep)
    for i in range(len(dir_parts)):
        if len(dir_parts[i]) > 0:
            if i > 0:
                os.chdir(dir_parts[i - 1])
            if ((not os.path.isdir(dir_parts[i])) and (dir_parts[i] not in ('.', '..'))):
                os.mkdir(dir_parts[i])
    os.chdir(prev_wd)


def compress_folder_as_cbz(folder_path: str):
    '''Compresses the files (not folders) in a given directory path.

    Args:
        folder_path (str): The path to the folder.
    '''
    if os.path.isdir(folder_path):
        with ZipFile('{}.cbz'.format(folder_path), 'w') as zip_file:
            for file in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file)
                if os.path.isfile(file_path):
                    zip_file.write(file_path, file)
    else:
        print('\033[31mError:\033[0m Not a folder')


def download_files(urls: list, dest_folder: str) -> List[Tuple[str, bool]]:
    '''Downloads a list of resources to a given folder.

    Args:
        urls (list of str): A list of URLs whose contents are to be saved.
        dest_folder (str): The folder where the resources would be saved to.

    Returns:
        list: The list of download sources and their completion status.
    '''
    # safeMkDir(dest_folder)
    os.makedirs(dest_folder, exist_ok=True)
    for url in urls:
        try:
            res = requests.get(url).content
            file_path = '{}{}{}'.format(
                dest_folder,
                '' if dest_folder.endswith(os.path.sep) else os.path.sep,
                url.split('/')[-1]
            )
            with open(file_path, mode='wb') as file:
                file.write(res)
            yield (url, True)
        except (ConnectionError, OSError) as ex:
            print('\033[33mError:\033[0m {} ({})'.format(ex.args[1], ex.__class__))
            yield (url, False)
