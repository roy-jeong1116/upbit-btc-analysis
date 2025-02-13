import requests, time
import pandas as pd

from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By

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

# 거래량 상위 구간 및 변동성 구하기
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

# UBCI 사이트에서 공포지수와 관련된 정보 가져오기
def fetch_data_from_ubci():
    driver = webdriver.Chrome()
    
    url = 'https://www.ubcindex.com/feargreed'
    driver.get(url)

    time.sleep(5)

    today_score = driver.find_element(By.CSS_SELECTOR, '.score_box > div > div > div > .score').text
    today_status = driver.find_element(By.CSS_SELECTOR, '.score_box > div > .items > .item.active').text

    # 현재 공포지수
    today_score = float(today_score.split('\n')[0])
    # 현재 공포지수 구간
    today_level = today_status.split('\n')[0]
    # 어제 공포지수와의 차이
    difference_yesterday = float(driver.find_element(By.CSS_SELECTOR, '.historyTbl > tbody > tr:nth-child(3) > td:nth-child(2) > div > div').text)
    # 일주일 전 공포지수와의 차이
    difference_week = float(driver.find_element(By.CSS_SELECTOR, '.historyTbl > tbody > tr:nth-child(3) > td:nth-child(3) > div > div').text)

    driver.quit()

    ubci_data = [today_score, today_level, difference_yesterday, difference_week]

    return ubci_data

# 공포지수 변화에 따른 시장 분석 메시지
def analyze_market_trend(today_level, difference_yesterday, difference_week):
    if today_level == '매우공포':
        if difference_yesterday > 0 and difference_week > 0: trend = "공포지수가 연속적으로 상승하며 투자 심리가 점진적으로 회복되고 있습니다. 단기적으로 매수세가 유입될 가능성이 있습니다."
        elif difference_yesterday > 0 and difference_week < 0: trend = "단기적으로 공포지수가 상승했으나, 중기적으로는 하락 추세였습니다. 시장이 변동성을 보이며 방향성을 찾는 중입니다."
        elif difference_yesterday < 0 and difference_week > 0: trend = "단기적으로 공포지수가 하락하며 투자 심리가 악화되고 있지만, 중기적으로는 회복세를 보일 가능성이 있습니다."
        else: trend = "공포지수가 단기 및 중기적으로 모두 하락하며 투자 심리가 극도로 위축되었습니다. 추가적인 매도세가 발생할 가능성이 큽니다."

    elif today_level == '공포':
        if difference_yesterday > 0 and difference_week > 0: trend = "공포지수가 지속적으로 상승하며 투자 심리가 회복되는 조짐을 보이고 있습니다. 시장의 안정 가능성이 높아지고 있습니다."
        elif difference_yesterday > 0 and difference_week < 0: trend = "단기적으로 공포지수가 상승했지만, 중기적으로는 하락하는 흐름입니다. 시장이 불안정한 조정을 겪을 수 있습니다."
        elif difference_yesterday < 0 and difference_week > 0: trend = "단기적인 투자 심리 악화에도 불구하고, 중기적으로는 매수 심리가 살아날 가능성이 있습니다."
        else: trend = "공포지수가 단기 및 중기적으로 모두 하락하며 매도세가 강하게 유지되고 있습니다."

    elif today_level == '중립':
        if difference_yesterday > 0 and difference_week > 0: trend = "공포지수가 지속적으로 상승하며 투자 심리가 개선되고 있습니다. 시장이 점진적으로 상승할 가능성이 있습니다."
        elif difference_yesterday > 0 and difference_week < 0: trend = "단기적인 매수 심리 개선이 있지만, 중기적으로는 불안정한 흐름이 지속될 수 있습니다."
        elif difference_yesterday < 0 and difference_week > 0: trend = "단기적으로 매도 우위가 형성되었지만, 중기적으로는 긍정적인 흐름을 기대할 수 있습니다."
        else: trend = "공포지수가 단기 및 중기적으로 모두 하락하며 조정 압력이 강해지고 있습니다."

    elif today_level == '탐욕':
        if difference_yesterday > 0 and difference_week > 0: trend = "공포지수가 연속적으로 상승하며 투자 심리가 더욱 강해지고 있습니다. 시장의 긍정적인 흐름이 지속될 가능성이 있습니다."
        elif difference_yesterday > 0 and difference_week < 0: trend = "단기적으로 매수 심리가 강해졌지만, 중기적으로는 차익 실현 매물이 출현할 가능성이 있습니다."
        elif difference_yesterday < 0 and difference_week > 0: trend = "단기적으로 매도 압력이 나타났지만, 중기적으로는 여전히 강세 흐름을 유지할 가능성이 있습니다."
        else: trend = "공포지수가 하락하며 탐욕 심리가 둔화되고 있습니다. 조정 국면이 발생할 가능성이 높습니다."

    elif today_level == '매우탐욕':
        if difference_yesterday > 0 and difference_week > 0: trend = "강한 매수세가 지속되며 시장이 상승 흐름을 유지하고 있습니다. 추가적인 상승 가능성이 높습니다."
        elif difference_yesterday > 0 and difference_week < 0: trend = "단기적으로는 강한 매수세가 유지되지만, 중기적으로는 과열된 시장이 조정될 가능성이 있습니다."
        elif difference_yesterday < 0 and difference_week > 0: trend = "단기적으로 차익 실현이 발생했지만, 중기적으로는 여전히 강한 상승 흐름을 유지할 가능성이 있습니다."
        else: trend = "공포지수가 단기 및 중기적으로 모두 하락하며 시장의 과열이 완화되고 있습니다. 조정 국면이 올 수 있습니다."

    else:
        trend = "공포지수 구간을 인식할 수 없습니다."

    return trend