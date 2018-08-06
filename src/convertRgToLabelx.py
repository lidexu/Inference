# convert regression results to LabelX format according to thr config.py

# -*- coding:utf-8 -*-
#from lxml import etree
import os
import sys
import argparse
import json

from rfcn_dcn_config import rfcn_dcn_config as CONFIG

# convert 

def parse_args():
    parser = argparse.ArgumentParser(
        description='labelx convert to pascal voc toolkit'
    )
    """
        regression format :
        weiboimg-2017-11-17-10-28-aHR0cHM6Ly93dzEuc2luYWltZy5jbi9vcmozNjAvM2ZmNWVjYjdqdzFmMW05NXYzdHh2ajIwcW8wdzJ0aWQuanBn.jpg\t[{"index": 1, "score": 0.9603773355484009, "pts": [[0, 33], [318, 33], [318, 418], [0, 418]], "class": "person"}]
    """
    parser.add_argument('--inputFile',
                        dest='inputFile',
                        default=None,
                        required=True,
                        help='input file regression format',
                        type=str)
    # parser.add_argument('--vocAnnoDirPath',
    #                     dest='vocAnnoDirPath',
    #                     default=None,
    #                     required=True,
    #                     help='pascal vol format dataset annotation folder path',
    #                     type=int)
    args = parser.parse_args()
    return args


def createLabelxFormatDict(url=None, bboxDataList=None):
    """
        url : image url
        bboxDataList : list , 
                        element is : dict
                        element_dict : {
                                            "class": "label class name",
                                            "ground_truth": true,
                                            "bbox": [[xmin,ymin],[xmax,ymin],[xmax,ymax],[xmin,ymax]]
                                       }

        return : labelx_dict
    """
    labelx_dict = dict()
    labelx_dict['url'] = url
    labelx_dict['type'] = "image"
    one_dict = dict()
    one_dict['name'] = 'detect'
    one_dict['type'] = 'detection'
    one_dict['version'] = '1'
    one_dict['data'] = bboxDataList
    labelx_dict_label_list = []
    labelx_dict_label_list.append(one_dict)
    labelx_dict['label'] = labelx_dict_label_list
    return labelx_dict


def regressionFormat_2_labelxFormat(regressionLine=None):
    """
        input is : regression format line
        output is : labelx format line
    """
    image_url = regressionLine.split('\t')[0]
    imageName_or_url = 'http://oquqvdmso.bkt.clouddn.com/atflow-log-proxy/images/' + image_url
    rg_bboxs_line = regressionLine.split('\t')[-1]
    rg_bboxs_list = json.loads(rg_bboxs_line)
    labelx_bboxs_list = []
    for rg_i_bbox in rg_bboxs_list:

        cls_ind = rg_i_bbox['index']
        if rg_i_bbox['score'] < CONFIG['label_thresholds'][cls_ind]:
            continue
        class_name = CONFIG['labelx_dict'][cls_ind]

        labelx_bbox = dict()
        labelx_bbox['class'] = class_name
        labelx_bbox['bbox'] = rg_i_bbox['pts']
        labelx_bbox['ground_truth'] = True
        labelx_bboxs_list.append(labelx_bbox)
    if len(labelx_bboxs_list) == 0:
        return None
    labelx_dict = createLabelxFormatDict(url=imageName_or_url,
                                         bboxDataList=labelx_bboxs_list)
    return json.dumps(labelx_dict)


def process(rgFile=None):
    labelxResultFile = rgFile+"-labelx.json"
    with open(rgFile, 'r') as f, open(labelxResultFile,'w') as w_f:
        for line in f.readlines():
            line = line.strip()
            labelxFormatLine = regressionFormat_2_labelxFormat(regressionLine=line)
            if not labelxFormatLine:
                continue
            w_f.write(labelxFormatLine)
            w_f.write('\n')

    pass

def main():
    args = parse_args()
    process(rgFile = args.inputFile)
    pass


if __name__ == '__main__':
    main()
