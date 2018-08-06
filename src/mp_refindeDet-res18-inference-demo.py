# -*- coding:utf-8 -*-
import os
import sys
import argparse
import json
import numpy as np
import multiprocessing
import urllib
#sys.path.insert(0, "/workspace/data/BK/refineDet-Dir/RefineDet/python")
import cv2
import caffe
from google.protobuf import text_format
from caffe.proto import caffe_pb2
import time

"""
    the script used to process inference with multiprocess
"""


class Producer_Of_ImageNameQueue(multiprocessing.Process):
    def __init__(self, imageNameQueue, paramDictJsonStr, threadName):
        multiprocessing.Process.__init__(self)
        self.imageNameQueue = imageNameQueue
        self.paramDict = json.loads(paramDictJsonStr)
        self.threadName = threadName

    def getTimeFlag(self):
        return time.strftime("%Y:%m:%d:%H:%M:%S", time.localtime())

    def run(self):
        print("LOGINFO---%s---Thread %s begin running" %
              (self.getTimeFlag(), self.threadName))
        fileName = self.paramDict['inputFileName']
        beginIndex = int(self.paramDict['beginIndex'])
        with open(fileName, 'r') as f:
            for line in f.readlines()[beginIndex:]:
                line = line.strip()
                if len(line) <= 0:
                    continue
                self.imageNameQueue.put(line)
        for i in range(int(self.paramDict['imageDataProducerCount'])):
            self.imageNameQueue.put(None)
        print("LOGINFO---%s---Thread %s end" %
              (self.getTimeFlag(), self.threadName))
        pass


class Producer_Of_ImageDataQueue_And_consumer_Of_imageNameQueue(multiprocessing.Process):
    def __init__(self, imageNameQueue, imageDataQueue, paramDictJsonStr, threadName):
        multiprocessing.Process.__init__(self)
        self.imageNameQueue = imageNameQueue
        self.imageDataQueue = imageDataQueue
        self.paramDict = json.loads(paramDictJsonStr)
        self.urlFlag = True
        self.threadName = threadName

    def getTimeFlag(self):
        return time.strftime("%Y:%m:%d:%H:%M:%S", time.localtime())

    def readImage_fun(self, isUrlFlag=None, imagePath=None):
        """
            isUrlFlag == True , then read image from url
            isUrlFlag == False , then read image from local path
        """
        im = None
        if isUrlFlag == True:
            try:
                data = urllib.urlopen(imagePath.strip()).read()
                nparr = np.fromstring(data, np.uint8)
                if nparr.shape[0] < 1:
                    im = None
            except:
                im = None
            else:
                try:
                    im = cv2.imdecode(nparr, 1)
                except:
                    im = None
            finally:
                return im
        else:
            im = cv2.imread(imagePath, cv2.IMREAD_COLOR)
        if np.shape(im) == ():
            return None
        return im

    def run(self):
        print("LOGINFO---%s---Thread %s begin running" %(self.getTimeFlag(), self.threadName))
        # self.urlFlag=self.paramDict['urlFlag']
        timeout_count = 0
        while True:
            try:
                imagePath = self.imageNameQueue.get(block=True, timeout=120)
            except:
                print("%s : %s  get timeout" % (self.getTimeFlag(),self.threadName))
                timeout_count += 1
                if timeout_count >5:
                    print("LOGINFO---%s---Thread exception,so kill %s" %
                          (self.getTimeFlag(),self.threadName))
                    break
                continue
            else:
                if imagePath == None:
                    print("LOGINFO---%s---Thread %s Exiting" %(self.getTimeFlag(), self.threadName))
                    break
                imgData = self.readImage_fun(isUrlFlag=self.urlFlag, imagePath=imagePath)
                if np.shape(imgData) == () or len(np.shape(imgData)) != 3 or np.shape(imgData)[-1] != 3:
                    print("WARNING---%s---imagePath %s can't read" %(self.getTimeFlag(), imagePath))
                else:
                    self.imageDataQueue.put([imagePath, imgData])
                    pass
        self.imageDataQueue.put(None)
        print("LOGINFO---%s---Thread %s end" %(self.getTimeFlag(), self.threadName))
    pass


