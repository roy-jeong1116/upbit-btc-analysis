import requests
import pandas as pd
from datetime import datetime, timedelta

# Upbit API에서 데이터 가져오기
def fetch_data_from_upbit():
    url = "https://api.upbit.com/v1/candles/days"
    params = {  
        'market': 'KRW-BTC',  
        'count': 60,
        'to': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
        'converting_price_unit': 'KRW'
    }  
    headers = {"accept": "application/json"}

    response = requests.get(url, params=params, headers=headers)
    data = response.json()

    return data

# 데이터 전처리
def preprocess_data(data):
    # 데이터를 데이터프레임으로 만들기
    df = pd.DataFrame(data)
    
    # 데이터 필터링
    df = df[['market', 'candle_date_time_kst', 'high_price', 'low_price', 'trade_price', 'candle_acc_trade_volume', 'change_rate']]
    df.columns = ['SYMBOL', 'DATE', 'HIGH_PRICE', 'LOW_PRICE', 'CLOSING_PRICE', 'TRADING_VOLUME', 'VARIANCE']
    
    # 가독성 향상
    df['DATE'] = pd.to_datetime(df['DATE']) 
    df['DATE'] = df['DATE'].dt.strftime('%Y-%m-%d')

    # 데이터 타입 변환
    df[['HIGH_PRICE', 'LOW_PRICE', 'CLOSING_PRICE', 'TRADING_VOLUME']] = df[['HIGH_PRICE', 'LOW_PRICE', 'CLOSING_PRICE', 'TRADING_VOLUME']].astype(int)
    
    return df

def calculate_price_bins(df):
    # 고가와 저가 사이의 값들을 40개의 구간으로 나누기
    bin_size = (df['HIGH_PRICE'].max() - df['LOW_PRICE'].min()) / 40
    df['PRICE_BIN_START'] = ((df['CLOSING_PRICE'] // bin_size) * bin_size).astype(int)
    df['PRICE_BIN_END'] = (df['PRICE_BIN_START'] + bin_size).astype(int)

    # 가격 구간별 거래량의 합과 변동성의 평균 구하기
    price_volume_variance = df.groupby('PRICE_BIN_START').agg({
        'TRADING_VOLUME': 'sum',
        'VARIANCE': 'mean'
    }).reset_index()

    # PRICE_BIN_END 값 계산해서 추가
    price_volume_variance['PRICE_BIN_END'] = (price_volume_variance['PRICE_BIN_START'] + bin_size).astype(int)

    # 거래량 상위 20%인 가격 구간 추출
    threshold = price_volume_variance['TRADING_VOLUME'].quantile(0.8)
    key_levels = price_volume_variance[price_volume_variance['TRADING_VOLUME'] >= threshold]

    # 컬럼 순서 변경
    key_levels = key_levels[['PRICE_BIN_START', 'PRICE_BIN_END', 'TRADING_VOLUME', 'VARIANCE']]

    return key_levels