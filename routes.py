from flask import render_template, redirect, url_for, request, flash, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from app import app, db, login_manager
from models import User, Project, Task, TaskSubmission, task_users
from datetime import datetime
import os

# إعدادات رفع الملفات
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'zip', 'rar'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# إنشاء مجلد الرفع إذا لم يكن موجوداً
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('home.html')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('اسم المستخدم موجود بالفعل')
            return redirect(url_for('register'))
        
        # أول مستخدم يصبح أدمن
        is_admin = User.query.count() == 0
        user = User(username=username, password=generate_password_hash(password), is_admin=is_admin)
        db.session.add(user)
        db.session.commit()
        
        flash('تم التسجيل بنجاح')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        print(f"محاولة تسجيل دخول: {username}")  # رسالة تصحيح
        
        if user and check_password_hash(user.password, password):
            print(f"تم التحقق من كلمة المرور بنجاح للمستخدم: {username}")  # رسالة تصحيح
            login_user(user)
            print(f"تم تسجيل دخول المستخدم: {username}, is_admin: {user.is_admin}")  # رسالة تصحيح
            flash('تم تسجيل الدخول بنجاح')
            if user.is_admin:
                print("إعادة التوجيه إلى لوحة الإدارة")  # رسالة تصحيح
                return redirect(url_for('admin_dashboard'))
            else:
                print("إعادة التوجيه إلى المشاريع")  # رسالة تصحيح
                return redirect(url_for('projects'))
        else:
            print(f"فشل في تسجيل الدخول للمستخدم: {username}")  # رسالة تصحيح
            flash('اسم المستخدم أو كلمة المرور غير صحيحة')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('تم تسجيل الخروج بنجاح')
    return redirect(url_for('home'))

@app.route('/projects')
@login_required
def projects():
    if current_user.is_admin:
        projects = Project.query.all()
    else:
        projects = current_user.projects
    return render_template('projects.html', projects=projects)

@app.route('/add_project', methods=['GET', 'POST'])
@login_required
def add_project():
    if not current_user.is_admin:
        flash('غير مصرح لك')
        return redirect(url_for('my_tasks'))
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        user_ids = request.form.getlist('users')
        project = Project(title=title, description=description)
        db.session.add(project)
        db.session.flush()  # للحصول على ID المشروع
        
        for user_id in user_ids:
            user = User.query.get(int(user_id))
            if user:
                project.users.append(user)
        
        db.session.commit()
        flash('تم إضافة المشروع')
        return redirect(url_for('projects'))
    users = User.query.filter_by(is_admin=False).all()
    return render_template('add_project.html', users=users)

@app.route('/project/<int:project_id>')
@login_required
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    if not current_user.is_admin and project not in current_user.projects:
        flash('غير مصرح لك بالوصول لهذا المشروع')
        return redirect(url_for('projects'))
    
    tasks = Task.query.filter_by(project_id=project_id).all()
    users = project.users
    return render_template('tasks.html', project=project, tasks=tasks, users=users)

@app.route('/project/<int:project_id>/add_task', methods=['GET', 'POST'])
@login_required
def add_task(project_id):
    if not current_user.is_admin:
        flash('غير مصرح لك بإضافة مهمة')
        return redirect(url_for('my_tasks'))
    
    project = Project.query.get_or_404(project_id)
    users = project.users
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        due_date_str = request.form['due_date']
        priority = request.form['priority']
        assigned_user_ids = request.form.getlist('assigned_users')
        
        # تحويل التاريخ
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('تاريخ غير صحيح')
            return render_template('add_task.html', users=users, project_id=project_id)
        
        task = Task(
            title=title,
            description=description,
            due_date=due_date,
            priority=priority,
            project_id=project_id,
            created_by=current_user.id
        )
        
        # إضافة المستخدمين الموكلة إليهم المهمة
        for user_id in assigned_user_ids:
            user = User.query.get(int(user_id))
            if user:
                task.assigned_users.append(user)
        
        db.session.add(task)
        db.session.commit()
        flash('تم إضافة المهمة بنجاح')
        return redirect(url_for('project_detail', project_id=project_id))
    
    return render_template('add_task.html', users=users, project_id=project_id)

