from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'glowvera_naturals_secret_key_2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///glowvera.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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
        new_product = Product(
            name=request.form['name'],
            description=request.form['description'],
            price=float(request.form['price']),
            image_url=request.form['image_url'],
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
        product.name = request.form['name']
        product.description = request.form['description']
        product.price = float(request.form['price'])
        product.image_url = request.form['image_url']
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
        
        full_name = f"{first_name} {last_name}"
        
        order = Order(
            user_id=current_user.id if current_user.is_authenticated else None,
            customer_name=full_name,
            customer_email=email,
            customer_phone=phone,
            total_amount=total,
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
