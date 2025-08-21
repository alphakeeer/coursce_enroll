import streamlit as st
import pandas as pd
import plotly.express as px
from dataclasses import dataclass
from typing import List
from dataloader import DataLoader


weekday_names = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
data_loader=DataLoader()
courses = data_loader.courses

# ---------- Streamlit 页面 ----------
st.set_page_config(layout="wide")
st.title("📚 选课系统示例 (MVP)")

if "selected_sections" not in st.session_state:
    st.session_state.selected_sections = []

# ---------- 左侧课程库 ----------
col1, col2 = st.columns([2,5])
with col1:
    st.subheader("课程库")

    for major in courses:
        with st.expander(major):
            for course in courses[major]:
                with st.expander(f"{course.id[-4:]}: {course.name}"):
                    for sec in course.sections:
                        selected = (course, sec) in st.session_state.selected_sections
                        if st.button(f"{sec.id}", key=f"toggle_{course.id}_{sec.id}"):
                            if selected:
                                st.session_state.selected_sections.remove((course, sec))
                            else:
                                st.session_state.selected_sections.append((course, sec))
                        st.markdown(
                            f"**{sec.type} - {sec.instructor}**  \n"  # 两个空格 + \n = 换行
                            f"{sec.real_time} @ {sec.room}"
                        )

# ---------- 周历可视化 ----------
import plotly.graph_objects as go
from collections import defaultdict
import plotly.colors as colors

with col2:
    st.subheader("📅 我的课表")

    rows = []
    for course, sec in st.session_state.selected_sections:
        for t in sec.times:
            rows.append({
                "课程": course.id+" "+sec.id,
                "weekday": t.weekday,  # 1=Mon
                "start": t.start_min / 60,   # 小时
                "end": t.end_min / 60,
                "course_obj": course,
            })

    if rows:
        df = pd.DataFrame(rows)

        # --- 冲突分组逻辑 ---
        # 按 weekday 分组，每天单独处理
        grouped = defaultdict(list)
        for _, row in df.iterrows():
            grouped[row["weekday"]].append(row)

        # 为每个 weekday 内的课程分配一个 "列索引"
        positioned = []
        for day, items in grouped.items():
            items = sorted(items, key=lambda x: x["start"])  # 按开始时间排序
            cols = []  # 当前占用的列（end_time）
            for item in items:
                placed = False
                for col_idx, col_end in enumerate(cols):
                    if item["start"] >= col_end:  # 不冲突，可以放进这个列
                        cols[col_idx] = item["end"]
                        positioned.append((item, col_idx, len(cols)))
                        placed = True
                        break
                if not placed:  # 新建一列
                    cols.append(item["end"])
                    positioned.append((item, len(cols)-1, len(cols)))

        # --- 生成课程颜色映射 ---
        distinct_courses = list({row["课程"] for row in rows})
        palette = colors.qualitative.Plotly
        color_map = {course_id: palette[i % len(palette)] for i, course_id in enumerate(distinct_courses)}

        # --- 画图 ---
        fig = go.Figure()

        for row, col_idx, col_count in positioned:
            # 每个课程宽度 = 0.8 / 列数
            width = 0.8 / col_count
            x0 = row["weekday"] - 0.4 + col_idx * width
            x1 = x0 + width
            y0, y1 = row["start"], row["end"]

            fillcolor = color_map[row["课程"]]

            fig.add_shape(
                type="rect",
                x0=x0, x1=x1,
                y0=y0, y1=y1,
                fillcolor=fillcolor,
                opacity=0.9,
                line=dict(color="white", width=1)
            )
            fig.add_annotation(
                x=(x0+x1)/2,
                y=(y0+y1)/2,
                text=row["课程"],
                showarrow=False,
                font=dict(color="black", size=10)
            )

        # --- 坐标轴设置 ---
        fig.update_xaxes(
            tickmode="array",
            tickvals=list(range(1,8)),
            ticktext=weekday_names,
            range=[0.5,7.5]
        )
        fig.update_yaxes(
            title="时间",
            tickvals=list(range(8,23)),  # 08:00 - 22:00
            ticktext=[f"{h}:00" for h in range(8,23)],
            range=[22,8]
        )

        fig.update_layout(
            title="课程表",
            height=600,
            plot_bgcolor="white"
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("👉 左侧选择课程后，这里会显示课表")

    # --- 已选课程面板 ---
    st.subheader("✅ 已选课程")
    if st.session_state.selected_sections:
        for i, (course, sec) in enumerate(st.session_state.selected_sections):
            if st.button(f"{course.id} | {sec.id} | {sec.real_time} | {sec.instructor}", key=f"remove_{course.id}_{sec.id}"):
                st.session_state.selected_sections.pop(i)
                st.experimental_rerun()
    else:
        st.write("还没有选择任何课程")