import re
import datetime

import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

stop_words = set(stopwords.words('english'))
ps = PorterStemmer()

def handle_special_tokens (line, doc_map):
    return_line = line
    for f in special_token_functions:
        return_line = f(return_line, doc_map)
    return return_line

def handle_acronyms (line, doc_map):
    regex = r"\b[A-Z][a-zA-Z\.]*[A-Z]\b\.?"
    raw_acronyms = re.findall(regex, line)
    clean_line = strip_line(raw_acronyms, line)
    cleaned_acronyms = map(clean_acronyms, raw_acronyms)
    update_doc_map(cleaned_acronyms, doc_map)
    return clean_line

def clean_acronyms (str):
    clean_str = str.replace('.', '')
    clean_str = clean_str.lower()
    return clean_str

def strip_line (symbols, str):
    clean_str = str
    for symbol in symbols:
        clean_str = clean_str.replace(symbol, '')
    return clean_str

def update_doc_map (tokens, doc_map):
    for token in tokens:
        exists = doc_map.get(token)
        if exists:
            doc_map[token] += 1
        else:
            doc_map[token] = 1

def handle_money (line, doc_map):
    regex =r"\b\$[\S]+"
    monies = re.findall(regex, line)
    for m in monies:
        m = m.rstrip(',;:.')
    update_doc_map(monies, doc_map)
    return strip_line(monies, line)

def handle_alphabet_digit (line, doc_map):
    regex = r"\b([A-Za-z]+\-[0-9]+)\b"
    a_d_matches = re.findall(regex, line)
    stripped_line = strip_line(a_d_matches, line)
    a_d_matches = clean_a_d(a_d_matches)
    update_doc_map(a_d_matches, doc_map)
    return stripped_line

def clean_a_d (list_matches):
    result = []
    for match in list_matches:
        split = match.split('-')
        if len(split[0]) > 2:
            result.append(split[0].lower())
            result.append((split[0] + split[1]).lower())
        else:
            result.append((split[0] + split[1]).lower())
    return result

def handle_digit_alphabet (line, doc_map):
    regex = r"\b([0-9]+\-[A-Za-z]+)\b"
    matches = re.findall(regex, line)
    clean_line = strip_line(matches, line)
    clean_matches = clean_d_a(matches)
    update_doc_map(clean_matches, doc_map)
    return clean_line

def clean_d_a (matches):
    result = []
    for m in matches:
        halves = m.split("-")
        if len(halves[1]) > 2:
            result.append(halves[1].lower())
            result.append((halves[0] + halves[1]).lower())
        else:
            result.append((halves[0] + halves[1]).lower())
    return result

def handle_hyphenated (line, doc_map):
    regex = r"\w+(?:-\w+)+"
    matches = re.findall(regex, line)
    clean_line = strip_line(matches, line)
    clean_matches = clean_hyphenated(matches)
    update_doc_map(clean_matches, doc_map)
    return clean_line

def clean_hyphenated (matches):
    common_prefixes = ['anti', 'auto', 'de', 'dis', 'down', 'extra', 'hyper', 'il', 'im', 'in', 'ir', 'inter', 'mega', 'mid', 'mis', 'non', 'over', 'out', 'post', 'pre', 'pro', 're', 'semi', 'sub', 'super', 'tele', 'trans', 'ultra', 'un', 'under', 'up']
    result = []
    for m in matches:
        pieces = m.split("-")
        if pieces[0] in common_prefixes:
            result.append(pieces[1].lower())
            result.append(pieces[0] + pieces[1].lower())
        else:
            for piece in pieces:
                if not piece in stop_words:
                    result.append(piece.lower())
            result.append("".join(pieces).lower())
    return result

def handle_nums (line, doc_map):
    regex = r'(?<!\S)(\d*\.?\d+|\d{1,3}(,\d{3})*(\.\d+)?[.,]?)(?!\S)'
    #gives me tuples (grouping), only interested in first item in each
    matches = re.findall(regex, line)
    clean_matches = clean_nums(matches)
    #devious minor bug here
    strip_matches = map(lambda t: t[0], matches)
    clean_line = strip_line(strip_matches, line)
    update_doc_map(clean_matches, doc_map)
    return clean_line

def clean_nums (matches):
    result = []
    for tuple in matches:
        num = tuple[0]
        if num.endswith((',', '.')):
            num = num[:-1]
        if '.' in num:
            num = num.rstrip('.0')
        num = num.replace(',', '')
        result.append(num)
    return result

def handle_emails (line, doc_map):
    regex = r'\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b'
    matches = re.findall(regex, line)
    clean_line = strip_line(matches, line)
    update_doc_map(matches, doc_map)
    return clean_line

