import os
from os.path import join

import processor


class report_generator:

    def __init__(self, top_dir):
        self.data_path = \
            '/Users/phshin/work/git/phshin/analysis/license/data/license_dir'
        self.ng_model = processor.NGramBuilder()


    def apply_function_on_all_files(self, function_ptr, top_dir_name):
        for root, dirs, files in os.walk(top_dir_name):
            # print (root, dirs, files)
            for file in files:
                function_ptr(join(root, file))

    def train_n_gram(self):
        pass

    base_dir = '/Users/phshin/work/git/phshin/analysis/license/'
    data_dir= base_dir + 'data/jporter/scratch/spdx/generated_files/'
    # file_path = base_dir + data_dir + 'ZPL-1.1.c'
    # data_dir = '/Users/phshin/work/git/phshin/analysis/license/data/scanner_evaluation_files-1.0.0/open_source/GNU_2.0'

    top_dir = '/Users/phshin/work/git/phshin/analysis/license/data/scanner_evaluation_files-1.0.0/open_source/'