class Consumer_Of_ImageDataQueue_Inference(multiprocessing.Process):
    def __init__(self, imageDataQueue, paramDictJsonStr, threadName):
        multiprocessing.Process.__init__(self)
        self.imageDataQueue = imageDataQueue
        self.paramDict = json.loads(paramDictJsonStr)
        self.threadName = threadName
        self.saveFileOp = None
        self.gpuId = None
        self.modelFileName = None
        self.deployFileName = None
        self.labelFileName = None
        self.net = None
        self.label_list = None

    def getTimeFlag(self):
        return time.strftime("%Y:%m:%d:%H:%M:%S", time.localtime())

    def preInitial(self):
        self.saveFileOp = open(self.paramDict['saveResultFileName'], 'w')
        self.gpuId = int(self.paramDict['gpuId'])
        self.modelFileName = self.paramDict['modelFileName']
        self.deployFileName = self.paramDict['deployFileName']
        self.labelFileName = self.paramDict['labelFileName']
        self.image_size = self.paramDict['imagSize']

    def initalNetModel(self):
        caffe.set_mode_gpu()
        caffe.set_device(self.gpuId)
        self.net = caffe.Net(str(self.deployFileName),
                             str(self.modelFileName), caffe.TEST)
        with open(str(self.labelFileName), 'r') as f:
            self.label_list = caffe_pb2.LabelMap()
            text_format.Merge(str(f.read()), self.label_list)

    def preProcess(self, oriImage=None):
        img = cv2.resize(oriImage, (self.image_size, self.image_size))
        img = img.astype(np.float32, copy=False)
        img = img - np.array([[[103.52, 116.28, 123.675]]])
        img = img * 0.017
        img = img.astype(np.float32)
        img = img.transpose((2, 0, 1))
        return img

    def postProcess(self, output=None, imagePath=None, height=None, width=None):
        """
            postprocess net inference result
        """
        w = width
        h = height
        bbox = output[0, :, 3:7] * np.array([w, h, w, h])
        cls = output[0, :, 1]
        conf = output[0, :, 2]
        result_dict = dict()
        result_dict['bbox'] = bbox.tolist()
        result_dict['cls'] = cls.tolist()
        result_dict['conf'] = conf.tolist()
        result_dict['imagePath'] = imagePath
        self.saveFileOp.write(json.dumps(result_dict)+'\n')
        self.saveFileOp.flush()

    def inference_fun(self, orginalImgData=None, imagePath=None):
        imgDataHeight = orginalImgData.shape[0]
        imgDataWidth = orginalImgData.shape[1]
        imgData = self.preProcess(orginalImgData)
        self.net.blobs['data'].data[...] = imgData
        output = self.net.forward()
        self.postProcess(output=output['detection_out'][0], imagePath=imagePath,
                         height=imgDataHeight, width=imgDataWidth)

    def run(self):
        print("LOGINFO---%s---Thread %s begin running" %
              (self.getTimeFlag(), self.threadName))
        self.preInitial()
        self.initalNetModel()
        endGetImageDataThreadCount = 0
        time_out_count = 0
        while True:
            # print("debug : %s   %s" % (str(self.imageDataQueue.qsize()),
            #                            str(self.imageDataQueue.empty())))
            try:
                next_imageData = self.imageDataQueue.get(block=True, timeout=120)
            except :
                print("%s  get timeout" % (self.threadName))
                time_out_count += 1
                if endGetImageDataThreadCount >= self.paramDict['imageDataProducerCount'] or time_out_count >8:
                    print("LOGINFO---%s---Thread Exception so kill  %s " %
                          (self.getTimeFlag(), self.threadName))
                    break
                continue
            else:
                if next_imageData == None:
                    endGetImageDataThreadCount += 1
                    if endGetImageDataThreadCount >= self.paramDict['imageDataProducerCount']:
                        print("LOGINFO---%s---Thread %s Exiting" %(self.getTimeFlag(), self.threadName))
                        break
                else:
                    imagePath = next_imageData[0]
                    orginalImgData = next_imageData[1]
                    self.inference_fun(
                        orginalImgData=orginalImgData, imagePath=imagePath)
        print("LOGINFO---%s---Thread %s end" %
              (self.getTimeFlag(), self.threadName))
    pass


def parser_args():
    parser = argparse.ArgumentParser('bk detect caffe  refineDet model!')
    # url list file name
    parser.add_argument('--urlfileName', dest='urlfileName', help='url file name',
                        default=None, type=str, required=True)
    parser.add_argument('--urlfileName_beginIndex', dest='urlfileName_beginIndex', help='begin index in the url file name',
                        default=0, type=int)
    parser.add_argument('--gpu_id', dest='gpu_id', help='The GPU ide to be used',
                        default=0, type=int)

    parser.add_argument('--modelBasePath', required=True, dest='modelBasePath', help='Path to the model',
                        default=None, type=str)
    parser.add_argument('--modelName', required=True, dest='modelName', help='the name of the model',
                        default=None, type=str)
    parser.add_argument('--deployFileName', required=True, dest='deployFileName', help='deploy file name',
                        default=None, type=str)
    parser.add_argument('--labelFileName', required=True, dest='labelFileName', help='label file name',
                        default=None, type=str)
    return parser.parse_args()


