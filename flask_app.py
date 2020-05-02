import flask
import sys
import os
import time
from queue import Queue
import random
import threading
from PIL import Image
import json
import io
import uuid
import base64
import copy
import matplotlib
matplotlib.use('Agg') # because https://stackoverflow.com/questions/49921721/runtimeerror-main-thread-is-not-in-main-loop-with-matplotlib-and-flask
import matplotlib.pyplot as plt
import datetime



#from flask_abm import *
import flask_abm

print("*"*70)
print("Running now ",datetime.datetime.now(),"*"*30)

id_read_from_form=1
user_counter = 1
global_diagnostic_strings = "START<br>"

global_number_diff_each_image = 1


### You create a Queue and start a scheduler, Start flask after that
def run_scheduler(app):
    global global_diagnostic_strings
    #print("run_scheduler")
    sleep_time = 1.5
    while True:
        time.sleep(sleep_time)
        #print('jobs Completed ->',app.jobs_completed)

        if app.jobs_to_be_processed_queue.qsize() > 0:
            print("noticed job in queue, lets process it! ", datetime.datetime.now())
            #print(f"qsize={app.jobs_to_be_processed_queue.qsize()}")
            global_diagnostic_strings += "queue size = "+str(app.jobs_to_be_processed_queue.qsize()) + "<br>"
            next_job_name = app.jobs_to_be_processed_queue.get()
            #print(f"No jobs being processed so scheduler will start processing the next image {next_job_name} from the queue")
            app.function_to_actually_crunch_the_numbers(next_job_name, app)
        else: # no jobs in queue - make sure we zap arrays
            app.global_job_dictionary.clear()
            app.jobs_completed.clear()
            app.job_processing_status_dict.clear()
            app.active_processing_threads.clear()


def function_to_actually_crunch_the_numbers(job_name, app):
    print("function_to_actually_crunch_the_numbers start ", datetime.datetime.now())
    global global_diagnostic_strings,global_number_diff_each_image
    global_number_diff_each_image += 1
    huge_number = 100


    flask_abm.NUM_AGENTS = int(app.global_job_dictionary[job_name]["nag"])
    flask_abm.TYPICAL_STARTING_MONEY = float(app.global_job_dictionary[job_name]["tsm"])
    flask_abm.NUM_AGENTS_FOR_PRICE_COMPARISON = int(app.global_job_dictionary[job_name]["npc"])
    flask_abm.TYPICAL_GOODS_MADE_PER_DAY = float(app.global_job_dictionary[job_name]["tgpd"])
    flask_abm.econ_iters_to_do_this_time = int(app.global_job_dictionary[job_name]["nir"])
    flask_abm.MAXIMUM_STOCK = float(app.global_job_dictionary[job_name]["maxst"])
    flask_abm.TYPICAL_DAYS_BETWEEN_PRICE_CHANGES = float(app.global_job_dictionary[job_name]["tdpc"])
    flask_abm.TYPICAL_DAYS_BETWEEN_PURCHASES = float(app.global_job_dictionary[job_name]["tdbp"])
    flask_abm.TYPICAL_STARTING_PRICE = float(app.global_job_dictionary[job_name]["tsp"])
    img_name =     app.global_job_dictionary[job_name]["resfilename"]

    global_diagnostic_strings += "Inside run_model() TYPICAL_STARTING_PRICE={a:.2f}<br>".format(a=flask_abm.TYPICAL_STARTING_PRICE)
    global_diagnostic_strings += "About to call initialise_model()<br>"
    flask_abm.initialise_model()
    global_diagnostic_strings += "Called initialise_model()<br>"

    global_diagnostic_strings += "job "+job_name+" using "+ str(flask_abm.econ_iters_to_do_this_time) +" agents<br>"

    print("loop start ", datetime.datetime.now())

    for i in range(0, flask_abm.econ_iters_to_do_this_time):
        flask_abm.iterate()
        flask_abm.append_current_state_to_history()

        perc = (i+1)*100/flask_abm.econ_iters_to_do_this_time
        if int(perc) % 5 == 0:
            app.job_processing_status_dict[job_name] = str(perc)

    print("loop done ", datetime.datetime.now())

    flask_abm.collect_data_for_plotting_histograms()
    print("collect data done ", datetime.datetime.now())

    do_all_plots(job_name, app)
    print("post done ", datetime.datetime.now())

    plt.savefig("static/"+img_name)
    print("save done ", datetime.datetime.now())

    #for i in range(huge_number):
    #    # some maths
    #    percentage_done = str((i+1)*100/huge_number)
    #    app.job_processing_status_dict[job_name] = percentage_done
    #    time.sleep(.2)

    app.job_processing_status_dict[job_name] = str(100.0)  # done!

    R = random.randint(0,256)
    G = random.randint(0,256)
    B = random.randint(0,256)
    img = Image.new('RGB', (60, 30), color =(R,G,B))
    chunk_of_ram=io.BytesIO()

    img.save(chunk_of_ram, "jpeg")
    app.jobs_completed[job_name] = {"status":1,"file": chunk_of_ram}
    #print(f"IC from function: {app.jobs_completed} **************************")
    #print("Error chase A")

    if app.job_processing_status_dict.get("num_jobs_completed",False):
        #print("Error chase B - if was true")
        global_diagnostic_strings += "app.job_processing_status_dict['num_jobs_completed'] incremented from "+str(app.job_processing_status_dict["num_jobs_completed"])+"<br>"
        app.job_processing_status_dict["num_jobs_completed"] += 1
    else:
        #print("Error chase C - if was false")
        app.job_processing_status_dict["num_jobs_completed"] = 1
        global_diagnostic_strings += "app.job_processing_status_dict['num_jobs_completed'] being set to 1<br>"
    print("Error chase D")

    del app.job_processing_status_dict[job_name]     # The del keyword is used to delete objects.
    #print("Error chase E")
    #del app.global_job_dictionary[job_name]
    #print("Error chase F")
    #print("About to return [",img_name,"]")
    #print("Error chase G")
    #dic = {"resimname":"dummievaluebugchasing.png"}
    #print("Error chase G2")

    #ret = flask.jsonify(dic)

    #print("Error chase H")
    #return ret
    #return flask.jsonify({"resimname":"dummievaluebugchasing.png"}) #process sucessful
    #return flask.jsonify({"resimname":img_name}) #process sucessful

