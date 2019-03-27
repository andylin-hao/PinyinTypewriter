"""
Utility for processing text data
"""
import json
import re
import os
from multiprocessing.pool import ThreadPool as Pool


def is_chinese(sentence):
    """
    Args:
        sentence(str)
    Returns:
        bool: True for Chinese
    """
    for word in sentence:
        if not '\u4e00' <= word <= '\u9fff':
            return False
    return True


def process_json_data(file_path):
    """
    Function for processing json text file
    Args:
         file_path(str): file path that can be found by this script
    """
    with open(file_path, 'r', encoding='gbk') as file:
        split_pattern = re.compile(r'[，。；！？\s]+')
        redundant_pattern = re.compile(r'[^\u4e00-\u9fff]+')
        if not os.path.exists('./Data'):
            os.mkdir('Data')
        processed_file = open(os.path.join('./Data', os.path.basename(file_path)), 'w', encoding='utf-8')
        print('Begin processing ' + file_path + '...')
        lines = file.readlines()
        for line in lines:
            line_data = json.loads(line)
            line_content = re.split(split_pattern, line_data['html'])
            line_title = re.split(split_pattern, line_data['title'])
            pool = Pool(processes=30)
            line_content = pool.map(lambda x: re.sub(redundant_pattern, '', x) + '\n', line_content)
            line_title = pool.map(lambda x: re.sub(redundant_pattern, '', x) + '\n', line_title)
            pool.close()
            pool.join()
            processed_file.writelines(line_content)
            processed_file.writelines(line_title)

        processed_file.close()
        print('Done processing ' + os.path.basename(file_path))


def concat_file(path='./Data'):
    """
    Concat the processed file and a word data file
    Args:
         path(str)
    """
    file_list = os.listdir(path)
    file_list = [os.path.join(path, file_name) for file_name in file_list]
    final_file = open(os.path.join(path, 'data.data'), 'w', encoding='utf-8')
    for file_path in file_list:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            for line in lines:
                if line != '\n':
                    final_file.write(line)

    with open(os.path.join(path, 'dict.txt'), 'r', encoding='utf-8') as file:
        lines = file.readlines()
        for line in lines:
            line = line.split()
            for i in range(int(line[1])):
                if is_chinese(line[0]):
                    final_file.write(line[0] + '\n')

    final_file.close()


def process(path='./RawData'):
    file_list = os.listdir(path)
    file_list = [os.path.join(path, file_name) for file_name in file_list]
    pool = Pool(processes=9)
    pool.map(process_json_data, file_list)
    pool.close()
    pool.join()
    concat_file()
