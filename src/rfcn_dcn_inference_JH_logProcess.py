# -*- coding: utf-8 -*-
"""
rfcn-dcn-demo script
"""
import _init_paths
import argparse
import os
import sys
import logging
import pprint
import cv2
sys.path.insert(0, os.path.join('/opt/dcn', 'rfcn'))
#import rfcn._init_paths
from config.config import config, update_config
from utils.image import resize, transform
import numpy as np
os.environ['PYTHONUNBUFFERED'] = '1'
os.environ['MXNET_CUDNN_AUTOTUNE_DEFAULT'] = '0'
os.environ['MXNET_ENABLE_GPU_P2P'] = '0'
import mxnet as mx
from core.tester import im_detect, Predictor
from symbols import *
from utils.load_model import load_param
from utils.show_boxes import show_boxes
from utils.tictoc import tic, toc
from nms.nms import py_nms_wrapper, cpu_nms_wrapper, gpu_nms_wrapper
import random
import urllib
import json
import copy
import time
from rfcn_dcn_config_JH_logProcess import rfcn_dcn_config as RFCN_DCN_CONFIG

def parse_args():
    parser = argparse.ArgumentParser(description='rfcn-dcn-inference demo',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--imageListFile', help='local images  list file', default=None, type=str,required=True)
    # urlFlag : 0 ,local image , 1 url image
    parser.add_argument('--urlFlag', help='url flag', required=True,type=int, default=0)
    parser.add_argument('--gpuId', required=True,dest='gpuId', help='the id of gpu', type=int)
    # outputFileFlag : 1 是回归测试文件，2 是 labex 格式的输出文件
    parser.add_argument('--outputFileFlag', required=True,help='out put file flag', type=int)
    # 0 no visualize  , 1 visualize
    parser.add_argument('--visualizeFlag', help='visualize the detect reuslt', type=int, default=0)
    parser.add_argument('--beginLineNum',help='beginLineNum', type=int, default=0)
    args = parser.parse_args()
    return args


def readImage_fun(isUrlFlag=False, imagePath=None):
    im = None
    if isUrlFlag:
        try:
            data = urllib.urlopen(imagePath.strip()).read()
            nparr = np.fromstring(data, np.uint8)
            if nparr.shape[0] < 1:
                im = None
        except:
            print("Read Url Exception : %s" % (imagePath))
            im = None
        else:
            im = cv2.imdecode(nparr, 1)
        finally:
            return im
    else:
        im = cv2.imread(imagePath, cv2.IMREAD_COLOR)
    if np.shape(im) == ():
        print("waringing info : %s can't be read" % (imagePath))
        return None
    return im


def show_boxes_write_rg(fileOp=None, image_name=None, im=None, dets=None, classes=None, vis=None, scale=1.0):
    color_black = (0, 0, 0)
    # write to terror det rg tsv file
    imageName = image_name
    writeInfo = []
    for cls_idx, cls_name in enumerate(classes[1:], start=1):
        if cls_idx not in RFCN_DCN_CONFIG['need_label_dict'].keys():
            continue
        write_bbox_info = {}
        #write_bbox_info['class'] = cls_name
        write_bbox_info['class'] = RFCN_DCN_CONFIG['need_label_dict'][cls_idx]
        """
            change log : rg : result class name :
                guns_true->guns,knives_true->knives
        """
        write_bbox_info['index'] = cls_idx
        cls_dets = dets[cls_idx-1]
        # color = (random.randint(0, 256), random.randint(
        #     0, 256), random.randint(0, 256))
        for det in cls_dets:
            bbox = det[:4] * scale
            score = det[-1]
            if float(score) < RFCN_DCN_CONFIG['need_label_thresholds'][cls_idx]:
                continue
            bbox = map(int, bbox)
            one_bbox_write = copy.deepcopy(write_bbox_info)
            bbox_position_list = []
            bbox_position_list.append([bbox[0], bbox[1]])
            bbox_position_list.append([bbox[2], bbox[1]])
            bbox_position_list.append([bbox[2], bbox[3]])
            bbox_position_list.append([bbox[0], bbox[3]])
            one_bbox_write["pts"] = bbox_position_list
            # one_bbox_write["score"] = float(score)
            one_bbox_write["score"] = float(score)
            writeInfo.append(one_bbox_write)
            if vis is not None and im is not None:
                cv2.rectangle(
                    im, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color=color_black, thickness=3)
                cv2.putText(im, '%s %.3f' % (cls_name, score), (
                    bbox[0], bbox[1] + 15), color=color_black, fontFace=cv2.FONT_HERSHEY_COMPLEX, fontScale=0.5)
    fileOp.write("%s\t%s" % (imageName.split('/')[-1], json.dumps(writeInfo)))
    fileOp.write('\n')
    fileOp.flush()
    if vis is not None and im is not None:
        out_file = os.path.join(vis,
                                imageName.split('/')[-1])
        cv2.imwrite(out_file, im)
    pass


def show_boxes_write_labelx(fileOp=None, image_name=None, im=None, dets=None, classes=None, vis=False, scale=1.0):
    color_black = (0, 0, 0)
    # write to terror det rg tsv file
    imageName = image_name
    writeInfo = dict()
    writeInfo['url'] = image_name
    writeInfo['type'] = "image"
    label_list = []
    label_list_element_dict=dict()
    bbox_list = []
    # color = (random.randint(0, 256), random.randint(
    #     0, 256), random.randint(0, 256))
    for cls_idx, cls_name in enumerate(classes[1:], start=1):
        if cls_idx not in RFCN_DCN_CONFIG['need_label_dict'].keys():
            continue
        cls_dets = dets[cls_idx-1]
        for det in cls_dets:
            bbox = det[:4] * scale
            score = det[-1]
            if float(score) < RFCN_DCN_CONFIG['need_label_thresholds'][cls_idx]:
                continue
            bbox = map(int, bbox)
            one_bbox = dict()
            one_bbox['class'] = cls_name
            pts_list = []
            pts_list.append([bbox[0], bbox[1]])
            pts_list.append([bbox[2], bbox[1]])
            pts_list.append([bbox[2], bbox[3]])
            pts_list.append([bbox[0], bbox[3]])
            one_bbox["bbox"] = pts_list
            one_bbox['ground_truth'] = True
            bbox_list.append(one_bbox)
            if vis is not None and im is not None:
                cv2.rectangle(
                    im, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color=color_black, thickness=3)
                cv2.putText(im, '%s %.3f' % (cls_name, score), (
                    bbox[0], bbox[1] + 15), color=color_black, fontFace=cv2.FONT_HERSHEY_COMPLEX, fontScale=0.5)
    if len(bbox_list) > 0:
        label_list_element_dict['name'] = 'detect'
        label_list_element_dict['type'] = 'detection'
        label_list_element_dict['version'] = '1'
        label_list_element_dict['data'] = bbox_list
        label_list.append(label_list_element_dict)
        writeInfo['label'] = label_list
        fileOp.write("%s" % (json.dumps(writeInfo)))
        fileOp.write('\n')
        fileOp.flush()
    if vis is not None and im is not None:
        out_file = os.path.join(vis,
                                imageName.split('/')[-1])
        out_file = out_file[:out_file.rfind('.')]+'.jpg'
        cv2.imwrite(out_file, im)
    pass


def show_boxes(isUrlFlag=None, im_name=None, dets=None, classes=None, scale=1, vis=None, fileOp=None, flag=1):
    im = None
    if vis is not None:
        im = readImage_fun(isUrlFlag=isUrlFlag, imagePath=im_name)
    if flag == 1:
        show_boxes_write_rg(fileOp=fileOp, image_name=im_name,
                            im=im, dets=dets, classes=classes, vis=vis)
    elif flag == 2:
        show_boxes_write_labelx(fileOp=fileOp, image_name=im_name,
                                im=im, dets=dets, classes=classes, vis=vis)
    pass


min_threshold = min(list(RFCN_DCN_CONFIG['need_label_thresholds'].values()))


def process_one_batch_images_fun(isUrlFlag=False, one_batch_images_list=None, init_model_param=None, fileOp=None, vis=None):
    num_classes = RFCN_DCN_CONFIG['num_classes']  # 0 is background,
    classes = RFCN_DCN_CONFIG['num_classes_name_list']
    image_names = one_batch_images_list
    if len(image_names) <= 0:
        return
    all_can_read_image = []
    data = []
    for im_name in image_names:
        #print("process : %s"%(im_name))
        im = readImage_fun(isUrlFlag=isUrlFlag, imagePath=im_name)
        # 判断 这个图片是否可读
        if np.shape(im) == ():
            print("ReadImageError : %s" % (im_name))
            continue
        if im.shape[2] != 3:
            print("%s channel is not 3" % (im_name))
            continue
        all_can_read_image.append(im_name)
        target_size = config.SCALES[0][0]
        max_size = config.SCALES[0][1]
        im, im_scale = resize(im, target_size, max_size,
                              stride=config.network.IMAGE_STRIDE)
        im_tensor = transform(im, config.network.PIXEL_MEANS)
        im_info = np.array(
            [[im_tensor.shape[2], im_tensor.shape[3], im_scale]], dtype=np.float32)
        data.append({'data': im_tensor, 'im_info': im_info})

    # get predictor
    data_names = ['data', 'im_info']
    label_names = []
    data = [[mx.nd.array(data[i][name]) for name in data_names]
            for i in xrange(len(data))]
    max_data_shape = [[('data', (1, 3, max(
        [v[0] for v in config.SCALES]), max([v[1] for v in config.SCALES])))]]
    provide_data = [[(k, v.shape) for k, v in zip(data_names, data[i])]
                    for i in xrange(len(data))]
    provide_label = [None for i in xrange(len(data))]

    predictor = Predictor(init_model_param[0], data_names, label_names,
                          context=[mx.gpu(int(args.gpuId))], max_data_shapes=max_data_shape,
                          provide_data=provide_data, provide_label=provide_label,
                          arg_params=init_model_param[1], aux_params=init_model_param[2])
    nms = gpu_nms_wrapper(config.TEST.NMS, 0)

    for idx, im_name in enumerate(all_can_read_image):
        data_batch = mx.io.DataBatch(data=[data[idx]], label=[], pad=0, index=idx, provide_data=[
                                     [(k, v.shape) for k, v in zip(data_names, data[idx])]], provide_label=[None])
        scales = [data_batch.data[i][1].asnumpy()[0, 2]
                  for i in xrange(len(data_batch.data))]

        tic()
        scores, boxes, data_dict = im_detect(
            predictor, data_batch, data_names, scales, config)
        boxes = boxes[0].astype('f')
        scores = scores[0].astype('f')
        dets_nms = []
        for j in range(1, scores.shape[1]):
            cls_scores = scores[:, j, np.newaxis]
            cls_boxes = boxes[:,
                              4:8] if config.CLASS_AGNOSTIC else boxes[:, j * 4:(j + 1) * 4]
            cls_dets = np.hstack((cls_boxes, cls_scores))
            keep = nms(cls_dets)
            cls_dets = cls_dets[keep, :]
            cls_dets = cls_dets[cls_dets[:, -1] > min_threshold, :]
            dets_nms.append(cls_dets)
        print('testing {} {:.4f}s'.format(im_name, toc()))
        show_boxes(isUrlFlag=isUrlFlag, im_name=im_name, dets=dets_nms,
                   classes=classes, scale=1, vis=vis, fileOp=fileOp, flag=args.outputFileFlag)
    print('process one batch images done')
    pass


def init_detect_model():
    # get symbol
    pprint.pprint(config)
    config.symbol = 'resnet_v1_101_rfcn_dcn'
    sym_instance = eval(config.symbol + '.' + config.symbol)()
    sym = sym_instance.get_symbol(config, is_train=False)
    arg_params, aux_params = load_param(
        os.path.join(RFCN_DCN_CONFIG['modelParam']['modelBasePath'], 'rfcn_voc'), RFCN_DCN_CONFIG['modelParam']['epoch'], process=True)
    return [sym, arg_params, aux_params]


def process_image_fun(urlFlag=None, imagesPath=None, fileOp=None, vis=None):
    if urlFlag == 0:
        isUrlFlag = False # local image
    elif urlFlag == 1:
        isUrlFlag = True  # url image
    # init rfcn dcn detect model (mxnet)
    model_params_list = init_detect_model()
    beginCount = args.beginLineNum
    endCount = beginCount
    for i in range(len(imagesPath)/int(RFCN_DCN_CONFIG['one_batch_size'])):
        endCount += int(RFCN_DCN_CONFIG['one_batch_size'])
        tempFileList = imagesPath[beginCount:endCount]
        process_one_batch_images_fun(
            isUrlFlag=isUrlFlag, one_batch_images_list=tempFileList, init_model_param=model_params_list, fileOp=fileOp, vis=vis)
        print("line %d process done" % (endCount))
        beginCount = endCount
    tempFileList = imagesPath[beginCount:]
    process_one_batch_images_fun(
        isUrlFlag=isUrlFlag, one_batch_images_list=tempFileList, init_model_param=model_params_list, fileOp=fileOp, vis=vis)
    print("the file  process done")
    pass

def main():
    update_config(RFCN_DCN_CONFIG["config_yaml_file"])
    time_str = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    visualizeOutPutPath = None
    if int(args.visualizeFlag) == 1:
        visualizeOutPutPath = os.path.join(
            os.path.dirname(args.imageListFile), "visDraw-"+time_str)
        if not os.path.exists(visualizeOutPutPath):
            os.makedirs(visualizeOutPutPath)
    outputFilePath = args.imageListFile+"-result-"+str(args.outputFileFlag)+'-'+time_str
    fileOp = open(outputFilePath, 'a+')  # 追加的方式，如果不存在就创建
    need_process_images_path_list = []
    with open(args.imageListFile,'r') as f:
        for line in f.readlines():
            line = line.strip()
            if len(line) == 0:
                continue
            need_process_images_path_list.append(line)
    process_image_fun(urlFlag=args.urlFlag,
                      imagesPath=need_process_images_path_list, fileOp=fileOp, vis=visualizeOutPutPath)

args = parse_args()
if __name__ == '__main__':
    print(args)
    main()

"""
python rfcn_dcn_inference.py \
--imageListFile /workspace/data/BK/terror-online-0420/test-0426.list \
--urlFlag 1 \
--gpuId 0  \
--outputFileFlag 2 \
--visualizeFlag 1 \
"""

