from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, URL, Regexp


class LoginForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Email is required."),
            Email(message="Enter a valid email address."),
            Length(max=255),
        ],
    )

    password = PasswordField(
        "Password",
        validators=[DataRequired(message="Password is required.")],
    )

    submit = SubmitField("Login")


class RegisterForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Email is required."),
            Email(message="Enter a valid email address."),
            Length(max=255),
        ],
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Password is required."),
            Length(min=8, message="Password must be at least 8 characters."),
            Regexp(
                r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$",
                message=(
                    "Password must contain at least one uppercase letter, "
                    "one lowercase letter, and one number."
                ),
            ),
        ],
    )

    submit = SubmitField("Register")


class OTPForm(FlaskForm):
    otp = StringField(
        "Verification Code",
        validators=[
            DataRequired(message="Code is required."),
            Length(min=4, max=6),
            Regexp(r"^[0-9]+$", message="Code must contain only numbers."),
        ],
    )

    submit = SubmitField("Verify")


class ProductForm(FlaskForm):
    url = StringField(
        "Product URL",
        validators=[
            DataRequired(message="Product URL is required."),
            URL(message="Enter a valid URL."),
            Length(max=2048),
        ],
    )

    submit = SubmitField("Add Product")