from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db, login_manager
from models import User, Project, Task
from flask import flash
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
        
        is_admin = False
        if User.query.count() == 0:
            is_admin = True
        user = User(username=username, password=generate_password_hash(password), is_admin=is_admin)
        db.session.add(user)
        db.session.commit()
        flash('تم التسجيل بنجاح! يمكنك تسجيل الدخول الآن.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('my_tasks'))
        else:
            flash('بيانات الدخول غير صحيحة')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/projects')
@login_required
def projects():
    if current_user.is_admin:
        projects = Project.query.all()
    

    else:
       
        projects = Project.query.join(Task).filter(Task.assigned_to == current_user.id).all()
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
        user_ids = request.form.getlist('users')  # يجب أن تكون قائمة
        project = Project(title=title, description=description)
        for user_id in user_ids:
            user = User.query.get(int(user_id))
            if user:
                project.users.append(user)
        db.session.add(project)
        db.session.commit()
        flash('تم إضافة المشروع')
        return redirect(url_for('projects'))
    users = User.query.filter_by(is_admin=False).all()  # لا تعرض الأدمن في القائمة
    return render_template('add_project.html', users=users)

@app.route('/project/<int:project_id>')
@login_required
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    tasks = Task.query.filter_by(project_id=project_id).all()
    users = User.query.all()
    return render_template('tasks.html', project=project, tasks=tasks, users=users)

@app.route('/project/<int:project_id>/add_task', methods=['GET', 'POST'])
@login_required
def add_task(project_id):
    if not current_user.is_admin:
        flash('غير مصرح لك بإضافة مهمة')
        return redirect(url_for('my_tasks'))
    project = Project.query.get_or_404(project_id)
    users = project.users  # فقط أعضاء المشروع
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        due_date = request.form['due_date']
        priority = request.form['priority']
        assigned_to = request.form['assigned_to']
        task = Task(
            title=title,
            description=description,
            due_date=due_date,
            priority=priority,
            project_id=project_id,
            assigned_to=assigned_to
        )
        db.session.add(task)
        db.session.commit()
        return redirect(url_for('project_detail', project_id=project_id))
    return render_template('add_task.html', users=users, project_id=project_id)


@app.route('/task/<int:task_id>/update_status', methods=['POST'])
@login_required
def update_task_status(task_id):
    task = Task.query.get_or_404(task_id)
    status = request.form['status']
    task.status = status
    db.session.commit()
    return redirect(url_for('project_detail', project_id=task.project_id))

@app.route('/my_tasks')
@login_required
def my_tasks():
    projects = current_user.projects  # المشاريع التي ينتمي لها المستخدم
    tasks = Task.query.filter_by(assigned_to=current_user.id).all()
    return render_template('my_tasks.html', projects=projects, tasks=tasks)

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('غير مصرح لك')
        return redirect(url_for('projects'))
    users = User.query.all()
    projects = Project.query.all()
    return render_template('admin_dashboard.html', users=users, projects=projects)

@app.route('/admin_add_task', methods=['POST'])
@login_required
def admin_add_task():
    if not current_user.is_admin:
        flash('غير مصرح لك')
        return redirect(url_for('admin_dashboard'))
    title = request.form['title']
    description = request.form['description']
    project_id = request.form['project_id']
    assigned_to = request.form['assigned_to']
    task = Task(
        title=title,
        description=description,
        project_id=project_id,
        assigned_to=assigned_to
    )
    db.session.add(task)
    db.session.commit()
    flash('تمت إضافة المهمة')
    return redirect(url_for('admin_dashboard'))
@app.route('/delete_task/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    # يمكن السماح فقط للأدمن أو لصاحب المهمة بحذفها
    if not current_user.is_admin and task.assigned_to != current_user.id:
        flash('غير مصرح لك بحذف هذه المهمة')
        return redirect(url_for('my_tasks'))
    db.session.delete(task)
    db.session.commit()
    flash('تم حذف المهمة بنجاح')
    return redirect(request.referrer or url_for('my_tasks'))