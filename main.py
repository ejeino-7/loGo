# -*- coding: utf-8 -*-

from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from werkzeug.utils import secure_filename
from passlib.hash import sha256_crypt
from functools import wraps
import os
import datetime
from datetime import datetime

app = Flask(__name__)
 
# Init stuff
UPLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/static/images/'
mysql = MySQL(app)
ALLOWED_EXTENSIONS = set(['png'])

# Config MySQL and othes
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'jesper'
app.config['MYSQL_PASSWORD'] = 'admin'
app.config['MYSQL_DB'] = 'D0018E'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
 
     # Get 5 phones from products
    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM products ORDER BY UNIX_TIMESTAMP(date_added) DESC LIMIT 5;")

    data = cur.fetchall()

    cur.close()

    first = data[0]
    phones = data[1:]

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

            if sha256_crypt.verify(password_cand, password):
                # Passed
                session['logged_in'] = True
                session['email'] = email
                cur.execute("SELECT userID FROM users WHERE email = %s", [session['email']])
                res = cur.fetchone()
                userID = res['userID']
                session['userID'] = userID

                flash('You are now logged in', 'success')
                return redirect(url_for('products'))
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


@app.route('/addProduct', methods=['GET', 'POST'])
def addProduct():
    if request.method == 'POST':
        title = request.form['title']
        desc = request.form['desc']
        price = request.form['price']
        image = request.files['image'] 

        # Create cursor
        cur = mysql.connection.cursor()
        
        # Execute query
        now = datetime.now()
        cur.execute("INSERT INTO products(ownerID, title, `desc`, price, date_added) VALUES(%s, %s, %s, %s, %s ) ", (session['userID'], title, desc, int(price), now ))
        # Commit to DB
        mysql.connection.commit()

        # Upload image to server
        cur.execute("SELECT MAX(productID) FROM products WHERE ownerID = %s", [session['userID']])
        res = cur.fetchone()
        productID = res['MAX(productID)']

        filename = str(session['userID']) + "_" + str(productID) + ".png"
        url = "/static/images/" + filename

        cur.execute("UPDATE products SET image=%s WHERE productID=%s;", (url, productID))
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        mysql.connection.commit()
        # Close connection
        cur.close()


        return redirect(url_for('myProducts'))
    return render_template('addProduct.html')


@app.route('/products')
def products():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM products;")
    
    products = cur.fetchall()
    
    cur.close()
    
    return render_template('/products.html', products = products)

@app.route('/shoppingcart')
def shoppingcart():

    cartitems = []

    cur = mysql.connection.cursor()
    userID = session['userID']
    cur.execute("SELECT * FROM shoppingCart WHERE userID = %s", [userID])
    cartitems = cur.fetchall()
    cur.close()

    return render_template('/shoppingcart.html', shoppingcart = cartitems, lenght= len(cartitems))

@app.route('/addToCart/<string:id>', methods=['GET', 'POST'])
def addToCart(id):
    if(session['logged_in']):

        cur = mysql.connection.cursor()
        userID = session['userID']
        cur.execute("INSERT INTO shoppingCart(userID, productID) VALUES (%s, %s)", (userID, int(id)))

        mysql.connection.commit()
        cur.close()

        return('',204)
       
       
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
        bought.append(["Nokia 3310", "blop blop", "11kr"])
        j+=1
    return render_template('transactions.html', soldPhones = sold, boughtPhones = bought, numSold = len(sold), numBought = len(bought))

@app.route('/myProducts')
def myProducts():
    phones = [] ## if emptyyyy..
    if (session['logged_in'] == True):
        cur = mysql.connection.cursor()
        userID = session['userID']

        cur.execute("SELECT * FROM products WHERE ownerID = %s", [userID])
        phones = cur.fetchall()
        cur.close()


    return render_template('/myProducts.html', products = phones)

@app.route('/editProduct')
def editProduct():
    return render_template('/editProduct.html')
           
@app.route('/review', methods=['GET', 'POST'])
def review():
    return render_template('/review.html')
 
@app.route('/product/<string:id>/')
def product(id):


    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM products WHERE productID =%s LIMIT 1;", [int(id)])

    product = cur.fetchone()

    cur.close()

    reviews = []
    i=0
    while (i<8):
        reviews.append(["best guy ever", "1"])
        i += 1
    return render_template('/product.html', phone = product, rates = reviews)

   
@app.route('/delete/<string:id>', methods=['GET', 'POST'])
def delete(id):

    if (session['logged_in'] == True):
        cur = mysql.connection.cursor()
        userID = session['userID']
        cur.execute("DELETE FROM products WHERE productID = %s AND ownerID = %s", (int(id), userID))

        mysql.connection.commit()
        cur.close()

        return redirect(url_for('myProducts'))

    return('', 204)
  
  
   
if __name__ == '__main__':
    app.secret_key = 'THISISTHEKEY'
    app.run(debug=True)
