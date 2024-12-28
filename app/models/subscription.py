from datetime import datetime
from app.extensions import db

class SubscriptionFeature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    tier = db.Column(db.String(20), nullable=False)  # basic, standard, premium
    
    def __repr__(self):
        return f'<SubscriptionFeature {self.name}>'

class SubscriptionTier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False, unique=True)  # basic, standard, premium
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    max_teachers = db.Column(db.Integer)
    max_students = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SubscriptionTier {self.name}>'