from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'glowvera_naturals_secret_key_2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///glowvera.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'images', 'products')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Currency Configuration
CURRENCIES = {
    'USD': {'rate': 1.0, 'symbol': '$', 'name': 'US Dollar'},
    'PKR': {'rate': 278.0, 'symbol': 'Rs', 'name': 'Pakistani Rupee'},
    'EUR': {'rate': 0.94, 'symbol': '€', 'name': 'Euro'},
    'AUD': {'rate': 1.54, 'symbol': 'A$', 'name': 'Australian Dollar'},
    'CAD': {'rate': 1.37, 'symbol': 'C$', 'name': 'Canadian Dollar'}
}

@app.context_processor
def utility_processor():
    def format_price(price):
        if not price:
            price = 0
        currency_code = session.get('currency', 'USD')
        if currency_code not in CURRENCIES:
            currency_code = 'USD'
        
        rate = CURRENCIES[currency_code]['rate']
        symbol = CURRENCIES[currency_code]['symbol']
        converted_price = float(price) * rate
        
        if currency_code == 'PKR':
            return f"{symbol} {int(converted_price):,}"
        return f"{symbol}{converted_price:,.2f}"
    
    return dict(format_price=format_price, currencies=CURRENCIES, current_currency=session.get('currency', 'USD'))

@app.template_filter('nl2br')
def nl2br_filter(s):
    if not s:
        return ""
    return s.replace('\n', '<br>\n')

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/set_currency/<currency_code>')
def set_currency(currency_code):
    if currency_code in CURRENCIES:
        session['currency'] = currency_code
    
    # Redirect back to the previous page or index
    next_page = request.args.get('next') or request.referrer or url_for('index')
    return redirect(next_page)

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
    status = db.Column(db.String(20), default='pending')
    payment_method = db.Column(db.String(30), default='cod')
    shipping_address = db.Column(db.Text, nullable=False)
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
    discount_type = db.Column(db.String(20), nullable=False)  # 'percentage' or 'fixed'
    discount_value = db.Column(db.Float, nullable=False)
    applies_to = db.Column(db.String(20), default='all')  # 'all' or 'specific'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    products = db.relationship('Product', secondary=promo_products, backref='promo_codes')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    featured_products = Product.query.filter_by(is_featured=True).limit(6).all()
    return render_template('index.html', featured_products=featured_products)

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
    return render_template('product_detail.html', product=product)

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
@login_required
def admin_dashboard():
    if not session.get('is_admin'):
        flash('Unauthorized access', 'error')
        return redirect(url_for('index'))
    
    total_products = Product.query.count()
    total_orders = Order.query.count()
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    low_stock_products = Product.query.filter(Product.stock_quantity < 10).all()
    
    return render_template('admin_dashboard.html', 
                         total_products=total_products,
                         total_orders=total_orders,
                         recent_orders=recent_orders,
                         low_stock_products=low_stock_products)

@app.route('/admin/products')
@login_required
def admin_products():
    if not session.get('is_admin'):
        flash('Unauthorized access', 'error')
        return redirect(url_for('index'))
    
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template('admin_products.html', products=products)

@app.route('/admin/product/new', methods=['GET', 'POST'])
@login_required
def admin_add_product():
    if not session.get('is_admin'):
        flash('Unauthorized access', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        image_url = request.form['image_url']
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
@login_required
def admin_edit_product(product_id):
    if not session.get('is_admin'):
        flash('Unauthorized access', 'error')
        return redirect(url_for('index'))
    
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        image_url = request.form['image_url']
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
@login_required
def admin_delete_product(product_id):
    if not session.get('is_admin'):
        flash('Unauthorized access', 'error')
        return redirect(url_for('index'))
    
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/orders')
@login_required
def admin_orders():
    if not session.get('is_admin'):
        flash('Unauthorized access', 'error')
        return redirect(url_for('index'))
    
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin_orders.html', orders=orders)

@app.route('/admin/order/<int:order_id>')
@login_required
def admin_order_detail(order_id):
    if not session.get('is_admin'):
        flash('Unauthorized access', 'error')
        return redirect(url_for('index'))
    
    order = Order.query.get_or_404(order_id)
    return render_template('admin_order_detail.html', order=order)

@app.route('/admin/order/<int:order_id>/update_status', methods=['POST'])
@login_required
def update_order_status(order_id):
    if not session.get('is_admin'):
        flash('Unauthorized access', 'error')
        return redirect(url_for('index'))
    
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
@login_required
def admin_order_invoice(order_id):
    if not session.get('is_admin'):
        flash('Unauthorized access', 'error')
        return redirect(url_for('index'))
    
    order = Order.query.get_or_404(order_id)
    return render_template('invoice.html', order=order)

@app.route('/admin/promo-codes')
@login_required
def admin_promo_codes():
    if not session.get('is_admin'):
        flash('Unauthorized access', 'error')
        return redirect(url_for('index'))
    
    promos = PromoCode.query.order_by(PromoCode.created_at.desc()).all()
    return render_template('admin_promo_codes.html', promos=promos)

@app.route('/admin/promo-codes/new', methods=['GET', 'POST'])
@login_required
def admin_add_promo():
    if not session.get('is_admin'):
        flash('Unauthorized access', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        code = request.form['code'].strip().upper()
        name = request.form['name'].strip()
        discount_type = request.form['discount_type']
        discount_value = float(request.form['discount_value'])
        applies_to = request.form['applies_to']
        
        # If fixed amount, convert from admin's current currency to USD (base) for storage
        if discount_type == 'fixed':
            current_currency = session.get('currency', 'USD')
            rate = CURRENCIES.get(current_currency, {}).get('rate', 1.0)
            discount_value = discount_value / rate
        
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
@login_required
def admin_toggle_promo(promo_id):
    if not session.get('is_admin'):
        flash('Unauthorized access', 'error')
        return redirect(url_for('index'))
    
    promo = PromoCode.query.get_or_404(promo_id)
    promo.is_active = not promo.is_active
    db.session.commit()
    status = "activated" if promo.is_active else "deactivated"
    flash(f'Promo code "{promo.code}" {status}!', 'success')
    return redirect(url_for('admin_promo_codes'))

@app.route('/admin/promo-codes/<int:promo_id>/delete', methods=['POST'])
@login_required
def admin_delete_promo(promo_id):
    if not session.get('is_admin'):
        flash('Unauthorized access', 'error')
        return redirect(url_for('index'))
    
    promo = PromoCode.query.get_or_404(promo_id)
    db.session.delete(promo)
    db.session.commit()
    flash(f'Promo code "{promo.code}" deleted!', 'success')
    return redirect(url_for('admin_promo_codes'))

@app.route('/admin/logout')
@login_required
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
        
        full_name = f"{first_name} {last_name}"
        
        order = Order(
            user_id=current_user.id if current_user.is_authenticated else None,
            customer_name=full_name,
            customer_email=email,
            customer_phone=phone,
            total_amount=total,
            payment_method=payment_method,
            shipping_address=shipping_address
        )
        db.session.add(order)
        db.session.flush()
        
        for product_id, quantity in cart.items():
            product = Product.query.get(int(product_id))
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
    
    return render_template('checkout.html', cart_items=cart_items, total=total)

@app.route('/order_confirmation/<int:order_id>')
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    # Basic check to prevent easy enumeration of orders, although guest checkout is public
    return render_template('order_confirmation.html', order=order)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
