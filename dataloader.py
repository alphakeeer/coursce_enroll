from dataclasses import dataclass
from typing import List,Dict
import os
import json,csv
import re
from datetime import datetime


# ---------- 数据结构 ----------
WEEKDAY_MAP = {
    "Mo":1,"Tu":2,"We":3,"Th":4,"Fr":5,"Sa":6,"Su":7
}

@dataclass
class TimeSlot:
    weekday: int  # 1=Mon ... 7=Sun
    start_min: int
    end_min: int
    weeks_mask: None

@dataclass
class Section:
    id: str
    type: str      # lecture / tutorial / lab
    room: str
    instructor: str
    times: List[TimeSlot]
    real_time: str = None  # 原始时间字符串

@dataclass
class Course:
    id: str
    name: str
    credits: int
    sections: List[Section]

@dataclass
class Major:
    name: str
    courses: List[Course]


class DataLoader:
    def __init__(self):
        self.field=["AIAA","DLED","DSAA","SMMG","UCUG","UFUG"]
        self.major={
            "AI":{"Fundamental":[],"Major Required":[],"Major Elective":[]},
            "DSBD":{"Fundamental":[],"Major Required":[],"Major Elective":[]},
            "SMMG":{"Fundamental":[],"Major Required":[],"Major Elective":[]}
        }
        self.courses={
            "UFUG": {},
            "UCUG": {},
            "DLED": {},
            "AIAA": {},
            "DSAA": {},
            "SMMG": {},
        }
        for field in self.field:
            self.load_field_courses(field)
        for major in self.major.keys():
            self.load_major_courses(major)

    def parse_time_string(self,s: str):
        """
        支持格式：
        - "01-SEP-2025 - 05-SEP-2025Tu 09:00AM - 09:50AM"
        - "Fr 09:00AM - 11:50AM"
        - "MoWeFr 10:00AM - 11:00AM"
        返回: List[dict]
        """
        # 提取星期部分（可能有多个）
        day_pattern = r"(Mo|Tu|We|Th|Fr|Sa|Su)"
        days = re.findall(day_pattern, s)
        if not days:
            return []

        # 提取时间段
        time_match = re.findall(r"(\d{1,2}:\d{2}[AP]M)", s)
        if len(time_match) != 2:
            return []

        start_str, end_str = time_match
        start_dt = datetime.strptime(start_str, "%I:%M%p")
        end_dt = datetime.strptime(end_str, "%I:%M%p")
        start_min = start_dt.hour*60 + start_dt.minute
        end_min = end_dt.hour*60 + end_dt.minute

        slots = []
        for d in days:
            timeslot=TimeSlot(
                weekday=WEEKDAY_MAP[d],
                start_min=start_min,
                end_min=end_min,
                weeks_mask=None
            )
            slots.append(timeslot)

        return slots

    # 加载专业课程详细信息
    def load_field_courses(self, field: str):
        file_path = f"class/schedule_{field}.json"
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for course_code, sections in data.items():
            course = Course(
                id=course_code[:9],
                name=course_code[12:],
                credits=course_code[-8] if course_code[-8].isdigit() else "1",
                sections=[]
            )
            for sec_type, sec_info in sections.items():
                for sec_id, details in sec_info.items():
                    sec_id=sec_id[:4]
                    time_info=self.parse_time_string(details[0])
                    room = details[1]
                    instructor = details[2] if len(details) > 2 else ""
                    section = Section(
                        id=sec_id,
                        type=sec_type.lower(),
                        room=room,
                        instructor=instructor,
                        times=time_info,
                        real_time=details[0]
                    )
                    course.sections.append(section)
            self.courses[field][course_code[:9]] = course

    # 加载专业所需课程
    def load_major_courses(self, major: str):
        file_path=f"class/require_{major}.csv"
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return

        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # Skip header row
            for row in reader:
                if not row or len(row) < 4:
                    continue
                course_code,course_type = row[0],row[3]
                self.major[major][course_type].append(course_code)

if __name__ == "__main__":
    data_loader = DataLoader()
    print(data_loader.courses)