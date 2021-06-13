
import requests
import pandas as pd
from io import StringIO
import time

#可以調整的參數
current_time = ['1105', '1104', '1103']
compare_time = ['1099', '10910', '10911', '10912', '1101', '1102']
threshold_ratio = 1.15


def get_all_stockid():
    # Init stock_index_list from TW Stock Index
    link = "https://www.twse.com.tw/exchangeReport/STOCK_DAY_ALL"
    r = requests.get(link)
    stockid_list = []
    stock_data = pd.DataFrame(r.json()['data'])
    stock_data.columns = ['STOCK_INDEX', 'NAME', 'VOLUME', 'AMOUNT', 'OPEN',
                'HIGH', 'LOW', 'CLOSE', 'PRICE_CHANGE', 'TRANSACTION']
    total_rows_stock_data = len(stock_data.index)
    for row_idx in range(total_rows_stock_data):
        stockid_list.append(stock_data['STOCK_INDEX'].iloc[row_idx])
    return stockid_list


def monthly_report(year_month):
    if len(year_month) <= 3:
        return

    year = int(year_month[0:3])
    month = int(year_month[3:])

    # 假如是西元，轉成民國
    if year > 1990:
        year -= 1911
    
    url = 'https://mops.twse.com.tw/nas/t21/sii/t21sc03_'+str(year)+'_'+str(month)+'_0.html'
    if year <= 98:
        url = 'https://mops.twse.com.tw/nas/t21/sii/t21sc03_'+str(year)+'_'+str(month)+'.html'
    
    # 偽瀏覽器
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.2171.95 Safari/537.36'}
    
    # 下載該年月的網站，並用pandas轉換成 dataframe
    r = requests.get(url, headers=headers)
    r.encoding = 'big5'

    dfs = pd.read_html(StringIO(r.text), encoding='big-5')

    df = pd.concat([df for df in dfs if df.shape[1] <= 11 and df.shape[1] > 5])
    
    if 'levels' in dir(df.columns):
        df.columns = df.columns.get_level_values(1)
    else:
        df = df[list(range(0,10))]
        column_index = df.index[(df[0] == '公司代號')][0]
        df.columns = df.iloc[column_index]
    
    df['當月營收'] = pd.to_numeric(df['當月營收'], 'coerce')
    df = df[~df['當月營收'].isnull()]
    df = df[df['公司代號'] != '合計']

    return df


#MAIN
stockid_list = get_all_stockid()

i = 0
j = 0
full_df = {}

print("下載各月份報表")
current_time.extend(compare_time)
for key in current_time:
    df = monthly_report(key)
    df = df.set_index('公司代號')
    full_df[key] = df
    print(key + " ready")

print("開始計算...")
for stockid in stockid_list:
    compare_time_revenue_avg = 0
    compare_time_revenue_sum = 0
    current_time_revenue_avg = 0
    current_time_revenue_sum = 0
    for current in current_time:
        try:
            current_time_revenue_sum += full_df[current].at[str(stockid), '當月營收']
        except Exception as e:
            break
    current_time_revenue_avg = int(current_time_revenue_sum / len(current_time)) 

    for compare in compare_time:
        try:
            compare_time_revenue_sum += full_df[compare].at[str(stockid), '當月營收']
        except Exception as e:
            break
    compare_time_revenue_avg = int(compare_time_revenue_sum / len(compare_time))

    if current_time_revenue_avg > compare_time_revenue_avg:
        if (compare_time_revenue_avg == 0):
            continue
        ratio = round((current_time_revenue_avg / compare_time_revenue_avg), 2)
    else:
        continue
    if (ratio > threshold_ratio):
        print(stockid + ", 近期營收平均:" +  str(current_time_revenue_avg) + ", 過去營收平均:" + str(compare_time_revenue_avg) + ", 成長百分比:" + str(ratio) )

