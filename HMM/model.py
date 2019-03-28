from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pypinyin import *
from utils import *
from eprogress import LineProgress
import numpy as np
import os


class Model:
    engine = create_engine('sqlite:///parameter')
    base = declarative_base()
    Session = sessionmaker(bind=engine)
    session = Session()

    @classmethod
    def init_database(cls):
        cls.base.metadata.drop_all(cls.engine)
        cls.base.metadata.create_all(bind=cls.engine, tables=[Transition.__table__, Init.__table__, Emission.__table__])

    @classmethod
    def insert(cls, to_table, **args):
        """
        Insert data into database
        Args:
            to_table: database of parameters
            args(dict): arguments
        """
        # noinspection PyArgumentList
        cls.session.add(to_table(**args))
        cls.session.commit()

    @classmethod
    def query_trans_emit(cls, character, pin_yin):
        """
        Query transition table joined by Emission
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
        Query the joined table of emission and transition
        Args:
            pin_yin(str)
            num(int)
        """
        result = cls.session.query(Emission.character, Emission.prob + Init.prob). \
            join(Init, Emission.character == Init.character). \
            filter(Emission.pin_yin == pin_yin). \
            order_by(desc(Emission.prob + Init.prob)). \
            limit(num).all()
        cls.session.commit()
        return result

    @classmethod
    def predict(cls, pinyin_input):
        """
        Implement the viterbi algorithm
        Args:
            pinyin_input(str)
        Returns:
            result(str)
        """
        pinyin_input = pinyin_input.split()
        if len(pinyin_input) == 0:
            return ""
        sentence_prob = dict(cls.query_emit_init(pinyin_input[0]))
        for pin_yin in pinyin_input[1:]:
            new_sentence_prob = dict()
            for sentence, prob in sentence_prob.items():
                predict = cls.query_trans_emit(sentence[-1], pin_yin)
                if predict is None:
                    continue
                next_char, next_prob = predict
                new_sentence_prob[sentence + next_char] = prob + next_prob

            if new_sentence_prob:
                sentence_prob = new_sentence_prob
            else:
                break
        sorted_prob = sorted(sentence_prob.items(), key=lambda item: item[1], reverse=True)
        if len(sorted_prob) == 0:
            return ""
        return sorted_prob[0][0]

    @classmethod
    def train(cls, path='./Data/data.data', ):
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
    def __train_init(cls, data_lines):
        """
        Train init parameter
        Args:
             data_lines(list): content list of training data
        """
        print('Begin training init parameter...')
        length = len(data_lines)
        progress = LineProgress(title='Training init')
        count = 0
        char_prob = dict()
        for line in data_lines:
            count += 1
            progress.update(count * 100 / length)
            line = line.strip()
            if len(line) == 0:
                continue
            if not is_chinese(line[0]):
                continue
            char_prob[line[0]] = char_prob.get(line[0], 0) + 1

        print('\nInserting into database...')
        for character, prob in char_prob.items():
            # noinspection PyTypeChecker
            cls.insert(Init, character=character, prob=float(np.log(prob / length)))
        print('Done training init parameter')

    @classmethod
    def __train_emission(cls, data_lines):
        """
        Train emission parameter
        Args:
            data_lines(list): content list of training data
        """
        print('Begin training emission parameter...')
        length = len(data_lines)
        progress = LineProgress(title='Training emission')
        count = 0
        char_pinyin_prob = dict()
        for line in data_lines:
            count += 1
            progress.update(count * 100 / length)
            line = line.strip()
            if len(line) == 0:
                continue
            if not is_chinese(line):
                continue
            pinyin_list = pinyin(line, style=NORMAL, heteronym=True)
            for character, pinyin_s in zip(line, pinyin_list):
                pinyin_prob = char_pinyin_prob.get(character, dict())
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
    def __train_transition(cls, data_lines):
        """
        Train emission parameter
        Args:
            data_lines(list): content list of training data
        """
        print('Begin training transition parameter...')
        length = len(data_lines)
        progress = LineProgress(title='Training transition')
        count = 0
        prev_next_prob = dict()
        for line in data_lines:
            count += 1
            progress.update(count * 100 / length)
            line = line.strip()
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


class Init(Model.base):
    """
    Database for init parameter
    """
    __tablename__ = 'INIT'

    id = Column(Integer, primary_key=True, autoincrement=True)
    character = Column(String(1), nullable=False, index=True)
    prob = Column(Float, nullable=false, index=True)


class Emission(Model.base):
    """
    Database for emission parameter
    """
    __tablename__ = 'EMISSION'

    id = Column(Integer, primary_key=True, autoincrement=True)
    character = Column(String(1), nullable=false, index=True)
    pin_yin = Column(String(10), nullable=false, index=True)
    prob = Column(Float, nullable=False, index=True)


class Transition(Model.base):
    """
    Database for transition parameter
    """
    __tablename__ = 'TRANSITION'

    id = Column(Integer, primary_key=True, autoincrement=True)
    prev_char = Column(String(1), nullable=false, index=True)
    next_char = Column(String(1), nullable=false, index=True)
    prob = Column(Float, nullable=False, index=True)
