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

    cur.execute("SELECT * FROM products WHERE buyerID IS NULL ORDER BY UNIX_TIMESTAMP(date_added) DESC LIMIT 5;")

    data = cur.fetchall()

    cur.close()

    if(len(data) > 0):
        first = data[0]
    else:
        first = 0
    if(len(data) > 1):
        phones = data[1:]
    else:
        phones = 0

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
 
        # Check if email or phonenumber already in use query
        cur.execute("SELECT * FROM users WHERE phoneNumber=%s OR email=%s", (phone, email))       
        row = cur.fetchone()
        if row:
            error = "Email or phone number already in use"
            return render_template('register.html', error = error)
        # Execute query
        else:
            cur.execute("INSERT INTO users(email, phoneNumber, password) VALUES(%s, %s, %s)", (email, phone, password))
            # Commit to DB
            mysql.connection.commit()

        # Close connection
        cur.close()
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
                active = data['active']
                if active:
                    session['logged_in'] = True
                    session['email'] = email
                    cur.execute("SELECT userID FROM users WHERE email = %s", [session['email']])
                    res = cur.fetchone()
                    userID = res['userID']
                    session['userID'] = userID
                else:
                    error = "This account has been suspended. For more info contact support."
                    return render_template('login.html', error = error)
                    
                if(userID == 0):
                    return admin("users")
                
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


@app.route('/products', methods=['GET', 'POST'])
def products():        
    if(request.method == 'POST'):
        search = request.form['search']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM products WHERE LOCATE(%s, title) > 0 AND buyerID IS NULL OR LOCATE(%s, `desc`) AND buyerID IS NULL", [str(search), str(search)])
        container_products = cur.fetchall()
        cur.close()
        return render_template('/products.html', products = container_products)
    else:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM products WHERE buyerID IS NULL;")
        products = cur.fetchall()
        cur.close()
    return render_template('/products.html', products = products)
    
   
@app.route('/shoppingcart')
def shoppingcart():

    cartitems = []

    cur = mysql.connection.cursor()
    userID = session['userID']

    cur.execute("SELECT * FROM products WHERE productID IN (SELECT shoppingCart.productID FROM shoppingCart WHERE userID = %s);", [userID])

    cartitems = cur.fetchall()

    for item in cartitems:
        cur.execute("SELECT price FROM shoppingCart WHERE userID = %s AND productID = %s;", (userID, item['productID']))
        res = cur.fetchone()
        item['price'] = res['price']  
     
    
    cur.close()

    return render_template('/shoppingcart.html', shoppingcart = cartitems, length= len(cartitems))

   
@app.route('/addToCart/<string:id>', methods=['GET', 'POST'])
def addToCart(id):
    if(session['logged_in']):       
        cur = mysql.connection.cursor()
        userID = session['userID']
        cur.execute("SELECT price FROM products WHERE productID=%s", [int(id)])
        price = cur.fetchone();
        price = price['price']
      
        cur.execute("INSERT IGNORE INTO shoppingCart(userID, productID, price) VALUES (%s, %s, %s)", (userID, int(id), price))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('products'))
       
   
@app.route('/shoppingcart/remove/<string:id>', methods=['GET', 'POST'])
def removeFromCart(id):
    if(session['logged_in']):
        cur = mysql.connection.cursor()
        userID = session['userID']
        cur.execute("DELETE FROM shoppingCart WHERE userID = %s AND productID = %s ", (userID, int(id)))

        mysql.connection.commit()
        cur.close()
        return redirect(url_for('shoppingcart'))

    return('',204)
   
@app.route('/buyProducts')
def buyProducts():
    if(session['logged_in']):
        cartitems = []
        cur = mysql.connection.cursor()
        userID = session['userID']
        
        cur.execute("START TRANSACTION;")
        cur.execute("SELECT * FROM products WHERE productID IN (SELECT shoppingCart.productID FROM shoppingCart WHERE userID = %s);", [userID])
        
        cartitems = cur.fetchall()
        now = datetime.now()
        for item in cartitems:
            cur.execute("SELECT price FROM shoppingCart WHERE userID = %s AND productID = %s;", (userID, item['productID']))
            res = cur.fetchone()  
            price = res['price']
            productID = item['productID']
            sellerID = item['ownerID']
            cur.execute("UPDATE products SET buyerID=%s, date_purchased=%s, price=%s WHERE productID=%s;", (userID, now, price, productID))
            cur.execute("INSERT INTO orders(price, productID, buyerID, sellerID) VALUES(%s, %s, %s, %s);", (price, productID, userID, sellerID))
            cur.execute("DELETE FROM shoppingCart WHERE productID=%s", [productID])
        
        cur.execute("COMMIT;")
        
        mysql.connection.commit()
        
        cur.close()

    return redirect(url_for('transactions'))
                        
