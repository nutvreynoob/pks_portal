import random
from flask import Flask, render_template, request

app = Flask(__name__)

# Blank runtime database - profiles ONLY exist when created via /register
users_db = {}

# Master list of pool classmates with pre-assigned rooms (1 to 10)
global_classmates_pool = [
    {"id": "11150", "name": "นายบ๊อบ ตัวตึงสายสตรีม", "room": 1, "status": "Afk กินขนม"},
    {"id": "22210", "name": "นายกัปตัน สกิบิดี้", "room": 3, "status": "Mewing ในห้องน้ำ"},
    {"id": "66666", "name": "เด็กหญิงพาวเวอร์พัฟเกิร์ล", "room": 5, "status": "กำลังแต่งเพลง"},
    {"id": "77740", "name": "นายจอนนี่ กิจกรรมเด่น", "room": 7, "status": "โดดร่มใน Roblox"},
    {"id": "99999", "name": "นายจอห์น วิค", "room": 7, "status": "ฟาร์มม้าอุมามุสุเมะ"},
    {"id": "88812", "name": "นายมิววิ่ง แชมเปี้ยน", "room": 9, "status": "Online อยู่หน้าคอม"},
]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        sid = request.form.get('student_id')
        dob = request.form.get('dob')
        name = request.form.get('name', 'นักเรียนใหม่')
        
        # Automatically assign a random room from 1 to 10 upon registration
        assigned_room = random.randint(1, 10)
        
        users_db[sid] = {
            "name": name, 
            "dob": dob, 
            "role": "student", 
            "room": assigned_room
        }
        return "<h1>ลงทะเบียนสำเร็จ!</h1><br><a href='/'>กลับหน้าต่างเข้าสู่ระบบ</a>"
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    sid = request.form.get('student_id')
    dob = request.form.get('dob')
    user_profile = users_db.get(sid)
    
    if user_profile and user_profile["dob"] == dob:
        student_room = user_profile["room"]
        
        # Generate the random 4-digit schedule layout code
        random_schedule = f"{random.randint(0, 9999):04d}"
        
        # Filter classmate pool: Only show students who share the exact same room
        matching_classmates = [mate for mate in global_classmates_pool if mate["room"] == student_room]
        
        # Insert the logged-in user at the top of their classroom list view
        matching_classmates.insert(0, {
            "id": sid, 
            "name": f"{user_profile['name']} (คุณ)", 
            "room": student_room, 
            "status": "Online"
        })
        
        return render_template('dashboard.html', 
                               uid=sid, 
                               name=user_profile["name"], 
                               role=user_profile["role"],
                               room_num=student_room,
                               schedule_num=random_schedule,
                               classmates=matching_classmates)
        
    return "<h1>เข้าสู่ระบบล้มเหลว!</h1><p>กรุณาลงทะเบียนบัญชีก่อนใช้งาน</p><a href='/'>ลองอีกครั้ง</a>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
