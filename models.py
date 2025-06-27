from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# جدول وسيط لربط المشاريع بالمستخدمين (علاقة متعدد لمتعدد)
project_users = db.Table('project_users',
    db.Column('project_id', db.Integer, db.ForeignKey('project.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)

class User(db.Model, UserMixin):
    """
    يمثل المستخدم في النظام
    يمكن أن يكون المستخدم عادي أو أدمن
    له علاقة واحد إلى متعدد مع المهام (tasks)
    له علاقة متعدد إلى متعدد مع المشاريع (projects) عبر الجدول الوسيط
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)  # يحدد إذا كان المستخدم أدمن
    tasks = db.relationship('Task', backref='user', lazy=True)  # جميع المهام الموكلة لهذا المستخدم

class Project(db.Model):
    """
    يمثل المشروع في النظام
    له علاقة واحد إلى متعدد مع المهام (tasks)
    له علاقة متعدد إلى متعدد مع المستخدمين (users) عبر الجدول الوسيط
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    tasks = db.relationship('Task', backref='project', lazy=True)  # جميع المهام التابعة لهذا المشروع
    users = db.relationship('User', secondary=project_users, backref='projects')  # جميع أعضاء المشروع

class Task(db.Model):
    """
    يمثل المهمة في النظام.
    كل مهمة مرتبطة بمشروع واحد (project_id)
    كل مهمة موكلة لمستخدم واحد (assigned_to)
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.String(50))  # تاريخ الاستحقاق (نصي)
    priority = db.Column(db.String(50))  # أولوية المهمة (نصي)
    status = db.Column(db.String(50), default='To Do')  # حالة المهمة الافتراضية
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)  # المشروع التابع له المهمة
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))  # المستخدم الموكلة إليه المهمة