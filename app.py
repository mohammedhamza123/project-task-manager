from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from models import db

app = Flask(__name__)
# إعدادات التطبيق (مفتاح التشفير وقاعدة البيانات)
app.config['SECRET_KEY'] = 'b7f3e2c1-4a9d-4e8a-9f2b-6c8e7d5a1f0c'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
# تهيئة قاعدة البيانات مع التطبيق
db.init_app(app)
# تهيئة إدارة تسجيل الدخول
login_manager = LoginManager(app)
login_manager.login_view = 'login' # اسم صفحة تسجيل الدخول الافتراضية

from routes import *

if __name__ == "__main__":
    with app.app_context():
        db.create_all()# إنشاء جميع الجداول في قاعدة البيانات
    app.run(debug=True)