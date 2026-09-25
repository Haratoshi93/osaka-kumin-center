import requests
from bs4 import BeautifulSoup
import datetime
import urllib3
import concurrent.futures
import json
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

FACILITIES = {
    '01': '大阪市立北区民センター', '02': '大阪市立大淀コミュニティセンター', '03': '都島区民センター',
    '04': '福島区民センター', '05': '大阪市立此花区民ホール', '06': 'J:COM中央区民センター',
    '07': '大阪市立中央会館', '08': '西区民センター', '10': '大阪市立港近隣センター',
    '11': '大正会館', '12': '大阪市立天王寺区民センター', '13': '大阪市立浪速区民センター',
    '14': '西淀川区民ホール', '15': '大阪市立西淀川区民会館', '16': '大阪市立淀川区民センター',
    '17': '大阪市立東淀川区民会館', '18': '大阪市立東成区民センター', '19': '大阪市立生野区民センター',
    '20': '旭区民センター', '22': '大阪市立鶴見区民センター', '23': '大阪市立阿倍野区民センター',
    '24': '大阪市立住之江会館', '25': '住吉区民センター', '26': '大阪市立東住吉会館',
    '27': '大阪市立平野区民センター', '28': '大阪市立平野区民ホール', '29': '大阪市立西成区民センター',
    '30': '大阪市立城東区民センター', '31': '大正区民ホール', '32': '大阪市立東淀川区民ホール',
    '33': '大阪市立すみのえ舞昆ホール', '34': '大阪市立東住吉区民ホール', '35': '大阪市立港区民センター'
}

def fetch_facility_week(s, csrf, scd, monday_str, url_post):
    post_data = {'_csrf': csrf, 'scd': scd, 'sdate': monday_str}
    resp = s.post(url_post, data=post_data, verify=False, timeout=10)
    resp.raise_for_status()
    return scd, monday_str, resp.json()

def main():
    today = datetime.date.today()
    # 5週間分（約1ヶ月）の月曜日を計算
    mondays = []
    monday = today - datetime.timedelta(days=today.weekday())
    for _ in range(5):
        mondays.append(monday.strftime("%Y-%m-%d"))
        monday += datetime.timedelta(days=7)

    s = requests.Session()
    s.headers.update({'User-Agent': 'Mozilla/5.0'})
    
    # CSRF取得 (適当な施設で取得)
    try:
        r = s.get('https://www.shisetsu-osaka.jp/shisetsu-nw/akijokyo.html?scd=18', verify=False, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, 'html.parser')
        csrf = soup.find('form', id='dForm').find('input', {'name': '_csrf'}).get('value')
    except Exception as e:
        print(f"Failed to get CSRF: {e}")
        return

    url_post = "https://www.shisetsu-osaka.jp/shisetsu-nw/restapi/akijokyo.html"
    
    # { scd: { name: "...", rooms: [ {name, capacity, dates: { "YYYY-MM-DD": {am, pm, night} } } ] } }
    data_store = {scd: {"name": name, "rooms": {}} for scd, name in FACILITIES.items()}
    
    tasks = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        for scd in FACILITIES.keys():
            for m_str in mondays:
                tasks.append(executor.submit(fetch_facility_week, s, csrf, scd, m_str, url_post))
        
        for future in concurrent.futures.as_completed(tasks):
            try:
                scd, m_str, result_json = future.result()
                if 'data' not in result_json or 'akijokyo' not in result_json['data']:
                    continue
                
                headers_info = result_json['data'].get('header', [])
                headers = [h['value'] for h in headers_info] # e.g. "2026/9/16(水)"
                
                for room in result_json['data']['akijokyo']:
                    room_name = room.get('roomName', room.get('roomDispName', '不明'))
                    capacity = int(room.get('tenin', 0) or 0)
                    
                    if room_name not in data_store[scd]["rooms"]:
                        data_store[scd]["rooms"][room_name] = {
                            "name": room_name,
                            "capacity": capacity,
                            "dates": {}
                        }
                    
                    for i, date_info in enumerate(room.get('dateList', [])):
                        if i < len(headers):
                            raw_date_str = date_info.get('riyoDate') # YYYY-MM-DD
                            if not raw_date_str: continue
                            
                            time_list = date_info.get('availTimeList', [])
                            am = ('-', '')
                            pm = ('-', '')
                            night = ('-', '')
                            
                            if len(time_list) >= 1:
                                ti = time_list[0]
                                am = (ti.get('statusDisp', '-'), f"{ti.get('availStartTimeDisp', '')}-{ti.get('availEndTimeDisp', '')}")
                            if len(time_list) >= 2:
                                ti = time_list[1]
                                pm = (ti.get('statusDisp', '-'), f"{ti.get('availStartTimeDisp', '')}-{ti.get('availEndTimeDisp', '')}")
                            if len(time_list) >= 3:
                                ti = time_list[2]
                                night = (ti.get('statusDisp', '-'), f"{ti.get('availStartTimeDisp', '')}-{ti.get('availEndTimeDisp', '')}")
                                
                            data_store[scd]["rooms"][room_name]["dates"][raw_date_str] = {
                                "header": headers[i],
                                "am": am,
                                "pm": pm,
                                "night": night
                            }
            except Exception as e:
                print(f"Task failed: {e}")

    # Convert rooms dict to list
    for scd in data_store:
        data_store[scd]["rooms"] = list(data_store[scd]["rooms"].values())

    output = {
        "last_updated": datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        "facilities": data_store
    }

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, separators=(',', ':'))

if __name__ == "__main__":
    main()
