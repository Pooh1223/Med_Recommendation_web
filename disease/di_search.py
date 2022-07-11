from flask import Blueprint,Flask, render_template, session, redirect, url_for, Response
import pickle
import pandas as pd
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import base64
from Class.AttrSelect import *

from configs import config

# # to import from parent folder
# import os, sys
# currentdir = os.path.dirname(os.path.realpath(__file__))
# parentdir = os.path.dirname(currentdir)
# sys.path.append(parentdir)

# app = Flask(__name__, template_folder='templates')
# app.config["SECRET_KEY"] = "123456"
# # app.config.from_object(config.DevelopmentConfig)

di_ = Blueprint('di_search',__name__,template_folder="../templates/disease")

di_name_mat = pd.read_csv('model/ICD_.csv')
# prob_mat = pd.read_csv('model/dm_mat.csv')

with open('model/di_cnt','rb') as fp:
    cnt_mat = pickle.load(fp)

di_name_list = di_name_mat['NAME_ZH'].tolist()
di_en_name_list = di_name_mat['NAME_EN'].tolist()
di_id_tmp = di_name_mat['ID'].tolist()
di_id_list = []
# disease name preprocessing
for item in di_id_tmp:
    try:
        di_id_list.append(float(item))
    except:
        di_id_list.append(item)

de_mat = pd.read_csv('model/func_type_mat.csv')
de_name_list = list(de_mat.loc[:,'name'])
gender_list = ['M','F']
age_list = [x for x in range(100)]

# department interchange with its id
de_name_id_list = {}
for i in range(len(de_name_list)):
    de_name_id_list[de_name_list[i]] = list(de_mat.loc[:,'id'])[i]

# insert default option for all list except disease

de_name_list.insert(0,'default')
gender_list.insert(0,'default')
age_list.insert(0,'default')

# # department data form in order to calculate the probability
# with open('model/dept_cnt','rb') as fp:
#     dept_cnt = pickle.load(fp)

# # gender data form in order to calculate the probability
# with open('model/gender_cnt','rb') as fp:
#     gender_cnt = pickle.load(fp)

# # age data form in order to calculate the probability
# with open('model/age_cnt','rb') as fp:
#     age_cnt = pickle.load(fp)

class GenderForm(FlaskForm):
    gender = SelectField('查看的性別', choices=gender_list, render_kw={"data-live-search":"true"})
    submit = SubmitField("確認")

class DepartmentForm(FlaskForm):
    # dept = SelectField('查看的科別', choices=de_name_list,render_kw={"data-live-search":"true"})

    # create custom choice array
    choice = [('default','default',dict())]

    for item in de_name_list[1:]:
        choice.append((item,item,{"data-tokens":de_name_id_list[item]}))

    dept = AttribSelectField('查看的科別', choices=choice,render_kw={"data-live-search":"true"})
    submit = SubmitField("確認")

class AgeFormUpper(FlaskForm):
    age = SelectField('查看的年齡上界', choices=age_list, render_kw={"data-live-search":"true"})
    submit = SubmitField("確認")

class AgeFormLower(FlaskForm):
    age = SelectField('查看的年齡下界', choices=age_list, render_kw={"data-live-search":"true"})
    submit = SubmitField("確認")

# disease form for searching probability

@di_.route('/di_search',methods=['GET','POST'])
def di_search():

    geForm = GenderForm()
    deForm = DepartmentForm()
    ageFormUpper = AgeFormUpper()
    ageFormLower = AgeFormLower()

    if geForm.validate_on_submit():
        session['chosen_age_upper'] = ageFormUpper.age.data
        session['chosen_age_lower'] = ageFormLower.age.data
        session['chosen_gender'] = geForm.gender.data
        session['chosen_dept'] = deForm.dept.data

        # print(diForm.med.data)
        # print(ageForm.age.data)
        # print(geForm.gender.data)
        # print(deForm.dept.data)
        # print(ageForm.validate_on_submit())
        # print(geForm.validate_on_submit())
        # print(deForm.validate_on_submit())

        return redirect(url_for('di_search.di_result'))

    return render_template('di_search.html',geForm=geForm,deForm=deForm,ageFormUpper=ageFormUpper,ageFormLower=ageFormLower)


def bar_chart_plot(plot_list,x_name,y_name,plot_name,rotate,filename):
    # entry in plot_list is of the form (name , prob)
    name = [x[0] for x in plot_list]
    prob = [x[-1] for x in plot_list]

    x = np.arange(len(name))
    plt.bar(x, prob)
    plt.xticks(x, name)
    plt.xticks(rotation=rotate)
    plt.xlabel(x_name)
    plt.ylabel(y_name)
    plt.title(plot_name)
    # plt.show()
    # fig = plt.figure(figsize=(6,4))
    # plt.close(fig)
    # fig.subplots_adjust(bottom=0.5)
    buffer = BytesIO()
    plt.savefig(buffer)
    plot_data = buffer.getvalue()

    imb = base64.b64encode(plot_data)
    ims = imb.decode()
    imd = "data:image/png;base64," + ims
    plt.close()

    return imd

