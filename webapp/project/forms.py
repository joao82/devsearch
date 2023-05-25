from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField, FileField
from wtforms.validators import DataRequired, InputRequired


class StringListField(TextAreaField):
    def _value(self):
        if self.data:
            return "\n".join(self.data)
        else:
            return ""

    def process_formdata(self, valuelist):
        if valuelist and valuelist[0]:
            self.data = [line.strip() for line in valuelist[0].split("\n")]
        else:
            self.data = []


class ProjectForm(FlaskForm):
    title = StringField(label='Project Title',
                        validators=[DataRequired()])
    description = TextAreaField(
        label='Project Description', validators=[DataRequired()])
    tag = StringListField(label='Tag')
    project_pic = FileField(label='Project picture')
    demo_link = StringField(label='Project Demo Link',
                            validators=[DataRequired()])
    source_link = StringField(label='Project Source Link',
                              validators=[DataRequired()])

    submit = SubmitField(label='Register')


class VoteForm(FlaskForm):
    review = SelectField('Leave Your Project Review', choices=[
        (1, 'Very Bad'), (2, 'Bad'), (3, 'Good'), (4, 'Very Good'), (5, 'Excellent')
    ])

    submit1 = SubmitField(label='Submit')


class TagForm(FlaskForm):
    tag = StringField(label='Tag', validators=[DataRequired()])

    submit = SubmitField(label='Submit')


class CommentForm(FlaskForm):
    content = TextAreaField(label='Comment')

    submit2 = SubmitField(label='Submit')


class SearchForm(FlaskForm):
    searched = StringField('Searched', validators=[InputRequired()])

    submit = SubmitField("Submit")


class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')