@app.route('/task/<int:task_id>/submit', methods=['GET', 'POST'])
@login_required
def submit_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    # التحقق من أن المستخدم موكلة إليه المهمة
    if current_user not in task.assigned_users:
        flash('غير مصرح لك بتسليم هذه المهمة')
        return redirect(url_for('my_tasks'))
    
    if request.method == 'POST':
        file = request.files['file']
        notes = request.form.get('notes', '')
        
        if file and file.filename:
            # التحقق من اسم الملف
            if not file.filename.lower().startswith(task.title.lower().replace(' ', '_')):
                flash('اسم الملف يجب أن يبدأ باسم المهمة')
                return render_template('submit_task.html', task=task)
            
            if file and allowed_file(file.filename):
                # حفظ اسم الملف الأصلي
                original_filename = file.filename
                
                # إنشاء اسم فريد للملف
                unique_filename = f"{task.id}_{current_user.id}_{original_filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                
                # إنشاء تسليم جديد - حفظ اسم الملف النسبي فقط
                submission = TaskSubmission(
                    task_id=task_id,
                    user_id=current_user.id,
                    file_path=unique_filename,  # حفظ الاسم النسبي فقط
                    file_name=original_filename,  # حفظ الاسم الأصلي
                    notes=notes
                )
                
                db.session.add(submission)
                db.session.commit()
                
                flash('تم تسليم المهمة بنجاح')
                return redirect(url_for('my_tasks'))
            else:
                flash('نوع الملف غير مسموح به')
        else:
            flash('يرجى اختيار ملف')
    
    return render_template('submit_task.html', task=task)

@app.route('/task/<int:task_id>/update_status', methods=['POST'])
@login_required
def update_task_status(task_id):
    task = Task.query.get_or_404(task_id)
    if not current_user.is_admin:
        flash('غير مصرح لك بتحديث حالة المهمة')
        return redirect(url_for('my_tasks'))
    
    status = request.form['status']
    task.status = status
    db.session.commit()
    flash('تم تحديث حالة المهمة')
    return redirect(url_for('project_detail', project_id=task.project_id))

@app.route('/my_tasks')
@login_required
def my_tasks():
    # المهام الموكلة للمستخدم
    assigned_tasks = current_user.assigned_tasks
    # المشاريع التي ينتمي لها المستخدم
    projects = current_user.projects
    
    return render_template('my_tasks.html', projects=projects, tasks=assigned_tasks)

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('غير مصرح لك')
        return redirect(url_for('projects'))
    
    users = User.query.all()
    projects = Project.query.all()
    tasks = Task.query.all()
    submissions = TaskSubmission.query.all()
    
    return render_template('admin_dashboard.html', 
                         users=users, 
                         projects=projects, 
                         tasks=tasks, 
                         submissions=submissions)

@app.route('/admin_add_task', methods=['POST'])
@login_required
def admin_add_task():
    if not current_user.is_admin:
        flash('غير مصرح لك')
        return redirect(url_for('admin_dashboard'))
    
    title = request.form['title']
    description = request.form['description']
    project_id = request.form['project_id']
    due_date_str = request.form['due_date']
    priority = request.form['priority']
    assigned_user_ids = request.form.getlist('assigned_users')
    
    try:
        due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
    except ValueError:
        flash('تاريخ غير صحيح')
        return redirect(url_for('admin_dashboard'))
    
    task = Task(
        title=title,
        description=description,
        due_date=due_date,
        priority=priority,
        project_id=project_id,
        created_by=current_user.id
    )
    
    for user_id in assigned_user_ids:
        user = User.query.get(int(user_id))
        if user:
            task.assigned_users.append(user)
    
    db.session.add(task)
    db.session.commit()
    flash('تمت إضافة المهمة')
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_task/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if not current_user.is_admin:
        flash('غير مصرح لك بحذف هذه المهمة')
        return redirect(url_for('my_tasks'))
    
    db.session.delete(task)
    db.session.commit()
    flash('تم حذف المهمة بنجاح')
    return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/download_submission/<int:submission_id>')
