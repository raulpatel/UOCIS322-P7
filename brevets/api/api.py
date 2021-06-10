import os
import logging
from flask import Flask, request, jsonify, abort
from flask_restful import Resource, Api
from pymongo import MongoClient
from itsdangerous import (TimedJSONWebSignatureSerializer \
                                  as Serializer, BadSignature, \
                                  SignatureExpired)
from passlib.hash import sha256_crypt as pwd_context

app = Flask(__name__)
api = Api(app)

client = MongoClient('mongodb://' + os.environ['MONGODB_HOSTNAME'], 27017)
db = client.tododb

SECRET_KEY = 'a8d09n@ j*djf%32$^mk'


def hash_password(password):
    return pwd_context.using(salt='s00p3rSeCret').encrypt(password)


def verify_password(password, hashVal):
    return pwd_context.verify(password, hashVal)


def generate_auth_token(username, password, expiration=600):
   s = Serializer(SECRET_KEY, expires_in=expiration)
   return s.dumps({'username': username, 'password': password})


def verify_auth_token(token):
    s = Serializer(SECRET_KEY)
    try:
        data = s.loads(token)
    except SignatureExpired:
        return False    # valid token, but expired
    except BadSignature:
        return False  # invalid token
    return True

def csv_form(lst, top):
    upper = list(lst[0].keys())  # make sure we have a list of the keys
    lst_len = len(lst)
    row_len = len(upper)
    upper = ",".join(upper)
    upper += "\n"
    vals = ""
    length = lst_len
    if top != -1 and top < lst_len:
        length = top  # set the new length if one is specified
    for i in range(length):
        rows = list(lst[i].values())
        for i in range(row_len):
            rows[i] = str(rows[i])
        row = ",".join(rows)
        row += "\n"
        vals += row
    return upper + vals
        

def json_form(lst, top):
    if top == -1:
        return jsonify(lst)
    else:
        if top > len(lst):
            top = len(lst)
        result = []
        for i in range(top):
            result.append(lst[i])
        return jsonify(result)


class listAll(Resource):
    def get(self, dtype='JSON'):
        token = request.args.get('token', type=str)
        if not verify_auth_token(token):
            abort(401)
        topk = int(request.args.get('top', default=-1))
        lst = list(db.tododb.find({}, {'_id': 0, 'km': 1, 'open': 1, 'close': 1}))
        if dtype == 'CSV':
            return csv_form(lst, topk)
        return json_form(lst, topk)


class listOpenOnly(Resource):
    def get(self, dtype='JSON'):
        token = request.args.get('token', type=str)
        if not verify_auth_token(token):
            abort(401)
        topk = int(request.args.get('top', default=-1))
        lst = list(db.tododb.find({}, {'_id': 0, 'km': 1, 'open': 1}))
        if dtype == 'CSV':
            return csv_form(lst, topk)
        return json_form(lst, topk)


class listCloseOnly(Resource):
    def get(self, dtype='JSON'):
        token = request.args.get('token', type=str)
        if not verify_auth_token(token):
            abort(401)
        topk = int(request.args.get('top', default=-1))
        lst = list(db.tododb.find({}, {'_id': 0, 'km': 1, 'close': 1}))
        if dtype == 'CSV':
            return csv_form(lst, topk)
        return json_form(lst, topk)


class register(Resource):
    def post(self):
        app.logger.debug("received request for register")
        username = request.args.get('un', type=str)
        password = request.args.get('pw', type=str)
        if db.users.find_one({'username': username}) is not None:
            app.logger.debug("Username taken")
            abort(400)
        password = hash_password(password)
        new_user = {
            'username': username,
            'password': password
        }
        db.users.insert_one(new_user)
        app.logger.debug("registration successful")
        return "New user added!", 201


class token(Resource):
    def get(self):
        username = request.args.get('un', type=str)
        password = request.args.get('pw', type=str)
        find_user = db.users.find_one({'username': username})
        if not find_user:
            app.logger.debug("account doesn't exist")
            abort(401)
        find_user = dict(find_user)
        if not verify_password(password, find_user['password']):
            app.logger.debug("incorrect password")
            abort(401)
        token = generate_auth_token(username, password)
        result = {
            'token': token,
            'duration': 600
        }
        app.logger.debug("login success")
        return jsonify(result)


# Create routes
# Another way, without decorators
api.add_resource(listAll, '/listAll', '/listAll/<string:dtype>')
api.add_resource(listOpenOnly, '/listOpenOnly', '/listOpenOnly/<string:dtype>')
api.add_resource(listCloseOnly, '/listCloseOnly', '/listCloseOnly/<string:dtype>')
api.add_resource(register, '/register')
api.add_resource(token, '/token')

app.logger.setLevel(logging.DEBUG)

# Run the application
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
