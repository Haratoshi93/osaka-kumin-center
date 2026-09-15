import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime

# 施設一覧
FACILITIES = {
    '01': '北区民センター',
    '02': '都島区民センター',
    '03': '福島区民センター',
    '04': '此花区民ホール',
    '05': '中央区民センター',
    '06': '西区民センター',
    '07': '港区民センター',
    '08': '大正区民ホール',
    '09': '天王寺区民センター',
    '10': '浪速区民センター',
    '11': '西淀川区民会館',
    '12': '淀川区民センター',
    '13': '東淀川区民会館',
    '14': '東成区民センター',
    '15': '生野区民センター',
    '16': '旭区民センター',
    '17': '城東区民センター',
    '18': '鶴見区民センター',
    '19': '阿倍野区民センター',
    '20': '住之江会館',
    '21': '住吉区民センター',
    '22': '東住吉会館',
    '23': '平野区民センター',
    '24': '西成区民センター',
    '25': '中央会館',
    '27': '大淀コミュニティセンター',
    '29': '港近隣センター',
    '30': '大正会館',
    '31': '西淀川区民ホール',
    '33': '東淀川区民ホール',
    '35': 'すみのえ舞昆ホール',
    '36': '東住吉区民ホール',
    '37': '平野区民ホール',
}

st.set_page_config(page_title="大阪市区民センター 空き状況", page_icon="🏢", layout="wide")
st.title("🏢 大阪市区民センター 空き状況確認")

st.markdown("""
大阪市の区役所附設会館（区民センターなど）の会議室の空き状況をリアルタイムで確認できます。
左のサイドバーから施設を選んでください。
""")

# サイドバー
st.sidebar.header("検索条件")
selected_name = st.sidebar.selectbox("施設を選択", list(FACILITIES.values()))

# コードを逆引き
selected_code = [k for k, v in FACILITIES.items() if v == selected_name][0]

@st.cache_data(ttl=600)
def fetch_availability(scd):
    url = f"https://www.shisetsu-osaka.jp/shisetsu-nw/akijokyo.html?scd={scd}"
    try:
        # SSL検証をスキップ
        response = requests.get(url, verify=False, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        table = soup.find('table', class_='tbl-akijokyo')
        if not table:
            return None, "空き状況の表が見つかりませんでした。"
            
        # ヘッダー取得（日付）
        headers = []
        thead = table.find('thead')
        date_rows = thead.find_all('tr')[0].find_all('th')
        for th in date_rows[1:]: # 最初の「部屋/時間帯」をスキップ
            headers.append(th.text.strip())
            
        data = []
        tbody = table.find('tbody')
        if not tbody:
             return None, "データが見つかりませんでした。"
             
        for tr in tbody.find_all('tr'):
            th = tr.find('th')
            if not th: continue
            
            # 部屋名
            room_name_span = th.find('span')
            room_name = room_name_span.text.strip() if room_name_span else "不明"
            
            # 状況（午前、午後、夜間 が各日付に対してある）
            tds = tr.find_all('td', class_='aday')
            
            row = {'部屋名': room_name}
            for i, date_header in enumerate(headers):
                # 1日につき3スロット（午前、午後、夜間）
                if i*3 + 2 < len(tds):
                    am = tds[i*3].get('data-obj', '-')
                    pm = tds[i*3+1].get('data-obj', '-')
                    night = tds[i*3+2].get('data-obj', '-')
                    row[date_header] = f"【午前】{am} 【午後】{pm} 【夜間】{night}"
            
            data.append(row)
            
        df = pd.DataFrame(data)
        return df, None
        
    except Exception as e:
        return None, f"エラーが発生しました: {e}"

if st.sidebar.button("空き状況を確認"):
    with st.spinner(f"{selected_name} の空き状況を取得中..."):
        # 警告を非表示
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        df, error = fetch_availability(selected_code)
        
        if error:
            st.error(error)
        elif df is not None and not df.empty:
            st.success(f"情報を取得しました！ ({datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')} 時点)")
            
            # テーブルの表示を綺麗にする
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )
            
            st.info("※ 「○」は空きあり、「×」は予約不可・空きなし、「-」は受付期間外などを表します。")
            st.markdown(f"[大阪市施設予約システムへ移動して予約する](https://www.shisetsu-osaka.jp/shisetsu-nw/akijokyo.html?scd={selected_code})")
            
        else:
            st.warning("データがありませんでした。")
