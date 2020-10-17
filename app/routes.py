from flask import render_template
from app import app
from app.filing_form import FilingReqForm

@app.route('/', methods=['GET'])
@app.route('/index')
def index():
  form = FilingReqForm()
  if form.validate_on_submit():
    results = filing_request(form)
    return render_template('index.html', form=form, data=results)
  return render_template('index.html', form=form, data=None)
