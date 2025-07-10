from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin # Importiere UserMixin

# Die User-Loader-Funktion wird jetzt in __init__.py definiert, wo login_manager initialisiert wird.

class User(UserMixin, db.Model): # Füge UserMixin hinzu
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

from datetime import datetime, date # Für created_at Zeitstempel und due_date

# Hinweise zur Datenbankerstellung und Admin-User-Erstellung bleiben relevant:
# Um die Datenbank und Tabellen zu erstellen (einmalig aus der Flask-Shell):
# from app import create_app, db
# app = create_app()
# with app.app_context():
#     db.create_all()
#     print("Datenbanktabellen erstellt.")

# Um den ersten Admin-User zu erstellen (einmalig aus der Flask-Shell):
# from app import create_app, db
# from app.models import User
# app = create_app()
# with app.app_context():
#     if not User.query.filter_by(username='developer').first():
#         admin = User(username='developer', is_admin=True)
#         admin.set_password('IhrSicheresPasswortHier') # BITTE ÄNDERN SIE DIESES PASSWORT!
#         db.session.add(admin)
#         db.session.commit()
#         print("Developer-Account erstellt.")
#     else:
#         print("Developer-Account existiert bereits.")

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # ForeignKey zu User Tabelle
    recipients = db.Column(db.String(500)) # Komma-separierte E-Mail Adressen

    author = db.relationship('User', backref=db.backref('reports', lazy=True)) # Beziehung zu User

    def __repr__(self):
        return f'<Report {self.title}>'

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    due_date = db.Column(db.Date, nullable=True) # Fälligkeitsdatum
    priority = db.Column(db.String(50), default='Mittel') # z.B. Niedrig, Mittel, Hoch
    status = db.Column(db.String(50), default='Offen') # z.B. Offen, In Arbeit, Erledigt
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Ersteller/Zugewiesener

    assignee = db.relationship('User', backref=db.backref('tasks', lazy=True))

    def __repr__(self):
        return f'<Task {self.title}>'
