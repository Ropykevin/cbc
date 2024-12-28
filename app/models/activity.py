from datetime import datetime
from app.extensions import db

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)  # e.g., 'create', 'update', 'delete'
    entity_type = db.Column(db.String(50), nullable=False)  # e.g., 'teacher', 'class', 'timetable'
    entity_id = db.Column(db.Integer)  # ID of the affected entity
    description = db.Column(db.String(200), nullable=False)
    details = db.Column(db.JSON)  # Additional details about the activity
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='activities')
    school = db.relationship('School', backref='activities')
    
    @staticmethod
    def log(user, action_type, entity_type, entity_id, description, details=None):
        """Create an activity log entry"""
        activity = Activity(
            user_id=user.id,
            school_id=user.school_id,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            details=details
        )
        db.session.add(activity)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to log activity: {str(e)}")
            
    def get_details_display(self):
        """Format activity details for display"""
        if not self.details:
            return ""
            
        if self.action_type == "update":
            changes = []
            for field, values in self.details.get("changes", {}).items():
                changes.append(f"{field}: {values['old']} → {values['new']}")
            return ", ".join(changes)
            
        return str(self.details)