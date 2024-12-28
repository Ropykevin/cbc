from datetime import datetime
from app.extensions import db

class School(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    subscription_type = db.Column(db.String(20), default='basic')
    subscription_end_date = db.Column(db.DateTime)
    max_teachers = db.Column(db.Integer, default=10)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='school', lazy=True)
    classes = db.relationship('Class', backref='school', lazy=True)
    subjects = db.relationship('Subject', backref='school', lazy=True)

    def has_premium_subscription(self):
        return (self.subscription_type == 'premium' and 
                self.subscription_end_date > datetime.utcnow())

    def can_add_teacher(self):
        if self.has_premium_subscription():
            return True
        return len(self.users) < self.max_teachers