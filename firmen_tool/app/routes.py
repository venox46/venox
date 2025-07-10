from flask import render_template, Blueprint, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, Report, Task # Task Modell importieren
from app import db
from functools import wraps # Für den Admin-Decorator
from datetime import datetime # Für due_date parsing

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/index')
def index():
    return render_template('index.html', title='Startseite')

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard')) # Oder eine andere Zielseite für eingeloggte User

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False # Optional: "Angemeldet bleiben"

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash('Login erfolgreich!', 'success')
            # Leite zu der Seite weiter, die der User ursprünglich ansteuern wollte
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Login fehlgeschlagen. Überprüfen Sie Benutzername und Passwort.', 'danger')

    return render_template('login.html', title='Login')

@main_bp.route('/logout')
@login_required # Stellt sicher, dass nur eingeloggte User sich ausloggen können
def logout():
    logout_user()
    flash('Sie wurden erfolgreich ausgeloggt.', 'info')
    return redirect(url_for('main.login'))

@main_bp.route('/dashboard')
@login_required # Diese Route erfordert jetzt einen Login
def dashboard():
    # Diese Seite ist nur für eingeloggte Benutzer zugänglich.
    # Später können wir hier spezifische Inhalte für den Developer/Admin anzeigen.
    if current_user.is_admin:
        greeting = f"Willkommen im Dashboard, Admin {current_user.username}!"
    else:
        greeting = f"Willkommen im Dashboard, {current_user.username}!"
    return render_template('dashboard.html', title='Dashboard', greeting=greeting)


# Decorator für Admin-geschützte Routen
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Für diese Aktion sind Administratorrechte erforderlich.", "danger")
            return redirect(url_for('main.index')) # Oder 'main.dashboard'
        return f(*args, **kwargs)
    return decorated_function

# --- Benutzerverwaltung (Admin) ---
@main_bp.route('/admin/users')
@login_required
@admin_required
def list_users():
    users = User.query.all()
    return render_template('admin/list_users.html', title="Benutzerverwaltung", users=users)

@main_bp.route('/admin/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        is_admin_form = request.form.get('is_admin') == 'on' # Checkbox Wert

        if not username or not password:
            flash('Benutzername und Passwort sind erforderlich.', 'danger')
        elif User.query.filter_by(username=username).first():
            flash('Dieser Benutzername existiert bereits.', 'warning')
        else:
            new_user = User(username=username, is_admin=is_admin_form)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash(f'Benutzer {username} erfolgreich erstellt.', 'success')
            return redirect(url_for('main.list_users'))

    return render_template('admin/add_user.html', title="Benutzer hinzufügen")

@main_bp.route('/admin/users/delete/<int:user_id>', methods=['POST']) # Nur POST, um CSRF zu vermeiden (besser mit Formular und CSRF-Token)
@login_required
@admin_required
def delete_user(user_id):
    user_to_delete = User.query.get_or_404(user_id)
    if user_to_delete.id == current_user.id:
        flash('Sie können sich nicht selbst löschen.', 'danger')
        return redirect(url_for('main.list_users'))

    # Verhindere das Löschen des letzten Admins, wenn es der einzige ist.
    # Diese Logik kann verfeinert werden.
    if user_to_delete.is_admin:
        admin_users_count = User.query.filter_by(is_admin=True).count()
        if admin_users_count <= 1:
            flash('Der letzte Administrator kann nicht gelöscht werden.', 'danger')
            return redirect(url_for('main.list_users'))

    db.session.delete(user_to_delete)
    db.session.commit()
    flash(f'Benutzer {user_to_delete.username} wurde gelöscht.', 'success')
    return redirect(url_for('main.list_users'))


# Es ist eine gute Praxis, Flask-WTF für Formulare zu verwenden,
# um CSRF-Schutz automatisch zu erhalten.
# Das Login-Template (`login.html`) müsste dann angepasst werden, um das Formular von Flask-WTF zu rendern.
# Beispiel:
# from flask_wtf import FlaskForm

# --- Berichtsfunktionen ---
@main_bp.route('/reports')
@login_required
def list_reports():
    # Zeige Berichte, die vom aktuellen Benutzer erstellt wurden
    reports = Report.query.filter_by(user_id=current_user.id).order_by(Report.created_at.desc()).all()
    return render_template('reports/list_reports.html', title="Meine Berichte", reports=reports)

@main_bp.route('/reports/create', methods=['GET', 'POST'])
@login_required
def create_report():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        recipients = request.form.get('recipients')

        if not title or not content:
            flash('Titel und Inhalt sind erforderlich.', 'danger')
        else:
            report = Report(title=title, content=content, recipients=recipients, author=current_user)
            db.session.add(report)
            db.session.commit()
            flash('Bericht erfolgreich erstellt.', 'success')
            # Später hier: E-Mail Versand Logik (noch nicht in diesem Schritt)
            # For now, we can simulate by flashing the recipients:
            if recipients:
                flash(f"Bericht würde an folgende Empfänger gesendet werden (Simulation): {recipients}", "info")
            return redirect(url_for('main.list_reports'))

    return render_template('reports/create_report.html', title="Neuen Bericht erstellen")

@main_bp.route('/reports/view/<int:report_id>')
@login_required
def view_report(report_id):
    report = Report.query.get_or_404(report_id)
    # Stelle sicher, dass der User nur eigene Berichte sieht, es sei denn er ist Admin
    if report.user_id != current_user.id and not current_user.is_admin:
        flash("Sie haben keine Berechtigung, diesen Bericht anzuzeigen.", "danger")
        return redirect(url_for('main.list_reports'))
    return render_template('reports/view_report.html', title=report.title, report=report)

@main_bp.route('/reports/delete/<int:report_id>', methods=['POST'])
@login_required
def delete_report(report_id):
    report_to_delete = Report.query.get_or_404(report_id)
    if report_to_delete.user_id != current_user.id and not current_user.is_admin:
        flash("Sie haben keine Berechtigung, diesen Bericht zu löschen.", "danger")
        return redirect(url_for('main.list_reports'))

    db.session.delete(report_to_delete)
    db.session.commit()
    flash(f'Bericht "{report_to_delete.title}" wurde gelöscht.', 'success')
    return redirect(url_for('main.list_reports'))
# from wtforms import StringField, PasswordField, BooleanField, SubmitField
# from wtforms.validators import DataRequired
#

# --- Aufgabenverwaltungsfunktionen ---
PRIORITY_CHOICES = ['Niedrig', 'Mittel', 'Hoch']
STATUS_CHOICES = ['Offen', 'In Arbeit', 'Erledigt']

@main_bp.route('/tasks')
@login_required
def list_tasks():
    # Zeige Aufgaben, die vom aktuellen Benutzer erstellt/ihm zugewiesen wurden
    # In dieser Basisversion gehen wir davon aus, dass user_id der Ersteller ist.
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.due_date.asc(), Task.created_at.desc()).all()
    return render_template('tasks/list_tasks.html', title="Meine Aufgaben", tasks=tasks)

