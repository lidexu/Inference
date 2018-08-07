该项目为RefineDet与rfcn联合推理
============================

分为两部分shell 和 src
----------------------------

### shell：

> 主脚本：Daily_Inference.sh 脚本的调用

> RefineDet脚本：  judge_run.sh interrupt_continue.sh loop_runScript.sh processInference.sh

>> 其中主脚本为judge_run.sh

> Rfcn脚本：rfcn_Inference.sh processInferenceRfcn-dcn.sh

> 整合rfcn结果脚本：merge.sh

> 后处理脚本：post_process.sh

### src：

> mp_refindeDet-res18-inference-demo.py RefineDet推理脚本

> rfcn_dcn_inference_JH_logProcess.py   rfcn推理脚本

> rfcn_dcn_config_JH_logProcess.py      rfcn配置文件

> parse-refinedet-inference-result.py   refinedet结果处理脚本

> convertRgToLabelx.py                  rfcn结果处理脚本

> rfcn_dcn_config.py                    rfcn结果处理脚本的配置文件

> md5-process.py                        md5去重脚本

> parse_classname_rfcn.py               rfcn结果类别处理脚本

> multi-model-inference.py              多模型推理脚本

> multiprocessing-class.py              多线程类

> refindet-class.py                     refindet模型类