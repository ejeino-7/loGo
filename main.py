# -*- coding: utf-8 -*-

from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    first = ["head", "desc", "https://i.ebayimg.com/images/g/ln4AAOSwkvFaXmcn/s-l400.jpg"]
    i = 0
    phones = []
    while(i < 4):
        phones.append(["head"+i, "desc"+i, "https://i.ebayimg.com/images/g/ln4AAOSwkvFaXmcn/s-l400.jpg"])
        i++
        
    return render_template('/home.html', first = first, phones = phones)


@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
