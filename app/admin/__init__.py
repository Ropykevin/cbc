from flask import Blueprint

bp = Blueprint('admin', __name__)

from app.admin import routes
from app.admin.Routes import curriculum_subject