def getFilePath_FileNameNotIncludePostfix(fileName=None):
    justFileName = os.path.split(fileName)[-1]
    filePath = os.path.split(fileName)[0]
    if '.' in justFileName:
        justFileName = justFileName[:justFileName.rfind('.')]
    return [filePath, justFileName, os.path.join(filePath, justFileName)]


def mainProcessFun(param_dict_JsonStr=None):
    param_dict = json.loads(param_dict_JsonStr)
    countOfgetUrlDataThread = param_dict['imageDataProducerCount']
    print("main process begin running")
    imageNameQueue = multiprocessing.Queue()
    imageDataQueue = multiprocessing.Queue()
    producer_Of_ImageNameQueue = Producer_Of_ImageNameQueue(
        imageNameQueue, param_dict_JsonStr, "producer_Of_ImageNameQueue-"+str(1))
    producer_Of_ImageNameQueue.daemon = True
    producer_Of_ImageNameQueue.start()
    time.sleep(10)
    threadList = []
    for i in range(1, countOfgetUrlDataThread+1):
        threadName = "producer_Of_ImageDataQue_And_consumer_Of_imageNameQueue-" + str(i)
        produce_and_consumer = Producer_Of_ImageDataQueue_And_consumer_Of_imageNameQueue(imageNameQueue, imageDataQueue, param_dict_JsonStr, threadName)
        threadList.append(produce_and_consumer)

    consumer_inference = Consumer_Of_ImageDataQueue_Inference(imageDataQueue, param_dict_JsonStr, "consumer_inference-"+str(1))

    for i_thread in threadList:
        i_thread.daemon = True
        i_thread.start()
    consumer_inference.start()
    time.sleep(10)
    producer_Of_ImageNameQueue.join()
    for i_thread in threadList:
        i_thread.join()
        # eval('produce_and_consumer-{}.join()'.format(i))
    consumer_inference.join()
    print("main process end")
    pass


args = parser_args()


def main():
    param_dict = dict()
    param_dict['inputFileName'] = args.urlfileName
    param_dict['beginIndex'] = args.urlfileName_beginIndex
    saveResultFileName = getFilePath_FileNameNotIncludePostfix(
        fileName=args.urlfileName)[-1]+'_'+str(args.urlfileName_beginIndex)+"-result.json"
    param_dict['saveResultFileName'] = saveResultFileName
    param_dict['modelFileName'] = os.path.join(
        args.modelBasePath, args.modelName)
    param_dict['deployFileName'] = os.path.join(
        args.modelBasePath, args.deployFileName)
    param_dict['labelFileName'] = os.path.join(
        args.modelBasePath, args.labelFileName)
    param_dict['gpuId'] = int(args.gpu_id)
    param_dict['imagSize'] = 320  # the image size into the model
    param_dict['imageDataProducerCount'] = 5  # one gpu, "urlProducerCount" get url data process
    # param_dict['urlFlag'] = True
    param_dict_JsonStr = json.dumps(param_dict)
    print(param_dict)
    mainProcessFun(param_dict_JsonStr=param_dict_JsonStr)
    pass


if __name__ == '__main__':
    main()

"""
test ::::

python mp_refindeDet-res18-inference-demo.py \
--urlfileName ../data/0331/test_url.list \
--modelBasePath /workspace/data/BK/terror-detect-Dir/refineDet-res18/models \
--modelName terror-res18-320x320-t2_iter_130000.caffemodel \
--deployFileName deploy.prototxt \
--labelFileName  labelmap_bk.prototxt  \
--gpu_id 0

nohup python -u mp_refindeDet-res18-inference-demo.py \
--urlfileName ../data/0331/normal_180318-0000 \
--modelBasePath /workspace/data/BK/terror-detect-Dir/refineDet-res18/models \
--modelName terror-res18-320x320-t2_iter_130000.caffemodel \
--deployFileName deploy.prototxt \
--labelFileName  labelmap_bk.prototxt  \
--gpu_id 0 \
> run.log 2> error.log &

"""

