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

# --- ページ設定 ---
st.set_page_config(page_title="大阪市区民センター 空き状況確認", layout="wide")

# --- カスタムCSS（デザインの大幅改善） ---
custom_css = """
<style>
    /* Streamlitデフォルトの不要なUIを隠す */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 全体のフォントと背景色 */
    html, body, [class*="css"] {
        font-family: 'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', 'Hiragino Sans', Meiryo, sans-serif;
    }
    
    /* メインタイトルの装飾 */
    .main-title {
        font-size: 28px;
        font-weight: 700;
        color: #2c3e50;
        margin-bottom: 10px;
        padding-bottom: 15px;
        border-bottom: 2px solid #3498db;
    }
    
    .sub-description {
        font-size: 14px;
        color: #7f8c8d;
        margin-bottom: 30px;
    }
    
    /* カスタムテーブルのデザイン */
    .table-wrapper {
        overflow-x: auto;
        margin-top: 20px;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        background: #ffffff;
    }
    
    table.custom-table {
        width: 100%;
        border-collapse: collapse;
        text-align: center;
        background-color: white;
    }
    
    table.custom-table th {
        background-color: #f8f9fa;
        color: #34495e;
        font-size: 13px;
        font-weight: 600;
        padding: 15px 10px;
        border-bottom: 2px solid #e9ecef;
        border-right: 1px solid #e9ecef;
        white-space: nowrap;
    }
    
    table.custom-table td {
        padding: 12px 10px;
        border-bottom: 1px solid #e9ecef;
        border-right: 1px solid #e9ecef;
        vertical-align: top;
    }
    
    table.custom-table tr:last-child td {
        border-bottom: none;
    }
    table.custom-table th:last-child, table.custom-table td:last-child {
        border-right: none;
    }
    
    /* 施設・部屋名のセル */
    .room-name-cell {
        text-align: left !important;
        font-weight: 600;
        color: #2c3e50;
        min-width: 180px;
        background-color: #fafbfc;
    }
    
    .facility-label {
        font-size: 11px;
        color: #7f8c8d;
        display: block;
        margin-bottom: 4px;
    }
    
    /* タイムスロットのバッジデザイン */
    .slot-container {
        display: flex;
        flex-direction: column;
        gap: 6px;
        align-items: center;
    }
    
    .badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
        width: 60px;
        text-align: center;
        letter-spacing: 0.5px;
    }
    
    .badge.available {
        background-color: #e8f5e9;
        color: #2e7d32;
        border: 1px solid #a5d6a7;
    }
    
    .badge.unavailable {
        background-color: #ffebee;
        color: #c62828;
        border: 1px solid #ffcdd2;
    }
    
    .badge.disabled {
        background-color: #f5f5f5;
        color: #9e9e9e;
        border: 1px solid #e0e0e0;
    }
    
    /* 外部リンクボタン */
    .reserve-link {
        display: inline-block;
        margin-top: 30px;
        padding: 12px 24px;
        background-color: #3498db;
        color: white !important;
        text-decoration: none;
        border-radius: 6px;
        font-weight: 600;
        transition: background-color 0.2s;
    }
    .reserve-link:hover {
        background-color: #2980b9;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- ヘッダー ---
st.markdown('<div class="main-title">大阪市区民センター 空き状況確認</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-description">指定した期間と施設の会議室の空き状況をリアルタイムで一括検索します。左のメニューから条件を指定してください。</div>', unsafe_allow_html=True)

# --- サイドバー設定 ---
st.sidebar.markdown("### 検索条件")

selected_names = st.sidebar.multiselect(
    "施設を選択（複数選択可）", 
    list(FACILITIES.values()),
    default=[FACILITIES['18']]
)

today = datetime.date.today()
default_end = today + datetime.timedelta(days=7)

col1, col2 = st.sidebar.columns(2)
start_date = col1.date_input("開始日", value=today)
end_date = col2.date_input("終了日", value=default_end)

NAME_TO_CODE = {v: k for k, v in FACILITIES.items()}
selected_codes = [NAME_TO_CODE[name] for name in selected_names]

def get_badge_html(time_name, status):
    if status == '〇':
        css_class = "available"
    elif status == '×':
        css_class = "unavailable"
    else:
        css_class = "disabled"
        status = "-"
    return f'<span class="badge {css_class}">{time_name} {status}</span>'

@st.cache_data(ttl=600)
def fetch_availability_html(scds, start_date, end_date):
    try:
        s = requests.Session()
        s.headers.update({'User-Agent': 'Mozilla/5.0'})
        
        # CSRFトークン取得
        url_get = f"https://www.shisetsu-osaka.jp/shisetsu-nw/akijokyo.html?scd={scds[0]}"
        resp_get = s.get(url_get, verify=False)
        resp_get.raise_for_status()
        
        soup = BeautifulSoup(resp_get.content, 'html.parser')
        form = soup.find('form', id='dForm')
        if not form:
            return None, "システムからセキュリティトークンが取得できませんでした。"
        csrf = form.find('input', {'name': '_csrf'}).get('value')
        
        current = start_date
        monday = current - datetime.timedelta(days=current.weekday())
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
                    dict_key = f"{scd}_{room_name}"
                    
                    if dict_key not in room_data_map:
                        room_data_map[dict_key] = {
                            'facility': facility_name,
                            'room': room_name,
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
                                
                                room_data_map[dict_key]['dates'][date_header] = {'am': am, 'pm': pm, 'night': night}
                                
        if not room_data_map:
             return None, "条件に一致する空き状況データがありませんでした。"
             
        # HTML組み立て
        sorted_dates = sorted(list(all_date_headers), key=lambda x: datetime.datetime.strptime(x.split('(')[0], "%Y/%m/%d"))
        
        html = '<div class="table-wrapper"><table class="custom-table">'
        html += '<thead><tr><th>施設・部屋名</th>'
        for d in sorted_dates:
            html += f'<th>{d}</th>'
        html += '</tr></thead><tbody>'
        
        for key, data in room_data_map.items():
            html += '<tr>'
            html += f'<td class="room-name-cell"><span class="facility-label">{data["facility"]}</span>{data["room"]}</td>'
            for d in sorted_dates:
                slots = data['dates'].get(d, {'am': '-', 'pm': '-', 'night': '-'})
                html += '<td><div class="slot-container">'
                html += get_badge_html('午前', slots['am'])
                html += get_badge_html('午後', slots['pm'])
                html += get_badge_html('夜間', slots['night'])
                html += '</div></td>'
            html += '</tr>'
            
        html += '</tbody></table></div>'
        return html, None
        
    except Exception as e:
        return None, f"エラーが発生しました: {e}"

# --- メイン処理 ---
if st.sidebar.button("空き状況を検索", type="primary", use_container_width=True):
    if not selected_codes:
        st.warning("施設を1つ以上選択してください。")
    elif start_date > end_date:
        st.warning("終了日は開始日以降の日付を選択してください。")
    else:
        with st.spinner("最新の空き状況を取得しています..."):
            html_table, error = fetch_availability_html(selected_codes, start_date, end_date)
            
            if error:
                st.error(error)
            elif html_table:
                st.markdown(f'<div style="text-align:right; font-size:12px; color:#95a5a6; margin-bottom:5px;">最終更新: {datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")}</div>', unsafe_allow_html=True)
                st.markdown(html_table, unsafe_allow_html=True)
                
                # 予約サイトへのリンク（選択したすべての施設分を生成）
                st.markdown('<div style="margin-top: 30px; font-weight: 600; color: #2c3e50;">💡 予約システムを開く</div>', unsafe_allow_html=True)
                links_html = '<div style="display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px;">'
                for code, name in zip(selected_codes, selected_names):
                    links_html += f'<a href="https://www.shisetsu-osaka.jp/shisetsu-nw/akijokyo.html?scd={code}" target="_blank" class="reserve-link" style="margin-top:0;">{name}を開く</a>'
                links_html += '</div>'
                st.markdown(links_html, unsafe_allow_html=True)
            else:
                st.warning("指定された条件のデータが見つかりませんでした。")
