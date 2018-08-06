# -*- coding:utf-8 -*-
import sys
import os
import json
import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        description='md5 process'
    )
    parser.add_argument('--labelxFile',
                        dest='labelxFile',
                        default=None,
                        required=True,
                        help='',
                        type=str)
    parser.add_argument('--md5File',
                        dest='md5File',
                        default=None,
                        required=True,
                        help='',
                        type=str)
    args = parser.parse_args()
    return args
     

md5Lib = "/workspace/data/BK/src/TERROR-DETECT-IMAGE-MD5.txt"
args = parse_args()

def convert_md5ValueFile(file=None):
    url_md5_dict = dict()
    with open(file,'r') as f:
        value = json.load(f)
        for key in value:
            url_md5_dict[key] = value[key]['md5']
    return url_md5_dict


def getMd5LibraryDict(md5LibFile=None):
    md5_library_dict = dict()
    with open(md5LibFile,'r') as f:
        for line in f.readlines():
            line = line.strip()
            if not line:
                continue
            line_list = line.split('\t')
            assert (len(line_list) == 2)
            assert(line_list[0] not in md5_library_dict)
            md5_library_dict[line_list[0]] = int(line_list[1])
    return md5_library_dict

def processMd5File(md5Lib=None,labelxFile=None,md5ValueFile=None,outputFile=None):
    url_md5_dict = convert_md5ValueFile(file=md5ValueFile)
    md5_library_dict = getMd5LibraryDict(md5LibFile=md5Lib)
    with open(labelxFile, 'r') as labelxFile_f, open(outputFile,'w') as output_f:
        for line in labelxFile_f.readlines():
            line = line.strip()
            if not line:
                continue
            url = json.loads(line)['url']
            md5OfUrl = url_md5_dict[url]
            if md5OfUrl in md5_library_dict: # the md5 of the url image already in md5 library
                md5_library_dict[md5OfUrl] += 1
                pass
            else:
                md5_library_dict[md5OfUrl] = 1
                output_f.write(line+'\n')
    with open(md5Lib,'w') as f:
        for key in md5_library_dict:
            line = key+'\t'+str(md5_library_dict[key])
            f.write(line+'\n')
    pass
def main():
    outputFile = args.labelxFile+"-md5Processed.json"
    processMd5File(md5Lib=md5Lib, labelxFile=args.labelxFile,
                   md5ValueFile=args.md5File, outputFile=outputFile)
    pass

if __name__ == '__main__':
    main()

