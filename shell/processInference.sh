#!/bin/bash
# set -x
if [ ! -n "$1" ]
then
    echo "must input file path"
    exit
else
    echo "the input file is : "$1
fi
scriptFile="../src/mp_refindeDet-res18-inference-demo.py"
inputFile=$1
splitFilePrefix="split_file-"
# gpu id  used to run
gpuArray=(0 1 2 3 4 5 6 7)
#gpuArray=(5 6 7)
# gpuNum=${#gpuArray[@]}
gpuNum=`nvidia-smi | grep Tesla | wc -l`
# inputfile
inputBasePath=`dirname $inputFile`
inputFileName=`basename $inputFile`
# split the input file by gpuNum
inputFileLineCount=`wc -l $inputFile|awk '{print $1}'`
perFileLineCount=`expr $inputFileLineCount / $gpuNum`
perFileLineCount_flag=`expr $inputFileLineCount % $gpuNum`
if [ $perFileLineCount_flag -ne 0 ]
then
    perFileLineCount=`expr $perFileLineCount + 1`
fi
echo "perFileLineCount : "$perFileLineCount
# split
split_output_prefix=$inputBasePath"/"$splitFilePrefix
split -l $perFileLineCount $inputFile -d -a 2 $split_output_prefix
# get split result file
splitFileArray=()
tempFileList=`ls $inputBasePath`
for file in $tempFileList
do
    if [[ $file == $splitFilePrefix* ]]
    then
        if [[ $file == *"result.json" ]] || [[ $file == *"run.log" ]] || [[ $file == *"stderr.log" ]]
        then
            echo "don't process the file : "$file
        else
            tempFile=$inputBasePath"/"$file
            splitFileArray=(${splitFileArray[*]} $tempFile)
        fi
    fi
done

# check
if [ $gpuNum -ne ${#splitFileArray[@]} ]
then
    echo "ERROR : log file count unequal gpu count"
    exit
fi


modelBasePath="/workspace/data/BK/models/refineDet-res18"
modelName="terror-res18-320x320-t2_iter_130000.caffemodel"
deployName="deploy.prototxt"
labelName="labelmap_bk.prototxt"
for(( i=0;i<$gpuNum;i++))
do
    echo "gpu id is : "${gpuArray[i]}
    echo "log file is : "${splitFileArray[i]}
    runCmd="nohup python -u "$scriptFile" \
    --urlfileName "${splitFileArray[i]}" \
    --modelBasePath "$modelBasePath" \
    --modelName "$modelName" \
    --deployFileName "$deployName" \
    --labelFileName "$labelName" --gpu_id "${gpuArray[i]}"  \
    > "${splitFileArray[i]}"_run.log \
    2> "${splitFileArray[i]}"_stderr.log &"
    echo $runCmd
    `eval $runCmd`
done
