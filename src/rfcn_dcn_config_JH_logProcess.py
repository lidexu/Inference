rfcn_dcn_config = {
    "config_yaml_file": "/workspace/data/BK/models/rfcn-0626/rfcn.yaml",
    "modelParam": {
        "modelBasePath":"/workspace/data/BK/models/rfcn-0626",
        "epoch":14
    },
    "one_batch_size":200,
    'num_classes':11,
    'num_classes_name_list': ['__background__',
                              'islamic flag', 'isis flag', 'tibetan flag', 'knives_true', 'guns_true',
                              'knives_false', 'knives_kitchen',
                              'guns_anime', 'guns_tools',
                              'not terror'],
    'need_label_dict': {
        1: 'islamic flag',
        2: 'isis flag',
        3: 'tibetan flag',
        4: 'knives',
        5: 'guns',
        6: 'knives_false',
        7: 'knives_kitchen',
        8: 'guns_anime',
        9: 'guns_tools',
        10: 'not terror'
    },
    'need_label_thresholds': {
        1: 0.1,
        2: 0.1,
        3: 0.1,
        4: 0.1,
        5: 0.1,
        6: 0.1,
        7: 0.1,
        8: 0.1,
        9: 0.1,
        10: 1.0
    }
}

