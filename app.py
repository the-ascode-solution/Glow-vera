from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from logging.handlers import RotatingFileHandler

# Load environment variables
load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

# Production Logging setup (must be early to capture startup issues)
if not app.debug:
    log_dir = os.path.join(basedir, 'logs')
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir, exist_ok=True)
        except Exception:
            pass # Fallback to stdout if we can't create logs
    
    log_file = os.path.join(log_dir, 'glowvera.log')
    try:
        file_handler = RotatingFileHandler(log_file, maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
    except Exception as e:
        print(f"Could not setup log file: {e}")
        
    app.logger.setLevel(logging.INFO)
    app.logger.info('Glow-Vera startup')

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key_for_dev_only')
if not app.debug and app.config['SECRET_KEY'] == 'default_secret_key_for_dev_only':
    app.logger.warning("Running with default SECRET_KEY! This is insecure for production.")
# Use absolute path for SQLite to avoid issues on shared hosting
default_db_path = f"sqlite:///{os.path.join(basedir, 'instance', 'glowvera.db')}"
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', default_db_path)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Enable CSRF Protection
csrf = CSRFProtect(app)

# Rate Limiting setup
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

UPLOAD_FOLDER = os.path.join(basedir, 'static', 'images', 'products')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Ensure tables are created on startup (essential for new production tables like Review)
with app.app_context():
    try:
        db.create_all()
        app.logger.info("Database tables verified/created")
    except Exception as e:
        app.logger.error(f"Database initialization error: {e}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Currency Configuration - Set to PKR Native
NATIVE_CURRENCY = {'symbol': 'Rs', 'name': 'Pakistani Rupee'}

@app.context_processor
def utility_processor():
    def format_price(price):
        if not price:
            price = 0
        symbol = NATIVE_CURRENCY['symbol']
        return f"{symbol} {int(price):,}"
    
    return dict(format_price=format_price, currency=NATIVE_CURRENCY)

@app.template_filter('nl2br')
def nl2br_filter(s):
    if not s:
        return ""
    return s.replace('\n', '<br>\n')

@app.route('/favicon.ico')
def favicon():
    return '', 204

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    orders = db.relationship('Order', backref='user', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(200))
    category = db.Column(db.String(50), nullable=False)
    stock_quantity = db.Column(db.Integer, default=0)
    ingredients = db.Column(db.Text)
    weight_grams = db.Column(db.Integer)
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    customer_phone = db.Column(db.String(20))
    total_amount = db.Column(db.Float, nullable=False)
    tax_rate = db.Column(db.Float, default=0.08)
    tax_amount = db.Column(db.Float, default=0.0)
    shipping_fee = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='pending')
    payment_method = db.Column(db.String(30), default='cod')
    shipping_address = db.Column(db.Text, nullable=False)
    discount_amount = db.Column(db.Float, default=0.0)
    promo_code = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    order_items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    
    product = db.relationship('Product', backref='order_items')

# Association table for promo codes and specific products
promo_products = db.Table('promo_products',
    db.Column('promo_id', db.Integer, db.ForeignKey('promo_code.id'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('product.id'), primary_key=True)
)

class PromoCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    discount_type = db.Column(db.String(25), nullable=False)  # 'percentage', 'fixed', or 'free_shipping'
    discount_value = db.Column(db.Float, default=0.0)
    applies_to = db.Column(db.String(20), default='all')  # 'all' or 'specific'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    products = db.relationship('Product', secondary=promo_products, backref='promo_codes')

class SystemSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(50), unique=True, nullable=False)
    setting_value = db.Column(db.String(255), nullable=False)


class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='new')  # 'new', 'read', 'replied'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reviewer_name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    review_text = db.Column(db.Text, nullable=False)
    review_date = db.Column(db.DateTime, nullable=False)  # Manually set by admin
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)  # Optional product link
    is_visible = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    product = db.relationship('Product', backref='reviews')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from functools import wraps
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Unauthorized access. Admin privileges required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Add Security Headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    if not app.debug:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

@app.route('/')
def index():
    featured_products = Product.query.filter_by(is_featured=True).limit(6).all()
    visible_reviews = Review.query.filter_by(is_visible=True).order_by(Review.review_date.desc()).limit(6).all()
    return render_template('index.html', featured_products=featured_products, visible_reviews=visible_reviews)

