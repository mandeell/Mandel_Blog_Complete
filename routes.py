from flask import render_template, redirect, url_for, Blueprint, flash
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, BlogPost, User, Comment
from forms import CreatePostForm, ContactForm, RegisterForm, LoginForm, CommentForm
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



routes = Blueprint('routes', __name__)
login_manager = LoginManager()

def send_email(to, subject, content):
    """Helper function to send emails"""
    context = ssl.create_default_context()
    msg = MIMEText(content, "plain", "utf-8")
    msg['Subject'] = subject
    msg['From'] = MY_EMAIL
    msg['To'] = to
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=20) as connection:
            connection.login(user=MY_EMAIL, password=MY_PASSWORD)
            connection.sendmail(
                from_addr=MY_EMAIL,
                to_addrs=to,
                msg=msg.as_string()
            )
        flash("Message sent successfully!", "success")
    except Exception as e:
        from main import app
        app.logger.error(f"Email failed: {str(e)}")
        flash("Failed to send message. Please try again later.", "danger")

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
def register():
    form = RegisterForm()
    if not current_user.is_authenticated or not getattr(current_user, 'admin', False):
        del form.agent
        del form.admin
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered. Login instead.')
            return redirect(url_for('routes.login'))

        hashed_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )

        agent = form.agent.data if 'agent' in form._fields else False
        admin = form.admin.data if 'admin' in form._fields else False

        new_user = User(
            name = form.name.data,
            email = form.email.data,
            phone = form.phone.data,
            password = hashed_and_salted_password,
            agent = agent,
            admin = admin
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

@routes.route('/post/<int:post_id>', methods=['GET', 'POST'])
def show_post(post_id):
    from main import gravatar
    requested_post = db.get_or_404(BlogPost, post_id)
    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        if current_user.is_authenticated:
            if not current_user.is_authenticated:
                flash("You need to login or register to comment.")
                return redirect(url_for("routes.login"))
        new_comment = Comment(
            comment_author=current_user,
            text=comment_form.comment_text.data,
            parent_post = requested_post,
            name = comment_form.name.data,
        )
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('routes.show_post', post_id=post_id))
    return render_template("post.html", post=requested_post,
                           form=comment_form, current_user=current_user)

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

@routes.route('/delete_comment/<int:comment_id>')
@admin_only
def delete_comment(comment_id):
    comment = db.get_or_404(Comment, comment_id)
    if not current_user.admin:
        flash("You don't have permission to perform this action", "danger")
        return redirect(url_for('routes.show_post', post_id=comment.post_id))
    db.session.delete(comment)
    db.session.commit()
    return redirect(url_for('routes.show_post', post_id=comment.post_id))

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
        send_email(to=MY_EMAIL,subject='Blog Contact Form', content=content)
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

@routes.context_processor
def inject_now():
    from datetime import datetime
    return {'year': datetime.now().year }


