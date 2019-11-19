# -*- coding: utf-8 -*-

from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'jesper'
app.config['MYSQL_PASSWORD'] = 'admin'
app.config['MYSQL_DB'] = 'D0018E'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)

@app.route('/')
def index():
    first = ["head", "desc", "https://i.ebayimg.com/images/g/ln4AAOSwkvFaXmcn/s-l400.jpg"]
    i = 0
    phones = []
    while(i < 4):
        phones.append(["head", "desc", "https://i.ebayimg.com/images/g/ln4AAOSwkvFaXmcn/s-l400.jpg"])
        i += 1
        
    return render_template('/home.html', first = first, phones = phones)

# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        phone = request.form['phone']
        password = sha256_crypt.encrypt(str(request.form['password']))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO users(email, phoneNumber, password) VALUES(%s, %s, %s)", (email, phone, password))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html')

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Getting Form Fields
        email = request.form['email']
        password_cand = request.form['password']
        
        cur = mysql.connection.cursor()
        
        result = cur.execute("SELECT * FROM users WHERE email = %s", [email])
        
        if result > 0:
            
            data = cur.fetchone()
            password = data['password']
            
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user is logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))


@app.route('/addProduct')
def addProduct():
    return render_template('addProduct.html')


@app.route('/product')
def product():
    i = 0
    phones = []
    # creates dummy phones
    while(i < 18):
        phones.append(["nokia 33 fucking 10", "descprigasd thone is fucking nice juuu", "https://i.ebayimg.com/images/g/ln4AAOSwkvFaXmcn/s-l400.jpg"])
        i += 1

    return render_template('/product.html', products = phones)

@app.route('/shoppingcart')
def shoppingcart():
    i = 0
    cartitems = []
    # creates dummy phones
    while(i < 8):
        cartitems.append(["nokia 33 10", "199 kr"])
        i += 1

    return render_template('/shoppingcart.html', shoppingcart = cartitems, lenght= len(cartitems))

@app.route('/transactions')
def transactions():
    i = 0
    j = 0
    sold = []
    bought = []
    #while (i<5):
    #    sold.append(["Nokia 3310", "blöp blöp", "11kr"])
    #    i+=1
    while (j<5):
        bought.append(["Nokia 3310", "blöp blöp", "11kr"])
        j+=1
    return render_template('transactions.html', soldPhones = sold, boughtPhones = bought, numSold = len(sold), numBought = len(bought))

if __name__ == '__main__':
    app.secret_key = 'THISISTHEKEY'
    app.run(debug=True)
