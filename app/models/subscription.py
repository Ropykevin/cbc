from datetime import datetime
from app.extensions import db

class SubscriptionFeature(db.Model):
    """Model representing features available in subscription tiers"""
    id = db.Column(db.Integer, primary_key=True)
    tier_id = db.Column(db.Integer, db.ForeignKey('subscription_tier.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tier = db.relationship('SubscriptionTier', backref='features')

    def __repr__(self):
        return f'<SubscriptionFeature {self.name}>'

    @staticmethod
    def get_tier_features(tier_id: int) -> list:
        """Get all active features for a subscription tier"""
        return SubscriptionFeature.query.filter_by(
            tier_id=tier_id,
            is_active=True
        ).all()
    
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
    
class SubscriptionPackage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    duration_months = db.Column(db.Integer, nullable=False)
    features = db.Column(db.JSON)
    is_recommended = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SubscriptionTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    package_id = db.Column(db.Integer, db.ForeignKey('subscription_package.id'), nullable=False)
    transaction_id = db.Column(db.String(100), unique=True)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # pending, completed, failed
    payment_date = db.Column(db.DateTime)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)