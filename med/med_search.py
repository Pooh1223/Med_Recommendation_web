from flask import Blueprint,Flask, render_template, session, redirect, url_for, Response , request , flash
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
import copy
from configs import config

# # to import from parent folder
# import os, sys
# currentdir = os.path.dirname(os.path.realpath(__file__))
# parentdir = os.path.dirname(currentdir)
# sys.path.append(parentdir)

# app = Flask(__name__, template_folder='templates')
# app.config["SECRET_KEY"] = "123456"
# # app.config.from_object(config.DevelopmentConfig)

med_ = Blueprint('med_search',__name__,template_folder="../templates/med")

di_name_mat = pd.read_csv('model/di_name_en_csv.csv')
med_name_dt = pd.read_csv('model/med_name_en_csv.csv')
# prob_mat = pd.read_csv('model/dm_mat.csv')

with open('model/big_matrix','rb') as fp:
    cnt_mat = pickle.load(fp)

di_name_list = di_name_mat['name'].tolist()
di_en_name_list = di_name_mat['en_name'].tolist()
di_id_list = di_name_mat['id'].tolist()
med_id_list = med_name_dt['name'].tolist()
med_en_name_list = med_name_dt['en_name'].tolist()

usable_threshold = 3
with open('model/unconf_matrix','rb') as fp:
    med_unconfident_cnt = pickle.load(fp)

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

# department data form in order to calculate the probability
with open('model/dept_cnt','rb') as fp:
    dept_cnt = pickle.load(fp)

# gender data form in order to calculate the probability
with open('model/gender_cnt','rb') as fp:
    gender_cnt = pickle.load(fp)

# age data form in order to calculate the probability
with open('model/age_cnt','rb') as fp:
    age_cnt = pickle.load(fp)

class DiseaseForm(FlaskForm):
    # med = SelectField('???????????????', choices=list(di_name_mat.loc[:,'name']))

    choice = []

    for i in range(len(di_name_list)):
        choice.append((di_name_list[i],di_name_list[i],{"data-tokens": di_en_name_list[i] + " " + str(di_id_list[i])}))

    med = AttribSelectField('???????????????', choices=choice,render_kw={"data-live-search":"true"})

    submit = SubmitField("??????")

class GenderForm(FlaskForm):
    gender = SelectField('???????????????', choices=gender_list, render_kw={"data-live-search":"true"})
    submit = SubmitField("??????")

class DepartmentForm(FlaskForm):
    # dept = SelectField('???????????????', choices=de_name_list,render_kw={"data-live-search":"true"})

    # create custom choice array
    choice = [('default','default',dict())]

    for item in de_name_list[1:]:
        choice.append((item,item,{"data-tokens":de_name_id_list[item]}))

    dept = AttribSelectField('???????????????', choices=choice,render_kw={"data-live-search":"true"})
    submit = SubmitField("??????")

class AgeFormLower(FlaskForm):
    age = SelectField('?????????????????????(???)', choices=age_list, render_kw={"data-live-search":"true"})
    submit = SubmitField("??????")

class AgeFormUpper(FlaskForm):
    age = SelectField('?????????????????????(???)', choices=age_list, render_kw={"data-live-search":"true"})
    submit = SubmitField("??????")

def DynamicMedResponse(number_of_med):
    # create the form dynamically

    class MedResponse(FlaskForm):
        # med_res.choises = eval
        submit = SubmitField("??????")

    for i in range(number_of_med):
        # eval = [5,4,3,2,1]
        setattr(MedResponse,f'f{i}',SelectField(f'F{i}',choices=[5,4,3,2,1]))
        # med_res = SelectField('')

    return MedResponse;


# disease form for searching probability

@med_.route('/med_search',methods=['GET','POST'])
def med_search():
    diForm = DiseaseForm()
    geForm = GenderForm()
    deForm = DepartmentForm()
    ageFormUpper = AgeFormUpper()
    ageFormLower = AgeFormLower()

    if diForm.validate_on_submit():
        session['chosen_disease'] = diForm.med.data
        session['chosen_age_lower'] = ageFormLower.age.data
        session['chosen_age_upper'] = ageFormUpper.age.data
        session['chosen_gender'] = geForm.gender.data
        session['chosen_dept'] = deForm.dept.data

        # print(diForm.med.data)
        # print(ageForm.age.data)
        # print(geForm.gender.data)
        # print(deForm.dept.data)
        # print(ageForm.validate_on_submit())
        # print(geForm.validate_on_submit())
        # print(deForm.validate_on_submit())

        return redirect(url_for('med_search.med_result'))

    return render_template('med_search.html',diForm=diForm,geForm=geForm,deForm=deForm,ageFormUpper=ageFormUpper,ageFormLower=ageFormLower)