@login_required
def download_submission(submission_id):
    submission = TaskSubmission.query.get_or_404(submission_id)
    
    # التحقق من الصلاحيات
    if not current_user.is_admin and submission.user_id != current_user.id:
        flash('غير مصرح لك بتحميل هذا الملف')
        return redirect(url_for('my_tasks'))
    
    # بناء المسار الكامل للملف
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], submission.file_path)
    
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=submission.file_name)
    else:
        flash('الملف غير موجود')
        return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/task_submissions/<int:task_id>')
@login_required
def task_submissions(task_id):
    task = Task.query.get_or_404(task_id)
    
    if not current_user.is_admin and current_user not in task.assigned_users:
        flash('غير مصرح لك بالوصول لهذه المهمة')
        return redirect(url_for('my_tasks'))
    
    submissions = TaskSubmission.query.filter_by(task_id=task_id).all()
    return render_template('task_submissions.html', task=task, submissions=submissions)

@app.route('/users')
@login_required
def users():
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول لهذه الصفحة')
        return redirect(url_for('projects'))
    
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/reports')
@login_required
def reports():
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول لهذه الصفحة')
        return redirect(url_for('projects'))
    
    # إحصائيات بسيطة
    total_projects = Project.query.count()
    total_tasks = Task.query.count()
    completed_tasks = Task.query.filter_by(status='تم الإنجاز').count()
    pending_tasks = Task.query.filter_by(status='قيد الإنجاز').count()
    
    return render_template('reports.html',
                         total_projects=total_projects,
                         total_tasks=total_tasks,
                         completed_tasks=completed_tasks,
                         pending_tasks=pending_tasks)

@app.route('/all_submissions')
@login_required
def all_submissions():
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول لهذه الصفحة')
        return redirect(url_for('projects'))
    
    # جلب جميع التسليمات مع معلومات المهمة والمستخدم
    submissions = db.session.query(TaskSubmission, Task, User).join(
        Task, TaskSubmission.task_id == Task.id
    ).join(
        User, TaskSubmission.user_id == User.id
    ).order_by(TaskSubmission.submitted_at.desc()).all()
    
    return render_template('all_submissions.html', submissions=submissions)

@app.route('/task/<int:task_id>/complete', methods=['POST'])
@login_required
def complete_task(task_id):
    if not current_user.is_admin:
        flash('غير مصرح لك بتغيير حالة المهمة')
        return redirect(url_for('my_tasks'))
    
    task = Task.query.get_or_404(task_id)
    task.status = 'تم الإنجاز'
    db.session.commit()
    flash('تم تغيير حالة المهمة إلى "منجزة"')
    return redirect(url_for('project_detail', project_id=task.project_id))

@app.route('/task/<int:task_id>/reopen', methods=['POST'])
@login_required
def reopen_task(task_id):
    if not current_user.is_admin:
        flash('غير مصرح لك بتغيير حالة المهمة')
        return redirect(url_for('my_tasks'))
    
    task = Task.query.get_or_404(task_id)
    task.status = 'قيد الإنجاز'
    db.session.commit()
    flash('تم إعادة فتح المهمة')
    return redirect(url_for('project_detail', project_id=task.project_id))

@app.route('/all_users')
@login_required
def all_users():
    if not current_user.is_admin:
        flash('غير مصرح لك بالوصول لهذه الصفحة')
        return redirect(url_for('my_tasks'))
    
    users = User.query.all()
    return render_template('all_users.html', users=users)

@app.route('/completed_tasks')
@login_required
def completed_tasks():
    if current_user.is_admin:
        # الأدمن يرى جميع المهام المنجزة
        tasks = Task.query.filter_by(status='تم الإنجاز').all()
    else:
        # المستخدم العادي يرى المهام المنجزة الموكلة إليه فقط
        tasks = Task.query.filter_by(status='تم الإنجاز').join(task_users).filter(task_users.c.user_id == current_user.id).all()
    
    return render_template('completed_tasks.html', tasks=tasks)

@app.context_processor
def inject_now():
    return {'now': datetime.now()}