@main_bp.route('/tasks/create', methods=['GET', 'POST'])
@login_required
def create_task():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        due_date_str = request.form.get('due_date')
        priority = request.form.get('priority')
        status = request.form.get('status')

        if not title:
            flash('Titel ist erforderlich.', 'danger')
        else:
            due_date = None
            if due_date_str:
                try:
                    due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                except ValueError:
                    flash('Ungültiges Datumsformat für Fälligkeitsdatum. Bitte JJJJ-MM-TT verwenden.', 'danger')
                    return render_template('tasks/create_task.html', title="Neue Aufgabe erstellen", priorities=PRIORITY_CHOICES, statuses=STATUS_CHOICES, task=request.form)

            task = Task(title=title, description=description, due_date=due_date,
                        priority=priority if priority in PRIORITY_CHOICES else 'Mittel',
                        status=status if status in STATUS_CHOICES else 'Offen',
                        assignee=current_user)
            db.session.add(task)
            db.session.commit()
            flash('Aufgabe erfolgreich erstellt.', 'success')
            return redirect(url_for('main.list_tasks'))

    return render_template('tasks/create_task.html', title="Neue Aufgabe erstellen", priorities=PRIORITY_CHOICES, statuses=STATUS_CHOICES)

@main_bp.route('/tasks/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id and not current_user.is_admin: # Admins dürfen alle Tasks bearbeiten
        flash("Sie haben keine Berechtigung, diese Aufgabe zu bearbeiten.", "danger")
        return redirect(url_for('main.list_tasks'))

    if request.method == 'POST':
        task.title = request.form.get('title')
        task.description = request.form.get('description')
        due_date_str = request.form.get('due_date')
        task.priority = request.form.get('priority')
        task.status = request.form.get('status')

        if not task.title:
            flash('Titel ist erforderlich.', 'danger')
        else:
            if due_date_str:
                try:
                    task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                except ValueError:
                    flash('Ungültiges Datumsformat für Fälligkeitsdatum. Bitte JJJJ-MM-TT verwenden.', 'danger')
                    # Formular erneut mit den bereits eingegebenen Daten anzeigen
                    return render_template('tasks/edit_task.html', title="Aufgabe bearbeiten", task=task, priorities=PRIORITY_CHOICES, statuses=STATUS_CHOICES)
            else:
                task.due_date = None # Erlaube das Leeren des Datums

            db.session.commit()
            flash('Aufgabe erfolgreich aktualisiert.', 'success')
            return redirect(url_for('main.list_tasks'))

    return render_template('tasks/edit_task.html', title="Aufgabe bearbeiten", task=task, priorities=PRIORITY_CHOICES, statuses=STATUS_CHOICES)

@main_bp.route('/tasks/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task_to_delete = Task.query.get_or_404(task_id)
    if task_to_delete.user_id != current_user.id and not current_user.is_admin:
        flash("Sie haben keine Berechtigung, diese Aufgabe zu löschen.", "danger")
        return redirect(url_for('main.list_tasks'))

    db.session.delete(task_to_delete)
    db.session.commit()
    flash(f'Aufgabe "{task_to_delete.title}" wurde gelöscht.', 'success')
    return redirect(url_for('main.list_tasks'))
# class LoginForm(FlaskForm):
#     username = StringField('Benutzername', validators=[DataRequired()])
#     password = PasswordField('Passwort', validators=[DataRequired()])
#     remember_me = BooleanField('Angemeldet bleiben')
#     submit = SubmitField('Login')
#
# Und in der Route:
# form = LoginForm()
# if form.validate_on_submit():
#     # Logik hier
#     pass
# return render_template('login.html', title='Login', form=form)
#
# Das Template würde dann {{ form.hidden_tag() }}, {{ form.username.label }}, {{ form.username() }} etc. verwenden.
# Für diese Iteration belassen wir es beim einfachen HTML-Formular, um die Komplexität gering zu halten.
