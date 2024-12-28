from app import create_app
from app.admin.routes import populate_curriculum_subjects

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        populate_curriculum_subjects()
    app.run(debug=True)