def handle_urls (line, doc_map):
    regex = r'\b((http:\/\/|https:\/\/)?(www\.)?\S+\.\S+)\b'
    matches = re.findall(regex, line)
    clean_matches = list(map(lambda t: t[0], matches))
    clean_line = strip_line(clean_matches, line)
    update_doc_map(clean_matches, doc_map)
    return clean_line

def handle_ip_addresses (line, doc_map):
    regex = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
    matches = re.findall(regex, line)
    clean_line = strip_line(matches, line)
    update_doc_map(matches, doc_map)
    return clean_line

def handle_files (line, doc_map):
    regex = r'\s(\w+\.(\w+)\b)'
    matches = re.findall(regex, line)
    strip_matches = list(map(lambda t: t[0], matches))
    clean_line = strip_line(strip_matches, line)
    flattened_matches = list(sum(matches, ()))
    update_doc_map(flattened_matches, doc_map)
    return clean_line

#I'm choosing to just handle the examples in the assignment
#otherwise it starts to spiral out of control
def handle_dates (line, doc_map):
    r1 = r'\b(([01]?[0-9])[\/\-]([0-3]?[0-9])[\/\-]([0-9][0-9]([0-9][0-9])?))\b'
    r2 = r'\b((January|February|March|April|May|June|July|August|September|October|November|Dec)\s([0-3]?[0-9]),\s([12][09][0-9][0-9]))\b'
    r3 = r'\b((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\-([0-3]?[0-9])\-([0-9][0-9](?:[0-9][0-9])?))\b'
    r1_matches = re.findall(r1, line)
    r1_strip_matches = list(map(lambda t: t[0], r1_matches))
    r1_clean_line = strip_line(r1_strip_matches, line)
    r1_final_matches = clean_r1_matches(r1_matches)
    r2_matches = re.findall(r2, line)
    r2_strip_matches = list(map(lambda t: t[0], r2_matches))
    r2_clean_line = strip_line(r2_strip_matches, r1_clean_line)
    r2_final_matches = clean_r2_matches(r2_matches)
    r3_matches = re.findall(r3, line)
    r3_strip_matches = list(map(lambda t: t[0], r3_matches))
    final_clean_line = strip_line(r3_strip_matches, r2_clean_line)
    r3_final_matches  = clean_r3_matches(r3_matches)
    merged_matches = r1_final_matches + r2_final_matches + r3_final_matches
    update_doc_map(merged_matches, doc_map)
    return final_clean_line



#TODO currently not checking for month-day validity (i.e. Feb. 31 would work)
def clean_r1_matches (matches):
    current_year = datetime.datetime.now().year
    lower_bound = current_year - 100
    results = []
    for match in matches:
        month = int(match[1])
        day = int(match[2])
        year = match[3]
        if month in range(1, 12) and day in range(1, 31):
            if len(str(month)) == 1:
                month = '0' + str(month)
            if len(str(day)) == 1:
                day = '0' + str(day)
            if len(year) == 2:
                if int('19' + year) < lower_bound:
                    year = '20' + year
                else:
                    year = '19' + year
            results.append(str(month) + '/' + str(day) + '/' + year)
    return results

def clean_r2_matches (matches):
    month_dict = {
        'January': '01',
        'February': '02',
        'March': '03',
        'April': '04',
        'May': '05',
        'June': '06',
        'July': '07',
        'August': '08',
        'September': '09',
        'October': '10',
        'November': '11',
        'December': '12'
    }
    results = []
    for date in matches:
        month = month_dict[date[1]]
        day = int(date[2])
        year = date[3]
        if day in range(1, 31) and len(str(day)) == 1:
            day = '0' + str(day)
            results.append(month + '/' + str(day) + '/' + year)
    return results

def clean_r3_matches (matches):
    current_year = datetime.datetime.now().year
    lower_bound = current_year - 100
    month_dict = {
        'Jan': '01',
        'Feb': '02',
        'Mar': '03',
        'Apr': '04',
        'May': '05',
        'Jun': '06',
        'Jul': '07',
        'Aug': '08',
        'Sep': '09',
        'Oct': '10',
        'Nov': '11',
        'Dec': '12'
    }
    results = []
    for date in matches:
        month = month_dict[date[1]]
        day = int(date[2])
        int_year = int(date[3])
        str_year = date[3]
        if day in range(1, 31) and len(str(day)) == 1:
            day = '0' + str(day)
            if len(str_year) == 2:
                if int('19' + str_year) < lower_bound:
                    str_year = '20' + str_year
                else:
                    str_year = '19' + str_year
            results.append(month + '/' + str(day) + '/' + str_year)
    return results

special_token_functions = [handle_acronyms, handle_money, handle_alphabet_digit, handle_digit_alphabet, handle_hyphenated, handle_dates, handle_nums, handle_files, handle_emails, handle_ip_addresses, handle_urls]
