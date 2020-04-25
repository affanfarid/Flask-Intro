from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)


# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'magicmouse'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#initalize mysql
mysql = MySQL(app)

Articles = Articles()

#index route
#url string of route in parenthesis
@app.route('/')

#homepage
def index():
    return render_template('home.html')

#about page
@app.route('/about')
def about():
    return render_template('about.html')

#all articles
@app.route('/articles')
def articles():
    return render_template('articles.html', articles = Articles)

#single article
@app.route('/article/<string:id>/')
def article(id):
    return render_template('article.html', id=id)

#register form class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1,max=50)])
    username = StringField('Username',[validators.Length(min=4,max=25)])
    email = StringField('Email',[validators.Length(min=6,max=50)])
    password = StringField('Password',[
        validators.DataRequired(),
        validators.EqualTo('confirm',message = 'Passwords do not match')
        ])
    confirm = PasswordField('Confirm Password')

#user register
@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        #register user
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        #create Cursor
        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s,%s, %s, %s)", (name, email, username, password))

        #commit to DB
        mysql.connection.commit()

        #close connection
        cur.close()

        #flash message when registered
        flash('User Register Successful', 'success')

        return redirect(url_for('login'))

        #return render_template('register.html',form=form)
    
    return render_template('register.html',form=form)

# user login
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        #if the form is submitted
        #get username and password from the form
        username = request.form['username']
        password_candidate = request.form['password']

        #create a cursor
        cur = mysql.connection.cursor()

        #get user by username
        
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username] )

        if result > 0:
            #get stored hash
            data = cur.fetchone()
            password = data['password']

            #compare passwords
            if sha256_crypt.verify(password_candidate, password):
                #app.logger.info('PASSWORD MATCHED')
                #passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard')) 

            else:
                #app.logger.info('PASSWORD NOT MATCHED')

                error = 'Invalid Login'
                return render_template('login.html', error=error)
            #close connection
            cur.close()

        else:
            #user not found
            #app.logger.info('NO USER FOUND')
            error = 'Username not found'
            return render_template('login.html', error=error)


    return render_template('login.html')


#check if user is logged in 
#decorator
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap


#log out
@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out successfully', 'success')
    return redirect(url_for('login'))


#dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.secret_key= 'secret123'
    app.run(debug=True)
    #app.run(host='localhost', port=9874,  debug=True)