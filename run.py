from app import create_app
from app.admin.routes import populate_curriculum_subjects,populate_grade_levels
from app.services.subscription_service import SubscriptionService

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        populate_curriculum_subjects(),
        populate_grade_levels(),
        SubscriptionService.initialize_subscription_tiers()
    app.run(debug=True)