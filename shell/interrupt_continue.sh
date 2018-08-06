#!/usr/bin/env bash
# 从中断的job继续执行，按job的最后修改时间，从最后修改的job执行processInferernce.sh

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


# Here what I changed

splitFilePrefix="Num-"

# get the job modified lastly

currentjob=`ls -t $inputBasePath | head -n 1`
echo "the currentjob is: "$currentjob

current_num=${currentjob#*job-}
echo "the current_num is: "$current_num

current_num_jobId=$((current_num-0))

# do we need remove the result which generated already?
check__()
{
    rm split*
}


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
jobFlag=`echo ${current_num} | awk '{print $0+0}'`
checkFlag=0
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
            pkill -9 python
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
    fi
done
