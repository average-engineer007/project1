from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from dateutil.relativedelta import relativedelta
from nselib import capital_market


curr_date = date.today().strftime("%d-%m-%Y")

app = Flask(__name__)
app.secret_key = 'just_fafo'  # Replace with your actual secret key

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

# Initialize Database within Application Context
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        new_user = User(username=username, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please login.')
        return redirect(url_for('index'))

    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        session['username'] = user.username
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid username or password')
        return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        return render_template('welcome.html', username=session['username'])
    else:
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/check_username', methods=['POST'])
def used_user_name():
    username = request.form.get('username')
    user = User.query.filter_by(username = username).first()
    if user:
        return jsonify({'status': 'Username already taken !!'})
    else:
        return jsonify({'status': 'Username available !!'})

@app.route('/fetchStockData', methods = ['POST'])
def fetchStockData():
    symbol = request.form.get('selectedStock')
    targ_date = date.today() + relativedelta(years=-1)
    targ_date = targ_date.strftime("%d-%m-%Y")
    print(f"Symbol received: {symbol}")
    df = capital_market.price_volume_and_deliverable_position_data(symbol=symbol, from_date=targ_date, to_date=curr_date)
    print("Data obtained")
    required_df = df[['Date',
                    'OpenPrice',
                    'ClosePrice',
                    'HighPrice',
                    'LowPrice']]
    numeric_columns = ['OpenPrice', 'ClosePrice', 'HighPrice', 'LowPrice']
    required_df[numeric_columns] = required_df[numeric_columns].replace({',': ''}, regex=True)
    required_df.to_csv('required.csv')
    required_df_in_json = df[['Date',
                            'OpenPrice',
                            'ClosePrice',
                            'HighPrice',
                            'LowPrice']].to_json(orient='split', index=False)
    data = jsonify(required_df_in_json)
    print("Data sent")

    return data

if __name__ == '__main__':
    app.run(debug=True,port=5001)
