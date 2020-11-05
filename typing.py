"""
Author: Hao Lin
Main entry point of the program
"""
from HMModel.model import HMModel
import os
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", "-t", action="store_true")
    parser.add_argument("--interact", "-i", action="store_true")
    parser.add_argument("--file", "-f", type=str)
    parser.add_argument("--output", "-o", type=str)
    parser.add_argument("--accuracy", "-a", action="store_true")
    parser.add_argument("--word_len", "-w", type=int)
    args = parser.parse_args()

    if args.word_len:
        HMModel.MAX_WORD_LEN = int(args.word_len)

    if args.train:
        if not os.path.exists('model'):
            os.mknod('model')
        HMModel.init()
        HMModel.train()

    if args.interact:
        print("This is an interactive console\n")
        try:
            while True:
                pinyin = input("Please input your pin yin here:")
                print(HMModel.translate(pinyin))
        except KeyboardInterrupt:
            print("\nGoodbye!")
            exit(0)

    if args.accuracy:
        HMModel.accuracy()

    if args.file:
        input_file = open(args.file, 'r', encoding='utf-8')
        if args.output:
            output_file = open(args.output, 'w', encoding='utf-8')
        else:
            output_file = open("out.txt", 'w', encoding='utf-8')
        lines = input_file.readlines()
        for line in lines:
            output_file.write(HMModel.translate(line) + '\n')
        input_file.close()
        output_file.close()