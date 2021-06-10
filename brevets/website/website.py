from urllib.parse import urlparse, urljoin
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_login import (LoginManager, current_user, login_required,
                         login_user, logout_user, UserMixin,
                         confirm_login, fresh_login_required)
from flask_wtf import FlaskForm as Form
from wtforms import BooleanField, StringField, validators
from passlib.hash import sha256_crypt as pwd_context
import json
import requests
import logging


class LoginForm(Form):
    username = StringField('Username', [
        validators.Length(min=2, max=25,
                          message=u"Huh, little too short for a username."),
        validators.InputRequired(u"Forget something?")])
    password = StringField('Password', [
        validators.Length(min=8, max=25,
                          message=u"Longer passwords are more secure! Make it more than 8 characters."),
        validators.InputRequired(u"Password is required for login!")])
    remember = BooleanField('Remember me')


class RegistrationForm(Form):
    username = StringField('Username', [
        validators.Length(min=2, max=25,
                          message=u"Huh, little too short for a username."),
        validators.InputRequired(u"Forget something?")])
    password = StringField('Password', [
        validators.Length(min=8, max=25,
                          message=u"Make sure you have a strong password!"),
        validators.InputRequired(u"Password is required for login!")])

def hash_password(password):
    return pwd_context.using(salt='s00p3rSeCret').encrypt(password)

def is_safe_url(target):
    """
    :source: https://github.com/fengsp/flask-snippets/blob/master/security/redirect_back.py
    """
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


class User(UserMixin):
    def __init__(self, username, token):
        self.username = username
        self.token = token


app = Flask(__name__)
app.secret_key = "and the cats in the cradle and the silver spoon"

app.config.from_object(__name__)

login_manager = LoginManager()
login_manager.init_app(app)

login_manager.session_protection = "strong"

login_manager.login_view = "login"
login_manager.login_message = u"Please log in to access this page."

login_manager.refresh_view = "login"
login_manager.needs_refresh_message = (
    u"To protect your account, please reauthenticate to access this page."
)
login_manager.needs_refresh_message_category = "info"

@login_manager.user_loader
def load_user(username):
    token = flask.session["token"]
    if not username or not token:
        return
    return User(username, token)

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit() and request.method == "POST" and "username" in request.form and "password" in request.form:
        username = request.form["username"]
        password = hash_password(request.form["password"])
        confirm = requests.post('http://restapi:5000/register' + "?un=" + str(username) + "&pw=" + str(password))
        if confirm:
            flash("Registered successfully! Login to access resources.")
            next = request.args.get("next")
            if not is_safe_url(next):
                abort(400)
            return redirect(next or url_for('index'))
        else:
            flash("An account with this name already exists. Please try again or log in if this is you!")
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit() and request.method == "POST" and "username" in request.form and "password" in request.form:
        username = request.form["username"]
        password = hash_password(request.form["password"])
        token = requests.get('http://restapi:5000/token' + "?un=" + str(username) + "&pw=" + str(password))
        if token:
            token = token.json()
            flask.session['token'] = token['token']
            remember = request.form.get("remember", "false") == "true"
            user = load_user(username)
            if login_user(user, remember=remember):
                flash("Logged in!")
                flash("I'll remember you") if remember else None
                next = request.args.get("next")
                if not is_safe_url(next):
                    abort(400)
                return redirect(next or url_for('index'))
            else:
                flash("Sorry, but you could not log in.")
        else:
            flash(u"Invalid username or password.")
    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.")
    return redirect(url_for("index"))

@app.route("/secret")
@login_required
def secret():
    return render_template("secret.html")

@app.route('/listAll', methods=['GET'])
@login_required
def listeverything():
    top = request.args.get('top')
    dtype = str(request.args.get('dtype'))
    if top:
        r = requests.get('http://restapi:5000/listAll/' + dtype + "?top=" + str(top))
    else:
        r = requests.get('http://restapi:5000/listAll/' + dtype)
    return r.text    

@app.route('/listOpenOnly', methods=['GET'])
@login_required
def listopen():
    top = request.args.get('top')
    dtype = str(request.args.get('dtype'))
    if top:
        r = requests.get('http://restapi:5000/listOpenOnly/' + dtype + "?top=" + str(top))
    else:
        r = requests.get('http://restapi:5000/listOpenOnly/' + dtype)
    return r.text

@app.route('/listCloseOnly', methods=['GET'])
@login_required
def listclose():
    top = request.args.get('top')
    dtype = str(request.args.get('dtype'))
    if top:
        r = requests.get('http://restapi:5000/listCloseOnly/' + dtype + "?top=" + str(top))
    else:
        r = requests.get('http://restapi:5000/listCloseOnly/' + dtype)
    return r.text


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
