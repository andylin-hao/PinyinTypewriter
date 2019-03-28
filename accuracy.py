from HMM.model import Model
from pypinyin import pinyin, NORMAL
from eprogress import LineProgress
import numpy as np


def test_accuracy(path='./Data/dict.txt', size=1000, loop=5):
    """
    Function for testing the model's accuracy
    Args:
        path(str): The path of test file
        size(int): The size of test data
        loop(int): The times of test
    """
    with open(path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        if size > len(lines):
            print("The size is too large")
            raise BaseException
        accurate_nums = list()
        for i in range(loop):
            progress = LineProgress(title='Loop ' + str(i + 1))
            test_pos_list = np.random.randint(0, len(lines), size)
            test_words = [lines[pos].split()[0] for pos in test_pos_list]
            accurate_num = 0
            for index, test_word in enumerate(test_words):
                progress.update(index / size * 100)
                pin_yin = ' '.join([py_list[0] for py_list in pinyin(test_word, style=NORMAL)])
                prediction = Model.predict(pin_yin)
                count = 0
                for j in range(len(prediction)):
                    if prediction[j] == test_word[j]:
                        count += 1
                accurate_num += count / len(test_word)
            accurate_nums.append(accurate_num)
        print("The test accuracy is: {:.2f}%".format(sum(accurate_nums) / (size * loop) * 100))
