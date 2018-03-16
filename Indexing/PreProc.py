import sys
import os
import html
import uuid
import shutil
import time
from special import *
from statistics import mean, median



path_to_input_files = sys.argv[1]
index_type = sys.argv[2]
path_to_output_files = sys.argv[3]
mem_constraint = int(sys.argv[4])

def clean_escape_sequences (str):
    clean_str = html.unescape(str)
    #for some reason &blank and &hyph don't get handled by html.unescape
    clean_str = clean_str.replace('&blank;', '&')
    clean_str = clean_str.replace('&hyph;', '-')
    return clean_str


def handle_regular_terms (line, doc_map):
    line = line.lower()
    regex = r'\w+'
    words = re.findall(regex, line)
    clean_words = [word for word in words if word not in stop_words]
    update_doc_map(clean_words, doc_map)

def offload_doc_map (doc_map, doc_id, lexicon, index, mem_constraint):
    for key, value in doc_map.items():
        exists = lexicon.get(key)
        if not exists:
            lexicon[key] = len(lexicon) + 1
        index.append((lexicon[key], doc_id, value))
        if len(index) == mem_constraint:
            write_index_to_disk(index)
            #delete the index entries in memory
            del index[:]


def write_index_to_disk (index):
    if not os.path.exists('./tmps'):
        os.makedirs('./tmps')
    #step1 sort the index
    sorted_index = sorted(index, key = lambda t: (t[0], t[1]))
    tf = open('./tmps/' + str(uuid.uuid4()) + '.txt', 'w')
    for triple in sorted_index:
        tf.write(str(triple[0]) + ' ' + triple[1] + ' ' + str(triple[2]) + '\n')
    tf.close()

def do_porter_stemming (line, doc_map):
    l = line.lower()
    regex = r'\b[a-z]+\b'
    words = re.findall(regex, line)
    clean_words = [word for word in words if word not in stop_words]
    stemmed_words = [ps.stem(w) for w in clean_words]
    update_doc_map(stemmed_words, doc_map)

def do_phrases (line, doc_map):
    r1 = r'(?=(\b[a-z]+\s[a-z]+\b))'
    r2 = r'(?=(\b[a-z]+\s[a-z]+\s[a-z]+\b))'
    two_phrases = re.findall(r1, line)
    three_phrases =re.findall(r2, line)
    clean_twos = []
    for p in two_phrases:
        s1,s2 = p.split(' ')
        if not s1 in stop_words and not s2 in stop_words:
            clean_twos.append(p)
    clean_3s = []
    for p in three_phrases:
        s1,s2,s3 = p.split(' ')
        if not s1 in stop_words and not s2 in stop_words and not s3 in stop_words:
            clean_3s.append(p)
    result = clean_twos + clean_3s
    update_doc_map(result, doc_map)

def do_positional (line, bag_of_words):
    l = line.lower()
    #this choice of regex is important (here only words, not nums/special things)
    regex = r'\b[a-z]+\b'
    words = re.findall(regex, l)
    bag_of_words += words

def offload_positional (bag_of_words, current_doc, lexicon, index, mem_constraint):
    seen = set()
    for w in bag_of_words:
        if not w in seen:
            seen.add(w)
            indices = [i for i, x in enumerate(bag_of_words) if x == w]
            exists = lexicon.get(w)
            if not exists:
                lexicon[w] = len(lexicon) + 1
            index.append((lexicon[w], current_doc, indices))
            if len(index) == mem_constraint:
                write_positional_to_disk(index)
                del index[:]

def write_positional_to_disk (index):
    if not os.path.exists('./tmps'):
        os.makedirs('./tmps')
    #step1 sort the index
    sorted_index = sorted(index, key = lambda t: (t[0], t[1]))
    tf = open('./tmps/' + str(uuid.uuid4()) + '.txt', 'w')
    for triple in sorted_index:
        tf.write(str(triple[0]) + ' ' + triple[1] + ' ')
        for i in triple[2]:
            tf.write(str(i) + ' ')
        tf.write('\n')
    tf.close()

def slim_phrase_index():

    cur_index = open(path_to_output_files + '/index.txt', 'r')
    new_index = open(path_to_output_files + '/index_slim.txt', 'w')

    index_line = cur_index.readline()
    term_id = index_line.split(' ')[0]
    term_count = 0
    term_index_lines = []

    term_id_set = set()

    while index_line != '':
        #same term_id
        if term_id == index_line.split(' ')[0]:
            term_count += 1
            term_index_lines.append(index_line)
            index_line = cur_index.readline()
        #we've hit a different term_id
        else:
            #choice of num here allows for tuning
            if term_count >= 12:
                term_id_set.add(term_id)
                for l in term_index_lines:
                    new_index.write(l)
            term_count = 1
            index_line = cur_index.readline()
            term_index_lines = [index_line]
            term_id = index_line.split(' ')[0]

    cur_index.close()
    new_index.close()

    os.remove(path_to_output_files + '/index.txt')

    return term_id_set

