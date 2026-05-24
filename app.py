import os
import random
from datetime import datetime
import pytz
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pks_secret_key_12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pks_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- OHIO CONFIGURATION ---
OHIO_TEACHERS = ["Dr. Sigma", "Professor Skibidi", "Mr. Rizzler", "Lord Grimace", "Duke Dennis", "Giga Chad", "Kai Cenat's Uncle"]
OHIO_SUBJECTS = ["Advanced Mewing", "Skibidi Toilet Defusal", "Quantum Rizzology", "Fanum Tax Accounting", "Griddy Mechanics", "Subway Surfers Focus"]

# --- DATABASE MODELS ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    money = db.Column(db.Integer, default=1000)               
    goodness_points = db.Column(db.Integer, default=100)       
    room = db.Column(db.Integer, default=1)                   

class SchoolState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    current_teacher = db.Column(db.String(100))
    current_subject = db.Column(db.String(100))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def randomize_weekly_classes():
    with app.app_context():
        users = User.query.all()
        for user in users:
            user.room = random.randint(1, 12)
        
        state = SchoolState.query.first()
        if not state:
            state = SchoolState()
            db.session.add(state)
        
        state.current_teacher = random.choice(OHIO_TEACHERS)
        state.current_subject = random.choice(OHIO_SUBJECTS)
        
        db.session.commit()
        print(f"[{datetime.now()}] Weekly Ohio Rotation Complete!")

scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Bangkok'))
scheduler.add_job(func=randomize_weekly_classes, trigger="cron", day_of_week='mon', hour=0, minute=0)
scheduler.start()

# --- ROUTES ---

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return redirect(url_for('register'))
            
        hashed_pw = generate_password_hash(password)
        # ถ้านี่คือคนแรกที่สมัคร จะได้เป็น Admin ทันที (ให้สมัคร Pencillayer1 เป็นคนแรก)
        is_first_user = User.query.count() == 0
        
        new_user = User(
            username=username, 
            password=hashed_pw, 
            is_admin=is_first_user,
            room=random.randint(1, 12)
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please fill out both fields.', 'error')
            return render_template('login.html')

        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid Username or Password', 'error')
                
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    state = SchoolState.query.first()
    teacher = state.current_teacher if state else "Dr. Sigma"
    subject = state.current_subject if state else "Advanced Mewing"
    
    roommates = User.query.filter(User.room == current_user.room, User.id != current_user.id).all()
    all_students = User.query.all()
    
    return render_template('dashboard.html', 
                           teacher=teacher, 
                           subject=subject, 
                           roommates=roommates, 
                           all_students=all_students)

# --- STUDENT CHEAT PANEL ROUTE (ฟังก์ชันที่ทำให้เกิดบัคตอนแรก ตอนนี้ใส่ให้ครบแล้ว) ---
@app.route('/update_my_stats', methods=['POST'])
@login_required
def update_my_stats():
    new_money = request.form.get('money')
    new_goodness = request.form.get('goodness_points')
    
    # อนุญาตให้ใส่เลขติดลบได้ด้วยการเช็ค lstrip('-')
    if new_money and new_money.lstrip('-').isdigit():
        current_user.money = int(new_money)
    if new_goodness and new_goodness.lstrip('-').isdigit():
        current_user.goodness_points = int(new_goodness)
        
    db.session.commit()
    flash('อัปเดตข้อมูลส่วนตัว (เงิน/คะแนนความดี) สำเร็จแล้ว!', 'success')
    return redirect(url_for('dashboard'))

# --- ADMIN ROUTES ---
@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash("Access denied: Admins only!", "error")
        return redirect(url_for('dashboard'))
        
    all_students = User.query.all()
    return render_template('admin.html', all_students=all_students)

@app.route('/admin/update_student', methods=['POST'])
@login_required
def update_student():
    if not current_user.is_admin:
        return "Unauthorized", 403
        
    student_id = request.form.get('student_id')
    money_action = request.form.get('money_action')
    money_amount = int(request.form.get('money_amount', 0))
    goodness_action = request.form.get('goodness_action')
    goodness_amount = int(request.form.get('goodness_amount', 0))
    
    student = User.query.get(student_id)
    if student:
        if money_action == "add": student.money += money_amount
        elif money_action == "delete": student.money -= money_amount
            
        if goodness_action == "add": student.goodness_points += goodness_amount
        elif goodness_action == "delete": student.goodness_points -= goodness_amount
            
        if student.goodness_points > 100: student.goodness_points = 100
            
        db.session.commit()
        flash(f"Successfully updated {student.username}!", "success")
        
    return redirect(url_for('admin_panel'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

with app.app_context():
    db.create_all()
    if not SchoolState.query.first():
        initial_state = SchoolState(current_teacher="Professor Skibidi", current_subject="Advanced Mewing")
        db.session.add(initial_state)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
