file_paths=["data/AI.pdf","data/DSBD.pdf","data/SMMG.pdf"]

import pdfplumber
import re
import pandas as pd
from collections import defaultdict

def print_pdf_info(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            print(text)

def extract_course_info(pdf_path):
    # 初始化数据结构
    courses = []
    current_section = None
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            lines = text.split('\n')
            
            # 确定当前页面所属的部分
            for line in lines:
                if "Fundamental Courses" in line:
                    current_section = "Fundamental"
                    continue
                elif "Major Required Courses" in line:
                    current_section = "Major Required"
                    continue
                elif "Major Elective Courses" in line:
                    current_section = "Major Elective"
                    continue
                
                # 跳过不需要的行
                if not line.strip() or "Course Code" in line or "Credit(s)" in line or "=====" in line or "OR" in line:
                    continue
                
                # 尝试匹配课程行
                # 匹配模式: 课程代码(可能有空格) 课程名称 学分
                pattern = r'([A-Z]{2,4})\s*(\d{4})\s+(.*?)\s+(\d+(?:-\d+)?)$'
                match = re.search(pattern, line)
                
                if match:
                    dept = match.group(1)
                    code = match.group(2)
                    title = match.group(3).strip()
                    credits = match.group(4)
                    
                    courses.append({
                        'course_code': f"{dept} {code}",
                        'course_title': title,
                        'credits': credits,
                        'course_type': current_section
                    })
                # else:
                #     # 尝试匹配没有明确课程代码的行（如Note行）
                #     note_pattern = r'(Note:.*)'
                #     note_match = re.search(note_pattern, line)
                #     if note_match and current_section:
                #         courses.append({
                #             'course_code': 'N/A',
                #             'course_title': note_match.group(1),
                #             'credits': 'N/A',
                #             'course_type': f"{current_section} Note"
                #         })
    
    return courses

def sort_courses(courses):
    # 按课程类型、代码排序
    # 类型顺序为：Fundamental, Major Required, Major Elective
    type_order = {
        'Fundamental': 1,
        'Major Required': 2,
        'Major Elective': 3
    }
    courses.sort(key=lambda x: (type_order[x['course_type']], x['course_code'][5:]))
    return courses

def save_to_csv(courses, output_file):
    df = pd.DataFrame(courses)
    df.to_csv(output_file, index=False)
    print(f"课程信息已保存到 {output_file}")

if __name__ == "__main__":
    pdf_files=["data/AI.pdf","data/DSBD.pdf","data/SMMG.pdf"]
    output_csvs = ["class/require_AI.csv","class/require_DSBD.csv","class/require_SMMG.csv"]

    for pdf_file, output_csv in zip(pdf_files, output_csvs):
    
        courses = extract_course_info(pdf_file)
        if pdf_file == "data/AI.pdf":
            courses.append({
                'course_code': 'UFUG 2602',
                'course_title': 'Data Structure and Algorithm Design',
                'credits': '4',
                'course_type': 'Fundamental'
            })
        
        if courses:
            courses = sort_courses(courses)
            save_to_csv(courses, output_csv)
            
            # 打印提取的课程信息
            for course in courses:
                print(f"{course['course_type']}: {course['course_code']} - {course['course_title']} ({course['credits']} credits)")
        else:
            print("未提取到任何课程信息")