@app.route('/transactions')
def transactions():
    if(session['logged_in']):
        cur = mysql.connection.cursor()
        userID = session['userID']
        #cur.execute("SELECT * FROM products WHERE ownerID = %s AND buyerID IS NOT NULL", [userID])
        cur.execute("SELECT products.title, products.price, users.email FROM products INNER JOIN users ON products.buyerID=users.userID WHERE products.ownerID = %s", [userID])
        sold = cur.fetchall()
        
        #cur.execute("SELECT * FROM products where buyerID = %s", [userID])
        cur.execute("SELECT products.title, products.price, products.ownerID, users.email FROM products INNER JOIN users ON products.ownerID=users.userID WHERE buyerID = %s", [userID])
        bought = cur.fetchall()
        cur.close()
        

        
        
    return render_template('transactions.html', soldPhones = sold, boughtPhones = bought, numSold = len(sold), numBought = len(bought))

@app.route('/myProducts')
def myProducts():
    phones = [] ## if emptyyyy..
    if (session['logged_in'] == True):
        cur = mysql.connection.cursor()
        userID = session['userID']

        cur.execute("SELECT * FROM products WHERE ownerID = %s AND buyerID IS NULL", [userID])
        phones = cur.fetchall()
        cur.close()


    return render_template('/myProducts.html', products = phones)


@app.route('/editProduct/<string:id>', methods=['GET', 'POST'])
def editProduct(id):
    if(request.method == 'POST'):
        if(session['logged_in']):
            id = int(id)


            title = request.form['title']
            description = request.form['desc']
            price = request.form['price']

            cur = mysql.connection.cursor()
            userID = session['userID']

            cur.execute("UPDATE products SET title = %s, `desc` = %s, price = %s WHERE ownerID = %s AND productID = %s;", (title, description, int(price), userID, id))

            mysql.connection.commit()
            cur.close()

        return redirect(url_for('myProducts'))
    else:
        if (session['logged_in'] == True):
            cur = mysql.connection.cursor()
            userID = session['userID']

            cur.execute("SELECT * FROM products WHERE ownerID = %s AND productID = %s", (userID, id))
            phone = cur.fetchone()
            cur.close()

        return render_template('/editProduct.html', phone = phone)


           
@app.route('/review/<string:sellerID>', methods=['GET', 'POST'])
def review(sellerID):
    if request.method == 'POST':
         rating = request.form['rating']
         review = request.form['review']

         # Create cursor
         cur = mysql.connection.cursor()

         cur.execute("INSERT IGNORE INTO grading(graderID, gradedID, grade, comment) VALUES(%s, %s, %s, %s)", (session['userID'], sellerID, int(rating), review))
         mysql.connection.commit()
         cur.close()
         return redirect(url_for('transactions'))
    return render_template('/review.html')
 
@app.route('/product/<string:id>/')
def product(id):


    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM products WHERE productID =%s LIMIT 1;", [int(id)])
    product = cur.fetchone()
    
    cur.execute("SELECT * FROM grading WHERE gradedID IN (SELECT products.ownerID FROM products WHERE productID = %s);", [int(id)])
    reviews = cur.fetchall()

    val = 0
    count = 0
    for a in reviews:
        val += a['grade']
        count += 1

    if(count > 0):
        averageRate = val/count
    else:
        averageRate = -1
    
    cur.close()

    return render_template('/product.html', phone = product, rates = reviews, average = averageRate)

   
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
  
  
import string
@app.route('/admin/<string:site>', methods=['GET', 'POST'])
def admin(site):
    print(site)
    print request.method
    if(session['logged_in'] == True):
        userID = session['userID']
        if(userID == 0):

            if("deleteUser" in site):
                id = int(site[10:])
                cur = mysql.connection.cursor()
                cur.execute("UPDATE users SET active = 0 WHERE userID = %s", [id])
                cur.commit()
                cur.close()
                return admin("users")
            elif("deleteProduct" in site):
                id = int(site[13:])
                cur = mysql.connection.cursor()
                cur.execute("DELETE FROM products WHERE productID = %s", [id])
                cur.commit()
                cur.close()
                return admin("products")


            content = []
            if(site == 'users'):
                cur = mysql.connection.cursor()
                cur.execute("SELECT * FROM users WHERE userID != 0; AND active = 1")
                content = cur.fetchall()
                cur.close()
            elif(site == 'products'):
                cur = mysql.connection.cursor()
                cur.execute("SELECT * FROM products WHERE buyerID IS NOT NULL;")
                content = cur.fetchall()
                cur.close()
            elif(site == 'orders'):
                cur = mysql.connection.cursor()
                cur.execute("SELECT * FROM orders;")
                content = cur.fetchall()
                
                for sub in content:
                    buyerID = sub['buyerID']
                    sellerID = sub['sellerID']
                    
                    cur.execute("SELECT email FROM users WHERE userID = %s;", [buyerID])
                    buyerName = cur.fetchone()
                    cur.execute("SELECT email FROM users WHERE userID = %s;", [sellerID])
                    sellerName = cur.fetchone()

                    sub['buyerID'] = buyerName
                    sub['sellerID'] = sellerName
                
                cur.close()

            return render_template('admin.html', site = site, content = content)

    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.secret_key = 'THISISTHEKEY'
    app.run(debug=True, host="0.0.0.0")

