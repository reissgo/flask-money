from flask import Flask, render_template, request, Response, jsonify
import sys
import os
import time

import matplotlib
matplotlib.use('Agg') # because https://stackoverflow.com/questions/49921721/runtimeerror-main-thread-is-not-in-main-loop-with-matplotlib-and-flask
import matplotlib.pyplot as plt
import copy



#from flask_abm import *
import flask_abm


user_form_diagnostic_string = "Not set yet"



def shall_we_show_this_graph(short_description,local_formlist):
    #global flask_abm.global_diagnostic_strings

    answer = user_value_of_form_var(short_description,local_formlist)

    if answer == "True":
        flask_abm.global_diagnostic_strings+="T"
        return True
    else:
        flask_abm.global_diagnostic_strings+="F"
        return False

def do_all_plots(local_formlist):
    print("do_all_plots: A")
    #global flask_abm.global_diagnostic_strings
    #if not colab:
    #    save_GUI_set_constants()
    # prep
    #plt.rcParams["figure.figsize"] = (18,12)

    #plt.cla()
    #plt.clf()


    my_dpi=96
    print("do_all_plots: A2")
    plt.subplots(figsize=(1200/my_dpi, 700/my_dpi), dpi=my_dpi)
    print("do_all_plots: A3")
    #plt.subplots_adjust(top=.98)
    #plt.subplots_adjust(bottom=.02)
    #plt.subplots_adjust(right=.98)
    #plt.subplots_adjust(left=.07)

    # count selected graphs
    numrows = 0

    print("do_all_plots: B")

    flask_abm.global_diagnostic_strings+="["
    for st in ["avsp","sp","sfs","gp","mon","wellmon","wellcon","wellmoncon","dtfe"]:
        if shall_we_show_this_graph(st,local_formlist):
            numrows += 1
    flask_abm.global_diagnostic_strings += "] numrows=" + str(numrows) + "<br>"

    numrows += 1  # for the row of histograms at the bottom
    current_row = 1
    print("do_all_plots: C")

    # show selected graphs
    if shall_we_show_this_graph("avsp",local_formlist):
        plt.subplot(numrows,1,current_row)
        plt.ylabel("Average\nselling price")
        plt.plot(list(range(flask_abm.econ_iters_to_do_this_time)), flask_abm.history_of_average_current_selling_price, ",")

        frac = .666
        maxrhs = max(flask_abm.history_of_average_current_selling_price[int(flask_abm.econ_iters_to_do_this_time*frac):])
        minrhs = min(flask_abm.history_of_average_current_selling_price[int(flask_abm.econ_iters_to_do_this_time*frac):])
        plt.text(flask_abm.econ_iters_to_do_this_time*frac, minrhs, "Range {:.1f}%".format((maxrhs-minrhs)*100/minrhs))
        plt.plot([flask_abm.econ_iters_to_do_this_time*frac, flask_abm.econ_iters_to_do_this_time], [maxrhs,maxrhs], color="#00ff00")
        plt.plot([flask_abm.econ_iters_to_do_this_time*frac, flask_abm.econ_iters_to_do_this_time], [minrhs,minrhs], color="#00ff00")

        current_row += 1

    if shall_we_show_this_graph("sp",local_formlist):
        plt.subplot(numrows,1,current_row)
        plt.ylabel(f"Agent{flask_abm.agent_to_diagnose}\nselling\nprice")

        plt.plot(list(range(flask_abm.econ_iters_to_do_this_time)), flask_abm.history_of_agents_price, ",")
        current_row += 1

    if shall_we_show_this_graph("sfs",local_formlist):
        plt.subplot(numrows,1,current_row)
        plt.ylabel(f"Agent{flask_abm.agent_to_diagnose}\nstock\nfor sale")
        axes = plt.gca()
        axes.set_ylim([0, max(max(flask_abm.history_of_agents_stock_for_sale), flask_abm.MAXIMUM_STOCK * 1.2)])
        plt.text(0, flask_abm.MAXIMUM_STOCK, "Max stock")
        plt.plot(list(range(flask_abm.econ_iters_to_do_this_time)), flask_abm.history_of_agents_stock_for_sale, ",")
        plt.plot([0, flask_abm.econ_iters_to_do_this_time], [flask_abm.MAXIMUM_STOCK, flask_abm.MAXIMUM_STOCK],color="#00ff00")
        start = -1
        for i in range(0, flask_abm.econ_iters_to_do_this_time):
            if flask_abm.history_of_agents_stock_for_sale[i] >= flask_abm.MAXIMUM_STOCK:
                if start == -1:
                    start = i
            if start >= 0 and flask_abm.history_of_agents_stock_for_sale[i] < flask_abm.MAXIMUM_STOCK:
               plt.plot([start, i], [flask_abm.MAXIMUM_STOCK, flask_abm.MAXIMUM_STOCK], color="#ff0000", linewidth=3)
               start = -1
        current_row += 1

    if shall_we_show_this_graph("dtfe",local_formlist):
        plt.subplot(numrows,1,current_row)
        plt.ylabel(f"Agent{flask_abm.agent_to_diagnose}\ndays till\nstock\nfull/empty")
        axes = plt.gca()
        axes.set_ylim([0, 25])
        plt.plot(list(range(flask_abm.econ_iters_to_do_this_time)), flask_abm.history_of_agents_days_to_full, ",", color="#ff0000")
        plt.plot(list(range(flask_abm.econ_iters_to_do_this_time)), flask_abm.history_of_agents_days_to_empty, ",", color="#00ff00")
        current_row += 1

    if shall_we_show_this_graph("gp",local_formlist):
        plt.subplot(numrows,1,current_row)
        plt.ylabel(f"Agent{flask_abm.agent_to_diagnose}\ngoods\npurchased")
        plt.plot(list(range(flask_abm.econ_iters_to_do_this_time)), flask_abm.history_of_agents_goods_purchased, ",")
        current_row += 1

    if shall_we_show_this_graph("mon",local_formlist):
        plt.subplot(numrows,1,current_row)
        plt.ylabel(f"Agent{flask_abm.agent_to_diagnose}\nour money")
        plt.plot(list(range(flask_abm.econ_iters_to_do_this_time)), flask_abm.history_of_agents_our_money, ",")
        current_row += 1

    if shall_we_show_this_graph("wellmon",local_formlist):
        plt.subplot(numrows,1,current_row)
        plt.ylabel(f"Agent{flask_abm.agent_to_diagnose}\nwellbeing\nfrom money")
        plt.plot(list(range(flask_abm.econ_iters_to_do_this_time)), flask_abm.history_of_agents_well_money, ",")
        current_row += 1

    if shall_we_show_this_graph("wellcon",local_formlist):
        plt.subplot(numrows,1,current_row)
        plt.ylabel(f"Agent{flask_abm.agent_to_diagnose}\nwellbeing\nfrom\nconsumption")
        plt.plot(list(range(flask_abm.econ_iters_to_do_this_time)), flask_abm.history_of_agents_well_coms, ",")
        current_row += 1

    if shall_we_show_this_graph("wellmoncon",local_formlist):
        plt.subplot(numrows,1,current_row)
        plt.ylabel(f"Agent{flask_abm.agent_to_diagnose}\nwellbeing\nfrom\nmon+con")
        plt.plot(list(range(flask_abm.econ_iters_to_do_this_time)), flask_abm.history_of_agents_well_money_plus_cons, ",")
        current_row += 1

    # show histograms

    plt.subplot(numrows, 4, (numrows-1) * 4 + 1)
    plt.ylabel("Selling Price")
    plt.hist(flask_abm.all_prices_as_list, range=(0, max(flask_abm.all_prices_as_list) * 1.1), bins=20)

    plt.subplot(numrows, 4, (numrows-1) * 4 + 2)
    plt.ylabel("Stock for sale")
    plt.hist(flask_abm.stock_for_sale_as_list, range=(0, max(flask_abm.stock_for_sale_as_list) * 1.1), bins=20)

    plt.subplot(numrows, 4, (numrows-1) * 4 + 3)
    plt.ylabel("Money")
    plt.hist(flask_abm.our_money_as_list, range=(0, max(flask_abm.our_money_as_list) * 1.1), bins=20)

    plt.subplot(numrows, 4, (numrows-1) * 4 + 4)
    plt.ylabel("Purchased")
    plt.hist(flask_abm.num_units_purchased_on_last_shopping_trip_as_list, range=(0, max(flask_abm.num_units_purchased_on_last_shopping_trip_as_list) * 1.3), bins=20)

    #plt.subplot(numrows, 5, (numrows-1) * 5 + 5)
    #plt.ylabel("Available")
    #plt.hist(flask_abm.num_units_available_on_last_shopping_trip_as_list, range=(0, max(flask_abm.num_units_available_on_last_shopping_trip_as_list) * 1.3), bins=20)

    #plt.show()