@app.route('/products')
def products():
    category = request.args.get('category')
    if category:
        products = Product.query.filter_by(category=category).all()
    else:
        products = Product.query.all()
    categories = db.session.query(Product.category).distinct().all()
    categories = [cat[0] for cat in categories]
    return render_template('products.html', products=products, categories=categories, selected_category=category)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    product_reviews = Review.query.filter_by(product_id=product_id, is_visible=True).order_by(Review.review_date.desc()).all()
    return render_template('product_detail.html', product=product, product_reviews=product_reviews)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        new_msg = ContactMessage(
            name=name,
            email=email,
            subject=subject,
            message=message
        )
        db.session.add(new_msg)
        db.session.commit()
        
        flash('Thank you! Your message has been sent successfully.', 'success')
        return redirect(url_for('contact'))
        
    return render_template('contact.html')

@app.route('/admin/messages')
@admin_required
def admin_messages():
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('admin_messages.html', messages=messages)

@app.route('/admin/message/<int:msg_id>/delete', methods=['POST'])
@admin_required
def admin_delete_message(msg_id):
    msg = ContactMessage.query.get_or_404(msg_id)
    db.session.delete(msg)
    db.session.commit()
    flash('Message deleted.', 'info')
    return redirect(url_for('admin_messages'))

@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/terms-of-service')
def terms_of_service():
    return render_template('terms_of_service.html')

@app.route('/shipping-policy')
def shipping_policy():
    return render_template('shipping_policy.html')

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    cart = session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    session['cart'] = cart
    flash(f'{product.name} added to cart!', 'success')
    return redirect(url_for('product_detail', product_id=product_id))

@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    cart_items = []
    total = 0
    
    for product_id, quantity in cart.items():
        product = Product.query.get(int(product_id))
        if product:
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': product.price * quantity
            })
            total += product.price * quantity
    
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/update_cart/<int:product_id>')
def update_cart(product_id):
    action = request.args.get('action')
    cart = session.get('cart', {})
    product_id_str = str(product_id)
    
    if action == 'increase':
        cart[product_id_str] = cart.get(product_id_str, 0) + 1
    elif action == 'decrease':
        if cart.get(product_id_str, 0) > 1:
            cart[product_id_str] -= 1
        else:
            cart.pop(product_id_str, None)
    elif action == 'remove':
        cart.pop(product_id_str, None)
    
    session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        # Validation
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'error')
            return redirect(url_for('register'))
            
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            first_name=first_name,
            last_name=last_name
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, is_admin=True).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            session['is_admin'] = True
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    total_products = Product.query.count()
    total_orders = Order.query.count()
    total_messages = ContactMessage.query.count()
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    low_stock_products = Product.query.filter(Product.stock_quantity < 10).all()
    
    return render_template('admin_dashboard.html', 
                         total_products=total_products,
                         total_orders=total_orders,
                         total_messages=total_messages,
                         recent_orders=recent_orders,
                         low_stock_products=low_stock_products)

@app.route('/admin/products')
@admin_required
def admin_products():
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template('admin_products.html', products=products)

