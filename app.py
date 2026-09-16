import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import urllib3
import concurrent.futures
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 施設一覧
FACILITIES = {
    '01': '大阪市立北区民センター',
    '02': '大阪市立大淀コミュニティセンター',
    '03': '都島区民センター',
    '04': '福島区民センター',
    '05': '大阪市立此花区民ホール',
    '06': 'J:COM中央区民センター',
    '07': '大阪市立中央会館',
    '08': '西区民センター',
    '10': '大阪市立港近隣センター',
    '11': '大正会館',
    '12': '大阪市立天王寺区民センター',
    '13': '大阪市立浪速区民センター',
    '14': '西淀川区民ホール',
    '15': '大阪市立西淀川区民会館',
    '16': '大阪市立淀川区民センター',
    '17': '大阪市立東淀川区民会館',
    '18': '大阪市立東成区民センター',
    '19': '大阪市立生野区民センター',
    '20': '旭区民センター',
    '22': '大阪市立鶴見区民センター',
    '23': '大阪市立阿倍野区民センター',
    '24': '大阪市立住之江会館',
    '25': '住吉区民センター',
    '26': '大阪市立東住吉会館',
    '27': '大阪市立平野区民センター',
    '28': '大阪市立平野区民ホール',
    '29': '大阪市立西成区民センター',
    '30': '大阪市立城東区民センター',
    '31': '大正区民ホール',
    '32': '大阪市立東淀川区民ホール',
    '33': '大阪市立すみのえ舞昆ホール',
    '34': '大阪市立東住吉区民ホール',
    '35': '大阪市立港区民センター'
}