@di_.route('/di_result')
def di_result():

    age_begin = 0
    age_end = 100
    gender_begin = 0
    gender_end = 2
    dept_begin = 0
    dept_end = len(de_name_list) - 1 # minus default
    # p_dept = 1
    # p_gender = 1
    # p_age = 1

    # check if all if default
    all_default = True

    # limit the scope
    if session['chosen_age_upper'] != 'default':
        # age_begin = int(session['chosen_age'])
        age_end = int(session['chosen_age_upper']) + 1

        # p_age = age_cnt[0][int(session['chosen_age'])][1] / age_cnt[1]

        all_default = False

    if session['chosen_age_lower'] != 'default':
        age_begin = int(session['chosen_age_lower'])
        # age_end = int(session['chosen_age']) + 1

        # p_age = age_cnt[0][int(session['chosen_age'])][1] / age_cnt[1]

        all_default = False

    if session['chosen_gender'] != 'default':
        if session['chosen_gender'] == 'M':
            gender_end = 1
        else :
            gender_begin = 1

        # p_gender = gender_cnt[0][session['chosen_gender']][1] / gender_cnt[1]

        all_default = False


    if session['chosen_dept'] != 'default':
        dept_begin = de_name_list.index(session['chosen_dept'])
        dept_end = de_name_list.index(session['chosen_dept']) + 1

        # p_dept = dept_cnt[0][de_name_id_list[session['chosen_dept']]][1] / dept_cnt[1]

        all_default = False


    # conditional probability denominator and numerator
    conditional_deno = 0
    conditional_numer = 0

    # print(dept_gender_age_di.shape)
    # print(de_name_list)

    # di_prob = 1
    # di_id = di_name_list.index(session['chosen_disease'])

    # print(di_id)
    print(gender_begin,gender_end)
    print(age_begin,age_end)

    # run through all possible disease and add them into alter_di
    # alter_di format: {med_name: count}
    alter_di = {}
    for i in range(dept_begin,dept_end):
        for j in range(gender_begin,gender_end):
            for k in range(age_begin,age_end):
                # disease_id = di_id
                
                for disease_id in cnt_mat[i][j][k][0].keys():
                    if disease_id not in alter_di:
                        alter_di[disease_id] = cnt_mat[i][j][k][0][disease_id]
                    else :
                        alter_di[disease_id] += cnt_mat[i][j][k][0][disease_id]

                conditional_deno += cnt_mat[i][j][k][1]

    # di_prob = conditional_numer / conditional_deno
    # print(di_prob)

    # med_prob format: [(med_name,prob)]
    di_prob = []

    for item in alter_di.keys():
        try:
            di_name = di_name_list[di_id_list.index(float(item))]
        except:
            try:
                di_name = di_name_list[di_id_list.index(item)]
            except:
                di_name = item
        di_prob.append([item,di_name,alter_di[item] / conditional_deno])

    mmm = [x[-1] for x in di_prob]
    print(mmm)
    print(sum(mmm))

    # find the corresponding icd code given disease chinese name
    # id = -1
    # for item in di_name_mat.values.tolist():
    #     if item[1] == session['chosen_disease']:
    #         id = item[0]
    #         break

    # multiply by conditional probability : p(med | disease) * p(disease | dept , gender , age) * p(dept) * p(gender) * p(age)

    # result_prob = []

    # for item in list(prob_mat.loc[:,id]):
    #     conditional_prob = item * di_prob * p_dept * p_gender * p_age
    #     result_prob.append(conditional_prob)

    # di_col = list(prob_mat.loc[:,id])
    # di_col = zip(di_col,list(x for x in range(len(di_col))))
    # di_col = zip(med_prob,list(x for x in range(len(med_prob))))
    di_col = sorted(di_prob,key = lambda s: s[-1],reverse = True)

    # med_name = list(med_name_dt.loc[:,'name'])

    di_name_prob = []

    # insert pair (med_name,probability)
    for i in range(min(10,len(di_col))):
        # print(med_prob[i][1])
        # print(type(med_prob[i][1]))
        di_name_prob.append([di_col[i][0],di_col[i][1],di_col[i][2]])

    # session['med'] = di_col
    # session['med_name'] = list(med_name_dt.loc[:,'name'])

    # plot the top 10 medicine as png (bar chart)
    print(di_name_prob)
    print(type(di_name_prob))
    di_img = bar_chart_plot(di_name_prob,'Di','Prob','Top 10 disease',20,'top10disease')

    # # calculate the distributions of three features
    # try :
    #     disease_name = float(di_name_mat['id'].tolist()[di_id])
    # except :
    #     disease_name = di_name_mat['id'].tolist()[di_id]
    # age_distribution , gender_distribution , dept_distribution = distributions(disease_name)

    # print(disease_name)
    # print(type(disease_name))
    # print(len(age_distribution[0]))
    # print(len(gender_distribution[0]))
    # print(len(dept_distribution[0]))

    # # transform distribution list into the form of bar_chart_plot (name,count)
    # age_dist = []
    # for item in age_distribution[0].keys():
    #     age_dist.append([item,age_distribution[0][item]])

    # gender_dist = []
    # for item in gender_distribution[0].keys():
    #     gender_dist.append([item,gender_distribution[0][item]])

    # dept_dist = []
    # for item in dept_distribution[0].keys():
    #     dept_dist.append([item,dept_distribution[0][item]])

    # print(len(age_dist))
    # print(len(gender_dist))
    # print(len(dept_dist))

    # # save their plot
    # age_img = bar_chart_plot(age_dist,'Age','Number','Age distribution',90,'age_dist')
    # gender_img = bar_chart_plot(gender_dist,'Gender','Number','gender distribution',0,'gender_dist')
    # dept_img = bar_chart_plot(dept_dist,'Department','Number','Dept distribution',0,'dept_dist')

    # origin html: <img src="{{url_for('static',filename='top10med.png')}}">

    return render_template("di_result.html",di = di_name_prob,di_img = di_img)