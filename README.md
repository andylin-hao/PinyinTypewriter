# An HMM Model-based Pinyin Typewriter

## Usages

Generally you can run the program by `python3 typing.py [-i|t|f|o|a|w params]`. 

* ``--file/-f INPUT_FILE_NAME`` is used to specify the input file, where each line is a pinyin sentence
* ``--output/-o OUTPUT_FILE_NAME`` is used to specify the output file, default to ``out.txt``
* ``--train/-t`` will retrain the model 
* ``--interact/-i`` will enter the interactive mode where you can type pinyin and get results immediately; type `Ctrl+C` to exit
* ``--accuracy/-a`` will run accuracy test
* ``--word_len/-w LENGTH`` will set the word model used to generate results. For example, type ``2`` and we will deem the length of a word is at most two Chinese characters