# --- ページ設定 ---
st.set_page_config(
    page_title="大阪市区民センター 空き状況確認",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- カスタムCSS ---
custom_css = """
<style>
    /* 不要なStreamlitのUIを非表示 */
    #MainMenu, [data-testid="stHeader"], footer, [data-testid="collapsedControl"] {visibility: hidden;}
    
    /* 全体フォント */
    html, body, [class*="css"] {
        font-family: 'Helvetica Neue', 'Hiragino Kaku Gothic ProN', 'Hiragino Sans', Meiryo, sans-serif;
    }
    
    /* スマホ向けに余白を削減 */
    .block-container {
        max-width: 1400px;
        padding: 1rem 1rem 4rem 1rem;
    }
    
    /* ページヘッダー */
    .page-header {
        text-align: center;
        padding: 20px 0 20px 0;
    }
    .page-header h1 {
        font-size: 24px;
        font-weight: 700;
        letter-spacing: -0.5px;
        margin-bottom: 4px;
    }
    .page-header p {
        font-size: 13px;
        color: #718096;
    }
    
    /* 検索ボタンのカスタム */
    div.stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 24px;
        font-size: 15px;
        font-weight: 600;
        width: 100%;
        cursor: pointer;
        letter-spacing: 0.3px;
        transition: all 0.2s ease;
        box-shadow: 0 4px 15px rgba(102,126,234,0.4);
    }
    div.stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(102,126,234,0.5);
    }
    
    /* テーブルラッパー */
    .result-panel {
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 12px rgba(0,0,0,0.04);
        overflow-x: auto;
    }
    
    .result-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
    }
    .result-title {
        font-size: 15px;
        font-weight: 700;
    }
    .result-timestamp {
        font-size: 11px;
        color: #a0aec0;
    }
    
    /* テーブル本体 */
    table.vc-table {
        width: 100%;
        border-collapse: collapse;
        /* スマホで折り返すためにnowrapは解除 */
    }
    table.vc-table th {
        font-size: 12px;
        font-weight: 700;
        padding: 12px 10px;
        border-bottom: 2px solid #edf2f7;
        text-align: center;
    }
    table.vc-table th.room-header {
        text-align: left;
        min-width: 120px;
        border-right: 2px solid #edf2f7;
    }
    /* 日付ヘッダー：土曜・日曜の色分け */
    table.vc-table th.sat {
        color: #3182ce;
    }
    table.vc-table th.sun, table.vc-table th.hol {
        color: #e53e3e;
    }
    table.vc-table td {
        padding: 12px 8px;
        border-bottom: 1px solid #f0f4f8;
        vertical-align: middle;
        text-align: center;
        min-width: 120px;
    }
    table.vc-table td.room-cell {
        text-align: left;
        border-right: 2px solid #edf2f7;
        padding-left: 10px;
        line-height: 1.4;
    }
    table.vc-table tr:last-child td {
        border-bottom: none;
    }
    
    /* 施設名・部屋名 */
    .facility-tag {
        display: inline-block;
        font-size: 10px;
        font-weight: 600;
        background: #ebf4ff;
        color: #3182ce;
        padding: 3px 8px;
        border-radius: 20px;
        margin-bottom: 6px;
        letter-spacing: 0.3px;
    }
    .room-label {
        font-size: 13px;
        font-weight: 700;
        color: #2d3748;
    }
    
    /* スロット表示（スマホ向けに横並び） */
    .slot-box {
        display: flex;
        flex-direction: row;
        justify-content: center;
        gap: 12px;
    }
    .slot-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
    }
    .slot-time {
        font-size: 10px;
        color: #a0aec0;
    }
    .slot-icon {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: 700;
        flex-shrink: 0;
    }
    .slot-icon.ok {
        background: #c6f6d5;
        color: #276749;
    }
    .slot-icon.ng {
        background: #fed7d7;
        color: #9b2335;
    }
    .slot-icon.na {
        background: #edf2f7;
        color: #a0aec0;
    }
    
    /* 予約リンクボタン */
    .link-section {
        margin-top: 20px;
        padding-top: 16px;
        border-top: 1px solid #edf2f7;
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        align-items: center;
    }
    .link-label {
        font-size: 12px;
        color: #718096;
        font-weight: 600;
    }
    a.booking-btn {
        display: inline-block;
        padding: 6px 14px;
        background: white;
        border: 1.5px solid #667eea;
        color: #667eea !important;
        text-decoration: none;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
        transition: all 0.15s;
    }
    a.booking-btn:hover {
        background: #667eea;
        color: white !important;
    }
    
    /* 凡例 */
    .legend {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        align-items: center;
        font-size: 11px;
        color: #718096;
        margin-top: 16px;
        padding-top: 12px;
        border-top: 1px solid #edf2f7;
    }
    .legend-item {
        display: flex;
        align-items: center;
        gap: 4px;
    }
    
    /* チェックボックス用のパディング調整 */
    .stCheckbox {
        padding-top: 35px;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- ページヘッダー ---
st.markdown("""
<div class="page-header">
    <h1>大阪市区民センター 空き状況確認</h1>
    <p>指定した日付の会議室空き状況を検索します</p>
</div>
""", unsafe_allow_html=True)

# --- 検索パネル ---
st.markdown("### 検索条件")

col_fac, col_date = st.columns([6, 4])

with col_fac:
    # デフォルトを東成区民センター(18)と阿倍野区民センター(23)に変更
    selected_names = st.multiselect(
        "施設を選択（複数可）",
        list(FACILITIES.values()),
        default=[FACILITIES['18'], FACILITIES['23']],
        placeholder="施設を選んでください..."
    )

today = datetime.date.today()

with col_date:
    target_date = st.date_input("検索日", value=today)

col_cap, col_type, col_btn = st.columns([3, 4, 3])

with col_cap:
    min_capacity = st.number_input("最低利用人数", min_value=0, value=0, step=1, help="この人数以上が定員の部屋のみ表示")

with col_type:
    st.write("") # 縦位置合わせ
    show_only_meeting = st.checkbox("集会室・会議室のみ表示", value=True)

with col_btn:
    st.write("") # 縦位置合わせ
    search_clicked = st.button("空き状況を検索", type="primary", use_container_width=True)

NAME_TO_CODE = {v: k for k, v in FACILITIES.items()}
selected_codes = [NAME_TO_CODE[name] for name in selected_names]

# --- 曜日判定 ---
def get_day_class(date_str):
    try:
        d = datetime.datetime.strptime(date_str.split('(')[0], "%Y/%m/%d")
        wd = d.weekday()
        if wd == 5: return "sat"
        if wd == 6: return "sun"
    except: pass
    return ""

def get_slot_html(status):
    if status == '〇':
        return '<div class="slot-icon ok">○</div>'
    elif status == '×':
        return '<div class="slot-icon ng">×</div>'
    else:
        return '<div class="slot-icon na">－</div>'

def fetch_single_facility(s, csrf, scd, monday_str, url_post):
    """並列処理用に1施設・1週間分のデータを取得する関数"""
    post_data = {'_csrf': csrf, 'scd': scd, 'sdate': monday_str}
    resp = s.post(url_post, data=post_data, verify=False, timeout=10)
    resp.raise_for_status()
    return scd, resp.json()

@st.cache_data(ttl=300)
def fetch_availability_html_single_day(scds, t_date, min_cap, only_meeting):
    try:
        s = requests.Session()
        s.headers.update({'User-Agent': 'Mozilla/5.0'})
        
        # セキュリティトークン(CSRF)を取得するために、最初の施設へGET
        url_get = f"https://www.shisetsu-osaka.jp/shisetsu-nw/akijokyo.html?scd={scds[0]}"
        resp_get = s.get(url_get, verify=False, timeout=10)
        resp_get.raise_for_status()
        
        soup = BeautifulSoup(resp_get.content, 'html.parser')
        form = soup.find('form', id='dForm')
        if not form:
            return None, "システムからセキュリティトークンが取得できませんでした。"
        csrf = form.find('input', {'name': '_csrf'}).get('value')
        
        # 該当週の月曜日を計算
        monday = t_date - datetime.timedelta(days=t_date.weekday())
        monday_str = monday.strftime("%Y-%m-%d")
        
        url_post = "https://www.shisetsu-osaka.jp/shisetsu-nw/restapi/akijokyo.html"
        
        room_data_map = {}
        target_date_header = ""
        
        # --- 並列処理で全施設へ同時にPOSTリクエストを送信 (高速化) ---
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_scd = {
                executor.submit(fetch_single_facility, s, csrf, scd, monday_str, url_post): scd 
                for scd in scds
            }
            
            for future in concurrent.futures.as_completed(future_to_scd):
                scd = future_to_scd[future]
                try:
                    scd_result, result_json = future.result()
                    
                    if 'data' not in result_json or 'akijokyo' not in result_json['data']:
                        continue
                        
                    headers_info = result_json['data'].get('header', [])
                    headers = [h['value'] for h in headers_info]
                    
                    facility_name = FACILITIES[scd]
                    
                    for room in result_json['data']['akijokyo']:
                        room_name = room.get('roomName', room.get('roomDispName', '不明'))
                        
                        # --- フィルター処理 ---
                        if only_meeting:
                            if "集会" not in room_name and "会議" not in room_name:
                                continue
                                
                        capacity = int(room.get('tenin', 0) or 0)
                        if min_cap > 0 and capacity < min_cap:
                            continue
                        # ----------------------
                        
                        dict_key = f"{scd}_{room_name}"
                        
                        for i, date_info in enumerate(room.get('dateList', [])):
                            if i < len(headers):
                                raw_date_str = date_info.get('riyoDate')
                                if not raw_date_str: continue
                                
                                cur_dt = datetime.datetime.strptime(raw_date_str, "%Y-%m-%d").date()
                                
                                # 指定された単一の日付のみを抽出
                                if cur_dt == t_date:
                                    target_date_header = headers[i]
                                    
                                    if dict_key not in room_data_map:
                                        room_data_map[dict_key] = {
                                            'facility': facility_name,
                                            'room': room_name,
                                            'capacity': capacity,
                                            'code': scd,
                                            'am': "-", 'pm': "-", 'night': "-"
                                        }
                                    
                                    time_list = date_info.get('availTimeList', [])
                                    if len(time_list) >= 1: room_data_map[dict_key]['am'] = time_list[0].get('statusDisp', '-')
                                    if len(time_list) >= 2: room_data_map[dict_key]['pm'] = time_list[1].get('statusDisp', '-')
                                    if len(time_list) >= 3: room_data_map[dict_key]['night'] = time_list[2].get('statusDisp', '-')
                                    
                except Exception as exc:
                    st.error(f"{FACILITIES[scd]} のデータ取得でエラーが発生しました: {exc}")
                    
        if not room_data_map or not target_date_header:
             return None, "条件に一致するデータが見つかりませんでした。"
             
        # 表示順を施設コード＞部屋名でソート
        sorted_keys = sorted(room_data_map.keys())
        
        # HTML組み立て (2カラム: 施設/部屋名 | スロット)
        day_cls = get_day_class(target_date_header)
        html = '<table class="vc-table">'
        html += f'<thead><tr><th class="room-header">施設 / 部屋名</th><th class="{day_cls}">{target_date_header}</th></tr></thead><tbody>'
        
        for key in sorted_keys:
            data = room_data_map[key]
            html += '<tr>'
            html += f'<td class="room-cell"><span class="facility-tag">{data["facility"]}</span><br><span class="room-label">{data["room"]} <span style="font-size:11px; color:#a0aec0; font-weight:normal;">(定員: {data["capacity"]}名)</span></span></td>'
            
            # スマホ用に最適化したスロット配置
            html += '<td><div class="slot-box">'
            html += f'<div class="slot-item"><span class="slot-time">午前</span>{get_slot_html(data["am"])}</div>'
            html += f'<div class="slot-item"><span class="slot-time">午後</span>{get_slot_html(data["pm"])}</div>'
            html += f'<div class="slot-item"><span class="slot-time">夜間</span>{get_slot_html(data["night"])}</div>'
            html += '</div></td>'
            
            html += '</tr>'
            
        html += '</tbody></table>'
        
        # 凡例
        html += '''
        <div class="legend">
            <div class="legend-item"><div class="slot-icon ok" style="margin:0;">○</div> 空きあり</div>
            <div class="legend-item"><div class="slot-icon ng" style="margin:0;">×</div> 予約済み・不可</div>
            <div class="legend-item"><div class="slot-icon na" style="margin:0;">－</div> 期間外など</div>
        </div>
        '''
        
        return html, None
        
    except Exception as e:
        return None, f"データの取得中にエラーが発生しました: {e}"

# --- メイン処理 ---
if search_clicked:
    if not selected_codes:
        st.warning("施設を1つ以上選択してください。")
    else:
        with st.spinner("データを高速取得しています..."):
            html_table, error = fetch_availability_html_single_day(tuple(selected_codes), target_date, min_capacity, show_only_meeting)
            
            if error:
                st.error(error)
            elif html_table:
                now_str = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                
                result_html = f'''<div class="result-panel">
<div class="result-header">
<div class="result-title">検索結果</div>
<div class="result-timestamp">最終更新：{now_str}</div>
</div>
{html_table}
<div class="link-section">
<span class="link-label">予約システムを開く：</span>
'''
                for code, name in zip(selected_codes, selected_names):
                    result_html += f'<a href="https://www.shisetsu-osaka.jp/shisetsu-nw/akijokyo.html?scd={code}" target="_blank" class="booking-btn">{name}</a>\n'
                result_html += '</div></div>'
                
                st.markdown(result_html, unsafe_allow_html=True)
