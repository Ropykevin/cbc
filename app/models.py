from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

class School(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    subscription_type = db.Column(db.String(20), default='free')
    users = db.relationship('User', backref='school', lazy=True)
    classes = db.relationship('ClassStream', backref='school', lazy=True)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='teacher')
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class ClassStream(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    grade_level = db.Column(db.Integer, nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'))
    timetable_entries = db.relationship('TimetableEntry', backref='class', lazy=True)

# class Subject(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(50), nullable=False)
#     code = db.Column(db.String(10), nullable=False)
#     lessons_per_week = db.Column(db.Integer, default=1)
#     school_id = db.Column(db.Integer, db.ForeignKey('school.id'))

class TimetableEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.Integer, nullable=False)  # 0-4 for Monday-Friday
    period = db.Column(db.Integer, nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'))


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))