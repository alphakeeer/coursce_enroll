# https://w5.hkust-gz.edu.cn/wcq/cgi-bin/2510/subject/DSAA
# https://w5.hkust-gz.edu.cn/wcq/cgi-bin/2510/subject/UCUG

import requests
from bs4 import BeautifulSoup
import json

codes=["AIAA","DSAA","UCUG","UFUG","SMMG","DLED"]
# codes=["UFUG"]

for code in codes:
    url = f"https://w5.hkust-gz.edu.cn/wcq/cgi-bin/2510/subject/{code}"

    resp = requests.get(url, timeout=10)
    resp.encoding = resp.apparent_encoding  # 自动识别编码

    html = resp.text

    # 或者保存到本地文件方便在浏览器里打开
    # with open(f"data/course_{code}.html", "w", encoding="utf-8") as f:
    #     f.write(html)
    
    course_infos=dict()
    
    # 遍历所有h2
    soup = BeautifulSoup(html, "html.parser")
    for h2 in soup.find_all("h2"):
        h2_text = h2.get_text(strip=True)
        course_code=h2_text if h2_text[9]==' ' else None
        if not course_code:
            continue
        course_infos[course_code]={
            # "Lecture": dict(),
            # "Tutorial": dict(),
            # "Lab": dict(),
            # "Recitation": dict()
        }

        #找到紧跟的section表格
        table = h2.find_next("table", class_="sections")
        headers = [th.get_text(strip=True) for th in table.find("tr").find_all("th")]
        for row in table.find_all("tr")[1:]:  # 跳过表头
            cols = []
            for td in row.find_all("td"):
                # instructor 可能带有 <a> 链接
                cols.append(td.get_text(strip=True))
            if cols:
                section=cols[0]
                if "LA" in section[:2]:
                    if not "Lab" in course_infos[course_code]:
                        course_infos[course_code]["Lab"] = {}
                    course_infos[course_code]["Lab"][section] = cols[1:-1]
                elif "T" == section[0] and section[1].isdigit():
                    if not "Tutorial" in course_infos[course_code]:
                        course_infos[course_code]["Tutorial"] = {}
                    course_infos[course_code]["Tutorial"][section] = cols[1:-1]
                elif "L" == section[0] and section[1].isdigit():
                    if not "Lecture" in course_infos[course_code]:
                        course_infos[course_code]["Lecture"] = {}
                    course_infos[course_code]["Lecture"][section] = cols[1:-1]
                elif "R" == section[0] and section[1].isdigit():
                    if not "Recitation" in course_infos[course_code]:
                        course_infos[course_code]["Recitation"] = {}
                    course_infos[course_code]["Recitation"][section] = cols[1:-1]

    save_path="class/schedule_" + code + ".json"
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(course_infos, f, ensure_ascii=False, indent=4)