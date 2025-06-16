from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.fields.simple import TextAreaField, PasswordField, BooleanField
from wtforms.validators import DataRequired, URL, Email, Regexp, length, EqualTo, ValidationError
from flask_ckeditor import CKEditorField
import phonenumbers, re
from wtforms.widgets.core import CheckboxInput


def validate_phone(form, field):
    phone = field.data
    try:
        parsed = phonenumbers.parse(phone, "NG")  # Default to Nigeria
        if not phonenumbers.is_valid_number(parsed):
            raise ValidationError('Invalid phone number')
    except:
        # Strict regex for Nigerian numbers
        if not re.match(r'^(\+234|0)?[789][01]\d{8}$', phone):
            raise ValidationError('Invalid Nigerian or international format')

class CreatePostForm(FlaskForm):
    title = StringField('Blog Post Title', validators=[DataRequired()])
    subtitle = StringField('Subtitle', validators=[DataRequired()])
    author = StringField('Your Name', validators=[DataRequired()])
    img_url = StringField('Blog Image URL', validators=[DataRequired(), URL()])
    body = CKEditorField('Blog Content', validators=[DataRequired()])
    submit = SubmitField('Submit Post')

class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired(), validate_phone])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Submit')

class RegisterForm(FlaskForm):
    name =  StringField('Name', validators=[DataRequired()])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired(), validate_phone])
    password = PasswordField('Password', validators=[DataRequired(), length(min=8),Regexp(
            r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
            message='Password must contain uppercase, lowercase, a digit, and a special character.'
        )])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password',message='Passwords must match.')])
    agent = BooleanField('Agent')
    admin = BooleanField('Admin')
    submit = SubmitField('Submit')

class LoginForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Submit')
