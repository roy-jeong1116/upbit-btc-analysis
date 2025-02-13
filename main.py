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

    # UBCI 데이터 가져오기
    ubci_data = fetch_data_from_ubci()

    # UBCI 정보 출력
    print(f"\n현재 공포지수: {ubci_data[0]} >>> {ubci_data[1]}")
    print(f"공포지수 변화: 전일 대비 {ubci_data[2]}, 일주일 전 대비 {ubci_data[3]}")

    # 시장 분석 수행
    trend_analysis = analyze_market_trend(ubci_data[1], ubci_data[2], ubci_data[3])

    # 분석 결과 출력
    print(f"\n시장 분석 결과: {trend_analysis}")

if __name__ == '__main__':
    main()