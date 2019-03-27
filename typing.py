from HMM.model import Model
import os
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_file", "-in", type=str)
    parser.add_argument("--output_file", "-out", type=str)
    parser.add_argument("--train", "-t", action="store_true")
    parser.add_argument("--interact", "-i", action="store_true")
    args = parser.parse_args()

    if args.train:
        if not os.path.exists('parameter'):
            os.mknod('parameter')
        Model.init_database()
        Model.train()

    if args.interact:
        try:
            while True:
                pinyin = input("input pinyin:")
                print(Model.predict(pinyin))
        except KeyboardInterrupt:
            print("\nSee you!")
            exit(0)

    if args.input_file and args.output_file:
        input_file = open(args.input_file, 'r', encoding='utf-8')
        output_file = open(args.output_file, 'w', encoding='utf-8')
        lines = input_file.readlines()
        for line in lines:
            output_file.write(Model.predict(line)+'\n')
        input_file.close()
        output_file.close()