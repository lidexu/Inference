# -*- coding:utf-8 -*-

import os
import sys
import argparse
import json
import re

# get the class we need

def parse_args():
    parser = argparse.ArgumentParser(
        description='remove the input class'
    )
    parser.add_argument('--inputClass',
                        dest='inputClass',
                        default=None,
                        required=True,
                        help='input the class which needs to be removed from dataset',
                        type=str)
    parser.add_argument('--inputFile',
                        dest='inputFile',
                        default=None,
                        required=True,
                        help='input the base file',
                        type=str)
    args = parser.parse_args()
    return args

args=parse_args()

def getClassName(line=None):
    line_dict = json.loads(line)
    key = line_dict['url']
    if line_dict['label'] == None or len(line_dict['label'])==0:
        return key, None
    label_dict = line_dict['label'][0]
    if label_dict['data'] == None or len(label_dict['data'])==0:
        return key, None
    data_dict_list = label_dict['data']
    label_bbox_list_elementDict = []
    for bbox in data_dict_list:
        if 'class' not in bbox or bbox['class'] == None or len(bbox['class']) == 0:
            continue
        label_bbox_list_elementDict.append(bbox['class'])
    return label_bbox_list_elementDict

def process(classname=None, baseFile=None, saveFile=None):
    regex = re.compile(classname)

    classline_dict = []

    with open(baseFile, 'r') as f:
        for line in f.readlines():
            line = line.strip()
            if not line:
                continue
            label_classname_list = getClassName(line=line)

            counter = 0
            class_len = len(label_classname_list)

            for name in label_classname_list:
                match = regex.search(name)
                if match:
                    counter += 1

            if counter == class_len:
                classline_dict.append(line)
                #print(line)
    print(len(classline_dict))

    with open(saveFile, 'w') as fw:
        with open(baseFile, 'r') as fr:
            for line in fr.readlines():
                line = line.strip()
                #line_dict = json.loads(line)
                if line in classline_dict:
                    continue
                fw.write(line)
                fw.write('\n')

def main():
    args=parse_args()
    saveFile=args.inputFile + '-rmclass'
    process(classname=args.inputClass,
            baseFile=args.inputFile,
            saveFile=saveFile)
    pass

if __name__ == '__main__':
    main()







