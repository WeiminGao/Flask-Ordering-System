from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sshtunnel import SSHTunnelForwarder
from flask_login import LoginManager
from sqlalchemy import create_engine
from flask_bootstrap import Bootstrap

app = Flask(__name__)
server = SSHTunnelForwarder(
    ('134.74.126.104', 22),
    ssh_username='huan2077',
    ssh_password='23242077',
    remote_bind_address=('134.74.146.21', 3306))
server.start()
engine = create_engine('mysql+pymysql://F17336Pwhuang:23242077@127.0.0.1:%s/F17336Pwhuang' % server.local_bind_port)
app.config[
    'SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://F17336Pwhuang:23242077@127.0.0.1:%s/F17336Pwhuang' % server.local_bind_port
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = '/Users/caizhuoying/Documents/Flask-Ordering-System/app/uploads'

login_manager = LoginManager(app)
Bootstrap(app)
db = SQLAlchemy(app)
app.config.update(dict(
    SECRET_KEY="powerful secretkey",
    WTF_CSRF_SECRET_KEY="a csrf secret key"
))
# UPLOAD_FOLDER = '/Users/James/Desktop/Flask-Ordering-System/app/uploads'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'super secret key'
from app import routes, models, errors
