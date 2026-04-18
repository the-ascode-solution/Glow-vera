from app import app, db, Product, User
from werkzeug.security import generate_password_hash
import os

def init_database():
    with app.app_context():
        # Drop all tables and recreate them
        db.drop_all()
        db.create_all()
        
        # Create admin user
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
        
        # Sample products for Glowvera Naturals
        products = [
            Product(
                name="Aloe Vera Soap",
                description="Pure organic aloe vera soap that gently cleanses and moisturizes your skin. Made with 100% natural ingredients including fresh aloe vera gel, coconut oil, and essential oils.",
                price=8.99,
                category="Soap",
                stock_quantity=50,
                ingredients="Aloe Vera Gel, Coconut Oil, Olive Oil, Shea Butter, Lavender Essential Oil",
                weight_grams=100,
                is_featured=True,
                image_url="https://via.placeholder.com/300x300/90EE90/FFFFFF?text=Aloe+Vera+Soap"
            ),
            Product(
                name="Tea Tree Face Wash",
                description="Refreshing face wash with tea tree oil to cleanse and purify your skin. Perfect for oily and acne-prone skin types.",
                price=12.99,
                category="Face Wash",
                stock_quantity=30,
                ingredients="Tea Tree Oil, Green Tea Extract, Aloe Vera, Witch Hazel, Vitamin E",
                weight_grams=150,
                is_featured=True,
                image_url="https://via.placeholder.com/300x300/98FB98/FFFFFF?text=Tea+Tree+Face+Wash"
            ),
            Product(
                name="Argan Hair Oil",
                description="Luxurious argan oil treatment for shiny, healthy hair. Repairs damage and adds natural shine without greasiness.",
                price=18.99,
                category="Hair Oil",
                stock_quantity=25,
                ingredients="Pure Argan Oil, Jojoba Oil, Vitamin E, Rosemary Extract",
                weight_grams=50,
                is_featured=True,
                image_url="https://via.placeholder.com/300x300/FFE4B5/FFFFFF?text=Argan+Hair+Oil"
            ),
            Product(
                name="Lavender Shampoo",
                description="Gentle lavender shampoo that cleanses while calming your senses. Suitable for all hair types.",
                price=10.99,
                category="Shampoo",
                stock_quantity=40,
                ingredients="Lavender Essential Oil, Chamomile Extract, Aloe Vera, Coconut Oil",
                weight_grams=250,
                is_featured=False,
                image_url="https://via.placeholder.com/300x300/E6E6FA/FFFFFF?text=Lavender+Shampoo"
            ),
            Product(
                name="Peppermint Soap",
                description="Invigorating peppermint soap that awakens your senses and provides a deep clean. Great for morning showers.",
                price=7.99,
                category="Soap",
                stock_quantity=35,
                ingredients="Peppermint Essential Oil, Shea Butter, Coconut Oil, Activated Charcoal",
                weight_grams=100,
                is_featured=False,
                image_url="https://via.placeholder.com/300x300/00CED1/FFFFFF?text=Peppermint+Soap"
            ),
            Product(
                name="Rose Face Wash",
                description="Delicate rose face wash that hydrates and tones your skin. Perfect for dry and sensitive skin types.",
                price=14.99,
                category="Face Wash",
                stock_quantity=20,
                ingredients="Rose Water, Rose Essential Oil, Glycerin, Aloe Vera, Vitamin C",
                weight_grams=150,
                is_featured=False,
                image_url="https://via.placeholder.com/300x300/FFB6C1/FFFFFF?text=Rose+Face+Wash"
            ),
            Product(
                name="Coconut Hair Oil",
                description="Pure coconut oil for deep conditioning and hair growth. Natural solution for dry, damaged hair.",
                price=9.99,
                category="Hair Oil",
                stock_quantity=45,
                ingredients="Pure Coconut Oil, Vitamin E, Almond Oil",
                weight_grams=100,
                is_featured=False,
                image_url="https://via.placeholder.com/300x300/F4A460/FFFFFF?text=Coconut+Hair+Oil"
            ),
            Product(
                name="Citrus Shampoo",
                description="Energizing citrus shampoo that revitalizes your hair and scalp. Contains vitamin C for healthy hair growth.",
                price=11.99,
                category="Shampoo",
                stock_quantity=30,
                ingredients="Orange Essential Oil, Lemon Extract, Aloe Vera, Biotin",
                weight_grams=250,
                is_featured=False,
                image_url="https://via.placeholder.com/300x300/FFA500/FFFFFF?text=Citrus+Shampoo"
            )
        ]
        
        for product in products:
            db.session.add(product)
        
        # Add default System Settings
        from app import SystemSetting
        db.session.add(SystemSetting(setting_key='tax_cod', setting_value='8'))
        db.session.add(SystemSetting(setting_key='tax_advance', setting_value='5'))
        
        db.session.commit()
        print("Database initialized with admin user, sample products, and default settings!")


if __name__ == '__main__':
    init_database()
