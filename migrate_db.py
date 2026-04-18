from app import app, db, User
import sqlite3

def migrate_database():
    with app.app_context():
        # Try to add the is_admin column if it doesn't exist
        try:
            # Create a raw SQLite connection to alter the table
            conn = sqlite3.connect('glowvera.db')
            cursor = conn.cursor()
            
            # Add the is_admin column if it doesn't exist
            try:
                cursor.execute("ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT 0")
                conn.commit()
                print("Added is_admin column to user table")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print("is_admin column already exists")
                else:
                    raise e
            
            conn.close()
            
            # Now create/update the admin user
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                from werkzeug.security import generate_password_hash
                admin_password_hash = generate_password_hash('faizi123')
                admin_user = User(
                    username='admin',
                    email='admin@glowvera.com',
                    password_hash=admin_password_hash,
                    first_name='Admin',
                    last_name='User',
                    is_admin=True
                )
                db.session.add(admin_user)
                print("Admin user created successfully!")
            else:
                # Update existing admin user to have admin privileges
                admin_user.is_admin = True
                print("Updated existing admin user with admin privileges")
            
            db.session.commit()
            print("Database migration completed successfully!")
            
        except Exception as e:
            print(f"Error during migration: {e}")

if __name__ == '__main__':
    migrate_database()
