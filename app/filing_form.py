from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired

class FilingReqForm(FlaskForm):
  ticker = StringField('ticker', validators=[DataRequired()])
  filing_type = SelectField('filing', choices=[('10-K', '10-K'), ('10-Q', '10-Q')])
  submit = SubmitField('Search')


