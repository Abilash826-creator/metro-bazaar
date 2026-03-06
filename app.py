import os
from datetime import datetime, date
from functools import wraps
from flask import (Flask, render_template, request, redirect,
                   url_for, session, jsonify, flash)
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from psycopg2.extras import RealDictCursor

# ─── App ──────────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'nmbb_secret_2024')

# ─── DB connection ────────────────────────────────────────────────────────────
def get_db():
    url = os.environ.get('DATABASE_URL', '')
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    return psycopg2.connect(url, cursor_factory=RealDictCursor)

# ─── Init / seed ──────────────────────────────────────────────────────────────
def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'admin',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

    c.execute("""CREATE TABLE IF NOT EXISTS categories (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

    c.execute("""CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        category_id INTEGER REFERENCES categories(id),
        price NUMERIC(10,2) NOT NULL,
        stock INTEGER DEFAULT 0,
        barcode TEXT,
        description TEXT,
        low_stock_threshold INTEGER DEFAULT 10,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

    c.execute("""CREATE TABLE IF NOT EXISTS bills (
        id SERIAL PRIMARY KEY,
        bill_number TEXT UNIQUE NOT NULL,
        customer_name TEXT,
        customer_phone TEXT,
        subtotal NUMERIC(10,2) NOT NULL,
        discount NUMERIC(10,2) DEFAULT 0,
        tax NUMERIC(10,2) DEFAULT 0,
        total NUMERIC(10,2) NOT NULL,
        payment_method TEXT DEFAULT 'cash',
        cashier_id INTEGER REFERENCES users(id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

    c.execute("""CREATE TABLE IF NOT EXISTS bill_items (
        id SERIAL PRIMARY KEY,
        bill_id INTEGER NOT NULL REFERENCES bills(id) ON DELETE CASCADE,
        product_id INTEGER NOT NULL REFERENCES products(id),
        product_name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price NUMERIC(10,2) NOT NULL,
        total_price NUMERIC(10,2) NOT NULL)""")

    conn.commit()

    # seed admin
    c.execute("SELECT id FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username,password,role) VALUES (%s,%s,%s)",
                  ('admin', generate_password_hash('admin123'), 'admin'))

    # seed categories
    for name, desc in [
        ("Men's Dresses",    "Shirts, pants, jeans, t-shirts"),
        ("Women's Dresses",  "Sarees, kurtis, leggings, tops"),
        ("Plastic Household","Buckets, containers, baskets"),
        ("Women's Fancy",    "Hair clips, bangles, cosmetics"),
        ("School Items",     "Notebooks, pens, bags, geometry boxes"),
    ]:
        c.execute("INSERT INTO categories(name,description) VALUES(%s,%s) ON CONFLICT(name) DO NOTHING", (name, desc))
    conn.commit()

    # seed products
    c.execute("SELECT COUNT(*) as cnt FROM products")
    if c.fetchone()['cnt'] == 0:
        def cid(n):
            c.execute("SELECT id FROM categories WHERE name=%s", (n,))
            return c.fetchone()['id']
        men=cid("Men's Dresses"); women=cid("Women's Dresses")
        plastic=cid("Plastic Household"); fancy=cid("Women's Fancy"); school=cid("School Items")
        for row in [
            ("Cotton Casual Shirt",men,349,80,10),("Slim Fit Jeans",men,799,60,10),
            ("Formal Trousers",men,599,45,10),("Round Neck T-Shirt",men,199,120,15),
            ("Polo T-Shirt",men,299,90,10),("Silk Saree",women,1299,30,5),
            ("Cotton Kurti",women,449,75,10),("Churidar Leggings",women,199,100,15),
            ("Casual Top",women,349,85,10),("Designer Salwar Set",women,899,40,8),
            ("Large Bucket 20L",plastic,149,50,10),("Storage Container Set",plastic,249,40,8),
            ("Laundry Basket",plastic,199,35,8),("Airtight Container",plastic,99,60,10),
            ("Plastic Tub",plastic,179,45,8),("Hair Clip Set",fancy,49,150,20),
            ("Glass Bangles Set",fancy,99,100,20),("Lipstick",fancy,149,80,15),
            ("Foundation Cream",fancy,249,60,10),("Eyeliner",fancy,79,90,15),
            ("A4 Notebook 200pg",school,59,200,30),("Ball Pen Pack(10)",school,49,180,30),
            ("School Bag Large",school,599,40,8),("Geometry Box",school,89,120,20),
            ("Colour Pencils Set",school,79,110,20),
        ]:
            c.execute("INSERT INTO products(name,category_id,price,stock,low_stock_threshold) VALUES(%s,%s,%s,%s,%s)", row)
        conn.commit()
    conn.close()

# ─── Helpers ──────────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def bill_number():
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT COUNT(*) as cnt FROM bills WHERE DATE(created_at)=CURRENT_DATE")
    n = c.fetchone()['cnt'] + 1; conn.close()
    return f"NMB{datetime.now().strftime('%Y%m%d')}{n:04d}"

# ─── Auth ─────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return redirect(url_for('dashboard') if 'user_id' in session else url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username','').strip()
        p = request.form.get('password','')
        try:
            conn = get_db(); c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=%s", (u,))
            user = c.fetchone(); conn.close()
            if user and check_password_hash(user['password'], p):
                session.update({'user_id':user['id'],'username':user['username'],'role':user['role']})
                flash('Welcome back, ' + user['username'] + '!', 'success')
                return redirect(url_for('dashboard'))
            flash('Invalid username or password.', 'danger')
        except Exception as e:
            flash(f'DB Error: {e}', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─── Dashboard ────────────────────────────────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT COUNT(*) as cnt FROM products"); total_products = c.fetchone()['cnt']
    c.execute("SELECT COUNT(*) as cnt FROM categories"); total_categories = c.fetchone()['cnt']
    c.execute("SELECT COALESCE(SUM(total),0) as total, COUNT(*) as cnt FROM bills WHERE DATE(created_at)=CURRENT_DATE")
    today_sales = c.fetchone()
    c.execute("SELECT p.*, c.name as cat_name FROM products p JOIN categories c ON p.category_id=c.id WHERE p.stock<=p.low_stock_threshold ORDER BY p.stock LIMIT 8")
    low_stock = c.fetchall()
    c.execute("SELECT b.*, u.username as cashier FROM bills b LEFT JOIN users u ON b.cashier_id=u.id ORDER BY b.created_at DESC LIMIT 5")
    recent_bills = c.fetchall()
    c.execute("SELECT DATE(created_at) as day, SUM(total) as total FROM bills WHERE created_at>=CURRENT_DATE-INTERVAL '7 days' GROUP BY day ORDER BY day")
    monthly_sales = c.fetchall()
    c.execute("SELECT p.name, SUM(bi.quantity) as qty_sold, SUM(bi.total_price) as revenue FROM bill_items bi JOIN products p ON bi.product_id=p.id GROUP BY p.id,p.name ORDER BY qty_sold DESC LIMIT 5")
    top_products = c.fetchall()
    conn.close()
    return render_template('dashboard.html', total_products=total_products,
        total_categories=total_categories, today_sales=today_sales,
        low_stock=low_stock, recent_bills=recent_bills,
        monthly_sales=monthly_sales, top_products=top_products)

# ─── Products ─────────────────────────────────────────────────────────────────
@app.route('/products')
@login_required
def products():
    search = request.args.get('search',''); cat_id = request.args.get('category','')
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT * FROM categories ORDER BY name"); cats = c.fetchall()
    q = "SELECT p.*, c.name as cat_name FROM products p JOIN categories c ON p.category_id=c.id WHERE 1=1"
    params = []
    if search: q += " AND (p.name ILIKE %s OR p.barcode ILIKE %s)"; params += [f'%{search}%',f'%{search}%']
    if cat_id: q += " AND p.category_id=%s"; params.append(cat_id)
    q += " ORDER BY c.name, p.name"
    c.execute(q, params); prods = c.fetchall(); conn.close()
    return render_template('products.html', products=prods, categories=cats, search=search, selected_cat=cat_id)

@app.route('/products/add', methods=['GET','POST'])
@login_required
def add_product():
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT * FROM categories ORDER BY name"); cats = c.fetchall()
    if request.method == 'POST':
        c.execute("INSERT INTO products(name,category_id,price,stock,barcode,description,low_stock_threshold) VALUES(%s,%s,%s,%s,%s,%s,%s)",
            (request.form['name'].strip(), request.form['category_id'], float(request.form['price']),
             int(request.form['stock']), request.form.get('barcode',''), request.form.get('description',''),
             int(request.form.get('low_stock_threshold',10))))
        conn.commit(); conn.close(); flash('Product added!','success')
        return redirect(url_for('products'))
    conn.close()
    return render_template('product_form.html', categories=cats, product=None)

@app.route('/products/edit/<int:pid>', methods=['GET','POST'])
@login_required
def edit_product(pid):
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT * FROM categories ORDER BY name"); cats = c.fetchall()
    c.execute("SELECT * FROM products WHERE id=%s", (pid,)); product = c.fetchone()
    if not product: conn.close(); flash('Not found','danger'); return redirect(url_for('products'))
    if request.method == 'POST':
        c.execute("UPDATE products SET name=%s,category_id=%s,price=%s,stock=%s,barcode=%s,description=%s,low_stock_threshold=%s WHERE id=%s",
            (request.form['name'].strip(), request.form['category_id'], float(request.form['price']),
             int(request.form['stock']), request.form.get('barcode',''), request.form.get('description',''),
             int(request.form.get('low_stock_threshold',10)), pid))
        conn.commit(); conn.close(); flash('Product updated!','success')
        return redirect(url_for('products'))
    conn.close()
    return render_template('product_form.html', categories=cats, product=product)

@app.route('/products/delete/<int:pid>', methods=['POST'])
@login_required
def delete_product(pid):
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT name FROM products WHERE id=%s",(pid,)); p = c.fetchone()
    if p: c.execute("DELETE FROM products WHERE id=%s",(pid,)); conn.commit(); flash(f'Deleted "{p["name"]}"','warning')
    conn.close(); return redirect(url_for('products'))

@app.route('/api/products')
@login_required
def api_products():
    search = request.args.get('q',''); cat = request.args.get('cat','')
    conn = get_db(); c = conn.cursor()
    q = "SELECT p.*, c.name as cat_name FROM products p JOIN categories c ON p.category_id=c.id WHERE p.stock>0"
    params = []
    if search: q += " AND (p.name ILIKE %s OR p.barcode ILIKE %s)"; params += [f'%{search}%',f'%{search}%']
    if cat: q += " AND p.category_id=%s"; params.append(cat)
    q += " ORDER BY c.name, p.name"
    c.execute(q, params); rows = c.fetchall(); conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/categories')
@login_required
def api_categories():
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT * FROM categories ORDER BY name"); rows = c.fetchall(); conn.close()
    return jsonify([dict(r) for r in rows])

# ─── Billing ──────────────────────────────────────────────────────────────────
@app.route('/billing')
@login_required
def billing():
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT * FROM categories ORDER BY name"); cats = c.fetchall(); conn.close()
    return render_template('billing.html', categories=cats)

@app.route('/billing/save', methods=['POST'])
@login_required
def save_bill():
    data = request.get_json()
    if not data or not data.get('items'):
        return jsonify({'success':False,'message':'No items'}), 400
    items = data['items']
    subtotal = sum(i['qty']*i['price'] for i in items)
    discount = float(data.get('discount',0))
    total = round(subtotal - discount, 2)
    bn = bill_number()
    conn = get_db(); c = conn.cursor()
    try:
        c.execute("INSERT INTO bills(bill_number,customer_name,customer_phone,subtotal,discount,tax,total,payment_method,cashier_id) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (bn, data.get('customer_name','').strip(), data.get('customer_phone','').strip(),
             subtotal, discount, 0, total, data.get('payment_method','cash'), session['user_id']))
        bill_id = c.fetchone()['id']
        for i in items:
            c.execute("INSERT INTO bill_items(bill_id,product_id,product_name,quantity,unit_price,total_price) VALUES(%s,%s,%s,%s,%s,%s)",
                (bill_id, i['id'], i['name'], i['qty'], i['price'], i['qty']*i['price']))
            c.execute("UPDATE products SET stock=stock-%s WHERE id=%s",(i['qty'],i['id']))
        conn.commit(); conn.close()
        return jsonify({'success':True,'bill_id':bill_id,'bill_number':bn,'total':total})
    except Exception as e:
        conn.rollback(); conn.close()
        return jsonify({'success':False,'message':str(e)}), 500

# ─── Receipt ──────────────────────────────────────────────────────────────────
@app.route('/receipt/<int:bill_id>')
@login_required
def receipt(bill_id):
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT b.*,u.username as cashier FROM bills b LEFT JOIN users u ON b.cashier_id=u.id WHERE b.id=%s",(bill_id,))
    bill = c.fetchone()
    if not bill: conn.close(); flash('Bill not found','danger'); return redirect(url_for('sales_history'))
    c.execute("SELECT * FROM bill_items WHERE bill_id=%s",(bill_id,)); items = c.fetchall(); conn.close()
    return render_template('receipt.html', bill=bill, items=items)

# ─── Sales History ────────────────────────────────────────────────────────────
@app.route('/sales')
@login_required
def sales_history():
    df = request.args.get('from',''); dt = request.args.get('to',''); search = request.args.get('search','')
    conn = get_db(); c = conn.cursor()
    q = "SELECT b.*,u.username as cashier FROM bills b LEFT JOIN users u ON b.cashier_id=u.id WHERE 1=1"
    params = []
    if df: q += " AND DATE(b.created_at)>=%s"; params.append(df)
    if dt: q += " AND DATE(b.created_at)<=%s"; params.append(dt)
    if search: q += " AND (b.bill_number ILIKE %s OR b.customer_name ILIKE %s)"; params += [f'%{search}%',f'%{search}%']
    q += " ORDER BY b.created_at DESC"
    c.execute(q, params); bills = c.fetchall()
    total_amount = sum(float(b['total']) for b in bills); conn.close()
    return render_template('sales.html', bills=bills, total_amount=total_amount,
                           date_from=df, date_to=dt, search=search)

@app.route('/bills/delete/<int:bill_id>', methods=['POST'])
@login_required
def delete_bill(bill_id):
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT bill_number FROM bills WHERE id=%s",(bill_id,)); bill = c.fetchone()
    if not bill: conn.close(); flash('Bill not found','danger'); return redirect(url_for('sales_history'))
    c.execute("SELECT product_id,quantity FROM bill_items WHERE bill_id=%s",(bill_id,))
    for item in c.fetchall():
        c.execute("UPDATE products SET stock=stock+%s WHERE id=%s",(item['quantity'],item['product_id']))
    c.execute("DELETE FROM bills WHERE id=%s",(bill_id,))
    conn.commit(); conn.close()
    flash(f'Bill {bill["bill_number"]} deleted and stock restored.','warning')
    return redirect(url_for('sales_history'))

# ─── Categories ───────────────────────────────────────────────────────────────
@app.route('/categories')
@login_required
def categories():
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT c.*,COUNT(p.id) as product_count FROM categories c LEFT JOIN products p ON p.category_id=c.id GROUP BY c.id ORDER BY c.name")
    cats = c.fetchall(); conn.close()
    return render_template('categories.html', categories=cats)

@app.route('/categories/add', methods=['POST'])
@login_required
def add_category():
    name = request.form.get('name','').strip(); desc = request.form.get('description','').strip()
    if name:
        conn = get_db(); c = conn.cursor()
        try:
            c.execute("INSERT INTO categories(name,description) VALUES(%s,%s)",(name,desc)); conn.commit()
            flash(f'Category "{name}" added!','success')
        except: conn.rollback(); flash('Category already exists.','danger')
        conn.close()
    return redirect(url_for('categories'))

@app.route('/categories/delete/<int:cid>', methods=['POST'])
@login_required
def delete_category(cid):
    conn = get_db(); c = conn.cursor()
    c.execute("DELETE FROM categories WHERE id=%s",(cid,)); conn.commit(); conn.close()
    flash('Category deleted.','warning'); return redirect(url_for('categories'))

# ─── Inventory ────────────────────────────────────────────────────────────────
@app.route('/inventory')
@login_required
def inventory():
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT p.*,c.name as cat_name FROM products p JOIN categories c ON p.category_id=c.id ORDER BY p.stock ASC")
    prods = c.fetchall(); conn.close()
    return render_template('inventory.html', products=prods)

@app.route('/inventory/restock/<int:pid>', methods=['POST'])
@login_required
def restock(pid):
    qty = int(request.form.get('qty',0))
    if qty > 0:
        conn = get_db(); c = conn.cursor()
        c.execute("UPDATE products SET stock=stock+%s WHERE id=%s",(qty,pid)); conn.commit(); conn.close()
        flash(f'Stock updated +{qty}','success')
    return redirect(url_for('inventory'))

# ─── Setup / Health routes ────────────────────────────────────────────────────
@app.route('/setup')
def setup():
    """Visit this URL once after deploying to create/reset the admin user."""
    try:
        init_db()
        conn = get_db(); c = conn.cursor()
        pwd = generate_password_hash('admin123')
        c.execute("SELECT id FROM users WHERE username='admin'")
        if c.fetchone():
            c.execute("UPDATE users SET password=%s WHERE username='admin'",(pwd,))
            msg = "✅ Admin password RESET to: admin123"
        else:
            c.execute("INSERT INTO users(username,password,role) VALUES('admin',%s,'admin')",(pwd,))
            msg = "✅ Admin user CREATED"
        conn.commit(); conn.close()
        return f"""<html><body style="font-family:sans-serif;padding:40px;max-width:480px;margin:auto">
        <h2>🏪 New Metro Big Bazaar — Setup</h2>
        <p style="color:green;font-size:1.1rem">{msg}</p>
        <p>Username: <strong>admin</strong></p>
        <p>Password: <strong>admin123</strong></p><br>
        <a href="/login" style="background:#1a237e;color:#fff;padding:12px 28px;
        border-radius:8px;text-decoration:none;font-size:1rem">Go to Login →</a>
        </body></html>"""
    except Exception as e:
        return f"""<html><body style="font-family:sans-serif;padding:40px">
        <h2>❌ Setup Error</h2><pre style="color:red">{e}</pre>
        <p>Make sure DATABASE_URL is set in Render environment variables.</p>
        </body></html>""", 500

@app.route('/health')
def health():
    """Render health check endpoint."""
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT COUNT(*) as cnt FROM users"); u = c.fetchone()['cnt']
        conn.close()
        return jsonify({'status':'ok','users':u})
    except Exception as e:
        return jsonify({'status':'error','message':str(e)}), 500

# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
