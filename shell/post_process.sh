# !/bin/bash
# 该脚本对rfcn结果去重，并对结果按所含暴恐目标进行分类, 并去除只含 枪的数据

set -x

if [ ! -n "$1" ]
then
    echo "must input the rfcn results!"
    exit
else
    echo "the rfcn results is :"$1
fi

rfcn_file=$1
rfcn_url=${rfcn_file}"-url"

cat ${rfcn_file} | jq -r '.url' >${rfcn_url}

# 计算md5
/workspace/data/softwares/qhash_proxy ${rfcn_url} 16 --output ${rfcn_url}"-output"

python ../src/md5-process.py --labelxFile ${rfcn_file} --md5File ${rfcn_url}"-output"

#python ./src/split_class.py --rfcnFile ${rfcn_file}"-md5Processed.json"

python ../src/parse_classname_rfcn.py --inputClass guns_true --inputFile ${rfcn_file}"-md5Processed.json"

shell_path=`pwd`

file_name=`dirname ${rfcn_file}`

# process_name=`basename ${rfcn_file}`

cd $file_name
rm q*
#rm -r job*
rm split_file*
cd $shell_path