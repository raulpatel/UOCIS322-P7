"""
Replacement for RUSA ACP brevet time calculator
(see https://rusa.org/octime_acp.html)

"""

import flask
import os
from flask import request, redirect, url_for, request, render_template
from pymongo import MongoClient
import arrow  # Replacement for datetime, based on moment.js
import acp_times  # Brevet time calculations

import logging

###
# Globals
###
app = flask.Flask(__name__)
client = MongoClient('mongodb://' + os.environ['MONGODB_HOSTNAME'], 27017)
db = client.tododb
###
# Pages
###


@app.route("/")
@app.route("/index")
def index():
    app.logger.debug("Main page entry")
    return flask.render_template('calc.html')


@app.errorhandler(404)
def page_not_found(error):
    app.logger.debug("Page not found")
    return flask.render_template('404.html'), 404

@app.route('/clear/', methods=['GET'])
def clear():
    db.tododb.delete_many({})
    return redirect(url_for('index'))

@app.route('/submit/', methods=['POST'])
def submit():
    index = int(request.form['index'])
    km = float(request.form['km'])
    open_time = ""
    close_time = ""
    brev_dist = int(request.form['dist'])
    start_time = request.form['start']
    
    open_time = acp_times.open_time(km, brev_dist, arrow.get(start_time)).format('YYYY-MM-DDTHH:mm')
    close_time = acp_times.close_time(km, brev_dist, arrow.get(start_time)).format('YYYY-MM-DDTHH:mm')

    item_doc = {
        'index': index,
        'km': km,
        'open': open_time,
        'close': close_time
    }
    if request.form['km'] != "":
        #app.logger.debug("Submitting row into db with:\n\tIndex: " + str(index) + ", Controle dist: " + str(km) + ", Brevet dist: " + str(brev_dist) + ", Open time: " + open_time + ", and Close time: " + close_time)
        db.tododb.insert_one(item_doc)

    return redirect(url_for('index'))

@app.route('/display/', methods=['GET'])
def display():
    #rows = tuple(db.tododb.find())
    #app.logger.debug(rows.join(", "))
    """for i in range(len(rows)):
        rows[i] = flask.jsonify(result=rows[i])"""
    ind = request.args.get('ind', type=int)
    #app.logger.debug("Checking db for index: " + str(ind))
    row = db.tododb.find_one({'index': ind})
    if row:
        row = dict(row)
        row['_id'] = str(row['_id'])
        #app.logger.debug(row)
        return flask.jsonify(result=row) # render_template('calc.html', items=list(db.tododb.find()))
    else:
        #app.logger.debug("Cannot find index: " + str(ind) + " in the db")
        return ""

###############
#
# AJAX request handlers
#   These return JSON, rather than rendering pages.
#
###############
"""@app.route("/_calc_times")
def _calc_times():
    """"""
    Calculates open/close times from miles, using rules
    described at https://rusa.org/octime_alg.html.
    Expects one URL-encoded argument, the number of miles.
    """"""
    app.logger.debug("Got a JSON request")
    km = request.args.get('km', 999, type=float) // 1
    start = request.args.get('start')
    brev_dist = request.args.get('brev_dist', type=int)
    app.logger.debug("km={}".format(km))
    app.logger.debug("start={}".format(start))
    app.logger.debug("brev_dist={}".format(brev_dist))
    app.logger.debug("request.args: {}".format(request.args))
    valid = 1
    # FIXME!
    # Right now, only the current time is passed as the start time
    # and control distance is fixed to 200
    # You should get these from the webpage!
    if km <= (brev_dist * 1.2):
        open_time = acp_times.open_time(km, int(brev_dist), arrow.get(start)).format('YYYY-MM-DDTHH:mm')
        close_time = acp_times.close_time(km, int(brev_dist), arrow.get(start)).format('YYYY-MM-DDTHH:mm')
    else:
        valid = 0
        open_time = ""
        close_time = ""
    result = {"valid": valid, "open": open_time, "close": close_time}
    return flask.jsonify(result=result)"""


#############

app.logger.setLevel(logging.DEBUG)

if __name__ == "__main__":
    #print("Opening for global access on port {}".format(CONFIG.PORT))
    app.run(host="0.0.0.0", debug=True)
