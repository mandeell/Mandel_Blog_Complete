from flask import render_template, redirect, url_for, Blueprint, flash
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, BlogPost, User
from forms import CreatePostForm, ContactForm, RegisterForm, LoginForm
from dotenv import load_dotenv
from email.mime.text import MIMEText
import smtplib, os, ssl
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from functools import wraps
from flask import abort


load_dotenv()
MY_EMAIL = os.getenv("MY_EMAIL")
MY_PASSWORD = os.getenv("MY_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")
context = ssl.create_default_context()

routes = Blueprint('routes', __name__)
login_manager = LoginManager()

def agent_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #If id is not 1 then return abort with 403 error
        if not current_user.agent:
            return abort(403)
        #Otherwise continue with the route function
        return f(*args, **kwargs)
    return decorated_function

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #If id is not 1 then return abort with 403 error
        if not current_user.admin:
            return abort(403)
        #Otherwise continue with the route function
        return f(*args, **kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

@routes.route('/register', methods=['GET', 'POST'])
@admin_only
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered. Login instead.')
            return redirect(url_for('routes.login'))

        hashed_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            name = form.name.data,
            email = form.email.data,
            phone = form.phone.data,
            password = hashed_and_salted_password,
            agent = form.agent.data,
            admin = form.admin.data
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('routes.get_all_posts'))

    return render_template("register.html", form=form)

@routes.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    email = form.email.data
    password = form.password.data
    if form.validate_on_submit():
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()
        if user:
            if check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('routes.get_all_posts'))
            else:
                flash('Incorrect Password. Please try again', 'danger')
                return redirect(url_for('routes.login'))
        else:
            flash('User not found.', 'warning')
            return redirect(url_for('routes.login'))
    return render_template("login.html", form=form)

@routes.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('routes.get_all_posts'))

@routes.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost).order_by(BlogPost.id.desc()))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts)

@routes.route('/post/<int:post_id>')
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    return render_template("post.html", post=requested_post)

@routes.route('/add_new_post', methods=['GET', 'POST'])
@login_required
@agent_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        if not current_user.agent:
            flash("You don't have permission to perform this action", "danger")
            return redirect(url_for('routes.get_all_posts'))
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            date = date.today().strftime("%B %d, %Y"),
            body = form.body.data,
            img_url = form.img_url.data,
            author = current_user,
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('routes.get_all_posts'))
    return render_template("make-post.html", form=form)

@routes.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@agent_only
@login_required
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title = post.title,
        subtitle = post.subtitle,
        body = post.body,
        img_url = post.img_url,
        author = post.author,
    )

    if edit_form.validate_on_submit():
        if not current_user.agent:
            flash("You don't have permission to perform this action", "danger")
            return redirect(url_for('routes.get_all_posts'))
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.body = edit_form.body.data
        post.author = edit_form.author.data
        post.img_url = edit_form.img_url.data
        db.session.commit()
        return redirect(url_for('routes.show_post', post_id=post.id))
    return render_template('make-post.html', is_edit=True, form=edit_form)

@routes.route('/delete/<int:post_id>')
@admin_only
@login_required
def delete(post_id):
    post = db.get_or_404(BlogPost, post_id)
    if not current_user.admin:
        flash("You don't have permission to perform this action", "danger")
        return redirect(url_for('routes.get_all_posts'))
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('routes.get_all_posts', post_id=post_id))

@routes.route("/about")
def about():
    return render_template("about.html")

@routes.route("/contact", methods=["GET", "POST"])
def contact():
    contact_form = ContactForm()
    if contact_form.validate_on_submit():
        content = (f'Name: {contact_form.name.data}\n'
                   f'Email: {contact_form.email.data}\n'
                   f'Phone Number: {contact_form.phone.data}\n'
                   f'Message: {contact_form.message.data}')
        msg = MIMEText(content, "plain", "utf-8")
        msg['Subject'] = "Blog Contact Form"
        msg['From'] = MY_EMAIL
        msg['To'] = contact_form.email.data.lower()
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=20) as connection:
                connection.login(user=MY_EMAIL, password=MY_PASSWORD)
                connection.sendmail(
                    from_addr=MY_EMAIL,
                    to_addrs=TO_EMAIL.lower(),
                    msg=msg.as_string()
                )
            flash("Message sent successfully!", "success")
        except Exception as e:
            from main import app
            app.logger.error(f"Email failed: {str(e)}")
            flash("Failed to send message. Please try again later.", "danger")
        return redirect(url_for('routes.contact'))
    elif contact_form.is_submitted() and not contact_form.validate():
        flash("Please correct the errors in the form.", "danger")
    return render_template('contact.html', form=contact_form)

@routes.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@routes.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
