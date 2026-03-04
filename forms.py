from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, URL


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Register")


class OTPForm(FlaskForm):
    otp = StringField("Verification Code", validators=[DataRequired(), Length(min=4, max=6)])
    submit = SubmitField("Verify")


class ProductForm(FlaskForm):
    url = StringField("Product URL", validators=[DataRequired(), URL(), Length(max=2048)])
    submit = SubmitField("Add Product")
