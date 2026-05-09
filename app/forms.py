# Add any form classes for Flask-WTF here
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, SubmitField, DateField,FileField
from wtforms.validators import InputRequired, InputRequired, Email, Length, Optional,FileRequired, FileAllowed, SelectMultipleField


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])


class SignUpForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email()])
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=20)])
    #first_name = StringField('First Name', validators=[InputRequired()])
    #last_name = StringField('Last Name', validators=[InputRequired()])
    full_name = StringField('Full Name', validators=[InputRequired()])
    
    
    #dob = DateField('Date of Birth', format='%Y-%m-%d', validators=[InputRequired()])

    role = SelectField('Gender', choices=[
        ('student', 'Student'), 
        ('admin', 'Admin'), 
        ('other', 'Other')
    ])
    
    parish = SelectField('Looking For', choices=[
        ('Kingston', 'Kingston'), 
        ('St. Andrew', 'St. Andrew'), 
        ('St. Thomas', 'St. Thomas'), 
        ('Portland', 'Portland'), 
        ('St. Mary', 'St. Mary'), 
        ('St. Ann', 'St. Ann'), 
        ('Trelawny', 'Trelawny'), 
        ('St. James', 'St. James'), 
        ('Hanover', 'Hanover'), 
        ('Westmoreland', 'Westmoreland'), 
        ('St. Elizabeth', 'St. Elizabeth'), 
        ('Manchester', 'Manchester'), 
        ('Clarendon', 'Clarendon'), 
        ('St. Catherine', 'St. Catherine'), ], validators=[InputRequired()])
    
    password = PasswordField('Password', validators=[
        InputRequired(), 
        Length(min=8)
    ])
    location_preferences = SelectField('Looking For', choices=[
        ('Kingston', 'Kingston'), 
        ('St. Andrew', 'St. Andrew'), 
        ('St. Thomas', 'St. Thomas'), 
        ('Portland', 'Portland'), 
        ('St. Mary', 'St. Mary'), 
        ('St. Ann', 'St. Ann'), 
        ('Trelawny', 'Trelawny'), 
        ('St. James', 'St. James'), 
        ('Hanover', 'Hanover'), 
        ('Westmoreland', 'Westmoreland'), 
        ('St. Elizabeth', 'St. Elizabeth'), 
        ('Manchester', 'Manchester'), 
        ('Clarendon', 'Clarendon'), 
        ('St. Catherine', 'St. Catherine'), ], validators=[InputRequired()])
    
    submit = SubmitField('Sign Up') 
