# 拼音输入法——基于HMM模型

## 使用

通过`python3 typing.py`加命令的形式运行，命令如下：

* --input_file\\-in INPUT_FILE_NAME 用于指定输入文件（一行一句拼音）
* --output_file\\-out OUTPUT_FILE_NAME 用于指定输出文件（一行一句拼音翻译）
* --train\\-t 是否进行训练
* --interact\\-i 是否进入交互模式，进入后可手动在控制台输入一行拼音并得到反馈，通过`Ctrl+C`退出

## 算法基本思路与实现

本拼音输入法的算法主要集中为两部分，一部分为模型相关的，一部分为数据相关的。

* 数据相关算法

  数据相关算法主要用于对原始的训练文本数据进行提取、解析和整合，算法代码位于`utils.py`中，其中的相关函数及功能如下：

  * `is_chinese`

    用于判断输入的句子是否全部为中文，算法为通过中文的Unicode编码范围进行判断。

  * `process_json_data`

    通过将新浪新闻的JSON原始数据中的内容和标题进行提取，并通过中文常见的终止符，使用正则匹配进行句子切割，将每一个数据中的内容和标题切割为单句。进一步，将切割出的单句进行处理，将其中的非中文字符使用正则匹配去除，本操作由于具有并发性，通过多线程进行加速。最后，将得到的单句一句一行写入新的处理文件中

  * `concat_file`

    将所有的处理后的文件，附加上一个从jieba分词库中获得的词库`dict.txt`，合并为一个新文件作为训练数据。其中`dict.txt`的数据形式为`word frequency`的组织形式，对于每一个word，将其写入训练数据文件时，重复写入该word共frequency次，一次一行。

  * `process`

    通过`process_json_data`多线程同步处理所有原始数据，并调用`concat_file`拼接训练数据文件。

* 模型相关算法

  模型相关算法位于`HMM package`中的`model.py`中。该文件中定义了四个类，一个是模型操作的类`Model`，三个是对应的数据库类`Init`、`Emission`、`Transition`类。在本系统中，使用HMM（隐马尔可夫模型）作为预测模型，HMM有三个重要参数，分别是起始概率，发射概率和转移概率，这三张数据库表`Init`、`Emission`、`Transition`就分别用于存储三种参数。本系统采用SQLite作为数据库，一是考虑到其便携性，二是考虑到查询的性能，使用SQL的join查询能够快速地实现维特比算法。

  模型操作类`Model`中包括以下方法：

  * `init_database`

    调用时用于清空原数据库，并创建新数据库。

  * `insert`

    提供了通用的接口用于向三张表中插入数据。

  * `query_trans_emit`

    用于`Transition`和`Emission`表的联合查询，根据输入的`character`和`pin_yin`，能够查询到`Transition`中前一字符与`character`相同，后一字符发音为`pin_yin`的概率最大的情况。

  * `query_emit_init`

    用于`Init`和`Emission`表的联合查询，根据输入的`pin_yin`，能够查询到第一个字符发言为输入`pin_yin`的最大概率的`num`个汉字

  * `predict`

    实现了维特比算法寻找最优解，通过结合`query_emit_init`和`query_trans_emit`，根据输入拼音提供概率最大的可能解，当中途无解时，放弃拼音转汉字。

  * `train`系列函数

    通过统计训练数据文件的每一行的数据，包括起始字，每句拼音、字与字之间的转移概率，训练HMM，结果参数储存在数据库中。

