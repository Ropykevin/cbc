from typing import List
from app.models.subscription import SubscriptionTier, SubscriptionFeature
from app.models.school import School

def check_feature_access(school: School, feature_name: str) -> bool:
    """Check if a school has access to a specific feature based on their subscription"""
    tier = SubscriptionTier.query.filter_by(name=school.subscription_type).first()
    if not tier:
        return False
        
    feature = SubscriptionFeature.query.filter_by(
        name=feature_name,
        tier=tier.name
    ).first()
    
    return feature is not None

def get_tier_features(tier_name: str) -> List[dict]:
    """Get all features available for a subscription tier"""
    features = SubscriptionFeature.query.filter_by(tier=tier_name).all()
    return [{'name': f.name, 'description': f.description} for f in features]

def can_add_teachers(school: School) -> bool:
    """Check if school can add more teachers based on their subscription"""
    tier = SubscriptionTier.query.filter_by(name=school.subscription_type).first()
    if not tier:
        return False
    
    current_teachers = len(school.users)
    return current_teachers < tier.max_teachers