def run_model(local_formlist):
    print("run model: A")
    #global flask_abm.global_diagnostic_strings
    #plt.close()
    print("run model: B")
    flask_abm.global_diagnostic_strings += "Inside run_model() TYPICAL_STARTING_PRICE={a:.2f}<br>".format(a=flask_abm.TYPICAL_STARTING_PRICE)

    flask_abm.global_diagnostic_strings += "About to call initialise_model()<br>"
    print("run model: C")

    flask_abm.initialise_model()
    flask_abm.global_diagnostic_strings += "Called initialise_model()<br>"

    print("About to loop")
    for i in range(0, flask_abm.econ_iters_to_do_this_time):
        flask_abm.iterate()
        flask_abm.append_current_state_to_history()
    print("Loop done")

    flask_abm.collect_data_for_plotting_histograms()
    print("run model: D")
    do_all_plots(local_formlist)
    print("run model: E")

flask_abm.initialise_model()
flask_abm.all_prices_as_list.clear()
flask_abm.stock_for_sale_as_list.clear()
flask_abm.our_money_as_list.clear()
flask_abm.num_units_purchased_on_last_shopping_trip_as_list.clear()
flask_abm.num_units_available_on_last_shopping_trip_as_list.clear()

global_formlist = []

app = Flask(__name__)
user_counter = 1
post_ctr = 0
get_ctr = 0
pg_hist="Start:"

