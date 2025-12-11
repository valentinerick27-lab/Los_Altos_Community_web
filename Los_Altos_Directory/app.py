print("Starting Los Altos de Ciudad Jardin website...")
print("Loading Flask...")

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlalchemy import or_
import os

print("Flask loaded successfully!")
print("Setting up application...")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "dev-key")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///community.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

print("Database configured!")

# ----------------------------
# Database Models
# ----------------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    house_number = db.Column(db.String(20), nullable=False)
    phone_number = db.Column(db.String(20))

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)

# ----------------------------
# Login Required Decorator
# ----------------------------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# ----------------------------
# Routes
# ----------------------------

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('homepage'))
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        house_number = request.form.get('house_number')
        phone_number = request.form.get('phone_number')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return render_template('signup.html', error='Email already registered')

        hashed_password = generate_password_hash(password)
        new_user = User(
            name=name,
            email=email,
            password=hashed_password,
            house_number=house_number,
            phone_number=phone_number
        )

        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.id
        session['user_name'] = new_user.name

        return redirect(url_for('homepage'))

    return render_template('signup.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            return redirect(url_for('homepage'))
        else:
            return render_template('signin.html', error='Invalid email or password')

    return render_template('signin.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/homepage')
@login_required
def homepage():
    return render_template('homepage.html', user_name=session.get('user_name'))

# ----------------------------
# Residents
# ----------------------------

@app.route('/residents')
@login_required
def residents():
    return render_template('residents.html')

@app.route('/api/search_residents')
@login_required
def search_residents():
    query = request.args.get('q', '').lower()

    if not query:
        users = User.query.limit(10).all()
    else:
        users = User.query.filter(
            or_(
                User.name.ilike(f'%{query}%'),
                User.email.ilike(f'%{query}%'),
                User.house_number.ilike(f'%{query}%')
            )
        ).limit(10).all()

    results = [{
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'house_number': user.house_number,
        'phone_number': user.phone_number
    } for user in users]

    return jsonify(results)

@app.route('/residents/<int:resident_id>')
@login_required
def resident_detail(resident_id):
    resident = User.query.get_or_404(resident_id)
    return render_template('resident_detail.html', resident=resident)

# ----------------------------
# Services
# ----------------------------

@app.route('/services')
@login_required
def services():
    return render_template('services.html')

@app.route('/api/search_services')
@login_required
def search_services():
    query = request.args.get('q', '').lower()

    if not query:
        services = Service.query.limit(10).all()
    else:
        services = Service.query.filter(
            or_(
                Service.name.ilike(f'%{query}%'),
                Service.email.ilike(f'%{query}%'),
                Service.phone_number.ilike(f'%{query}%'),
                Service.address.ilike(f'%{query}%')
            )
        ).limit(10).all()

    results = [{
        'id': service.id,
        'name': service.name,
        'email': service.email,
        'phone_number': service.phone_number,
        'address': service.address
    } for service in services]

    return jsonify(results)

@app.route('/services/<int:service_id>')
@login_required
def service_detail(service_id):
    service = Service.query.get_or_404(service_id)
    return render_template('service_detail.html', service=service)

@app.route('/services/add', methods=['GET', 'POST'])
@login_required
def add_service():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')
        address = request.form.get('address')

        new_service = Service(
            name=name,
            email=email,
            phone_number=phone_number,
            address=address
        )

        db.session.add(new_service)
        db.session.commit()

        return redirect(url_for('services'))

    return render_template('add_service.html')

# ----------------------------
# Run App
# ----------------------------

if __name__ == '__main__':
    print("\nCreating database tables...")
    with app.app_context():
        db.create_all()
    print("Database ready!")
    print("\n" + "="*50)
    print(" Starting Los Altos de Ciudad Jardin Website!")
    print("="*50)
    print("\n Open your browser and go to:")
    print("   http://127.0.0.1:5000")
    print("\n Press CTRL+C to stop the server\n")
    print("="*50 + "\n")

    app.run(debug=True)