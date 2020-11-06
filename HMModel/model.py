"""
Author: Hao Lin
HMM Model class
"""
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pypinyin import *
from utils import *
from eprogress import LineProgress
import numpy as np
import os
import jieba

"""
HMM Model Class
"""


class HMModel:
    # SQLite engine
    engine = create_engine('sqlite:///model')
    base = declarative_base()
    Session = sessionmaker(bind=engine)
    session = Session()
    MAX_WORD_LEN = 5

    @classmethod
    def init(cls):
        cls.base.metadata.drop_all(cls.engine)
        cls.base.metadata.create_all(bind=cls.engine,
                                     tables=[Transition.__table__, Initial.__table__, Emission.__table__])

    @classmethod
    def __translate(cls, input, prev=''):
        """
        The actual function of translation, which works in a recursion manner
        Args:
            input(list): the input pinyin, split into a list
            prev(str): the previous character or word
        Returns:
            result(dict): dictionary of {sentences: probabilities}
        """
        if len(input) == 0:
            return {"": 0}

        result = dict()
        for i in range(min(cls.MAX_WORD_LEN, len(input)) - 1, -1, -1):
            new_input = [' '.join(input[:i + 1])] + input[i + 1:]
            if prev == '':
                sen_prob = dict(cls.query_emit_init(new_input[0]))
            else:
                sen_prob = cls.query_trans_emit(prev.split('/')[-1], new_input[0])
                if sen_prob is None:
                    return {None: 0}
                else:
                    sen_prob = {sen_prob[0]: sen_prob[1]}
            is_prune = False
            for sentence, prob in sen_prob.items():
                if (prob == 0 and sen_prob is not None) or len(sen_prob) == 1:
                    is_prune = True
                successive_prob = cls.__translate(new_input[1:], sentence)
                if successive_prob.get(None, None) is not None:
                    successive_prob = cls.__translate(new_input[1:])
                for successive, s_prob in successive_prob.items():
                    if successive is None:
                        continue
                    result[sentence + '/' + successive] = prob + s_prob
            if is_prune:
                break
        if len(result) == 0:
            return {None: 0}
        result = sorted(result.items(), key=lambda item: item[1], reverse=True)
        result = {result[0][0]: result[0][1]}
        return result

    @classmethod
    def translate(cls, input):
        """
        Predicting the possible Chinese of given input using the viterbi algorithm
        Args:
            input(str)
        Returns:
            result(str)
        """
        input = input.split()
        if len(input) == 0:
            return ""
        result = cls.__translate(input)
        prob = sorted(result.items(), key=lambda item: item[1], reverse=True)
        if len(prob) == 0:
            return ""
        if prob[0][0] is None:
            return ''
        return ''.join(prob[0][0].split("/"))

    @classmethod
    def train(cls, path='./Data/data.data'):
        """
        Args:
            path(str): the directory path for training data
        """
        if not os.path.exists(path):
            process()
        data_lines = open(path, 'r', encoding='utf-8').readlines()
        cls.__train_init(data_lines)
        cls.__train_emission(data_lines)
        cls.__train_transition(data_lines)

    @classmethod
    def accuracy(cls, path='./Data/test.txt', size=1000, rounds=5):
        """
        Test the model accuracy
        Args:
            path(str): path of test data
            size(int): size of test data
            rounds(int): rounds of test
        """
        with open(path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            if size > len(lines):
                print("The size is too large")
                raise BaseException
            accuracy_count = list()
            for i in range(rounds):
                progress = LineProgress(title='Round ' + str(i + 1))
                positives = np.random.randint(0, len(lines), size)
                words = [lines[pos].split()[0] for pos in positives]
                accurate_num = 0
                for index, word in enumerate(words):
                    progress.update(index / size * 100)
                    pin_yin = ' '.join([py_list[0] for py_list in pinyin(word, style=NORMAL)])
                    prediction = HMModel.translate(pin_yin)
                    count = 0
                    for j in range(len(prediction)):
                        if prediction[j] == word[j]:
                            count += 1
                    accurate_num += count / len(word)
                accuracy_count.append(accurate_num)
            print("The test accuracy is: {:.2f}%".format(sum(accuracy_count) / (size * rounds) * 100))

    @classmethod
    def insert(cls, table, **args):
        """
        Insert data into database
        Args:
            table: database of parameters
            args(dict): arguments
        """
        # noinspection PyArgumentList
        cls.session.add(table(**args))
        cls.session.commit()

    @classmethod
    def query_trans_emit(cls, character, pin_yin):
        """
        Transition table joined by Emission
        Args:
             character(str)
             pin_yin(str)
        """
        result = cls.session.query(Transition.next_char, Emission.prob + Transition.prob). \
            join(Emission, Emission.character == Transition.next_char). \
            filter(Transition.prev_char == character). \
            filter(Emission.pin_yin == pin_yin). \
            order_by(desc(Emission.prob + Transition.prob))
        result = result.first()
        cls.session.commit()
        return result

    @classmethod
    def query_emit_init(cls, pin_yin, num=5):
        """
        Emission table joined by transition
        Args:
            pin_yin(str)
            num(int)
        """
        result = cls.session.query(Emission.character, Emission.prob + Initial.prob). \
            join(Initial, Emission.character == Initial.character). \
            filter(Emission.pin_yin == pin_yin). \
            order_by(desc(Emission.prob + Initial.prob)). \
            limit(num).all()
        cls.session.commit()
        return result

    @classmethod
    def __train_init(cls, char_lines):
        """
        Train init parameter
        Args:
             char_lines(list): content list of training data
        """
        print('Begin training init parameter...')
        length = len(char_lines)
        progress = LineProgress(title='Training initials')
        count = 0
        char_prob = dict()
        for line in char_lines:
            count += 1
            progress.update(count * 100 / length)
            line = line.strip()
            line, data_type = line.split()[0], line.split()[1]
            if data_type == 'S':
                line = list(jieba.cut(line))
            if len(line) == 0:
                continue
            if not is_chinese(line[0]):
                continue
            char_prob[line[0]] = char_prob.get(line[0], 0) + 1
            if data_type == "W":
                char_prob[line] = char_prob.get(line, 0) + 1

        print('\nInserting into database...')
        for character, prob in char_prob.items():
            # noinspection PyTypeChecker
            cls.insert(Initial, character=character, prob=float(np.log(prob / length)))
        print('Done training init parameter')

    @classmethod
    def __train_emission(cls, char_lines):
        """
        Train emission parameter
        Args:
            char_lines(list): content list of training data
        """
        print('Begin training emission parameter...')
        length = len(char_lines)
        progress = LineProgress(title='Training emission')
        count = 0
        char_pinyin_prob = dict()
        for line in char_lines:
            count += 1
            progress.update(count * 100 / length)
            line = line.strip()
            line, data_type = line.split()[0], line.split()[1]
            if data_type == 'S':
                line = list(jieba.cut(line))
            if len(line) == 0:
                continue
            if not is_chinese(line):
                continue
            if data_type == 'S':
                pinyin_list = [pinyin(word, style=NORMAL) for word in line]
            else:
                pinyin_list = pinyin(line, style=NORMAL)
            for character, pinyin_s in zip(line, pinyin_list):
                pinyin_prob = char_pinyin_prob.get(character, dict())
                pin_yin = ' '.join([py[0] for py in pinyin_s])
                pinyin_prob[pin_yin] = pinyin_prob.get(pin_yin, 0) + 1
                if data_type == 'W':
                    for pin_yin in pinyin_s:
                        pinyin_prob[pin_yin] = pinyin_prob.get(pin_yin, 0) + 1
                char_pinyin_prob[character] = pinyin_prob

        print('\nInserting into database...')
        for character, pinyin_prob in char_pinyin_prob.items():
            for pin_yin, prob in pinyin_prob.items():
                # noinspection PyTypeChecker
                cls.insert(Emission, character=character, pin_yin=pin_yin,
                           prob=float(np.log(prob / sum(pinyin_prob.values()))))
        print('Done training emission parameter')

    @classmethod
    def __train_transition(cls, char_lines):
        """
        Train emission parameter
        Args:
            char_lines(list): content list of training data
        """
        print('Begin training transition parameter...')
        length = len(char_lines)
        progress = LineProgress(title='Training transition')
        count = 0
        prev_next_prob = dict()
        for line in char_lines:
            count += 1
            progress.update(count * 100 / length)
            line = line.strip()
            line, data_type = line.split()[0], line.split()[1]
            if data_type == 'S':
                line = list(jieba.cut(line))
            if len(line) <= 1:
                continue
            if not is_chinese(line):
                continue
            for prev_char, next_char in zip(line[:-1], line[1:]):
                next_prob = prev_next_prob.get(prev_char, dict())
                next_prob[next_char] = next_prob.get(next_char, 0) + 1
                prev_next_prob[prev_char] = next_prob

        print('\nInserting into database...')
        for prev_char, next_prob in prev_next_prob.items():
            for next_char, prob in next_prob.items():
                # noinspection PyTypeChecker
                cls.insert(Transition, prev_char=prev_char, next_char=next_char,
                           prob=float(np.log(prob / sum(next_prob.values()))))
        print('Done training transition parameter')


"""
Table for initial parameter
"""


class Initial(HMModel.base):
    __tablename__ = 'INIT'

    id = Column(Integer, primary_key=True, autoincrement=True)
    character = Column(String(20), nullable=False, index=True)
    prob = Column(Float, nullable=false, index=True)


"""
Table for emission parameter
"""


class Emission(HMModel.base):
    __tablename__ = 'EMISSION'

    id = Column(Integer, primary_key=True, autoincrement=True)
    character = Column(String(20), nullable=false, index=True)
    pin_yin = Column(String(20), nullable=false, index=True)
    prob = Column(Float, nullable=False, index=True)


"""
Table for transition parameter
"""


class Transition(HMModel.base):
    __tablename__ = 'TRANSITION'

    id = Column(Integer, primary_key=True, autoincrement=True)
    prev_char = Column(String(20), nullable=false, index=True)
    next_char = Column(String(20), nullable=false, index=True)
    prob = Column(Float, nullable=False, index=True)
