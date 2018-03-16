import os
import re
import html

#constants to be used later (seems foolish to compute at runtime since they're not gonna change)
NUM_DOCUMENTS = 1768
COLLECTION_SIZE = 1240085
AVERAGE_DOC_LENGTH = 705

doc_length_dict = {}

def clean_escape_sequences (str):
    clean_str = html.unescape(str)
    #for some reason &blank and &hyph don't get handled by html.unescape
    clean_str = clean_str.replace('&blank;', '&')
    clean_str = clean_str.replace('&hyph;', '-')
    return clean_str

for file in os.listdir('../Indexing/BigSample'):
    cur_file = open('../Indexing/BigSample/' + file)
    cur_line = cur_file.readline()
    cur_doc = ''
    cur_doc_length = 0
    tokenize = False
    while cur_line != '':
        if cur_line.startswith('<DOCNO>'):
            if cur_doc_length != 0:
                doc_length_dict[cur_doc] = cur_doc_length
            cur_doc = cur_line.split(' ')[1]
            cur_doc_length = 0
        elif cur_line.startswith('<TEXT>'):
            tokenize = True
        elif cur_line.startswith('</TEXT>'):
            tokenize = False
        elif tokenize and not cur_line.startswith('<'):
            cur_line = clean_escape_sequences(cur_line)
            l = cur_line.lower()
            #just words, not nums/special thangs
            regex = r'\b[a-z]+\b'
            words = re.findall(regex, l)
            cur_doc_length += len(words)

        cur_line = cur_file.readline()

doc_length = open('./doc_length.txt', 'w')

for key, value in doc_length_dict.items():
    doc_length.write(key + ' ' + str(value) + '\n')

doc_length.close()