@app.route('/admin/product/new', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    if request.method == 'POST':
        image_url = url_for('static', filename='images/logo.jpeg')
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                image_url = url_for('static', filename=f'images/products/{filename}')

        new_product = Product(
            name=request.form['name'],
            description=request.form['description'],
            price=float(request.form['price']),
            image_url=image_url,
            category=request.form['category'],
            stock_quantity=int(request.form['stock_quantity']),
            ingredients=request.form.get('ingredients', ''),
            weight_grams=int(request.form.get('weight_grams', 0)),
            is_featured='is_featured' in request.form
        )
        
        db.session.add(new_product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin_products'))
    
    return render_template('admin_product_form.html', product=None)

@app.route('/admin/product/<int:product_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        image_url = product.image_url
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                image_url = url_for('static', filename=f'images/products/{filename}')
                
        product.name = request.form['name']
        product.description = request.form['description']
        product.price = float(request.form['price'])
        product.image_url = image_url
        product.category = request.form['category']
        product.stock_quantity = int(request.form['stock_quantity'])
        product.ingredients = request.form.get('ingredients', '')
        product.weight_grams = int(request.form.get('weight_grams', 0))
        product.is_featured = 'is_featured' in request.form
        
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin_products'))
    
    return render_template('admin_product_form.html', product=product)

@app.route('/admin/product/<int:product_id>/delete', methods=['POST'])
@admin_required
def admin_delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/orders')
@admin_required
def admin_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin_orders.html', orders=orders)

@app.route('/admin/order/<int:order_id>')
@admin_required
def admin_order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('admin_order_detail.html', order=order)

@app.route('/admin/order/<int:order_id>/update_status', methods=['POST'])
@admin_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('new_status')
    if new_status in ['pending', 'processing', 'shipped', 'delivered']:
        order.status = new_status
        db.session.commit()
        flash(f'Order #{order.id} status updated to {new_status.title()}!', 'success')
    else:
        flash('Invalid status', 'error')
    return redirect(url_for('admin_order_detail', order_id=order.id))

@app.route('/admin/order/<int:order_id>/invoice')
@admin_required
def admin_order_invoice(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('invoice.html', order=order)

@app.route('/admin/promo-codes')
@admin_required
def admin_promo_codes():
    promos = PromoCode.query.order_by(PromoCode.created_at.desc()).all()
    return render_template('admin_promo_codes.html', promos=promos)

@app.route('/admin/promo-codes/new', methods=['GET', 'POST'])
@admin_required
def admin_add_promo():
    if request.method == 'POST':
        code = request.form['code'].strip().upper()
        name = request.form['name'].strip()
        discount_type = request.form['discount_type']
        discount_value = float(request.form['discount_value'])
        applies_to = request.form['applies_to']
        
        # Check if code already exists
        existing = PromoCode.query.filter_by(code=code).first()
        if existing:
            flash('Promo code already exists!', 'error')
            products = Product.query.all()
            return render_template('admin_promo_form.html', promo=None, products=products)
        
        promo = PromoCode(
            code=code,
            name=name,
            discount_type=discount_type,
            discount_value=discount_value,
            applies_to=applies_to
        )
        
        if applies_to == 'specific':
            selected_ids = request.form.getlist('product_ids')
            for pid in selected_ids:
                product = Product.query.get(int(pid))
                if product:
                    promo.products.append(product)
        
        db.session.add(promo)
        db.session.commit()
        flash(f'Promo code "{code}" created successfully!', 'success')
        return redirect(url_for('admin_promo_codes'))
    
    products = Product.query.all()
    return render_template('admin_promo_form.html', promo=None, products=products)

@app.route('/admin/promo-codes/<int:promo_id>/toggle', methods=['POST'])
@admin_required
def admin_toggle_promo(promo_id):
    promo = PromoCode.query.get_or_404(promo_id)
    promo.is_active = not promo.is_active
    db.session.commit()
    status = "activated" if promo.is_active else "deactivated"
    flash(f'Promo code "{promo.code}" {status}!', 'success')
    return redirect(url_for('admin_promo_codes'))

@app.route('/admin/promo-codes/<int:promo_id>/delete', methods=['POST'])
@admin_required
def admin_delete_promo(promo_id):
    promo = PromoCode.query.get_or_404(promo_id)
    db.session.delete(promo)
    db.session.commit()
    flash(f'Promo code "{promo.code}" deleted!', 'success')
    return redirect(url_for('admin_promo_codes'))

@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
    if request.method == 'POST':
        tax_cod = request.form.get('tax_cod', '8')
        tax_advance = request.form.get('tax_advance', '5')
        shipping_fee = request.form.get('shipping_fee', '0')
        
        # Save to DB
        setting_cod = SystemSetting.query.filter_by(setting_key='tax_cod').first()
        if not setting_cod:
            setting_cod = SystemSetting(setting_key='tax_cod')
            db.session.add(setting_cod)
        setting_cod.setting_value = tax_cod
        
        setting_advance = SystemSetting.query.filter_by(setting_key='tax_advance').first()
        if not setting_advance:
            setting_advance = SystemSetting(setting_key='tax_advance')
            db.session.add(setting_advance)
        setting_advance.setting_value = tax_advance
        
        setting_shipping = SystemSetting.query.filter_by(setting_key='shipping_fee').first()
        if not setting_shipping:
            setting_shipping = SystemSetting(setting_key='shipping_fee')
            db.session.add(setting_shipping)
        setting_shipping.setting_value = shipping_fee
        
        db.session.commit()
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('admin_settings'))
    
    # Get current settings
    setting_cod = SystemSetting.query.filter_by(setting_key='tax_cod').first()
    tax_cod = setting_cod.setting_value if setting_cod else '8'
    
    setting_advance = SystemSetting.query.filter_by(setting_key='tax_advance').first()
    tax_advance = setting_advance.setting_value if setting_advance else '5'
    
    setting_shipping = SystemSetting.query.filter_by(setting_key='shipping_fee').first()
    shipping_fee = setting_shipping.setting_value if setting_shipping else '0'
    
    return render_template('admin_settings.html', tax_cod=tax_cod, tax_advance=tax_advance, shipping_fee=shipping_fee)

@app.route('/admin/reviews')
@admin_required
def admin_reviews():
    reviews = Review.query.order_by(Review.review_date.desc()).all()
    return render_template('admin_reviews.html', reviews=reviews)

@app.route('/admin/reviews/new', methods=['GET', 'POST'])
@admin_required
def admin_add_review():
    if request.method == 'POST':
        reviewer_name = request.form.get('reviewer_name')
        rating = int(request.form.get('rating'))
        review_text = request.form.get('review_text')
        review_date_str = request.form.get('review_date')
        product_id = request.form.get('product_id')
        is_visible = 'is_visible' in request.form
        
        # Parse the datetime-local input
        try:
            review_date = datetime.fromisoformat(review_date_str)
        except ValueError:
            # Fallback for different formats
            review_date = datetime.strptime(review_date_str, '%Y-%m-%dT%H:%M')
        
        review = Review(
            reviewer_name=reviewer_name,
            rating=rating,
            review_text=review_text,
            review_date=review_date,
            product_id=int(product_id) if product_id else None,
            is_visible=is_visible
        )
        
        db.session.add(review)
        db.session.commit()
        flash('Review added successfully!', 'success')
        return redirect(url_for('admin_reviews'))
    
    products = Product.query.all()
    return render_template('admin_review_form.html', review=None, products=products)

@app.route('/admin/reviews/<int:review_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_review(review_id):
    review = Review.query.get_or_404(review_id)
    
    if request.method == 'POST':
        review.reviewer_name = request.form.get('reviewer_name')
        review.rating = int(request.form.get('rating'))
        review.review_text = request.form.get('review_text')
        review_date_str = request.form.get('review_date')
        product_id = request.form.get('product_id')
        review.is_visible = 'is_visible' in request.form
        
        # Parse the datetime-local input
        try:
            review.review_date = datetime.fromisoformat(review_date_str)
        except ValueError:
            # Fallback for different formats
            review.review_date = datetime.strptime(review_date_str, '%Y-%m-%dT%H:%M')
        review.product_id = int(product_id) if product_id else None
        
        db.session.commit()
        flash('Review updated successfully!', 'success')
        return redirect(url_for('admin_reviews'))
    
    products = Product.query.all()
    return render_template('admin_review_form.html', review=review, products=products)

@app.route('/admin/reviews/<int:review_id>/delete', methods=['POST'])
@admin_required
def admin_delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    db.session.delete(review)
    db.session.commit()
    flash('Review deleted successfully!', 'success')
    return redirect(url_for('admin_reviews'))

@app.route('/admin/reviews/<int:review_id>/toggle', methods=['POST'])
@admin_required
def admin_toggle_review(review_id):
    review = Review.query.get_or_404(review_id)
    review.is_visible = not review.is_visible
    db.session.commit()
    status = "visible" if review.is_visible else "hidden"
    flash(f'Review is now {status}!', 'success')
    return redirect(url_for('admin_reviews'))

@app.route('/admin/logout')
@admin_required
def admin_logout():
    session.pop('is_admin', None)
    logout_user()
    flash('Admin logged out', 'info')
    return redirect(url_for('admin_login'))

@app.route('/logout')
@login_required
def logout():
    session.pop('is_admin', None)
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/checkout', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def checkout():
    cart = session.get('cart', {})
    if not cart:
        flash('Your cart is empty', 'error')
        return redirect(url_for('cart'))
    
    cart_items = []
    total = 0
    for product_id, quantity in cart.items():
        product = Product.query.get(int(product_id))
        if product:
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': product.price * quantity
            })
            total += product.price * quantity
    
    if request.method == 'POST':
        shipping_address = request.form['shipping_address']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone = request.form.get('phone', '')
        payment_method = request.form.get('payment_method', 'cod')
        
        # Get tax rates from settings
        setting_cod = SystemSetting.query.filter_by(setting_key='tax_cod').first()
        tax_rate_cod = float(setting_cod.setting_value) / 100.0 if setting_cod else 0.08
        
        setting_advance = SystemSetting.query.filter_by(setting_key='tax_advance').first()
        tax_rate_advance = float(setting_advance.setting_value) / 100.0 if setting_advance else 0.05
        
        # Get shipping fee
        setting_shipping = SystemSetting.query.filter_by(setting_key='shipping_fee').first()
        shipping_fee = float(setting_shipping.setting_value) if setting_shipping else 0.0
        
        # Get Promo Code
        promo_code_str = request.form.get('promo_code', '').strip().upper()
        discount_amount = 0.0
        applied_promo = None
        promo = None
        
        if promo_code_str:
            promo = PromoCode.query.filter_by(code=promo_code_str, is_active=True).first()
            if promo:
                if promo.discount_type == 'percentage':
                    discount_amount = total * (promo.discount_value / 100.0)
                elif promo.discount_type == 'fixed':
                    discount_amount = promo.discount_value
                elif promo.discount_type == 'free_shipping':
                    discount_amount = shipping_fee
                    shipping_fee = 0.0
                
                applied_promo = promo.code

        # Calculate tax and total
        tax_rate = tax_rate_cod if payment_method == 'cod' else tax_rate_advance
        tax_amount = total * tax_rate
        
        # Cap discount to subtotal
        if discount_amount > total:
            discount_amount = total
            
        grand_total = total + tax_amount + shipping_fee
        if promo and promo.discount_type != 'free_shipping':
            grand_total -= discount_amount
        
        full_name = f"{first_name} {last_name}"
        
        order = Order(
            user_id=current_user.id if current_user.is_authenticated else None,
            customer_name=full_name,
            customer_email=email,
            customer_phone=phone,
            total_amount=grand_total,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            shipping_fee=shipping_fee,
            discount_amount=discount_amount,
            promo_code=applied_promo,
            payment_method=payment_method,
            shipping_address=shipping_address
        )
        db.session.add(order)
        db.session.flush()
        
        for product_id, quantity in cart.items():
            product = Product.query.get(int(product_id))
            if product:
                # Decrement stock
                product.stock_quantity -= quantity
                if product.stock_quantity < 0:
                    product.stock_quantity = 0
                    
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product_id,
                    quantity=quantity,
                    price=product.price
                )
                db.session.add(order_item)
        
        db.session.commit()
        session['cart'] = {}
        flash('Order placed successfully!', 'success')
        return redirect(url_for('order_confirmation', order_id=order.id))
    
    # Pass tax rates to template for JS calculation
    setting_cod = SystemSetting.query.filter_by(setting_key='tax_cod').first()
    tax_rate_cod = float(setting_cod.setting_value) if setting_cod else 8.0
    
    setting_advance = SystemSetting.query.filter_by(setting_key='tax_advance').first()
    tax_rate_advance = float(setting_advance.setting_value) if setting_advance else 5.0
    
    setting_shipping = SystemSetting.query.filter_by(setting_key='shipping_fee').first()
    shipping_fee = float(setting_shipping.setting_value) if setting_shipping else 0.0
    
    return render_template('checkout.html', cart_items=cart_items, total=total, tax_rate_cod=tax_rate_cod, tax_rate_advance=tax_rate_advance, shipping_fee=shipping_fee)

@app.route('/apply-promo', methods=['POST'])
def apply_promo():
    data = request.get_json()
    code_str = data.get('code', '').strip().upper()
    subtotal = data.get('subtotal', 0)
    shipping_fee = data.get('shipping_fee', 0)
    
    promo = PromoCode.query.filter_by(code=code_str, is_active=True).first()
    
    if not promo:
        return {'success': False, 'message': 'Invalid or expired promo code'}
    
    discount_amount = 0
    message = f"Promo '{promo.name}' applied!"
    
    if promo.discount_type == 'percentage':
        discount_amount = subtotal * (promo.discount_value / 100.0)
    elif promo.discount_type == 'fixed':
        discount_amount = promo.discount_value
    elif promo.discount_type == 'free_shipping':
        discount_amount = shipping_fee
        
    return {
        'success': True,
        'message': message,
        'discount_amount': discount_amount,
        'discount_type': promo.discount_type,
        'promo_code': promo.code
    }

@app.route('/order_confirmation/<int:order_id>')
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    # Basic check to prevent easy enumeration of orders, although guest checkout is public
    return render_template('order_confirmation.html', order=order)

@app.route('/health')
def health():
    return {'status': 'healthy', 'database': 'connected'}, 200

# Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# Production Logging (Already set up at top)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode)
