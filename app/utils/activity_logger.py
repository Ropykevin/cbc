from functools import wraps
from flask import current_app
from app.models.activity import Activity

def log_activity(action_type, entity_type, description_template):
    """Decorator to log activities for model operations"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                result = f(*args, **kwargs)
                
                # Get entity_id from result if it's a model instance
                entity_id = getattr(result, 'id', None)
                if entity_id:
                    # Format description with function arguments
                    description = description_template.format(**kwargs)
                    
                    Activity.log(
                        user=current_user,
                        action_type=action_type,
                        entity_type=entity_type,
                        entity_id=entity_id,
                        description=description
                    )
                
                return result
            except Exception as e:
                current_app.logger.error(f"Activity logging failed: {str(e)}")
                raise
                
        return decorated_function
    return decorator

def track_changes(old_data, new_data, tracked_fields):
    """Track changes in specific fields between old and new data"""
    changes = {}
    for field in tracked_fields:
        old_value = getattr(old_data, field, None)
        new_value = getattr(new_data, field, None)
        if old_value != new_value:
            changes[field] = {
                'old': old_value,
                'new': new_value
            }
    return changes if changes else None