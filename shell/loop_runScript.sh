#!/usr/bin/env bash
# 这个脚本的作用是将一个大数据分成 N 分，一份跑完，再跑其他的，一份一份的跑
set -x
if [ ! -n "$1" ]
then
    echo "must input file path"
    exit
else
    echo "the input file is : "$1
fi
N=500
bash_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
inputFile=$1
inputBasePath=`dirname $inputFile`
inputFileName=`basename $inputFile`

# inputfile
splitFilePrefix="Num-"
# split the input file by gpuNum
inputFileLineCount=`wc -l $inputFile|awk '{print $1}'`
perFileLineCount=`expr $inputFileLineCount / $N`
perFileLineCount_flag=`expr $inputFileLineCount % $N`
if [ $perFileLineCount_flag -ne 0 ]
then
    perFileLineCount=`expr $perFileLineCount + 1`
fi
echo "perFileLineCount : "$perFileLineCount
# split
split_output_prefix=$inputBasePath"/"$splitFilePrefix
split -l $perFileLineCount $inputFile -d -a 4 $split_output_prefix

jobNum=$[N-1]
for i in $(seq 0 $jobNum)
do
    job_id=`printf "%.4d" $i`
    tempDir=$inputBasePath"/job-"$job_id
    mkdir $tempDir
    mv $inputBasePath"/"$splitFilePrefix$job_id  $tempDir
done
check()
{
    count=`ps auxww | grep $1 | grep -v grep |grep -v defunct |wc -l`
    return $count
    #echo $count
    # if [ $count -eq 0 ]; then
    #   #statements
    #   return 0
    # fi
    # return 1
}
check_Sl()
{
    count=`ps auxww | grep $1 | grep -v grep |grep -v defunct |awk '$8=="Sl"{print}'|wc -l`
    return $count
    #echo $count
    # if [ $count -eq 0 ]; then
    #   #statements
    #   return 0
    # fi
    # return 1
}
# add kill process function
kill_process_fun()
{
    process_name_flag=$1
    for process_id in `ps auxww | grep  $process_name_flag| grep -v grep |grep -v defunct |awk '$8=="Sl"{print}'|awk '{print $2}'`;
    do
        kill -9 $process_id;
    done
}

jobFlag=0
checkFlag=0
job_sl_count=0
while [ $jobFlag -lt $N ]; do
    check mp_refindeDet-res18-inference-demo.py
    a=$?
    check_Sl mp_refindeDet-res18-inference-demo.py
    b=$?
    if [ $a -eq 0 ]; then
        date
        job_id=`printf "%.4d" $jobFlag`
        echo "no job running, so run ---"$job_id"--- and sleep 100s"
        cd $bash_dir
        ./processInference.sh  $inputBasePath"/job-"$job_id"/"$splitFilePrefix$job_id
        echo "nohup runing the ---"$job_id"--- and begin sleep 100s"
        jobFlag=$[jobFlag+1]
        sleep 100
    elif [ $a -eq $b ];then
        checkFlag=$[checkFlag+1]
        if [ $checkFlag -gt 5 ];then
            #pkill -9 python
            kill_process_fun mp_refindeDet-res18-inference-demo.py
            checkFlag=0
        else
            sleep 60
        fi
    else
        date
        nowRunJobFlag=$[jobFlag-1]
        job_id=`printf "%.4d" $nowRunJobFlag`
        echo "job ---"$job_id"--- running,sleep 60s"
        sleep 60
                job_sl_count=$[job_sl_count+1]
    fi
        if [ $job_sl_count -gt 10 ]; then
            date
            kill_process_fun mp_refindeDet-res18-inference-demo.py
            job_sl_count=0
        fi
done