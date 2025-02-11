from utils import *

def main():
    # Upbit API에서 데이터 가져오기
    data = fetch_data_from_upbit()

    # 데이터 전처리
    df = preprocess_data(data)

    # 지지 및 저항 구간 계산
    key_levels = calculate_price_bins(df)

    # 지지 및 저항 구간 출력
    print(key_levels)

if __name__ == '__main__':
    main()