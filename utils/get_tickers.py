import json
import requests
import psycopg2
import pandas as pd
from distutils.log import INFO
import LoraLogger
import math

logger = LoraLogger.logger(__name__, INFO)

session = requests.Session()
user = 'elastic'
password = 'dj7386e3YGPN38d7FK7mJDi8'
session.auth = (user, password)
end_point = 'http://es-cluster-8-es-internal-http.elasticsearch:9200'
auth = session.post(end_point)


def get_ind_stocks(ind_code_8, bm25):
    bm25 = round(bm25, 2)
    data = {
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "industry_code": ind_code_8
                        }
                    },
                    {
                        "match": {
                            "is_etf": False
                        }
                    }
                ]
            }
        },
        "size": 500
    }

    resp = session.get(
        url='http://es-cluster-8-es-internal-http.elasticsearch:9200/stock-info-usd/_search', json=data)

    # format: (symbol, eng_name, zhant_name, sector_score)
    stock_list_unranked = [(t['_source']['ticker'], t['_source']['ticker_name_en_us'], t['_source']
                            ['ticker_name_zh_hant'], bm25) for t in json.loads(resp.content)['hits']['hits']]

    # stock_list = []
    # sort stocks by market cap
    # for s in stock_list_unranked:
    #     conn = psycopg2.connect(host="psql.psql", port="5432",
    #                             database="quant_staging", user="nlp_readonly", password="nlp_readonly")
    #     cur = conn.cursor()
    #     cur.execute(
    #         f"SELECT value FROM data.latest_mktcap WHERE ticker = '{s[0]}' ORDER BY trading_day DESC LIMIT 1")
    #     rows = cur.fetchall()
    #     conn.close()
    #     s = list(s)
    #     s.append(rows[0][0])
    #     stock_list.append(tuple(s))

    return stock_list_unranked


def append_stock_mkt_cap(stock):
    # sort stocks by market cap
    conn = psycopg2.connect(host="psql.psql", port="5432",
                            database="quant_staging", user="nlp_readonly", password="nlp_readonly")
    cur = conn.cursor()
    cur.execute(
        f"SELECT value FROM data.latest_mktcap WHERE ticker = '{stock[0]}' ORDER BY trading_day DESC LIMIT 1")
    rows = cur.fetchall()
    conn.close()
    stock.append(rows[0][0])
    return stock


def calc_complex_score(row):
    # score = round((row['sector_score'] / highest_score)
    #               * math.log(row['mkt_cap']), 2)
    logged_cap = math.log(row['mkt_cap'])
    if logged_cap >= 1:
        score = round(row['sector_score'] * (logged_cap ** 2), 2)
    else:
        score = round(row['sector_score'] * logged_cap, 2)

    return score


def rank_stocks_to_df(stock_list):

    df = pd.DataFrame(stock_list, columns=[
                      'symbol', 'name_es', 'name_zh_hant', 'sector_score', 'mkt_cap'])

    # min_mkt_cap = min(df['mkt_cap'].tolist())

    df['complex_score'] = df.apply(
        lambda row: calc_complex_score(row), axis=1)
    # df = df.sort_values(by=['complex_score'], ascending=False)
    df = df.sort_values(by=['complex_score'], ascending=False)
    df = df.reset_index().drop(['index'], axis=1)
    return df


def combine_stock_sector_scores(stock_list_all):
    stock_list = set([(r[0], r[1], r[2]) for r in stock_list_all])
    merged_list = []
    for s in stock_list:
        score = sum([r[3] for r in stock_list_all if r[0] == s[0]])
        s = list(s)
        s.append(score)
        s = append_stock_mkt_cap(s)

        merged_list.append(tuple(s))

    return merged_list


def get_stock_list_with_ind(ind_results, topn=50):
    code_lengths = ['4', '6', '8']

    results4 = [(k, v) for k, v in ind_results[code_lengths[0]].items()]
    results6 = [(k, v) for k, v in ind_results[code_lengths[1]].items()]
    results8 = [(k, v) for k, v in ind_results[code_lengths[2]].items()]

    results = {code_lengths[0]: results4, code_lengths[1]: results6, code_lengths[2]: results8}

    # highest_score4 = max([i[1] for i in results4])
    # highest_score6 = max([i[1] for i in results6])
    # highest_score8 = max([i[1] for i in results8])

    # highest_scores = {code_lengths[0]: results4,
    #                   code_lengths[1]: results6, code_lengths[2]: results8}

    stock_list_all = []

    for cl, result in results.items():
        for ind in result:
            stock_list_all.extend(get_ind_stocks(ind[0], ind[1]))

    stock_list_all = combine_stock_sector_scores(stock_list_all)

    # if len(stock_list_all) > topn:
    #     stock_list_all = stock_list_all[:topn]

    return rank_stocks_to_df(stock_list_all).head(topn)
