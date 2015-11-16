import os
from os import listdir
from os.path import isfile, join
from collections import Counter, defaultdict
import pprint
import sys

import location_identifier as loc_id


class NGramBuilder:
    def __init__(self):
        self.data_path = \
            '/Users/phshin/work/git/phshin/analysis/license/data/license_dir'
        # '/Users/phshin/work/git/phshin/analysis/license/data/jporter/scratch/spdx/license-list'
        # self.data_path = '/Users/phshin/work/git/phshin/analysis/license/data/licences-1.18'
        
        self.unigram_count = Counter()
        self.bigram_count = Counter()
        self.trigram_count = Counter()
        
        self.unique_chars = Counter()

        self.license_unigram = defaultdict(Counter)
        self.license_bigram = defaultdict(Counter)
        self.license_trigram = defaultdict(Counter)
        
        self.onlyfiles = [ f for f in listdir(self.data_path) if isfile(join(self.data_path,f)) ]
        self.license_names = [ name.split('.txt')[0] for name in self.onlyfiles]

    def apply_function_on_all_files(self, function_ptr, top_dir_name):
        for root, dirs, files in os.walk(top_dir_name):
            # print (root, dirs, files)
            for file in files:
                function_ptr(join(root, file))
        
    def insert_ngrams(self, first, second, third):
        self.unigram_count[first] += 1
        self.bigram_count [first, second]  += 1
        self.trigram_count[first, second, third] += 1

    def build_license_vector(self, license_name, first, second, third):
        self.license_unigram[license_name][first] += 1
        self.license_bigram [license_name][first, second]  += 1
        self.license_trigram[license_name][first, second, third] += 1
        
    def build_ngrams(self):
        for myfile in self.onlyfiles:
            try:
                fp = open(join(self.data_path, myfile), encoding='ascii', errors='surrogateescape')
                license_str = fp.readlines()
                # print license_str
                fp.close()
            except OSError as err:
                print('OS error: {0}'.format(err))
            except:
                print (myfile)
                print (sys.exc_info()[0])
                print (sys.exc_info())
                print ()

            curr_word = ''
            prev_word = ''
            prev2_word = ''
            license_name = myfile.split('.txt')[0]
            
            for line in license_str:
                words = line.split()
                for word in words:
                    prev2_word = prev_word
                    prev_word = curr_word
                    curr_word = word
                    self.insert_ngrams(curr_word, prev_word, prev2_word)
                    self.build_license_vector(license_name, curr_word, prev_word, prev2_word)
                    
                    for char in word:
                        self.unique_chars[char] += 1

    def analyze_file(self, fp):
        try:
            src_file = open(fp, encoding='ascii', errors='surrogateescape')
            src_str = src_file.readlines()
            
        except:
            print ('error happened opening this file', fp)
            src_str = ''

        curr_word = ''
        prev_word = ''
        prev2_word = ''
        license_name = 'unknown'

        src_uni = Counter()
        src_bi = Counter()
        src_tri = Counter()
        
        for line in src_str:
            words = line.split()
            for word in words:
                prev2_word = prev_word
                prev_word = curr_word
                curr_word = word 
                self.process_word_seq(curr_word, prev_word, prev2_word,
                                      src_uni, src_bi, src_tri)
        self.src_uni = src_uni
        self.src_bi = src_bi
        self.src_tri = src_tri

        self.measure_similarity()

        self.match_file_name(fp)
        # self.for_Jesse_program(fp)
        

    def for_Jesse_program(self, fp):
        license_found = max (self.similarity_dict, key=self.similarity_dict.get)

        path_Peter = '/Users/phshin/work/git/phshin/analysis/license/data/'
        path_Jesse = '/vagrant/'
        
        prt_str=fp.replace(path_Peter, path_Jesse)
        license_found = license_found.replace('Apache-2.0-PS', 'Apache-2.0')
        license_found = license_found.replace('BSD-ref-PS', 'BSD')
        license_found = license_found.replace('GPL-1.0-license-PS', 'GPL-1.0')
        license_found = license_found.replace('GPL-2.0-license-PS', 'GPL-2.0+')
        license_found = license_found.replace('GPL-3.0-license-PS', 'GPL-3.0')
        license_found = license_found.replace('LGPL-2.0-license-PS', 'LGPL-2.0+')
        license_found = license_found.replace('LGPL-2.1-license-PS', 'LGPL-2.1+')
        license_found = license_found.replace('Python-2.0-ref-PS', 'Python')
        license_found = license_found.replace('Unicode-TOU', 'Unicode')

        print('{};{},None,None'.format(prt_str, license_found))

                
    def match_file_name(self, fp):
        fname = os.path.basename(fp)
        fname2 = fp
        license_found = max (self.similarity_dict, key=self.similarity_dict.get)
        max_val = self.similarity_dict[max (self.similarity_dict, key=self.similarity_dict.get)]

        if (max_val > 0.02):
            if license_found in fname:
                found_str = '1'
            else:
                found_str = '0'

            print('{},{},{},{},{}'.format(found_str, fname, fname2, license_found, max_val))
            print ('{},{},{}'.format(fname2, license_found, max_val))

            license_fp = self.data_path + '/' + license_found + '.txt'
            loc_finder = loc_id.Location_Finder()
            print ()
            [start_ind, end_ind, start_offset, end_offset, score] = loc_finder.main_process(license_fp, fname2)
            if score > 0.02:
                print (start_ind, end_ind, start_offset, end_offset, score)
            else:
                print ("No license seems to match - the matched region has very low score")
            print ()
        else:
            print ('License not found in {}.'.format(fname))

    def process_word_seq(self, cw, pw, ppw, uni, bi, tri):
        if cw in self.unigram_count:
            uni[cw] += 1
        if (cw, pw) in self.bigram_count:
            bi[cw, pw] += 1
        if (cw, pw, ppw) in self.trigram_count:
            tri[cw, pw, ppw] += 1
        
    def measure_similarity(self):
        """
        Return the similarity measure.  
        Assume that the license lookup is available.
        """
        self.similarity_dict = Counter()
        for license_name in self.license_unigram:
            self.similarity_dict[license_name] = self.measure_Jaccard_distance(license_name)

            
    def measure_Jaccard_distance(self, license_name):
        """
        |A intersection B| / |A union B|
        """
        uni_intersect = self.license_unigram[license_name] & self.src_uni
        bi_intersect = self.license_bigram[license_name] & self.src_bi
        tri_intersect = self.license_trigram[license_name] & self.src_tri

        uni_union = self.license_unigram[license_name] | self.src_uni
        bi_union = self.license_bigram[license_name] | self.src_bi
        tri_union = self.license_trigram[license_name] | self.src_tri

        if (sum(uni_union.values()) > 0):
            uni_score = float(sum(uni_intersect.values())) / sum(uni_union.values())
        else:
            uni_score = 0.0

        if (sum(bi_union.values()) > 0):
            bi_score = float(sum(bi_intersect.values())) / sum(bi_union.values())
        else:
            bi_score = 0.0
        if (sum(tri_union.values()) > 0):
            tri_score = float(sum(tri_intersect.values())) / sum(tri_union.values())
        else:
            tri_score = 0.0
            
        return (uni_score + bi_score*6 + tri_score*8 )/15
        


# def main(self):            
# get a list of the license file names
ng_model = NGramBuilder()
data_path = ng_model.data_path
        
pp = pprint.PrettyPrinter()
        
ng_model.build_ngrams()

# pp.pprint(ng_model.unigram_count)

base_dir = '/Users/phshin/work/git/phshin/analysis/license/'
data_dir= base_dir + 'data/jporter/scratch/spdx/generated_files/'
# file_path = base_dir + data_dir + 'ZPL-1.1.c'
# data_dir = '/Users/phshin/work/git/phshin/analysis/license/data/scanner_evaluation_files-1.0.0/open_source/GNU_2.0'

top_dir = '/Users/phshin/work/git/phshin/analysis/license/data/scanner_evaluation_files-1.0.0/open_source/'
ng_model.apply_function_on_all_files(ng_model.analyze_file, top_dir)
                                                  
# for f in listdir(data_dir):
    # if isfile(join(data_dir,f)):
        # ng_model.analyze_file(join(data_dir,f))


#        if __name__ == "__main__":
#            main()