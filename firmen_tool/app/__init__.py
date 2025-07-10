from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Initialisiere Erweiterungen hier, damit sie global verfügbar sind
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'main.login' # Die Route, zu der umgeleitet wird, wenn ein Login erforderlich ist
login_manager.login_message = "Bitte melden Sie sich an, um diese Seite aufzurufen."
login_manager.login_message_category = "info" # Kategorie für Flash-Nachrichten

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'eine_sehr_geheime_zufaellige_zeichenkette_bitte_aendern'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)

    # Importiere Modelle, damit sie bei der Erstellung der DB bekannt sind
    # und für den User-Loader
    from . import models

    # User loader Funktion für Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))

    # Importiere und registriere Blueprints
    from .routes import main_bp
    app.register_blueprint(main_bp)

    with app.app_context():
        # Hier könnten wir eine Funktion zum Erstellen von DB-Tabellen aufrufen,
        # aber es ist oft besser, dies explizit über einen CLI-Befehl zu tun.
        # Zum Beispiel: db.create_all()
        pass

    return app
