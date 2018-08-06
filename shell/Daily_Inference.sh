#!/usr/bin/env bash
# BK检测日常推理
# 输入日期进行日常推理
# 要判断是否发生中断

set -x

if [ ! -n "$1" ]
then
    echo "must input a Date"
    exit
else
    echo "the input Data is :"$1
fi

Task_date=$1

Filename=${Task_date}".log"

if [ -e ${Filename} ]; then
    echo "File exists! Interruption!"
else
    echo "No Interruption!"
    echo "0" > ${Filename}
fi

save_path="/workspace/data/BK/logFiles"

goto_step()
{
    if [ $1 -eq 0 ]; then
        echo "1" >$Filename

    elif [ $1 -eq 1 ]; then
        echo "Download data:"
        ./downloadUrlFile.sh $Task_date
        echo "2" >$Filename
    elif [ $1 -eq 2 ]; then
        echo "Run RefineDet inference"
        refineDir=${save_path}"/"${Task_date}"/qpulp_origin_"${Task_date}".json-url"
        ./judge_run.sh ${refineDir}
        echo "3" >$Filename

    elif [ $1 -eq 3 ]; then
        echo "Parse the result obtained by RefineDet..."
        script="../src/parse-refinedet-inference-result.py"
        Dir=${save_path}"/"${Task_date}
        runCmd="python -u "${script}" \
        --inputDir "${Dir}""
        echo $runCmd
        `eval $runCmd`
        echo "4" >$Filename

    elif [ $1 -eq 4 ]; then
        echo "Run Rfcn inference..."
        rfcnDir=${save_path}"/"${Task_date}"/"${Task_date}"_labelxFormat-result.json"
        ./rfcn_Inference.sh ${rfcnDir}
        echo "5" >$Filename

    elif [ $1 -eq 5 ]; then
        echo "merge result obtained by Rfcn..."
        merDir=${save_path}"/"${Task_date}
        ./merge.sh $merDir
        echo "6" >$Filename

    elif [ $1 -eq 6 ]; then
        # convert regression format to labelx format
        echo "convert regression format to labelx format..."
        script_con="../src/convertRgToLabelx.py"
        rfcn_results=${save_path}"/"${Task_date}"/"${Task_date}"_rfcn.json"
        runCmd="python -u "${script_con}" \
        --inputFile "${rfcn_results}""
        echo $runCmd
        `eval $runCmd`
        echo "7" >$Filename

    elif [ $1 -eq 7 ]; then
        # postprocessing(md5-processing, remove-class-processing)
        echo "run post-processing:"
        processing_dir=${save_path}"/"${Task_date}"/"${Task_date}"_rfcn.json-labelx.json"
        ./post_process.sh ${processing_dir}
        echo "8" >$Filename

    elif [ $1 -eq 8 ]; then
        echo "put the results obtained by rfcn to the bucket: label-x-result"
        ./qrsctlLoginLi.sh
        /workspace/data/softwares/qrsctl put label-x-result ${Task_date}"_data""/":${Task_date}"_rfcn.json-labelx.json-md5Processed.json-rmclass" ${save_path}"/"${Task_date}"/"${Task_date}"_rfcn.json-labelx.json-md5Processed.json-rmclass"

    else
        echo "ERROR : Something wrong!"
        exit
    fi


}

running=1
while [ $running -eq 1 ]; do
    flag=`cat $Filename | awk '{printf $0}'`
    echo "Current step is : "$flag
    if [ $flag -gt 7 ]; then
        running=0
    fi
    goto_step $flag
done