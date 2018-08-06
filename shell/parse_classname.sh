# !/bin/bash
# 该脚本用于处理需要从数据集中去除某种类别的数据。
# 在split_class.py 的结果之后。
set -x

if [ ! -n "$1" ]
then 
    echo "must input the rfcn file"
    exit
else
    echo "the rfcn file is:"
fi

rfcn_file=$1

shell_path=`pwd`

file_name=`dirname ${rfcn_file}`

cd $file_name

cat *guns* | sort | uniq >${rfcn_file}"_guns"

cat *flag* *knives* | sort | uniq >${rfcn_file}"_others"

# only guns

grep -F -v -f ${rfcn_file}"_others" ${rfcn_file}"_others" | sort | uniq >${rfcn_file}"_onlygun"

grep -F -v -f ${rfcn_file}"_others" ${rfcn_file} | sort | uniq >${rfcn_file}"_sort"

shuf ${rfcn_file}"_sort" -o ${rfcn_file}"_final"

cd $shell_path



