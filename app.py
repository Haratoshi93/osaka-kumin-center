import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

# Streamlit特有の英語メニューやフッターを非表示にする
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

st.title("🏢 大阪市区民センター 空き状況確認")

st.markdown("""
大阪市の区役所附設会館（区民センターなど）の会議室の空き状況をリアルタイムで確認できます。左のサイドバーから検索条件を設定してください。
""")

# サイドバー設定
st.sidebar.header("🔍 検索条件")

# 複数施設選択
selected_names = st.sidebar.multiselect(
    "施設を選択（複数選択可）", 
    list(FACILITIES.values()),
    default=[FACILITIES['18']] # デフォルトで東成区民センターを選択
)

# 日付範囲選択
today = datetime.date.today()
default_end = today + datetime.timedelta(days=7)
date_range = st.sidebar.date_input(
    "対象期間（開始日〜終了日）", 
    value=(today, default_end)
)

# コードを逆引きする辞書
NAME_TO_CODE = {v: k for k, v in FACILITIES.items()}
selected_codes = [NAME_TO_CODE[name] for name in selected_names]

@st.cache_data(ttl=600)
def fetch_availability(scds, start_date, end_date):
    """
    指定された複数の施設コードと日付範囲に基づいて空き状況を一括取得する
    """
    try:
        s = requests.Session()
        s.headers.update({'User-Agent': 'Mozilla/5.0'})
        
        # まずCSRFトークンを取得（どの施設コードでもOKなので最初のものを使用）
        url_get = f"https://www.shisetsu-osaka.jp/shisetsu-nw/akijokyo.html?scd={scds[0]}"
        resp_get = s.get(url_get, verify=False)
        resp_get.raise_for_status()
        
        soup = BeautifulSoup(resp_get.content, 'html.parser')
        form = soup.find('form', id='dForm')
        if not form:
            return None, "システムからセキュリティトークンが取得できませんでした。"
        csrf = form.find('input', {'name': '_csrf'}).get('value')
        
        # 取得すべき週（月曜日）のリストを作成
        current = start_date
        monday = current - datetime.timedelta(days=current.weekday())
        target_mondays = []
        while monday <= end_date:
            target_mondays.append(monday)
            monday += datetime.timedelta(days=7)
            
        all_data = [] # 最終的な行データのリスト
        all_date_headers = set() # 取得した日付のヘッダー一覧
        
        url_post = "https://www.shisetsu-osaka.jp/shisetsu-nw/restapi/akijokyo.html"
        
        # 施設ごとにデータ取得
        for scd in scds:
            facility_name = FACILITIES[scd]
            # 施設内の各部屋のデータ（日付を跨いで統合するため部屋ごとに辞書で管理）
            room_data_map = {} 
            
            for monday_date in target_mondays:
                post_data = {
                    '_csrf': csrf,
                    'scd': scd,
                    'sdate': monday_date.strftime("%Y-%m-%d")
                }
                resp_post = s.post(url_post, data=post_data, verify=False)
                resp_post.raise_for_status()
                result = resp_post.json()
                
                if 'data' not in result or 'akijokyo' not in result['data']:
                    continue
                    
                headers_info = result['data'].get('header', [])
                headers = [h['value'] for h in headers_info]
                
                for room in result['data']['akijokyo']:
                    room_name = room.get('roomName', room.get('roomDispName', '不明'))
                    
                    if room_name not in room_data_map:
                        room_data_map[room_name] = {'施設・部屋名': f"【{facility_name}】{room_name}"}
                    
                    for i, date_info in enumerate(room.get('dateList', [])):
                        if i < len(headers):
                            raw_date_str = date_info.get('riyoDate') # "YYYY-MM-DD"
                            if not raw_date_str: continue
                            
                            # 対象期間内の日付か判定
                            cur_dt = datetime.datetime.strptime(raw_date_str, "%Y-%m-%d").date()
                            if start_date <= cur_dt <= end_date:
                                date_header = headers[i]
                                all_date_headers.add(date_header)
                                
                                am, pm, night = "-", "-", "-"
                                time_list = date_info.get('availTimeList', [])
                                if len(time_list) >= 1: am = time_list[0].get('statusDisp', '-')
                                if len(time_list) >= 2: pm = time_list[1].get('statusDisp', '-')
                                if len(time_list) >= 3: night = time_list[2].get('statusDisp', '-')
                                
                                room_data_map[room_name][date_header] = f"【午前】{am} 【午後】{pm} 【夜間】{night}"
                                
            # 施設の全データをリストに追加
            all_data.extend(list(room_data_map.values()))
            
        if not all_data:
             return None, "条件に一致する空き状況データがありませんでした。"
             
        df = pd.DataFrame(all_data)
        
        # 列の並び替え（「施設・部屋名」を一番左にし、残りは日付順）
        # setからリスト化してソート（YYYY/MM/DDなので文字列ソートでOKだが、一応ちゃんとソートする）
        sorted_dates = sorted(list(all_date_headers), key=lambda x: datetime.datetime.strptime(x.split('(')[0], "%Y/%m/%d"))
        columns_order = ['施設・部屋名'] + sorted_dates
        
        # 存在しない日付列は作らないようにフィルタリング
        columns_order = [col for col in columns_order if col in df.columns]
        df = df[columns_order]
        
        # NaNをハイフンに置換
        df = df.fillna("-")
        
        return df, None
        
    except Exception as e:
        return None, f"エラーが発生しました: {e}"

if st.sidebar.button("空き状況を確認", type="primary"):
    # 日付のバリデーション
    if not selected_codes:
        st.warning("施設を1つ以上選択してください。")
    elif isinstance(date_range, tuple) and len(date_range) != 2:
        st.warning("対象期間の「終了日」も選択してください。（1日だけの場合は同じ日を2回クリックしてください）")
    else:
        start_date = date_range[0] if isinstance(date_range, tuple) else date_range
        end_date = date_range[1] if isinstance(date_range, tuple) and len(date_range) == 2 else start_date
        
        with st.spinner("データを取得・集計中..."):
            df, error = fetch_availability(selected_codes, start_date, end_date)
            
            if error:
                st.error(error)
            elif df is not None and not df.empty:
                st.success(f"情報を取得しました！（{datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')} 時点）")
                
                # スクロール可能な広い表を表示
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )
                
                st.info("※ 「〇」は空きあり、「×」は予約不可・空きなし、「-」は受付期間外などを表します。")
                
                # リンク生成（選択した最初の施設をリンクにする）
                st.markdown(f"[大阪市施設予約システムへ移動して予約する](https://www.shisetsu-osaka.jp/shisetsu-nw/akijokyo.html?scd={selected_codes[0]})")
                
            else:
                st.warning("データがありませんでした。")
