"""
Author: Hao Lin
Data processing utility
"""
import codecs
import re
import os
from multiprocessing.pool import ThreadPool as Pool
from xml.dom.minidom import parse
import xml.dom.minidom
import jieba


def process_xml_data(file_path, out_path):
    f = codecs.open(file_path, 'r', 'gb18030')
    text = f.read()
    f.close()
    temp = file_path.split('.xml')[0] + 'temp.xml'
    f = open(temp, 'w', encoding='utf-8')
    f.write('<?xml version="1.0" encoding="utf-8"?>')
    f.write("<root>")
    text = text.replace("&", "")
    f.write(text)
    f.write("</root>")
    f.close()
    dom_tree = xml.dom.minidom.parse(temp)
    os.remove(temp)

    collection = dom_tree.documentElement
    docs = collection.getElementsByTagName("doc")
    out_file = open(out_path, 'a+', encoding='utf-8')
    split_pattern = re.compile(r'[，。；！？\s]+')
    redundant_pattern = re.compile(r'[^\u4e00-\u9fff]+')

    for doc in docs:
        title_node = doc.getElementsByTagName("content")[0].firstChild
        content_node = doc.getElementsByTagName("contenttitle")[0].firstChild
        if (title_node is None) or (content_node is None):
            continue
        title = title_node.data
        content = content_node.data
        content_lines = re.split(split_pattern, content)
        title_lines = re.split(split_pattern, title)
        pool = Pool(processes=30)
        content_lines = pool.map(lambda x: re.sub(redundant_pattern, '', x) + '\n', content_lines)
        title_lines = pool.map(lambda x: re.sub(redundant_pattern, '', x) + '\n', title_lines)
        pool.close()
        pool.join()
        out_file.writelines(content_lines)
        out_file.writelines(title_lines)


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


def assemble_data(path='./Data'):
    """
    Concat the processed file and a word data file
    Args:
         path(str)
    """
    final_file = open(os.path.join(path, 'data.data'), 'w', encoding='utf-8')

    with open(os.path.join(path, 'sentence.txt'), 'r', encoding='utf-8') as file:
        lines = file.readlines()
        for line in lines:
            line = line.strip()
            if len(line) > 0 and is_chinese(line):
                # S implies that this line is a sentence
                words = list(jieba.cut(line))
                words = [word + ' W' + '\n' for word in words]
                final_file.writelines(words)
                final_file.write(line + ' S' + '\n')

    with open(os.path.join(path, 'dict.txt'), 'r', encoding='utf-8') as file:
        lines = file.readlines()
        for line in lines:
            line = line.split()
            for i in range(int(line[1])):
                if is_chinese(line[0]):
                    # W implies that this line is a word
                    final_file.write(line[0] + ' W' + '\n')

    final_file.close()


def process():
    if not os.path.exists("./Data/sentence.txt"):
        files = os.listdir("./Data")
        for file in files:
            if file.startswith("news.allsites"):
                print("Processing {}".format(file))
                process_xml_data(os.path.abspath("./Data/{}".format(file)), "./Data/sentence.txt")
    assemble_data()


if __name__ == "__main__":
    process()