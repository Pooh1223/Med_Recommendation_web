from flask import Blueprint,Flask, render_template, session, redirect, url_for, Response, request
import pandas as pd
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField

from med.med_search import med_
from disease.di_search import di_

app = Flask(__name__, template_folder='templates')
app.config["SECRET_KEY"] = "123456"
# app.config.from_object(config.DevelopmentConfig)

app.register_blueprint(med_)
app.register_blueprint(di_)

# disease form for searching probability

@app.route('/',methods=['GET','POST'])
def main():
    if request.method == "POST":
        print(request.form['to_page'])
        if request.form['to_page'] == 'med':
            return redirect(url_for('med_search.med_search'))
        else :
            return redirect(url_for('di_search.di_search'))

    return render_template('index.html')

if __name__ == '__main__':

    app.run()