class Webserver(flask.Flask):
    def __init__(self,*args,**kwargs):
        scheduler_func = kwargs["scheduler_func"]
        function_to_actually_crunch_the_numbers = kwargs["function_to_actually_crunch_the_numbers"]
        queue_MAXSIZE = kwargs["queue_MAXSIZE"]
        del kwargs["function_to_actually_crunch_the_numbers"], kwargs["scheduler_func"], kwargs["queue_MAXSIZE"]
        super(Webserver, self).__init__(*args, **kwargs)
        self.start_time = time.strftime("%d/%m/%Y %H:%M")
        self.queue_MAXSIZE = queue_MAXSIZE
        self.active_processing_threads = []
        self.job_processing_status_dict = {}
        self.global_job_dictionary = {}
        self.jobs_completed = {}
        self.jobs_to_be_processed_queue = Queue(maxsize=queue_MAXSIZE)
        self.function_to_actually_crunch_the_numbers = function_to_actually_crunch_the_numbers
        self.scheduler_thread = threading.Thread(target=scheduler_func, args=(self,),daemon=True)
        self.global_image_number = 1

app = Webserver(__name__,
                  template_folder="./templates",
                  static_folder="./",
                  static_url_path='',
                  scheduler_func = run_scheduler,
                  function_to_actually_crunch_the_numbers = function_to_actually_crunch_the_numbers,
                  queue_MAXSIZE = 20,
                 )

