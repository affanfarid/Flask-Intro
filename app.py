from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
#from data import Articles
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

#Articles = Articles()

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
    #create cursor
    cur = mysql.connection.cursor()

    #get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No articles found'
        return render_template('articles.html',msg=msg)

    #close connection
    cur.close()
    #return render_template('articles.html', articles = Articles)

#single article
@app.route('/article/<string:id>/')
def article(id):
    #create cursor
    cur = mysql.connection.cursor()

    #get articles
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    return render_template('article.html', article=article)

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
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out successfully', 'success')
    return redirect(url_for('login'))


#dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    #create cursor
    cur = mysql.connection.cursor()

    #get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No articles found'
        return render_template('dashboard.html',msg=msg)

    #close connection
    cur.close()


#article form class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1,max=200)])
    body = TextAreaField('Body',[validators.Length(min=30)])

#add article route
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST'  and form.validate():
        title = form.title.data
        body = form.body
        
        #create cursor

        cur = mysql.connection.cursor()

        #execute
        cur.execute("INSERT INTO articles(title,body,author) VALUES(%s,%s,%s)",(title,body,session['username']))

        #commit to db
        mysql.connection.commit()

        #close connection

        cur.close()

        flash('Article Created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)


#Edit article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    #create cursor
    cur = mysql.connection.cursor()

    #get article by id
    result = cur.execute("SELECT * FROM articles WHERE id = %s",[id])
    
    article = cur.fetchone()


    #get form
    form = ArticleForm(request.form)
    
    #populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']
    
    if request.method == 'POST'  and form.validate():
        title = request.form['title']
        body = request.form['body']
        
        #create cursor

        cur = mysql.connection.cursor()

        #execute
        #cur.execute("UPDATE INTO articles(title,body,author) VALUES(%s,%s,%s)",(title,body,session['username']))
        #cur.execute("UPDATE articles SET name=%s , body=%s WHERE id=%s",(title,body,id))
        #
        cur.execute("UPDATE articles SET title=%s, body=%s WHERE id = %s", (title,body,id))
        
        #commit to db
        mysql.connection.commit()

        #close connection

        cur.close()

        flash('Article Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)

#delete article
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    #create cursor
    cur = mysql.connection.cursor()

    #exceute
    cur.execute("DELETE FROM articles WHERE id=%s",[id])

    #commit to db
    mysql.connection.commit()

    #close connection

    cur.close()

    flash('Article Deleted', 'success')

    return redirect(url_for('dashboard'))





if __name__ == '__main__':
    app.secret_key= 'secret123'
    app.run(debug=True)
    #app.run(host='localhost', port=9874,  debug=True)