def slim_phrase_lexicon(id_set):

    cur_lexicon = open(path_to_output_files + '/lexicon.txt', 'r')
    new_lexicon = open(path_to_output_files + '/slim_lexicon.txt', 'w')

    line = cur_lexicon.readline()

    while line != '':
        if line.split(' ')[0] in id_set:
            new_lexicon.write(line)
        line = cur_lexicon.readline()

    cur_lexicon.close()
    new_lexicon.close()

    os.remove(path_to_output_files + '/lexicon.txt')

#for the stats in my report
def calculate_df ():

    dfs = []
    index = open(path_to_output_files + '/index_slim.txt', 'r')
    line = index.readline()

    term_id = line.split(' ')[0]
    count = 0

    while line != '':
        if term_id == line.split(' ')[0]:
            count += 1
            line = index.readline()
        else:
            dfs.append(count)
            term_id = line.split(' ')[0]
            count = 1
            line = index.readline()

    min_df = min(dfs)
    max_df = max(dfs)
    mean_df = mean(dfs)
    median_df = median(dfs)

    return (max_df, min_df, mean_df, median_df)



def build():

    #mainly makes running it easier for me
    if os.path.exists('./tmps'):
        shutil.rmtree('./tmps')
    if os.path.exists(path_to_output_files):
        shutil.rmtree(path_to_output_files)

    lexicon = {}
    index = []

    for file in os.listdir(path_to_input_files):

        current_file = open(path_to_input_files + '/' + file)
        current_line = current_file.readline()
        current_doc = ''
        tokenize = False
        doc_term_map = {}
        positional_word_bag = []

        #work with the current file line by line
        while current_line != '':
            if current_line.startswith('<DOCNO>'):
                current_doc = current_line.split(" ")[1]
            elif current_line.startswith('<TEXT>'):
                tokenize = True
            elif current_line.startswith('</TEXT>'):
                tokenize = False
                if index_type == 'positional':
                    #run offload_positional
                    offload_positional(positional_word_bag, current_doc, lexicon, index, mem_constraint)
                    positional_word_bag = []
                else:
                    #offload doc_map to lexicon and index
                    offload_doc_map(doc_term_map, current_doc, lexicon, index, mem_constraint)
                    doc_term_map = {}

            elif tokenize and not current_line.startswith('<'):
                current_line = clean_escape_sequences(current_line)
                if index_type == 'single':
                    current_line = handle_special_tokens(current_line, doc_term_map)
                    handle_regular_terms(current_line, doc_term_map)
                elif index_type == 'stem':
                    do_porter_stemming(current_line, doc_term_map)
                elif index_type == 'phrase':
                    do_phrases(current_line, doc_term_map)
                elif index_type == 'positional':
                    do_positional(current_line, positional_word_bag)

            current_line = current_file.readline()

    if index_type == 'positional':
        write_positional_to_disk(index)

    else:
        write_index_to_disk(index)

    #now merge all the temp files
    tmp_files = os.listdir('./tmps')

    os.makedirs(path_to_output_files)

    output_file = open(path_to_output_files + '/index.txt', 'w')

    file_stream_dict = {}

    for file in tmp_files:
        fs = open('./tmps/' + file, 'r')
        file_stream_dict[fs] = fs.readline()

    exhausted = False

    while not exhausted:
        exhausted = True
        min_key = None
        #kinda hacky, should be better way
        min_val = '1000000 zzzzzzzzzzz'
        for key, val in file_stream_dict.items():
            if val:
                exhausted = False
                #extract termid and docNo
                pieces = val.split(' ')
                term_id = int(pieces[0])
                doc_id = pieces[1]
                if term_id < int(min_val.split(' ')[0]):
                    min_key = key
                    min_val = val
                elif term_id == int(min_val.split(' ')[0]) and doc_id < min_val.split(' ')[1]:
                    min_key = key
                    min_val = val
        if not exhausted:
            output_file.write(min_val)
            file_stream_dict[min_key] = min_key.readline()

    lexicon_file = open(path_to_output_files + '/lexicon.txt', 'w')
    for term, term_id in lexicon.items():
        lexicon_file.write(str(term_id) + ' ' + term + '\n')

    output_file.close()
    lexicon_file.close()

    shutil.rmtree('./tmps')

    if index_type == 'phrase':
        ids = slim_phrase_index()
        slim_phrase_lexicon(ids)

build()