def distributions(disease_name):
    # calculate the distributions of age, department , gender
    # return the amount dist of three features

    # [{age : number ,} , total_count]
    age_dist = [{},0]
    gender_dist = [{},0]
    dept_dist = [{},0]

    # assign the number of each age that has the specific disease
    for age in age_cnt[0].keys():
        if disease_name in age_cnt[0][age][0].keys():
            age_dist[0][age] = age_cnt[0][age][0][disease_name]
            age_dist[1] += age_cnt[0][age][0][disease_name]

    # assign the number of each gender that has the specific disease
    for gender in gender_cnt[0].keys():
        if disease_name in gender_cnt[0][gender][0].keys():
            gender_dist[0][gender] = gender_cnt[0][gender][0][disease_name]
            gender_dist[1] += gender_cnt[0][gender][0][disease_name]

    # assign the number of each dept that has the specific disease
    for dept in dept_cnt[0].keys():
        if disease_name in dept_cnt[0][dept][0].keys():
            dept_dist[0][dept] = dept_cnt[0][dept][0][disease_name]
            dept_dist[1] += dept_cnt[0][dept][0][disease_name]

    return age_dist , gender_dist , dept_dist

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

@med_.route('/med_result',methods=["GET","POST"])
def med_result():

    # showing result page

    age_begin = 0
    age_end = 100
    gender_begin = 0
    gender_end = 2
    dept_begin = 0
    dept_end = len(de_name_list) - 1 # minus default

    # and add 5-graded form in each item in med_name_prob
    med_res_form = DynamicMedResponse(10)(request.form)
    # for i in range(10):
    #     med_res_form.append(MedResponse())

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
    di_id = di_name_list.index(session['chosen_disease'])

    print(di_id)
    print(gender_begin,gender_end)
    print(age_begin,age_end)


    # calculate the distributions of three features
    try :
        disease_name = float(di_name_mat['id'].tolist()[di_id])
    except :
        disease_name = di_name_mat['id'].tolist()[di_id]
    age_distribution , gender_distribution , dept_distribution = distributions(disease_name)

    print(disease_name)
    print(type(disease_name))
    print(len(age_distribution[0]))
    print(len(gender_distribution[0]))
    print(len(dept_distribution[0]))

    # transform distribution list into the form of bar_chart_plot (name,count)
    age_dist = []
    for item in age_distribution[0].keys():
        age_dist.append([item,age_distribution[0][item]])

    gender_dist = []
    for item in gender_distribution[0].keys():
        gender_dist.append([item,gender_distribution[0][item]])

    dept_dist = []
    for item in dept_distribution[0].keys():
        dept_dist.append([item,dept_distribution[0][item]])

    print(len(age_dist))
    print(len(gender_dist))
    print(len(dept_dist))

    # if under certain situation, the medicine unconfident count is more than threshold
    # then it will be discarded
    with open('model/unconf_matrix','rb') as fp:
        med_unconfident_cnt = pickle.load(fp)

    # after submit the evaluation form -> redirect
    if med_res_form.validate_on_submit():
        # get response from result page
        eval = []
        cnt = 1
        # for name,item in zip(session['top_10_med'],med_res_form):
        #     eval.append([name,int(item.med_res.data)])
        #     cnt += 1
        for i in range(len(session['top_10_med'])):
            eval.append([session['top_10_med'][i],int(getattr(med_res_form,f'f{i}').data)])
            print(int(getattr(med_res_form,f'f{i}').data))
            cnt += 1

        print(eval)
        # flash('Submit successfully!')
        
        # split the count averagely to all the cell
        for item in eval:
            if item[1] != 5:
                # the medicine unconfident value need to update
                chip = (5 - item[1]) / 5 / (age_end - age_begin) / (gender_end - gender_begin) / len(dept_dist)

                # averagely add them to matrix
                for item in eval:
                    for i in range(dept_begin,dept_end):
                        for j in range(gender_begin,gender_end):
                            for k in range(age_begin,age_end):
                                if item[0] not in med_unconfident_cnt[di_id][i][j][k]:
                                    med_unconfident_cnt[di_id][i][j][k][item[0]] = chip
                                else :
                                    med_unconfident_cnt[di_id][i][j][k][item[0]] += chip

        with open('model/unconf_matrix','wb') as fp:
            pickle.dump(med_unconfident_cnt,fp)

        session['response'] = eval

        return redirect(url_for('med_search.med_response'))
        # return render_template('med_res_result.html',di_name=session['chosen_disease'],result=eval)


    # run through all possible medicine and add them into alter_med
    # alter_med format: {med_name: count}
    
    # med_unconf sum up the  unconf value under all situation
    # med_unconf format: {med_name: unconf_val}

    alter_med = {}
    med_unconf = {}
    for i in range(dept_begin,dept_end):
        for j in range(gender_begin,gender_end):
            for k in range(age_begin,age_end):
                disease_id = di_id
                print(cnt_mat[disease_id][i][j][k][0].keys())
                for item in cnt_mat[disease_id][i][j][k][0].keys():
                    if item not in alter_med:
                        alter_med[item] = cnt_mat[disease_id][i][j][k][0][item]
                    else :
                        alter_med[item] += cnt_mat[disease_id][i][j][k][0][item]

                    # maybe there's no unconf (unconf_val = 0)
                    if item not in med_unconfident_cnt[disease_id][i][j][k].keys():
                        med_unconf[item] = 0
                    else :
                        if item not in med_unconf:
                            med_unconf[item] = med_unconfident_cnt[disease_id][i][j][k][item]
                        else :
                            med_unconf[item] += med_unconfident_cnt[disease_id][i][j][k][item]

                conditional_deno += cnt_mat[disease_id][i][j][k][1]

    # di_prob = conditional_numer / conditional_deno
    # print(di_prob)

    # med_prob format: [(med_name,prob)]
    med_prob = []

    for item in alter_med.keys():
        med_name = med_en_name_list[med_id_list.index(item)]
        if med_unconf[item] < usable_threshold:
            med_prob.append([item,med_name,alter_med[item] / conditional_deno])

    mmm = [x[-1] for x in med_prob]
    print(mmm)
    print(sum(mmm))

    # find the corresponding icd code given disease chinese name
    id = -1
    for item in di_name_mat.values.tolist():
        if item[1] == session['chosen_disease']:
            id = item[0]
            break

    di_col = sorted(med_prob,key = lambda s: s[-1],reverse = True)

    # med_name = list(med_name_dt.loc[:,'name'])

    med_name_prob = []

    # insert pair (med_name,probability)
    
    for i in range(min(10,len(di_col))):
        # print(med_prob[i][1])
        # print(type(med_prob[i][1]))
        
        med_name_prob.append([di_col[i][0],di_col[i][1],di_col[i][2]])

    # session['med'] = di_col
    # session['med_name'] = list(med_name_dt.loc[:,'name'])

    # plot the top 10 medicine as png (bar chart)
    print(med_name_prob)
    print(type(med_name_prob))
    med_img = bar_chart_plot(med_name_prob,'Med','Prob','Top 10 medicine',20,'top10med')

    

    # save their plot
    age_img = bar_chart_plot(age_dist,'Age','Number','Age distribution',90,'age_dist')
    gender_img = bar_chart_plot(gender_dist,'Gender','Number','gender distribution',0,'gender_dist')
    dept_img = bar_chart_plot(dept_dist,'Department','Number','Dept distribution',0,'dept_dist')

    # origin html: <img src="{{url_for('static',filename='top10med.png')}}">

    # record medicine id
    session['top_10_med'] = [x[1] for x in med_name_prob]


    return render_template("med_result.html",di_name = session['chosen_disease'],med = med_name_prob,med_form=med_res_form,med_img = med_img,age_img = age_img,dept_img = dept_img, gender_img = gender_img)


@med_.route('/med_response',methods=["GET","POST"])
def med_response():
    if request.method == "POST":
        print("post")
        return redirect(url_for('main'))

    return render_template('med_res_result.html',di_name=session['chosen_disease'],result=session['response'])