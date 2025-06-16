import logging, os
from logging.handlers import RotatingFileHandler
from flask import Flask, request, redirect
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from models import db
from routes import routes, login_manager
from dotenv import load_dotenv
from flask_migrate import Migrate
from flask_gravatar import Gravatar


load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
migrate = Migrate(app, db)

ckeditor = CKEditor(app)
Bootstrap5(app)
db.init_app(app)
app.register_blueprint(routes)
login_manager.init_app(app)

gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False,
                    force_lower=False, use_ssl=False, base_url=None)

if not app.debug:
    file_handler = RotatingFileHandler('app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.setLevel(logging.DEBUG)
    app.logger.info('Application startup')

@app.before_request
def enforce_https():
    if os.environ.get('FLASK_ENV') == 'production':
        if request.headers.get('X-Forwarded-Proto') == 'http':
            url = request.url.replace('http://', 'https://', 1)
            return redirect(url, code=301)
    return None

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    # if os.environ.get('FLASK_ENV') == 'production':
    #     from waitress import serve
    #     serve(app, host="0.0.0.0", port=5000)
    # else:
        app.run(debug=True)
