from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from dateutil.relativedelta import relativedelta
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta



curr_date = datetime.today().strftime('%Y-%m-%d')

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
    
def get_intraday_stock_data(symbol, duration, interval, has_time, monthly=False):
    # Calculate the start and end dates for the data
    if not monthly:
        targ_date = (datetime.today() - timedelta(days=duration)).strftime('%Y-%m-%d')
        print("mounthly")
    else:
        targ_date = (datetime.today() - relativedelta(months=duration)).strftime('%Y-%m-%d')
    print("Tasrget Date: ",targ_date)
    # Fetch intraday data using yfinance
    data = yf.download(symbol, start=targ_date, end=curr_date, interval=interval)
    data = data.reset_index()
    if(has_time):
        data.rename(columns = {'Datetime':'Date'}, inplace=True)
    return data



@app.route('/fetchStockData', methods=['POST'])
def fetchStockData():
    symbol = request.form.get('selectedStock')+".NS"
    basis = request.form.get('basis')
    duration = int(request.form.get('duration'))
    print("Duration:", duration)
    print("Basis: ", basis)
    print(f"Symbol received: {symbol}")

    # Fetch intraday data using yfinance
    if basis == "1m":
        df = get_intraday_stock_data(symbol, duration, "1m", True)
    elif basis == "5m":
        df = get_intraday_stock_data(symbol, duration, "5m", True)
    elif basis == "weekly":
        df = get_intraday_stock_data(symbol, (duration*7), "1d" , False)
    elif basis == "monthly":
        df = get_intraday_stock_data(symbol, duration, "1d", False, True)
    elif basis == "yearly":
        df = get_intraday_stock_data(symbol, 12*duration, "1d", False, True)
        
    # Check the actual column names of the DataFrame
    print("Actual Column Names:", df.columns)

    # Reset index to turn the timestamp index into a regular column

    print("Actual Column Names:", df.columns)
    if 'Date' in df.columns:
        # Convert timestamp to string for JSON serialization
        df['FormattedDatetime'] = df['Date'].dt.strftime('%Y-%m-%d %H:%M:%S')
    else:
        # If 'Date' is not present, use the existing timestamp column
        df['FormattedDatetime'] = df[df.columns[0]].dt.strftime('%Y-%m-%d %H:%M:%S')

    # Extract required columns and handle any data type conversion or cleanup
    required_df = df[['Date', 'FormattedDatetime', 'Open', 'Close', 'High', 'Low']]
    # Convert timestamp to string for JSON serialization if the 'Date' column exists
    # Convert timestamp to string for JSON serialization if the 'Date' column exists
    # Convert timestamp to string for JSON serialization if the 'Date' column exists
    if 'Date' in required_df.columns:
        datetime_column = required_df['Date']
        # Check if the values are integers (Unix timestamps)
        if pd.api.types.is_integer_dtype(datetime_column):
            required_df['Date'] = pd.to_datetime(datetime_column, unit='ms')
        # If the values are already strings, assume they are in the desired format
        elif pd.api.types.is_string_dtype(datetime_column):
            required_df['Date'] = pd.to_datetime(datetime_column)

        # Format 'Date' column to a human-readable format
        required_df['FormattedDatetime'] = required_df['Date'].dt.strftime('%Y-%m-%d %H:%M:%S')

    # Drop unnecessary columns for JSON conversion
    required_df_for_json = required_df[['Date', 'FormattedDatetime', 'Open', 'Close', 'High', 'Low']]
    print(required_df)
    # Convert DataFrame to JSON
    json_data = required_df_for_json.to_json(orient='split', index=False, date_format='iso')
    data = jsonify(json_data)
    print("Data sent")

    return data




if __name__ == '__main__':
    app.run(debug=True,port=5001)
