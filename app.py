import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from dataclasses import dataclass
from typing import List
from dataloader import DataLoader

data_loader=DataLoader()
courses = data_loader.courses # 课程的详细信息
majors = data_loader.major # 专业的课程信息

# ---------- Streamlit 页面 ----------
st.set_page_config(layout="wide")
st.title("💗 简单の选课系统")

st.markdown("""
- **✨ Made from Sato ✨**
- 用途：用来预选查看课程时间是否冲突，方便决策  
- 用法：左侧选择专业后，可在专业选择列表中查看该专业的选课要求，若未决定专业也可直接在下方总课程库中选择
    可以通过再次点击课程or课程表来取消选择，记得顺带勾选lecture对应的tutorial/lab
- 来源：课程信息来自[UCUG](https://w5.hkust-gz.edu.cn/wcq/cgi-bin/2510/subject/UCUG) 和 [VPTLO](https://vptlo.hkust-gz.edu.cn/ugeducation/#/UC#fourth)  
- 目前只含三个专业，且未对课程日期方面（如晚开课或早结课）进行处理
- 仅供参考，强烈建议各位正式选课前再多加确认  
- Github 仓库：[alphakeeer/coursce_enroll](https://github.com/alphakeeer/coursce_enroll)  
""")

if "selected_sections" not in st.session_state:
    st.session_state.selected_sections = []

# ---------- 选专业 ----------
st.sidebar.header("❤️ 选择专业")
selected_major = st.sidebar.selectbox("❤️ 选择专业", options=list(data_loader.major.keys()))

col1, col2 = st.columns([2,5])

# ---------- 选课列表 ----------
def render_section_button(course, sec, source="", group=""):
    # 按钮的唯一 key：区分来源（避免 Streamlit 冲突）
    safe_course_id = str(course.id).strip()
    safe_sec_id = str(sec.id).strip()
    btn_key = f"toggle_{safe_course_id}_{safe_sec_id}_{source}_{group}"
    selected = (course, sec) in st.session_state.selected_sections

    if st.button(f"{sec.id}", key=btn_key):
        if selected:
            st.session_state.selected_sections.remove((course, sec))
        else:
            # 加的时候判断是否已经存在
            if (course, sec) not in st.session_state.selected_sections:
                st.session_state.selected_sections.append((course, sec))

    st.markdown(
        f"**{sec.type} - {sec.instructor}**  \n"
        f"{sec.real_time} @ {sec.room}"
    )

with col1:
    st.subheader("📕 专业选课列表")
    for course_type in majors[selected_major].keys():
        with st.expander(course_type):
            for course_code in majors[selected_major][course_type]:
                try:
                    course = data_loader.courses[course_code[:4]][course_code]
                except:
                    st.markdown(f"{course_code} 这学期不开")
                    continue
                with st.expander(f"{course.id} - {course.name}"):
                    for sec in course.sections:
                        render_section_button(course, sec, source="major", group=course_type)
    
    st.subheader("📚 总课程库")
    for major in courses:
        with st.expander(major):
            for course in courses[major].values():
                with st.expander(f"{course.id[-4:]}: {course.name}"):
                    for sec in course.sections:
                        render_section_button(course, sec, source="all", group="all")

# ---------- 周历可视化（streamlit-calendar） ----------
from datetime import datetime, timedelta

with col2:
    st.subheader("📅 我的课表（Calendar）")

    # 将已选课程转为 FullCalendar 事件
    # 选一个参考周的周一（固定日期，避免跨周偏移）：2025-01-06 是周一
    # base_monday = datetime(2025, 1, 6)

    events = []
    # 记录一个映射，便于根据点击事件回溯到 (course, sec)
    id_to_pair = {}

    for course, sec in st.session_state.selected_sections:
        for t in sec.times:
            # 计算当天日期
            # day_offset = t.weekday - 1  # 1=Mon -> 0
            # date = base_monday + timedelta(days=day_offset)

            start_hour, start_min = divmod(t.start_min, 60)
            end_hour, end_min = divmod(t.end_min, 60)

            # start_iso = f"{date.strftime('%Y-%m-%d')}T{start_hour:02}:{start_min:02}:00"
            # end_iso = f"{date.strftime('%Y-%m-%d')}T{end_hour:02}:{end_min:02}:00"

            fc_day = (t.weekday % 7)  # Sunday=0
            start_time = f"{start_hour:02}:{start_min:02}:00"
            end_time = f"{end_hour:02}:{end_min:02}:00"

            evt_id = f"{course.id}|{sec.id}|{fc_day}|{t.start_min}-{t.end_min}"
            id_to_pair[evt_id] = (course, sec)

            events.append({
                "id": evt_id,
                "title": f"{course.id} {sec.id}",
                "daysOfWeek": [fc_day],
                "startTime": start_time,
                "endTime": end_time,
                # 颜色可自定，也可不设让日历自动配色
                # "color": "#4CAF50",
                "extendedProps": {
                    "room": sec.room,
                    "instructor": sec.instructor,
                    "type": sec.type
                }
            })

    cal_options = {
        "initialView": "timeGridWeek",
        "slotMinTime": "09:00:00",
        "slotMaxTime": "22:00:00",
        "allDaySlot": False,
        "firstDay": 1,  # 周一作为一周的第一天
        "weekNumbers": False,
        "height": "720px",
        "expandRows": True,
        "locale": "zh-cn",
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "timeGridWeek,dayGridMonth,listWeek"
        },
        "nowIndicator": True,
    }

    cal_state = calendar(events=events, options=cal_options, key="course_calendar")

    # 支持点击事件以取消（尽量兼容不同版本的返回字段）
    # 如果解析失败，不会报错，仍可通过下方“已选课程”列表取消
    try:
        clicked = None
        # 常见键名尝试
        for key in ("clickedEvent", "eventClick", "last_clicked", "selectedEvent"):
            if isinstance(cal_state, dict) and cal_state.get(key):
                clicked = cal_state.get(key)
                break
        if clicked:
            # 不同版本字段结构不同，尽量兼容：
            # 1) {"id": ..., "title": ...}
            # 2) {"event": {"id": ..., "title": ...}}
            if isinstance(clicked, dict) and "id" in clicked:
                evt_id = clicked["id"]
            elif isinstance(clicked, dict) and "event" in clicked and isinstance(clicked["event"], dict):
                evt_id = clicked["event"].get("id")
            else:
                evt_id = None

            if evt_id and evt_id in id_to_pair:
                pair = id_to_pair[evt_id]
                if pair in st.session_state.selected_sections:
                    st.session_state.selected_sections.remove(pair)
                    try:
                        st.rerun()
                    except Exception:
                        st.experimental_rerun()
    except Exception:
        pass

    # --- 已选课程面板（位于课表下方） ---
    st.subheader("✅ 已选课程")
    if st.session_state.selected_sections:
        total_credits = sum(getattr(course, "credit", 0) for course, _ in st.session_state.selected_sections)
        st.markdown(f"**总学分: {total_credits}**")
        for i, (course, sec) in enumerate(st.session_state.selected_sections):
            if st.button(f"{course.id} | {sec.id} | {sec.real_time} | {sec.instructor}", key=f"remove_{course.id}_{sec.id}"):
                st.session_state.selected_sections.pop(i)
                try:
                    st.rerun()
                except Exception:
                    st.experimental_rerun()
    else:
        st.write("还没有选择任何课程")