@app.route("/",methods=["GET"])
def render_basic_whole_webpage():
    global global_diagnostic_strings
    global user_counter

    formlist = copy.deepcopy(global_formlist)

    #print("render_basic_whole_webpage()")

    id_read_from_form = -1
    user_counter += 1

    if not flask.current_app.scheduler_thread.isAlive():
        flask.current_app.scheduler_thread.start()

    if id_read_from_form == -1:
        id_for_hidden_thing = user_counter
    else:
        id_for_hidden_thing = id_read_from_form

    global_diagnostic_strings += "render_basic_whole_webpage() idrff="+str(id_read_from_form)+"<br>"


    fname="zilch"

    return flask.render_template('bernardo.htm',
                                        queue_size = flask.current_app.jobs_to_be_processed_queue.qsize(),
                                        max_queue_size = flask.current_app.queue_MAXSIZE ,
                                        being_processed = len(flask.current_app.active_processing_threads),
                                        total = flask.current_app.job_processing_status_dict.get("num_jobs_completed",0),
                                        start_time = flask.current_app.start_time,
                                        distr = global_diagnostic_strings,


                                        thestring='/static/'+fname,
                                        defid=id_for_hidden_thing,
                                        params1="",#url_for('/static'),
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

@app.route("/begin_crunching",methods=["POST"])
def server_process_request_to_begin_crunching():
    global global_diagnostic_strings,global_number_diff_each_image
    global id_read_from_form
    global_number_diff_each_image+=1

    job_name = json.loads(flask.request.data)["job_name"]
    customer_id = json.loads(flask.request.data)["CustId"]

    app.global_job_dictionary[job_name] = {
                                        "nag":json.loads(flask.request.data)["nag"],
                                        "tsm":json.loads(flask.request.data)["tsm"],
                                        "npc":json.loads(flask.request.data)["npc"],
                                        "tgpd":json.loads(flask.request.data)["tgpd"],
                                        "nir":json.loads(flask.request.data)["nir"],
                                        "maxst":json.loads(flask.request.data)["maxst"],
                                        "tdpc":json.loads(flask.request.data)["tdpc"],
                                        "tdbp":json.loads(flask.request.data)["tdbp"],
                                        "tsp":json.loads(flask.request.data)["tsp"],
                                        "avsp":json.loads(flask.request.data)["avsp"],
                                        "sp":json.loads(flask.request.data)["sp"],
                                        "sfs":json.loads(flask.request.data)["sfs"],
                                        "gp":json.loads(flask.request.data)["gp"],
                                        "mon":json.loads(flask.request.data)["mon"],
                                        "wellmon":json.loads(flask.request.data)["wellmon"],
                                        "wellcon":json.loads(flask.request.data)["wellcon"],
                                        "wellmoncon":json.loads(flask.request.data)["wellmoncon"],
                                        "dtfe":json.loads(flask.request.data)["dtfe"],
                                        "uniquenum":global_number_diff_each_image,
                                        "resfilename":"res"+str(global_number_diff_each_image)+"_"+str(random.randint(10000,90000))+".png"  # the random number is just to avoid browser cache
                                        }


    global_diagnostic_strings += "server_process_request_to_begin_crunching() "+str(customer_id)+"<br>"

    if (flask.current_app.jobs_to_be_processed_queue.qsize() >= flask.current_app.queue_MAXSIZE ):
        while(not flask.current_app.jobs_to_be_processed_queue.empty()):
            flask.current_app.jobs_to_be_processed_queue.get()

    requestedImage_status = {"name":job_name, "id":uuid.uuid1(), "diagstring": global_diagnostic_strings}

    flask.current_app.jobs_to_be_processed_queue.put(job_name)
    return flask.jsonify(requestedImage_status)

@app.route("/get_progress",methods=["POST"])
def server_asked_to_return_progress():
    global global_diagnostic_strings
    if len(global_diagnostic_strings) > 10000:
        global_diagnostic_strings="RESET"

    #print(f'Current job being processed: {flask.current_app.job_processing_status_dict}')
    #print(f'Current jobs completed: {flask.current_app.jobs_completed}')
    #print("queue is: ",list(app.jobs_to_be_processed_queue.queue))
    job_name = json.loads(flask.request.data)["job_name"]
    is_finished = flask.current_app.jobs_completed.get(job_name,{"status":0,"file": ''})["status"]
    customer_id = json.loads(flask.request.data)["CustId"]
    global_diagnostic_strings += "server_asked_to_return_progress() in="+job_name+" cud="+str(customer_id)+" prog="+flask.current_app.job_processing_status_dict.get(job_name,"0")+"<br>"
    requestedImage_status = {
            "is_finished": is_finished,
            "progress":    flask.current_app.job_processing_status_dict.get(job_name,"0"),
            "diagstring": global_diagnostic_strings,
            "jobsaheadofus":app.jobs_to_be_processed_queue.qsize(),
            "inqueue":list(app.jobs_to_be_processed_queue.queue)
            }
    return flask.jsonify(requestedImage_status) #job_processing_status_dict[job_name]})

@app.route("/get_image",methods=["POST"])
def get_processed_image():
    global global_diagnostic_strings
    job_name = json.loads(flask.request.data)["job_name"]
    customer_id = json.loads(flask.request.data)["CustId"]
    file_bytes = flask.current_app.jobs_completed[job_name]["file"] #open("binary_image.jpeg", 'rb').read()
    file_bytes = base64.b64encode(file_bytes.getvalue()).decode()
    flask.current_app.jobs_completed.clear()
    global_diagnostic_strings += "get_processed_image() in="+job_name+" cud="+str(customer_id)+"<br>"
    return flask.jsonify(
                            {job_name:file_bytes,
                            "diagstring": global_diagnostic_strings,
                            "resimname":app.global_job_dictionary[job_name]["resfilename"]
                            }) #job_processing_status_dict[job_name]})

def shall_we_show_this_graph(short_description,local_formlist):
    #global flask_abm.global_diagnostic_strings

    answer = user_value_of_form_var(short_description,local_formlist)

    if answer == "True":
        flask_abm.global_diagnostic_strings+="T"
        return True
    else:
        flask_abm.global_diagnostic_strings+="F"
        return False

def do_all_plots(job_name, app):
    print("do_all_plots entry ", datetime.datetime.now())
    sum = 0
    for i in range(10000):
        sum += 99
    print("do_all_plots entry post speedtest ", datetime.datetime.now())
    #print("do_all_plots: A")
    #global flask_abm.global_diagnostic_strings
    #if not colab:
    #    save_GUI_set_constants()
    # prep
    #plt.rcParams["figure.figsize"] = (18,12)

    plt.cla()
    plt.clf()


    my_dpi=96
    #print("do_all_plots: A2")
    plt.subplots(figsize=(1200/my_dpi, 700/my_dpi), dpi=my_dpi)
    #print("do_all_plots: A3")
    #plt.subplots_adjust(top=.98)
    #plt.subplots_adjust(bottom=.02)
    #plt.subplots_adjust(right=.98)
    #plt.subplots_adjust(left=.07)

    # count selected graphs
    numrows = 0

    #print("do_all_plots: B")

    flask_abm.global_diagnostic_strings+="["
    for st in ["avsp","sp","sfs","gp","mon","wellmon","wellcon","wellmoncon","dtfe"]:
        if int(app.global_job_dictionary[job_name][st]): #shall_we_show_this_graph(st,local_formlist):
            numrows += 1
    flask_abm.global_diagnostic_strings += "] numrows=" + str(numrows) + "<br>"

    numrows += 1  # for the row of histograms at the bottom
    current_row = 1
    #print("do_all_plots: C")

    print("do_all_plots A ", datetime.datetime.now())

    # show selected graphs
    if int(app.global_job_dictionary[job_name]["avsp"]): #shall_we_show_this_graph("avsp",local_formlist):
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

    print("do_all_plots B ", datetime.datetime.now())

    if int(app.global_job_dictionary[job_name]["sp"]): #shall_we_show_this_graph("sp",local_formlist):
        plt.subplot(numrows,1,current_row)
        plt.ylabel(f"Agent{flask_abm.agent_to_diagnose}\nselling\nprice")

        plt.plot(list(range(flask_abm.econ_iters_to_do_this_time)), flask_abm.history_of_agents_price, ",")
        current_row += 1

    if int(app.global_job_dictionary[job_name]["sfs"]): #shall_we_show_this_graph("sfs",local_formlist):
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

    if int(app.global_job_dictionary[job_name]["dtfe"]): #shall_we_show_this_graph("dtfe",local_formlist):
        plt.subplot(numrows,1,current_row)
        plt.ylabel(f"Agent{flask_abm.agent_to_diagnose}\ndays till\nstock\nfull/empty")
        axes = plt.gca()
        axes.set_ylim([0, 25])
        plt.plot(list(range(flask_abm.econ_iters_to_do_this_time)), flask_abm.history_of_agents_days_to_full, ",", color="#ff0000")
        plt.plot(list(range(flask_abm.econ_iters_to_do_this_time)), flask_abm.history_of_agents_days_to_empty, ",", color="#00ff00")
        current_row += 1

    if int(app.global_job_dictionary[job_name]["gp"]): #shall_we_show_this_graph("gp",local_formlist):
        plt.subplot(numrows,1,current_row)
        plt.ylabel(f"Agent{flask_abm.agent_to_diagnose}\ngoods\npurchased")
        plt.plot(list(range(flask_abm.econ_iters_to_do_this_time)), flask_abm.history_of_agents_goods_purchased, ",")
        current_row += 1

    if int(app.global_job_dictionary[job_name]["mon"]): #shall_we_show_this_graph("mon",local_formlist):
        plt.subplot(numrows,1,current_row)
        plt.ylabel(f"Agent{flask_abm.agent_to_diagnose}\nour money")
        plt.plot(list(range(flask_abm.econ_iters_to_do_this_time)), flask_abm.history_of_agents_our_money, ",")
        current_row += 1

    if int(app.global_job_dictionary[job_name]["wellmon"]): #shall_we_show_this_graph("wellmon",local_formlist):
        plt.subplot(numrows,1,current_row)
        plt.ylabel(f"Agent{flask_abm.agent_to_diagnose}\nwellbeing\nfrom money")
        plt.plot(list(range(flask_abm.econ_iters_to_do_this_time)), flask_abm.history_of_agents_well_money, ",")
        current_row += 1

    if int(app.global_job_dictionary[job_name]["wellcon"]): #shall_we_show_this_graph("wellcon",local_formlist):
        plt.subplot(numrows,1,current_row)
        plt.ylabel(f"Agent{flask_abm.agent_to_diagnose}\nwellbeing\nfrom\nconsumption")
        plt.plot(list(range(flask_abm.econ_iters_to_do_this_time)), flask_abm.history_of_agents_well_coms, ",")
        current_row += 1

    if int(app.global_job_dictionary[job_name]["wellmoncon"]): #shall_we_show_this_graph("wellmoncon",local_formlist):
        plt.subplot(numrows,1,current_row)
        plt.ylabel(f"Agent{flask_abm.agent_to_diagnose}\nwellbeing\nfrom\nmon+con")
        plt.plot(list(range(flask_abm.econ_iters_to_do_this_time)), flask_abm.history_of_agents_well_money_plus_cons, ",")
        current_row += 1

    print("do_all_plots C ", datetime.datetime.now())

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
    print("do_all_plots D ", datetime.datetime.now())

def run_model(local_formlist):
    #print("run model: A")
    #global flask_abm.global_diagnostic_strings
    #plt.close()

    flask_abm.global_diagnostic_strings += "Inside run_model() TYPICAL_STARTING_PRICE={a:.2f}<br>".format(a=flask_abm.TYPICAL_STARTING_PRICE)
    flask_abm.global_diagnostic_strings += "About to call initialise_model()<br>"
    flask_abm.initialise_model()
    flask_abm.global_diagnostic_strings += "Called initialise_model()<br>"

    for i in range(0, flask_abm.econ_iters_to_do_this_time):
        flask_abm.iterate()
        flask_abm.append_current_state_to_history()

    print("??loop done ", datetime.datetime.now())
    flask_abm.collect_data_for_plotting_histograms()

    do_all_plots(local_formlist)
    print("??plots done ", datetime.datetime.now())


flask_abm.initialise_model()
flask_abm.all_prices_as_list.clear()
flask_abm.stock_for_sale_as_list.clear()
flask_abm.our_money_as_list.clear()
flask_abm.num_units_purchased_on_last_shopping_trip_as_list.clear()
flask_abm.num_units_available_on_last_shopping_trip_as_list.clear()

global_formlist = []

#app = Flask(__name__)
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

@app.route("/a_dummie_not_root", methods=["POST", "GET"])
def home():
    global user_counter,has_been_executed,id_read_from_form,diagnostic_string,post_ctr,get_ctr, pg_hist, global_formlist

    cr_diagnostic_cr("home("+flask.request.method+")")

    formlist = copy.deepcopy(global_formlist)
    diagnostic_string = ""
    id_read_from_form = -1

    all_vars_good = True
    if flask.request.method == 'POST':
        #print("server detects user just clicked go")
        for fi in formlist:
            try:
                fi.user_value = flask.request.form[fi.form_var]
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

        id_read_from_form = str(flask.request.form['custId'])
        #print("Server has chewed on the form sent")

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

        if id_read_from_form == -1:
            flask_abm.global_diagnostic_strings += "id_read_from_form == -1 so not calling run_model()<br>"
        else:

            flask_abm.global_diagnostic_strings += ("Calling run_model() iters="+str(flask_abm.econ_iters_to_do_this_time)+" tsp="+str(flask_abm.TYPICAL_STARTING_PRICE)+" tsm="+str(flask_abm.TYPICAL_STARTING_MONEY)+" output to "+fname+"<br>")

            #print("About to call run model")
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
    file_list = os.listdir("static/")
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

    return flask.render_template("index.htm",
        thestring='/static/'+fname,
        defid=id_for_hidden_thing,
        params1="",#url_for('/static'),
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




'''
"nag"
"tsm"
"npc"
"tgpd"
"nir"
"maxst"
"tdpc"
"tdbp"
"tsp"
"avsp"
"sp"
"sfs"
"gp"
"mon"
"wellmon"
"wellcon"
"wellmoncon"
"dtfe"
'''



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



print("*"*70)
print("Running now II",datetime.datetime.now(),"*"*30)

if __name__ == "__main__": # I think this is false on pythonanywhere.com
    print("Self launch ",datetime.datetime.now())
    app.run(debug=True)

