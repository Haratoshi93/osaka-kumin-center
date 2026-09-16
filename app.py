import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime

# 施設一覧
FACILITIES = {
    '01': '大阪市立北区民センター',
    '02': '大阪市立大淀コミュニティセンター',
    '03': 'まるよし精肉店 都島区民センター',
    '04': 'NORBDENCE福島区民センター',
    '05': '大阪市立此花区民ホール',
    '06': 'J:COM中央区民センター',
    '07': '大阪市立中央会館',
    '08': '株式会社ノーブデンス西区民センター',
    '10': '大阪市立港近隣センター',
    '11': '藤井組 大正会館',
    '12': '大阪市立天王寺区民センター',
    '13': '大阪市立浪速区民センター',
    '14': '近藤技研工業 西淀川区民ホール',
    '15': '大阪市立西淀川区民会館',
    '16': '大阪市立淀川区民センター',
    '17': '大阪市立東淀川区民会館',
    '18': '大阪市立東成区民センター',
    '19': '大阪市立生野区民センター',
    '20': '日タク旭区民センター',
    '22': '大阪市立鶴見区民センター',
    '23': '大阪市立阿倍野区民センター',
    '24': '大阪市立住之江会館',
    '25': '錦秀会住吉区民センター',
    '26': '大阪市立東住吉会館',
    '27': '大阪市立平野区民センター',
    '28': '大阪市立平野区民ホール',
    '29': '大阪市立西成区民センター',
    '30': '大阪市立城東区民センター',
    '31': '藤井組 大正区民ホール',
    '32': '大阪市立東淀川区民ホール',
    '33': '大阪市立すみのえ舞昆ホール',
    '34': '大阪市立東住吉区民ホール',
    '35': '大阪市立港区民センター'
}

st.set_page_config(page_title="大阪市区民センター 空き状況", page_icon="🏢", layout="wide")
st.title("🏢 大阪市区民センター 空き状況確認")

st.markdown("""
大阪市の区役所附設会館（区民センターなど）の会議室の空き状況をリアルタイムで確認できます。左のサイドバーから施設を選んでください。
""")

# サイドバー
st.sidebar.header("検索条件")
selected_name = st.sidebar.selectbox("施設を選択", list(FACILITIES.values()))

# コードを逆引き
selected_code = [k for k, v in FACILITIES.items() if v == selected_name][0]

@st.cache_data(ttl=600)
def fetch_availability(scd):
    try:
        s = requests.Session()
        s.headers.update({'User-Agent': 'Mozilla/5.0'})
        
        # 1. ページにアクセスしてCSRFトークンを取得
        url_get = f"https://www.shisetsu-osaka.jp/shisetsu-nw/akijokyo.html?scd={scd}"
        resp_get = s.get(url_get, verify=False)
        resp_get.raise_for_status()
        
        soup = BeautifulSoup(resp_get.content, 'html.parser')
        form = soup.find('form', id='dForm')
        if not form:
            return None, "トークンが見つかりませんでした。"
            
        csrf = form.find('input', {'name': '_csrf'}).get('value')
        
        # 2. REST APIにPOSTしてデータを取得
        url_post = "https://www.shisetsu-osaka.jp/shisetsu-nw/restapi/akijokyo.html"
        post_data = {
            '_csrf': csrf,
            'scd': scd,
            'sdate': ''
        }
        resp_post = s.post(url_post, data=post_data, verify=False)
        resp_post.raise_for_status()
        
        result = resp_post.json()
        if 'data' not in result or 'akijokyo' not in result['data']:
            return None, "空き状況データが取得できませんでした。"
            
        headers_info = result['data'].get('header', [])
        headers = [h['value'] for h in headers_info]
        
        data = []
        for room in result['data']['akijokyo']:
            room_name = room.get('roomName', room.get('roomDispName', '不明'))
            row = {'部屋名': room_name}
            
            for i, date_info in enumerate(room.get('dateList', [])):
                if i < len(headers):
                    date_header = headers[i]
                    am = "-"
                    pm = "-"
                    night = "-"
                    
                    time_list = date_info.get('availTimeList', [])
                    if len(time_list) >= 1: am = time_list[0].get('statusDisp', '-')
                    if len(time_list) >= 2: pm = time_list[1].get('statusDisp', '-')
                    if len(time_list) >= 3: night = time_list[2].get('statusDisp', '-')
                    
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
            st.success(f"情報を取得しました！（{datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')} 時点）")
            
            # テーブルの表示を綺麗にする
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )
            
            st.info("※ 「〇」は空きあり、「×」は予約不可・空きなし、「-」は受付期間外などを表します。")
            st.markdown(f"[大阪市施設予約システムへ移動して予約する](https://www.shisetsu-osaka.jp/shisetsu-nw/akijokyo.html?scd={selected_code})")
            
        else:
            st.warning("データがありませんでした。")