include_xy_test_code = False
id_read_from_form=1
has_been_executed="not yet"
diagnostic_string="...  "

class FormItemStartSetup:
    def __init__(self, text, thetype, form_var, value, minv, maxv):

        # these are fixed forever
        self.text_to_display = text
        self.form_var = form_var
        self.type = thetype # int / float / flag
        self.start_value = value
        self.minv = minv
        self.maxv = maxv

        self.user_error_message = ""
        self.user_error_flag = False
        self.user_value = value

def idx_of_form_var(fv):
    for i, fi in enumerate(global_formlist):
        if fi.form_var == fv:
            return i
    return -99

def user_value_of_form_var(fv,fl):
    return fl[idx_of_form_var(fv)].user_value

def cr_diagnostic_cr(text):  # enforce <br> at start and end
    #global flask_abm.global_diagnostic_strings
    if flask_abm.global_diagnostic_strings[-4:] != "<br>" and len(flask_abm.global_diagnostic_strings) > 0:
        flask_abm.global_diagnostic_strings+="<br>"
    flask_abm.global_diagnostic_strings += text+"<br>"






@app.route("/", methods=["POST", "GET"])
def home():
    global user_counter,has_been_executed,id_read_from_form,diagnostic_string,post_ctr,get_ctr, pg_hist, global_formlist

    cr_diagnostic_cr("home("+request.method+")")

    formlist = copy.deepcopy(global_formlist)
    diagnostic_string = ""
    id_read_from_form = -1

    all_vars_good = True
    if request.method == 'POST':
        print("server detects user just clicked go")
        for fi in formlist:
            try:
                fi.user_value = request.form[fi.form_var]
            except:
                fi.user_value= "???"

            if fi.type == "flag" and fi.user_value != "???": # When submitting an HTML form, unchecked checkboxes do not send any data. On Flask's side, there will not be a key in form, since no value was received.
                    fi.user_value = "True"

            if fi.type == "float":
                try:
                    float(fi.user_value)
                except:
                    fi.user_error_message = "Bad float"
                    all_vars_good = False
            elif fi.type == "int":
                try:
                    int(fi.user_value)
                except:
                    fi.user_error_message = "Bad integer"
                    all_vars_good = False

            if fi.type == "int" and fi.user_error_message == "" and fi.minv != "":
                if int(fi.user_value) < int(fi.minv):
                    fi.user_error_message = "Must be at least "+fi.minv
                    all_vars_good = False
            if fi.type == "int" and fi.user_error_message == "" and fi.maxv != "":
                if int(fi.user_value) > int(fi.maxv):
                    fi.user_error_message = "Must be at most "+fi.maxv
                    all_vars_good = False
            if fi.type == "float" and fi.user_error_message == "" and fi.minv != "":
                if float(fi.user_value) < float(fi.minv):
                    fi.user_error_message = "Must be at least "+fi.minv
                    all_vars_good = False
            if fi.type == "float" and fi.user_error_message == "" and fi.maxv != "":
                if float(fi.user_value) > float(fi.maxv):
                    fi.user_error_message = "Must be at most "+fi.maxv
                    all_vars_good = False

        if int(user_value_of_form_var("npc",formlist)) > int(user_value_of_form_var("nag",formlist)):
            formlist[idx_of_form_var("npc")].user_error_message = "'"+formlist[idx_of_form_var("npc")].text_to_display+"' must be less than '"+formlist[idx_of_form_var("nag")].text_to_display+"'"
            formlist[idx_of_form_var("nag")].user_error_message = "'"+formlist[idx_of_form_var("npc")].text_to_display+"' must be less than '"+formlist[idx_of_form_var("nag")].text_to_display+"'"
            all_vars_good = False

        id_read_from_form = str(request.form['custId'])
        print("Server has chewed on the form sent")

    user_counter += 1

    cr_diagnostic_cr("id_read_from_form="+str(id_read_from_form)+" user_counter="+str(user_counter)+" all_vars_good="+str(all_vars_good))

    if all_vars_good:
        if include_xy_test_code:
            fname = "test"+str(id_read_from_form)+"_"+str(formlist[idx_of_form_var("form_x")].user_value)+"_"+str(formlist[idx_of_form_var("form_y")].user_value)+".png"
        else:
            fname="output_"+str(id_read_from_form)+"_"+str(time.time())+".png"

        plt.cla()
        plt.clf()

        #if include_xy_test_code:
        #    plt.plot([0,float(user_value_of_form_var("form_x",formlist))],[0,float(user_value_of_form_var("form_y",formlist))])
        #else:

        flask_abm.NUM_AGENTS = int(user_value_of_form_var("nag",formlist))
        flask_abm.TYPICAL_STARTING_MONEY = float(user_value_of_form_var("tsm",formlist))
        flask_abm.NUM_AGENTS_FOR_PRICE_COMPARISON = int(user_value_of_form_var("npc",formlist))
        flask_abm.TYPICAL_GOODS_MADE_PER_DAY = float(user_value_of_form_var("tgpd",formlist))
        flask_abm.econ_iters_to_do_this_time = int(user_value_of_form_var("nir",formlist))
        flask_abm.MAXIMUM_STOCK = float(user_value_of_form_var("maxst",formlist))
        flask_abm.TYPICAL_DAYS_BETWEEN_PRICE_CHANGES = float(user_value_of_form_var("tdpc",formlist))
        flask_abm.TYPICAL_DAYS_BETWEEN_PURCHASES = float(user_value_of_form_var("tdbp",formlist))
        flask_abm.TYPICAL_STARTING_PRICE = float(user_value_of_form_var("tsp",formlist))


        #user_form_diagnostic_string = user_value_of_form_var("dstr",formlist)
        #cr_diagnostic_cr("User string = ["+user_form_diagnostic_string+"]")

        if id_read_from_form == -1:
            flask_abm.global_diagnostic_strings += "id_read_from_form == -1 so not calling run_model()<br>"
        else:

            flask_abm.global_diagnostic_strings += ("Calling run_model() iters="+str(flask_abm.econ_iters_to_do_this_time)+" tsp="+str(flask_abm.TYPICAL_STARTING_PRICE)+" tsm="+str(flask_abm.TYPICAL_STARTING_MONEY)+" output to "+fname+"<br>")

            print("About to call run model")
            run_model(formlist)

            try:
                os.remove('static/'+fname)
            except:
                pass
            plt.savefig('static/'+fname)

    else:
        fname="test-no-xy.png"
        plt.plot([0,1],[0,1])
        plt.savefig('static/'+fname)

    now = time.time()
    file_list = os.listdir("static")
    for f in file_list:
        if f.find(".png") >= 0:
            age = int(now-os.path.getmtime("static/"+f))
            diagnostic_string += ("["+f+"]["+str(age)+"]  ")
            if age > (60*60):
                os.remove("static/"+f)
        else:
            diagnostic_string += ("["+f+"]["+"NOT-A-PNG!!"+"]  ")

    #if user_seen_before(id_read_from_form):
    #else:


    if id_read_from_form == -1:
        id_for_hidden_thing = user_counter
    else:
        id_for_hidden_thing = id_read_from_form

    return render_template("index.htm",
        thestring='/static/'+fname,
        defid=id_for_hidden_thing,
        params1="",#url_for('/mysite/static'),
        params2="Python version "+sys.version,
        params3="Matplotlib version "+matplotlib.__version__,
        params4="os.getcwd() is "+os.getcwd(),
        params5=str(user_counter),
        params6=diagnostic_string,
        fl=formlist,
        post_c=post_ctr,
        get_c=get_ctr,
        mds=flask_abm.global_diagnostic_strings,
        pg_hist=pg_hist,
        showpng=(str(id_read_from_form) != "-1")
        )

