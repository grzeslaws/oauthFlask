from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_login import LoginManager, login_user, UserMixin, current_user, logout_user, login_required
from passlib.hash import sha256_crypt
from datetime import datetime 
from flask_dance.contrib.twitter import make_twitter_blueprint, twitter
from flask_dance.consumer.backend.sqla import OAuthConsumerMixin, SQLAlchemyBackend
from flask_dance.consumer import oauth_authorized
from sqlalchemy.orm.exc import NoResultFound

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:admin@localhost/flasksqlalchemy"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////Users/grzesiek/Desktop/sqlalchemy/test.db"
app.config["SECRET_KEY"] = "thisissecretkey"

twitter_blueprint = make_twitter_blueprint(api_key='Wxheh706myGRPdIzg1UG8NCmD', api_secret='z2gPTdT8v1pCTNEX7xxtf0bbqLwLJgfiqgdgDa03GTf7M5m13T')
app.register_blueprint(twitter_blueprint, url_prefix='/twitter_login')

db = SQLAlchemy(app)

login_manager = LoginManager() 
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"
login_manager.refresh_view = "index"

class Post(db.Model):
    __tablename__ = "Post"
    id = db.Column("id", db.Integer, primary_key=True)
    title = db.Column("title", db.String(50)) 
    subtitle = db.Column("subtitle", db.String(100)) 
    content = db.Column("content", db.Text) 
    author = db.Column("author", db.String(50))
    created_on = db.Column('created_on' , db.DateTime)

class User(UserMixin, db.Model):
    __tablename__ = "User"
    id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column("name", db.String(50)) 
    password = db.Column("password", db.String(300)) 
    email = db.Column("email", db.String(50))

class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    user = db.relationship(User)

twitter_blueprint.backend = SQLAlchemyBackend(OAuth, db.session, user = current_user, user_required=False)

def hashPassword(password):
    return sha256_crypt.encrypt(password)

# @login_manager.unauthorized_handler
# def unauthorized_handler():
#     return 'Unauthorized'

@app.route('/twitter') 
def twitter_login():
    
    if not twitter.authorized:
        print('\x1b[6;30;42m' + 'sdsdsds' + '\x1b[0m')
        return redirect(url_for('twitter.login'))

    account_info = twitter.get('account/settings.json')
    account_info_json = account_info.json()

    return '<h1>Your Twitter name is @{}'.format(account_info_json['screen_name']) 

@oauth_authorized.connect_via(twitter_blueprint)
def twitter_logged_in(blueprint, token):
    
    if not token:
        flash("Failed to log in with Twitter.", category="error")
        return False

    account_info_settings = twitter.get('account/settings.json')
    account_info_settings_json = account_info_settings.json()
    account_info = blueprint.session.get('account/verify_credentials.json')

    if not account_info.ok:
        msg = "Failed to fetch user info from Twitter."
        flash(msg, category="error")
        return False

    account_info_json = account_info.json()
    twitter_user_id = str(account_info_json["id"])

    query = OAuth.query.filter_by(
        provider = blueprint.name,
        id = twitter_user_id
    )

    try:
        oauth = query.one()
        login_user(user)
    except NoResultFound:
        oauth = OAuth(
            provider = blueprint.name,
            id = twitter_user_id,
            token = token,
        )
    
    if oauth.user:
        login_user(oauth.user)
        flash("Successfull signed by Twitter!")

    else:
        user = User(
            email = "grzesupel@gmail.com",
            name = account_info_settings_json["screen_name"]
        )

        oauth.user = user
        db.session.add_all([user, oauth])
        db.session.commit()
        login_user(user)
        flash("Successfull created account by Twitter!")

    return False

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def index():
    return render_template("home.html")

@app.route("/admin")
@login_required
def admin():
    return render_template("home.html", currentUser=current_user.name)

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = hashPassword(request.form['password'])
        
        user = User(name=name, password=password, email=email)
        db.session.add(user)
        db.session.commit()

    return render_template("register.html")

@app.route("/add_post", methods=["GET", "POST"])
@login_required
def add_post():

    if request.method == "POST":
        title = request.form["title"]
        subtitle = request.form["subtitle"]
        content = request.form["content"]

        new_post = Post(title = title, subtitle = subtitle, content = content, author = current_user.name, created_on = datetime.now())

        db.session.add(new_post)
        db.session.commit()

        flash("Post has been added", "success")

        return redirect(url_for("posts"))

    return render_template("add_post.html")

@app.route("/posts")
def posts():
    posts = Post.query.all()
    print(posts)
    return render_template("posts.html", posts = posts)

@app.route('/post/<int:post_id>')
def post(post_id):
    post = Post.query.filter_by(id=post_id).first()
    print(post)
    return render_template("post.html", post = post)

@app.route("/login", methods=["POST", "GET"]) 
def login():

    if request.method == "POST":
        userFromDb = User.query.filter_by(name=request.form["name"]).first()
        passFormForm = request.form["password"]

        print("userFromDb: ", userFromDb)
        print("passFormForm: ", passFormForm)

        if sha256_crypt.verify(passFormForm, userFromDb.password):
            user = User.query.filter_by(name=userFromDb.name).first()
            login_user(user)
            flash("You are logged in", "success")
            return redirect(url_for("admin"))
        else:
            flash("Incorrect password", "success")

    return render_template("login.html")
    
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You are logged out")
    return redirect(url_for("index"))

@app.route("/terms")
def terms():
    return "terms"

if __name__ == "__main__": 
    app.secret_key = "sepersecretkey"
    app.run(debug=True)

 