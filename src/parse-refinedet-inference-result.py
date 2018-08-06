# -*- coding:utf-8 -*-
# -*- coding:utf-8 -*-
import os
import sys
import json
import argparse
BK_LABEL_6 = {
    # 0: "background",
    1: "guns",
    2: "knives",
    3: "tibetan flag",
    4: "islamic flag",
    5: "isis flag"
    # 6: "not terror"
}
BK_LABEL_6_score = {
    # 0: "background",
    1: 0.7,
    2: 0.8,
    3: 0.7,
    4: 0.8,
    5: 0.8
    # 6: "not terror"
}
"""
    the script used to process refineDet
    这个脚本用于处理 refineDet res 18 处理的结果
    由于模型 只是打印出，预测的结果，并没有后续的处理。
    这里完成后续的处理
"""


def parse_args():
    parser = argparse.ArgumentParser(
        description="process res18 6 class detect result", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--inputDir', help='input file path', default=None, type=str)
    # 这里的 inputDir : /workspace/data/BK/processJH_Log_Dir/logFiles/20180403 
    return parser.parse_args()


def getFilePath_FileNameNotIncludePostfix(fileName=None):
    justFileName = os.path.split(fileName)[-1]
    filePath = os.path.split(fileName)[0]
    if '.' in justFileName:
        justFileName = justFileName[:justFileName.rfind('.')]
    return [filePath, justFileName, os.path.join(filePath, justFileName)]


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


def convertLine(line=None):
    # line : refineDet detection out
    # return : labelx format line
    new_line = None
#    print(line)
    try:
        line_dict = json.loads(line)
    except:
        return None
    url = line_dict['imagePath']
    bboxDataList = []
    for i, cls_i in enumerate(line_dict['cls']):
        if int(cls_i) not in BK_LABEL_6.keys():
            # print("WARNING : %s" % (line))
            continue
        score = line_dict['conf'][i]
        if score < BK_LABEL_6_score[int(cls_i)]:
            continue
        bbox_dict = dict()
        a_bbox = line_dict['bbox'][i]
        # a_bbox = [str(i) for i in a_bbox]
        xmin = a_bbox[0]
        ymin = a_bbox[1]
        xmax = a_bbox[2]
        ymax = a_bbox[3]
        bbox_dict['bbox'] = [[xmin, ymin], [
            xmax, ymin], [xmax, ymax], [xmin, ymax]]
        bbox_dict['class'] = BK_LABEL_6[int(cls_i)]
        bbox_dict["ground_truth"] = True
        bboxDataList.append(bbox_dict)
    if len(bboxDataList) <= 0:
        return new_line
    else:
        new_dict = createLabelxFormatDict(url=url, bboxDataList=bboxDataList)
        new_line = json.dumps(new_dict)
    return new_line


def process_One_File(fileName=None, saveFileOp=None):
    with open(fileName, 'r') as f:
        for line in f.readlines():
            line = line.strip()
            if len(line) <= 0:
                continue
            new_line = convertLine(line=line)
            if new_line == None:
                continue
            else:
                saveFileOp.write(new_line+'\n')
    pass
def getAllInferenceResult(folderPath=None, fileFlagBegin="split_file-", fileFlagEnd="-result.json"):
    result_file_list = []
    """
    	os.walk(top, topdown=True, onerror=None, followlinks=False)
    	可以得到一个三元tupple(dirpath, dirnames, filenames),
    	第一个为起始路径，第二个为起始路径下的文件夹，第三个是起始路径下的文件。
    	dirpath 是一个string，代表目录的路径，
    	dirnames 是一个list，包含了dirpath下所有子目录的名字。
    	filenames 是一个list，包含了非目录文件的名字(只是文件名字，没有路径信息)。
    	这些名字不包含路径信息，如果需要得到全路径，需要使用os.path.join(dirpath, name).
    	# print "parent is : "+ parent # parent 该文件的目录名称
    	# print "filename is : " + filename # filename 该文件的名称
    	# print "the full name of the file is : " + os.path.join(parent, filename) 
    	# 由路径名称+文件名称构成 绝对路径
    	"""
    for parent, dirnames, filenames in os.walk(folderPath):
        for filename in filenames:
            oneFileList = os.path.join(parent, filename)
            if filename.endswith(fileFlagEnd) and filename.startswith(fileFlagBegin):
                result_file_list.append(oneFileList)
    return result_file_list


def processAllInfereneFiles(folderName=None, saveFileOp=None):
    """
        这个函数是用于处理所有的单个结果小文件
    """
    all_result_file_list = getAllInferenceResult(folderPath=folderName)
    for i_file in all_result_file_list:
        print(i_file)
        process_One_File(fileName=i_file, saveFileOp=saveFileOp)
    pass


def main():
    args = parse_args()
    timeFlag = getFilePath_FileNameNotIncludePostfix(
        fileName=args.inputDir)[1]
    saveFileName = os.path.join(
        args.inputDir, timeFlag+'_labelxFormat-result.json')
    saveFileName_Op = open(saveFileName, 'w')
    processAllInfereneFiles(folderName=args.inputDir,
                            saveFileOp=saveFileName_Op)
    saveFileName_Op.close
    pass

if __name__ == '__main__':
    main()

