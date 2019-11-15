# -*- coding: utf-8 -*-

from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    first = ["head", "desc", "https://i.ebayimg.com/images/g/ln4AAOSwkvFaXmcn/s-l400.jpg"]
    i = 0
    phones = []
    while(i < 4):
        phones.append(["head", "desc", "https://i.ebayimg.com/images/g/ln4AAOSwkvFaXmcn/s-l400.jpg"])
        i += 1
        
    return render_template('/home.html', first = first, phones = phones)


@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

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



if __name__ == '__main__':
    app.run(debug=True)
