import os
import sqlite3
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "secret_school_key_2026"
DATABASE = 'school_results.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                national_id TEXT,
                student_name TEXT,
                grade_level TEXT,
                arabic TEXT,
                english TEXT,
                math TEXT,
                multidisciplinary TEXT,
                religion TEXT,
                physical_health TEXT,
                studies TEXT,
                science TEXT,
                ict TEXT,
                status TEXT
            )
        ''')
        conn.commit()

def get_color(score):
    try:
        if score is None or str(score).strip() == '': return '#ffffff'
        score_str = str(score).strip()
        if "اجتياز" in score_str or "يجتاز" in score_str: return '#00a550'
        if "عدم" in score_str: return '#ed0028'
        
        score = float(score)
        if score < 50: return '#ed0028'
        if score < 65: return '#eaed00'
        if score < 85: return '#00a550'
        return '#0247fe'
    except:
        return '#ffffff'

def get_religion_color(score):
    try:
        if score is None or str(score).strip() == '': return '#ffffff'
        score = float(score)
        if score <= 69: return '#ed0028'
        if score <= 79: return '#eaed00'
        if score <= 89: return '#00a550'
        return '#0247fe'
    except:
        return '#ffffff'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    grade = request.form.get('cl')
    national_id = request.form.get('rl').strip()
    
    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE national_id = ? AND grade_level = ?", (national_id, grade))
        student = cursor.fetchone()
        
    if student:
        # حساب الألوان داخل السيرفر لحماية السرية ومنع التسريب
        colors = {
            'arabic': get_color(student['arabic']),
            'english': get_color(student['english']),
            'math': get_color(student['math']),
            'multidisciplinary': get_color(student['multidisciplinary']),
            'religion': get_religion_color(student['religion']),
            'physical_health': get_color(student['physical_health']),
            'studies': get_color(student['studies']),
            'science': get_color(student['science']),
            'ict': get_color(student['ict'])
        }
        # نرسل فقط البيانات الأساسية والألوان المحسوبة مسبقاً لحظر أي تسريب درجات
        student_data = {
            'student_name': student['student_name'],
            'grade_level': student['grade_level'],
            'national_id': student['national_id'],
            'status': student['status']
        }
        return render_template('result.html', student=student_data, colors=colors)
    
    flash("لم يتم العثور على النتيجة، يرجى التأكد من الرقم القومي والصف الدراسي.")
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        grade_level = request.form.get('grade_level')
        file = request.files.get('excel_file')
        
        if file and file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
            df = df.fillna('')
            
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM students WHERE grade_level = ?", (grade_level,))
                for _, row in df.iterrows():
                    status_value = str(row.get('نتيجة الطالب', '')).strip()
                    if "برنامج علاجي" in status_value:
                        status_value = "دور ثاني"
                        
                    cursor.execute('''
                        INSERT INTO students 
                        (national_id, student_name, grade_level, arabic, english, math, multidisciplinary, religion, physical_health, studies, science, ict, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        str(row.get('الرقم القومي', '')).split('.')[0].strip(),
                        str(row.get('اسم الطالب', '')).strip(),
                        grade_level,
                        str(row.get('اللغة العربية', '')),
                        str(row.get('اللغة الإنجليزية', '')),
                        str(row.get('الرياضيات', '')),
                        str(row.get('متعدد التخصصات', '')),
                        str(row.get('التربية الدينية', '')),
                        str(row.get('تربية بدنية وصحية', '')),
                        str(row.get('الدراسات الاجتماعية', '')),
                        str(row.get('العلوم', '')),
                        str(row.get('تكنولوجيا المعلومات', '')),
                        status_value
                    ))
                conn.commit()
            flash(f"تم رفع وتحديث نتيجة الصف {grade_level} بنجاح!")
            return redirect(url_for('admin'))
    return render_template('admin.html')

if __name__ == '__main__':
    init_db()
    app.run()
