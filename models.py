from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import os

db = SQLAlchemy()

# جدول وسيط لربط المشاريع بالمستخدمين (علاقة متعدد لمتعدد)
project_users = db.Table('project_users',
    db.Column('project_id', db.Integer, db.ForeignKey('project.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)

# جدول العلاقة بين المهام والمستخدمين
task_users = db.Table('task_users',
    db.Column('task_id', db.Integer, db.ForeignKey('task.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    """
    يمثل المستخدم في النظام
    يمكن أن يكون المستخدم عادي أو أدمن
    له علاقة متعدد إلى متعدد مع المهام (tasks) عبر الجدول الوسيط
    له علاقة متعدد إلى متعدد مع المشاريع (projects) عبر الجدول الوسيط
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)  # يحدد إذا كان المستخدم أدمن
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # العلاقة مع المهام المعينة
    assigned_tasks = db.relationship('Task', secondary=task_users, backref=db.backref('assigned_users', lazy='dynamic'))
    
    # العلاقة مع تسليمات المهام
    submissions = db.relationship('TaskSubmission', backref='user', lazy=True)

class Project(db.Model):
    """
    يمثل المشروع في النظام
    له علاقة واحد إلى متعدد مع المهام (tasks)
    له علاقة متعدد إلى متعدد مع المستخدمين (users) عبر الجدول الوسيط
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # العلاقة مع المهام
    tasks = db.relationship('Task', backref='project', lazy=True)
    users = db.relationship('User', secondary=project_users, backref='projects')  # جميع أعضاء المشروع

class Task(db.Model):
    """
    يمثل المهمة في النظام.
    كل مهمة مرتبطة بمشروع واحد (project_id)
    يمكن أن تكون موكلة لعدة مستخدمين
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime, nullable=False)  # تاريخ الاستحقاق
    priority = db.Column(db.String(20), default='متوسط')  # عالية، متوسط، منخفضة
    status = db.Column(db.String(20), default='قيد الإنجاز')  # قيد الإنجاز، تم الإنجاز، لم يتم التسليم
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)  # المشروع التابع له المهمة
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # منشئ المهمة
    
    # العلاقة مع تسليمات المهام
    submissions = db.relationship('TaskSubmission', backref='task', lazy=True)

class TaskSubmission(db.Model):
    """
    يمثل تسليم المهمة من قبل المستخدم
    """
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    notes = db.Column(db.Text)
    file_path = db.Column(db.String(255), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def is_late(self):
        """التحقق من أن التسليم متأخر"""
        # مقارنة دقيقة بين تاريخ التسليم وتاريخ الاستحقاق
        return self.submitted_at > self.task.due_date
    
    def get_status_display(self):
        """الحصول على حالة التسليم مع التفاصيل"""
        if self.is_late():
            return 'متأخر'
        return 'في الوقت'
    
    def get_late_minutes(self):
        """الحصول على عدد الدقائق المتأخرة"""
        if self.is_late():
            time_diff = self.submitted_at - self.task.due_date
            return int(time_diff.total_seconds() / 60)
        return 0