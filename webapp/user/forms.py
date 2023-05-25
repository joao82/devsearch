from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, FileField
from wtforms.validators import DataRequired, Length, InputRequired


class UserForm(FlaskForm):
    fullname = StringField(label='Full Name', validators=[DataRequired()])
    intro = StringField(label='User Introduction', validators=[DataRequired()])
    about_me = TextAreaField(label='About Me', validators=[DataRequired()])
    location = StringField(label='Location', validators=[DataRequired()])
    social_github = StringField(label='Github link')
    social_stakoverflow = StringField(label='Stack Overflow Link')
    social_twitter = StringField(label='Twitter Link')
    social_linkedin = StringField(label='LinkedIn Link')
    social_website = StringField(label='Website Address')
    profile_pic = FileField(label='Profile picture')

    submit = SubmitField(label='Register')


class SkillForm(FlaskForm):
    skill = StringField(label='Skill Name', validators=[DataRequired()])
    description = TextAreaField(label='Skill description')

    submit = SubmitField(label='Submit')


class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')


class MessageForm(FlaskForm):
    username = StringField(label='User Name')
    email = StringField(label='Email')
    subject = StringField(label='Subject', validators=[DataRequired()])
    body = TextAreaField(label='Message Body', validators=[
        DataRequired(), Length(min=2, max=14000)])

    submit = SubmitField('Submit')


class SearchForm(FlaskForm):
    searched = StringField('Searched', validators=[InputRequired()])

    submit = SubmitField("Submit")
