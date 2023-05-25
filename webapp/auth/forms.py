from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, EqualTo, ValidationError, Length, InputRequired, Email
from webapp.models import User


class RegistrationForm(FlaskForm):
    username = StringField(label="Username", validators=[DataRequired()])
    email = StringField(
        label="Email", validators=[InputRequired(), Email(message="Invalid email"), Length(min=4, max=50)]
    )
    password = PasswordField(label="Password", validators=[DataRequired()])
    confirm_password = PasswordField(label="Confirm Password", validators=[DataRequired(), EqualTo("password")])

    submit = SubmitField(label="Register")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError("Please use a different username.")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError("Please use a different email address.")


class LoginForm(FlaskForm):
    username = StringField(label="Username", validators=[DataRequired()])
    password = PasswordField(label="Password", validators=[DataRequired()])
    submit = SubmitField(label="Login")


class ResetPasswordRequestForm(FlaskForm):
    email = StringField(label="Email", validators=[InputRequired()])
    submit = SubmitField(label="Request Password Reset")


class ResetPasswordForm(FlaskForm):
    password = PasswordField(label="New Password", validators=[DataRequired()])
    confirm_password = PasswordField(label="Repeat Password", validators=[DataRequired()])
    submit = SubmitField(label="Request Password Reset")
