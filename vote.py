import json
import requests
import psycopg2
import csv
from more_itertools import take

with open('assets/icb_code_explanation.csv') as f:
    industry_info = csv.reader(f, delimiter=';')
    code_2_map = {i[1]: i[2] for i in industry_info}
with open('assets/icb_code_explanation.csv') as f:
    industry_info = csv.reader(f, delimiter=';')
    code_4_map = {i[3]: i[4] for i in industry_info}
with open('assets/icb_code_explanation.csv') as f:
    industry_info = csv.reader(f, delimiter=';')
    code_6_map = {i[5]: i[6] for i in industry_info}
with open('assets/icb_code_explanation.csv') as f:
    industry_info = csv.reader(f, delimiter=';')
    code_8_map = {i[7]: i[8] for i in industry_info}
with open('assets/icb_code_explanation.csv') as f:
    industry_info = csv.reader(f, delimiter=';')
    desciption_map = {i[7]: i[9] for i in industry_info}


session = requests.Session()
user = 'elastic'
password = 'dj7386e3YGPN38d7FK7mJDi8'
session.auth = (user, password)
end_point = 'http://192.168.1.152:9200'
auth = session.post(end_point)


def construct_data(input):
    constructed = {
        "query": {
            "bool": {
                "should": [
                    {
                        "match_phrase": {
                            "text": {
                                "query": input,
                                "boost": 100
                            }
                        }
                    },
                    {
                        "match": {
                            "text": {
                                "query": input,
                                "operator": "and",
                                "boost": 10
                            }
                        }
                    },
                    {
                        "match": {
                            "text": {
                                "query": input,
                                "operator": "or",
                                "boost": 0.1
                            }
                        }
                    }
                ]
            }
        },
        "_source": [
            "ticker",
            "company_name",
            "sector"
        ],
        "size": 500
    }
    return constructed


def get_result(data, session):
    resp = session.get(
        url='http://192.168.1.152:9200/class1-live-noname/_search', json=data)
    return resp.content


def sector_voting(results, code_length, topn=6):
    code_map = None
    if code_length == 2:
        code_map = code_2_map
    elif code_length == 4:
        code_map = code_4_map
    elif code_length == 6:
        code_map = code_6_map
    elif code_length == 8:
        code_map = code_8_map

    code_score_list = [(t[0], t[1]['sector'][0:code_length])
                       for t in results if t[1]['sector'] != 'None']
    code_set = set([t[1] for t in code_score_list])
    voting_result = {}

    for code in code_set:
        code_name = code_map[code]
        total_score = sum([t[0] for t in code_score_list if t[1] == code])
        voting_result[code_name] = total_score

    voting_result = {k: v for k, v in sorted(
        voting_result.items(), key=lambda item: item[1], reverse=True)}
    voting_result = take(topn, voting_result.items())
    voting_result = {k: v for k, v in voting_result}

    return voting_result


def get_voting_result(query, code_length, topn=6):
    query_string = query
    constructed = construct_data(query_string)
    result_raw = json.loads(get_result(constructed, session))[
        'hits']['hits']
    results = result_raw
    results = [(r['_score'], r['_source']) for r in results]

    voting_result = sector_voting(results, code_length, topn)

    return constructed, result_raw, voting_result