global_formlist.append(FormItemStartSetup(                         "Number of agents","int",         "nag",    "30", "2","100"))
global_formlist.append(FormItemStartSetup(                   "Typical starting money","float",       "tsm", "100.0", ".001","1000000"))
global_formlist.append(FormItemStartSetup(            "Num agents for price comparison","int",       "npc",     "3", "1","100"))
global_formlist.append(FormItemStartSetup(               "Typical goods made per day","float",      "tgpd",  "10.0", ".001","100"))
global_formlist.append(FormItemStartSetup(                "Num iterations to run (1000=1day)",       "int",   "nir","10000", "1","1000000"))
global_formlist.append(FormItemStartSetup(                                "Max stock","float",     "maxst",  "70.0", "1",""))
global_formlist.append(FormItemStartSetup(       "Typical days between price changes","float",      "tdpc",   "3.0", ".1","100"))
global_formlist.append(FormItemStartSetup(           "Typical days between purchases","float",      "tdbp",   "1.0", ".1","100"))
global_formlist.append(FormItemStartSetup(                   "Typical starting price","float",       "tsp",   "2.0", ".00001",""))


global_formlist.append(FormItemStartSetup(                            "Average selling price","flag",       "avsp",         "True", "",""))
global_formlist.append(FormItemStartSetup(                                    "Selling price","flag",       "sp",           "True", "",""))
global_formlist.append(FormItemStartSetup(                                   "Stock for sale","flag",       "sfs",          "True", "",""))
global_formlist.append(FormItemStartSetup(                                  "Goods purchased","flag",       "gp",           "True", "",""))
global_formlist.append(FormItemStartSetup(                               "Our stock of money","flag",       "mon",          "True", "",""))
global_formlist.append(FormItemStartSetup(                             "Wellbeing from money","flag",       "wellmon",      "False", "",""))
global_formlist.append(FormItemStartSetup(                       "Wellbeing from consumption","flag",       "wellcon",      "False", "",""))
global_formlist.append(FormItemStartSetup("Wellbeing from money + Wellbeing from consumption","flag",       "wellmoncon",   "False", "",""))
global_formlist.append(FormItemStartSetup(                             "Days till empty/full","flag",       "dtfe",         "False", "",""))




if __name__ == "__main__":
    app.run(debug=True)
