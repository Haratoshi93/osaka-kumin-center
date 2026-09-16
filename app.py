import streamlit as st
import requests
from bs4 import BeautifulSoup
import datetime
import urllib3
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
    
    /* ページ最大幅を制限して中央寄せ */
    .block-container {
        max-width: 1400px;
        padding: 2rem 2rem 5rem 2rem;
    }
    
    /* ページヘッダー */
    .page-header {
        text-align: center;
        padding: 40px 0 30px 0;
    }
    .page-header h1 {
        font-size: 30px;
        font-weight: 700;
        letter-spacing: -0.5px;
        margin-bottom: 8px;
    }
    .page-header p {
        font-size: 14px;
        color: #718096;
    }
    
    /* 検索ボタンのカスタム */
    div.stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 14px 32px;
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
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 12px rgba(0,0,0,0.04);
        overflow-x: auto;
    }
    
    .result-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
    .result-title {
        font-size: 16px;
        font-weight: 700;
    }
    .result-timestamp {
        font-size: 12px;
        color: #a0aec0;
    }
    
    /* テーブル本体 */
    table.vc-table {
        width: 100%;
        border-collapse: collapse;
        white-space: nowrap;
    }
    table.vc-table th {
        font-size: 12px;
        font-weight: 700;
        padding: 14px 16px;
        border-bottom: 2px solid #edf2f7;
        text-align: center;
    }
    table.vc-table th.room-header {
        text-align: left;
        min-width: 200px;
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
        padding: 12px 10px;
        border-bottom: 1px solid #f0f4f8;
        vertical-align: middle;
        text-align: center;
        min-width: 90px;
    }
    table.vc-table td.room-cell {
        text-align: left;
        border-right: 2px solid #edf2f7;
        padding-left: 16px;
    }
    table.vc-table tr:last-child td {
        border-bottom: none;
    }
    table.vc-table tr:hover td {
        background: #f7fafc;
    }
    table.vc-table tr:hover td.room-cell {
        background: #edf2f7;
    }
    
    /* 施設名・部屋名 */
    .facility-tag {
        display: inline-block;
        font-size: 10px;
        font-weight: 600;
        background: #ebf4ff;
        color: #3182ce;
        padding: 2px 7px;
        border-radius: 20px;
        margin-bottom: 5px;
        letter-spacing: 0.3px;
    }
    .room-label {
        font-size: 13px;
        font-weight: 700;
        color: #2d3748;
    }
    
    /* スロット表示 */
    .slot-box {
        display: flex;
        flex-direction: column;
        gap: 4px;
        align-items: center;
    }
    .slot-item {
        display: flex;
        align-items: center;
        gap: 5px;
        font-size: 12px;
    }
    .slot-time {
        font-size: 10px;
        color: #a0aec0;
        width: 20px;
        text-align: right;
    }
    .slot-icon {
        width: 22px;
        height: 22px;
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
        margin-top: 24px;
        padding-top: 20px;
        border-top: 1px solid #edf2f7;
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        align-items: center;
    }
    .link-label {
        font-size: 12px;
        color: #718096;
        font-weight: 600;
    }
    a.booking-btn {
        display: inline-block;
        padding: 8px 18px;
        background: white;
        border: 1.5px solid #667eea;
        color: #667eea !important;
        text-decoration: none;
        border-radius: 8px;
        font-size: 13px;
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
        gap: 16px;
        align-items: center;
        font-size: 12px;
        color: #718096;
        margin-top: 16px;
        padding-top: 16px;
        border-top: 1px solid #edf2f7;
    }
    .legend-item {
        display: flex;
        align-items: center;
        gap: 5px;
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
    <p>大阪市内の区民センター・会館の会議室空き状況をまとめて検索できます</p>
</div>
""", unsafe_allow_html=True)

# --- 検索パネル ---
st.markdown("### 検索条件")

col_fac, col_start, col_end = st.columns([4, 2, 2])

with col_fac:
    selected_names = st.multiselect(
        "施設を選択（複数可）",
        list(FACILITIES.values()),
        default=[FACILITIES['18']],
        placeholder="施設を選んでください..."
    )

today = datetime.date.today()
default_end = today + datetime.timedelta(days=7)

with col_start:
    start_date = st.date_input("開始日", value=today)

with col_end:
    end_date = st.date_input("終了日", value=default_end)

col_cap, col_type, col_btn = st.columns([2, 3, 3])

with col_cap:
    min_capacity = st.number_input("最低利用人数", min_value=0, value=0, step=1, help="この人数以上が定員の部屋のみ表示します（0の場合は全て表示）")

with col_type:
    st.write("") # 縦位置合わせ
    show_only_meeting = st.checkbox("集会室・会議室のみ表示", value=True, help="チェックを入れると「集会」または「会議」という名前が含まれる部屋のみに絞り込みます（ホール等は除外されます）")

with col_btn:
    st.write("") # 縦位置合わせ
    search_clicked = st.button("空き状況を検索", type="primary")

NAME_TO_CODE = {v: k for k, v in FACILITIES.items()}
selected_codes = [NAME_TO_CODE[name] for name in selected_names]

# --- 曜日判定 ---
def get_day_class(date_str):
    """日付文字列（例：2026/9/16(水)）から曜日CSSクラスを返す"""
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

@st.cache_data(ttl=600)
def fetch_availability_html(scds, start_date, end_date, min_cap, only_meeting):
    try:
        s = requests.Session()
        s.headers.update({'User-Agent': 'Mozilla/5.0'})
        
        url_get = f"https://www.shisetsu-osaka.jp/shisetsu-nw/akijokyo.html?scd={scds[0]}"
        resp_get = s.get(url_get, verify=False)
        resp_get.raise_for_status()
        
        soup = BeautifulSoup(resp_get.content, 'html.parser')
        form = soup.find('form', id='dForm')
        if not form:
            return None, "システムからセキュリティトークンが取得できませんでした。"
        csrf = form.find('input', {'name': '_csrf'}).get('value')
        
        monday = start_date - datetime.timedelta(days=start_date.weekday())
        target_mondays = []
        while monday <= end_date:
            target_mondays.append(monday)
            monday += datetime.timedelta(days=7)
            
        all_date_headers = set()
        room_data_map = {}
        url_post = "https://www.shisetsu-osaka.jp/shisetsu-nw/restapi/akijokyo.html"
        
        for scd in scds:
            facility_name = FACILITIES[scd]
            for monday_date in target_mondays:
                post_data = {'_csrf': csrf, 'scd': scd, 'sdate': monday_date.strftime("%Y-%m-%d")}
                resp_post = s.post(url_post, data=post_data, verify=False)
                resp_post.raise_for_status()
                result = resp_post.json()
                
                if 'data' not in result or 'akijokyo' not in result['data']:
                    continue
                    
                headers_info = result['data'].get('header', [])
                headers = [h['value'] for h in headers_info]
                
                for room in result['data']['akijokyo']:
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
                    
                    if dict_key not in room_data_map:
                        room_data_map[dict_key] = {
                            'facility': facility_name,
                            'room': room_name,
                            'capacity': capacity,
                            'code': scd,
                            'dates': {}
                        }
                    
                    for i, date_info in enumerate(room.get('dateList', [])):
                        if i < len(headers):
                            raw_date_str = date_info.get('riyoDate')
                            if not raw_date_str: continue
                            
                            cur_dt = datetime.datetime.strptime(raw_date_str, "%Y-%m-%d").date()
                            if start_date <= cur_dt <= end_date:
                                date_header = headers[i]
                                all_date_headers.add(date_header)
                                
                                am, pm, night = "-", "-", "-"
                                time_list = date_info.get('availTimeList', [])
                                if len(time_list) >= 1: am = time_list[0].get('statusDisp', '-')
                                if len(time_list) >= 2: pm = time_list[1].get('statusDisp', '-')
                                if len(time_list) >= 3: night = time_list[2].get('statusDisp', '-')
                                
                                room_data_map[dict_key]['dates'][date_header] = (am, pm, night)
                                
        if not room_data_map:
             return None, "条件に一致するデータが見つかりませんでした。人数条件を緩めるか、期間や施設を変えてお試しください。"
             
        sorted_dates = sorted(list(all_date_headers), key=lambda x: datetime.datetime.strptime(x.split('(')[0], "%Y/%m/%d"))
        
        # HTML組み立て
        html = '<table class="vc-table">'
        html += '<thead><tr><th class="room-header">施設 / 部屋名</th>'
        for d in sorted_dates:
            day_cls = get_day_class(d)
            html += f'<th class="{day_cls}">{d}</th>'
        html += '</tr></thead><tbody>'
        
        for key, data in room_data_map.items():
            html += '<tr>'
            html += f'<td class="room-cell"><span class="facility-tag">{data["facility"]}</span><br><span class="room-label">{data["room"]} <span style="font-size:11px; color:#a0aec0; font-weight:normal;">(定員: {data["capacity"]}名)</span></span></td>'
            for d in sorted_dates:
                slots = data['dates'].get(d)
                if slots:
                    am, pm, night = slots
                    html += '<td><div class="slot-box">'
                    html += f'<div class="slot-item"><span class="slot-time">午前</span>{get_slot_html(am)}</div>'
                    html += f'<div class="slot-item"><span class="slot-time">午後</span>{get_slot_html(pm)}</div>'
                    html += f'<div class="slot-item"><span class="slot-time">夜間</span>{get_slot_html(night)}</div>'
                    html += '</div></td>'
                else:
                    html += '<td><div class="slot-icon na" style="margin:auto;">－</div></td>'
            html += '</tr>'
            
        html += '</tbody></table>'
        
        # 凡例
        html += '''
        <div class="legend">
            <div class="legend-item"><div class="slot-icon ok" style="margin:0;">○</div> 空きあり</div>
            <div class="legend-item"><div class="slot-icon ng" style="margin:0;">×</div> 予約済み・空きなし</div>
            <div class="legend-item"><div class="slot-icon na" style="margin:0;">－</div> 受付期間外など</div>
        </div>
        '''
        
        return html, None
        
    except Exception as e:
        return None, f"データの取得中にエラーが発生しました: {e}"

# --- メイン処理 ---
if search_clicked:
    if not selected_codes:
        st.warning("施設を1つ以上選択してください。")
    elif start_date > end_date:
        st.warning("終了日は開始日以降に設定してください。")
    else:
        with st.spinner("データを取得・集計しています..."):
            html_table, error = fetch_availability_html(tuple(selected_codes), start_date, end_date, min_capacity, show_only_meeting)
            
            if error:
                st.error(error)
            elif html_table:
                now_str = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                
                # インデントをなくしてMarkdownのコードブロック扱いになるのを防ぐ
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
            else:
                st.warning("指定された条件のデータが見つかりませんでした。")
