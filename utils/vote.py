from asyncio.log import logger
import json
import requests
import psycopg2
import csv
from more_itertools import take
from pathlib import Path
import re
import chinese_converter

with open('utils/icb_code_explanation.csv') as f:
    industry_info = csv.reader(f, delimiter=';')
    code_2_map = {i[1]: i[2] for i in industry_info}
with open('utils/icb_code_explanation.csv') as f:
    industry_info = csv.reader(f, delimiter=';')
    code_4_map = {i[3]: i[4] for i in industry_info}
with open('utils/icb_code_explanation.csv') as f:
    industry_info = csv.reader(f, delimiter=';')
    code_6_map = {i[5]: i[6] for i in industry_info}
with open('utils/icb_code_explanation.csv') as f:
    industry_info = csv.reader(f, delimiter=';')
    code_8_map = {i[7]: i[8] for i in industry_info}
with open('utils/icb_code_explanation.csv') as f:
    industry_info = csv.reader(f, delimiter=';')
    desciption_map = {i[7]: i[9] for i in industry_info}


session = requests.Session()
user = 'elastic'
password = 'dj7386e3YGPN38d7FK7mJDi8'
session.auth = (user, password)
end_point = 'http://es-cluster-8-es-internal-http.elasticsearch:9200'
auth = session.post(end_point)


def construct_eng_part(input):
    data = {
        "bool": {
            "should": [
                {
                    "match_phrase": {
                        "text": {
                            "query": input,
                            "boost": 10
                        }
                    }
                },
                {
                    "match": {
                        "text": {
                            "query": input,
                            "operator": "and",
                            "boost": 1
                        }
                    }
                }
            ]

        }
    }
    return data


def construct_cn_part(input):
    data = {
        "bool": {
            "should": [
                {
                    "match_phrase": {
                        "text_cn": {
                            "query": input,
                            "analyzer": "smartcn",
                            "boost": 10
                        }
                    }
                },
                {
                    "match": {
                        "text_cn": {
                            "query": input,
                            "operator": "and",
                            "analyzer": "smartcn",
                            "boost": 1
                        }
                    }
                }
            ]
        }
    }
    return data


def split_eng_cn(input):
    cn = re.findall(r'[\u4e00-\u9fff]+', input)
    cn_text = ''
    if cn != None:
        for n in cn:
            cn_text += ' '
            cn_text += n
            input = input.replace(n, '')
    eng = input
    return eng, cn_text


def construct_data(input):
    should_list = []
    eng, cn = split_eng_cn(input)
    if (re.search('[a-zA-Z]', eng)):
        should_list.append(construct_eng_part(eng))
    if (cn != ''):
        cn = chinese_converter.to_simplified(cn)
        should_list.append(construct_cn_part(cn))
    constructed = {
        "query": {
            "bool": {
                "should": should_list
            }
        },
        "_source": [
            "ticker",
            "company_name",
            "sector"
        ],
        "size": 500
    }

    logger.info(constructed)

    return constructed


def get_result(data, session):
    resp = session.get(
        url='http://192.168.1.152:9200/class1-live-noname/_search', json=data)
    return resp.content


def sector_voting(results, get_code=False, topn=6):
    code_maps = {'2': code_2_map, '4': code_4_map,
                 '6': code_6_map, '8': code_8_map}

    code_lengths = ['4', '6', '8']

    code4_score_list = [(t[0], t[1]['sector'][0:int(code_lengths[0])])
                        for t in results if t[1]['sector'] != 'None']
    code6_score_list = [(t[0], t[1]['sector'][0:int(code_lengths[1])])
                        for t in results if t[1]['sector'] != 'None']
    code8_score_list = [(t[0], t[1]['sector'][0:int(code_lengths[2])])
                        for t in results if t[1]['sector'] != 'None']
    code_score_lists = {'4': code4_score_list,
                        '6': code6_score_list, '8': code8_score_list}

    code4_set = set([t[1] for t in code4_score_list])
    code6_set = set([t[1] for t in code6_score_list])
    code8_set = set([t[1] for t in code8_score_list])
    code_sets = {'4': code4_set, '6': code6_set, '8': code8_set}

    voting_result4 = {}
    voting_result6 = {}
    voting_result8 = {}
    voting_results = {'4': voting_result4,
                      '6': voting_result6, '8': voting_result8}
    for l in code_lengths:
        for code in code_sets[l]:
            if get_code is False:
                code_name = code_maps[l][code]
            else:
                code_name = code
            total_score = sum([t[0]
                              for t in code_score_lists[l] if t[1] == code])
            voting_results[l][code_name] = total_score
    for length, voting_result in voting_results.items():
        voting_result = {k: v for k, v in sorted(
            voting_result.items(), key=lambda item: item[1], reverse=True)}
        voting_result = take(topn, voting_result.items())
        voting_result = {k: v for k, v in voting_result}
        voting_results[length] = voting_result

    return voting_results


def get_voting_result(query, get_code=False, topn=6):
    query_string = query
    constructed = construct_data(query_string)
    result_raw = json.loads(get_result(constructed, session))[
        'hits']['hits']
    results = result_raw
    results = [(r['_score'], r['_source']) for r in results]

    voting_results = sector_voting(results, get_code, topn)

    return constructed, result_raw, voting_results
