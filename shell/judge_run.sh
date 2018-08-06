#!/usr/bin/env bash
# 判断是否意外中断，如果意外中断从中断的job开始执行，反之执行loop_runScript.sh

set -x
if [ ! -n "$1" ]
then
    echo "must input file path"
    exit
else
    echo "the input file is : "$1
fi

bash_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
inputFile=$1
inputBasePath=`dirname $inputFile`
inputFileName=`basename $inputFile`

ls -l $inputBasePath | grep "job*"

interruption_flag=$?

if [ $interruption_flag == 0 ];then
	echo "Interruption!"
	cd $bash_dir
	./interrupt_continue.sh $inputFile

else
	echo "No Interruption!"
	cd $bash_dir
	./loop_runScript.sh $inputFile
fi
