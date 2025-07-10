import os
from app import create_app, db
from app.models import User, Report, Task # Alle Modelle importieren für db.create_all()

# Erstelle die Flask-App-Instanz
app = create_app()

def initialize_database():
    """Initialisiert die Datenbank und erstellt den Admin-Benutzer, falls nicht vorhanden."""
    with app.app_context():
        db_file = app.config.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///site.db').replace('sqlite:///', '')

        if not os.path.exists(db_file):
            print(f"Datenbankdatei {db_file} nicht gefunden. Erstelle Datenbank und Tabellen...")
            try:
                db.create_all()
                print("Datenbank und Tabellen erfolgreich erstellt.")
            except Exception as e:
                print(f"Fehler beim Erstellen der Datenbanktabellen: {e}")
                return False
        else:
            # Auch wenn die Datei existiert, könnten Tabellen fehlen, wenn Modelle später hinzugefügt wurden.
            # create_all() fügt nur fehlende Tabellen hinzu und ändert bestehende nicht.
            try:
                db.create_all()
                print("Tabellen überprüft/erstellt (falls notwendig).")
            except Exception as e:
                print(f"Fehler beim Überprüfen/Erstellen der Tabellen: {e}")
                # Nicht unbedingt ein fataler Fehler, wenn die DB schon existiert und nur ein Check fehlschlägt
                # aber für neue Modelle wäre es ein Problem.

        # Überprüfe und erstelle den Admin-Benutzer
        admin_username = 'developer'
        admin_password = 'admin' # Standardpasswort

        existing_admin = User.query.filter_by(username=admin_username).first()
        if not existing_admin:
            print(f"Admin-Benutzer '{admin_username}' nicht gefunden. Erstelle Admin-Benutzer...")
            try:
                admin = User(username=admin_username, is_admin=True)
                admin.set_password(admin_password)
                db.session.add(admin)
                db.session.commit()
                print(f"Admin-Benutzer '{admin_username}' mit Passwort '{admin_password}' erfolgreich erstellt.")
                print(f"BITTE ÄNDERN SIE DAS ADMIN-PASSWORT '{admin_password}' NACH DEM ERSTEN LOGIN!")
            except Exception as e:
                print(f"Fehler beim Erstellen des Admin-Benutzers: {e}")
                # db.session.rollback() # Bei Fehler Rollback durchführen
                return False
        else:
            print(f"Admin-Benutzer '{admin_username}' existiert bereits.")
            # Optional: Passwort-Reset-Logik, falls das Passwort vergessen wurde (nicht Teil dieser einfachen Version)
            # Man könnte hier auch prüfen, ob das Standardpasswort noch gesetzt ist und erneut warnen.

    return True

if __name__ == '__main__':
    print("Initialisiere die Anwendung...")
    if initialize_database():
        print("Initialisierung abgeschlossen.")
        print("Starte den Flask Development Server...")
        print("Das Tool ist erreichbar unter: http://127.0.0.1:5000/")
        print("Drücken Sie STRG+C, um den Server zu beenden.")
        app.run(debug=True, host='0.0.0.0') # host='0.0.0.0' macht es im lokalen Netzwerk erreichbar
    else:
        print("Fehler bei der Initialisierung. Die Anwendung konnte nicht gestartet werden.")
