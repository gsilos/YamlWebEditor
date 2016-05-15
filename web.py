#!/usr/bin/python -u
# encoding: utf-8

# References:
# http://sedimental.org/remap.html
# http://boltons.readthedocs.org/en/latest/iterutils.html#boltons.iterutils.remap
# http://stackoverflow.com/questions/13687924/setting-a-value-in-a-nested-python-dictionary-given-a-list-of-indices-and-value
# http://pythex.org/

from flask import Flask, render_template, request, g, session, Markup, url_for
from netaddr import all_matching_cidrs
import paramiko
import yaml
import re
import hashlib
import time
import sys
import copy


def getFromDict(dataDict, mapList):
    return reduce(lambda d, k: d[k], mapList, dataDict)

def setInDict(dataDict, mapList, value):
    if   isinstance(getFromDict(dataDict, mapList[:-1])[mapList[-1]], bool):
        getFromDict(dataDict, mapList[:-1])[mapList[-1]] = bool(value)
    elif isinstance(getFromDict(dataDict, mapList[:-1])[mapList[-1]], int):
        getFromDict(dataDict, mapList[:-1])[mapList[-1]] = int(value)
    elif isinstance(getFromDict(dataDict, mapList[:-1])[mapList[-1]], float):
        getFromDict(dataDict, mapList[:-1])[mapList[-1]] = float(value)
    elif isinstance(getFromDict(dataDict, mapList[:-1])[mapList[-1]], str):
        getFromDict(dataDict, mapList[:-1])[mapList[-1]] = str(value)
    else:
        raise Exception("setInDict: {}={}".format(",".join(mapList),type(value)))

def newInDict(dataDict, mapList, value):

    for key in mapList[:-1]:
        dataDict = dataDict.setdefault(key, {})

    if isinstance(value, bool):
        dataDict[mapList[-1]] = bool(value)
    elif isinstance(value , int):
        dataDict[mapList[-1]] =int(value)
    elif isinstance(value, float):
        dataDict[mapList[-1]] = float(value)
    elif isinstance(value, str):
        dataDict[mapList[-1]] = str(value)
    else:
        raise Exception("newInDict: {}={}".format(",".join(mapList), type(value)))

def delInDict(dataDict, mapList):
    for key in mapList[:-1]:
        dataDict = dataDict.setdefault(key, {})
    del dataDict[mapList[-1]]

def walk(d):
    for k, v in d.items():
        if isinstance(v,bool) or isinstance(v, str) or isinstance(v, int) or isinstance(v, float):
            g.path.append(str(k))
            key = ",".join(g.path)
            if isinstance(v,bool):
                g.keyvalue[str(key)] = bool(v)
            elif isinstance(v, str):
                g.keyvalue[str(key)] = str(v)
            elif isinstance(v, int):
                g.keyvalue[str(key)] = int(v)
            elif isinstance(v, float):
                g.keyvalue[str(key)] = float(v)
            g.path.pop()
        elif v is None:
            continue
        elif isinstance(v, dict):
            g.path.append(str(k))
            walk(v)
            g.path.pop()
        else:
            raise Exception("Type {} not recognized: {}.{}={}".format(type(v), ".".join(g.path), k, v))

def hide(d):
    for k, v in d.items():
        if isinstance(v, str) or isinstance(v, int):
            g.path.append(str(k))
            key = ",".join(g.path)
            if isinstance(v, str):
                if any(search in key for search in g.HiddenFields):
                    g.keyvaluehide[str(key)] = "*" * len(v)
            if isinstance(v, int):
                if any(search in key for search in g.HiddenFields):
                    g.keyvaluehide[str(key)] = 99999999
            g.path.pop()
        elif isinstance(v, dict):
            g.path.append(str(k))
            hide(v)
            g.path.pop()


def convert_keys_to_string(dictionary):
    if not isinstance(dictionary, dict):
        return dictionary
    return dict((str(k), convert_keys_to_string(v))
        for k, v in dictionary.items())

def initialize():
    g.path = []
    g.keyvalue = {}
    g.Fields = ""
    g.Total_Lines = 0
    g.dictionary = {}
    g.keyvaluehide = {}
    g.HiddenFields = ["password", "secret", "key", "credentials", "vcap_services", "mongodb.uri", "mongodb,uri", "etl,uri", "etl.uri"]

#libera endpoints sensiveis para ips especificos
def accept(ip):

        hasAccess = [   "127.0.0.1/32",
                        "192.168.0.0/16" ]

        check = all_matching_cidrs(ip , hasAccess )
        if len(check) > 0:
                return True
        else:
                return False




########## Let the game begin

app = Flask(__name__)

app.secret_key = 'super secret key'

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/start', methods=['GET'])
def start():

    initialize()

    session.clear()
    session.modified = True


    remotehost = request.args.get('hostname')
    remotefile = request.args.get('config')
    md5hash    = request.args.get('md5hash')

    if remotehost and remotefile:

        randonfile =    hashlib.md5(str(time.time())).hexdigest()

        sshuser = "USERNAME"
        localfile = "tmp/" + randonfile

        try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(remotehost, username=sshuser, key_filename="key.pub")
                ftp = ssh.open_sftp()
                ftp.get(remotefile, localfile)
                ftp.close()
        except Exception, e:
                raise Exception("scp {}@{}:{} {} -> {}".format(sshuser, remotehost, remotefile, localfile, e))

        stream = open(localfile, "r")

        session['yml'] = convert_keys_to_string(yaml.load(stream))

    elif md5hash:

        stream = open("basket/" + md5hash, "r")

        session['yml'] = convert_keys_to_string(yaml.load(stream))

    else:
        raise Exception("hey dude, do you really know what you are doing here? :-)")

    try:
        walk(session['yml'])
    except KeyError:
        raise Exception("walk failed")


    for key, value in sorted(g.keyvalue.items()):

        g.Total_Lines += 1
        if any(search in key for search in g.HiddenFields):
            g.Fields += """ <label for="{0}">{0}:</label>
          <input type="password" style="width:100%" name="{0}" value="sbrubles" disabled>
          <br/>\n""".format(key, value)
        elif type(value) == bool:
            if value:
                g.Fields += """ <label for="{0}">{0}:</label>
                <input type="text" style="width:100%" name="{0}" value="{1}" disabled>
                <br/>\n""".format(key, value)
            else:
                g.Fields += """ <label for="{0}">{0}:</label>
                <input type="text" style="width:100%" name="{0}" value="{1}" disabled>
                <br/>\n""".format(key, value)
        else:
            g.Fields += """ <label for="{0}">{0}:</label>
          <input type="text" style="width:100%" name="{0}" value=\"{1}\" disabled>
          <br/>\n""".format(key, value)

    g.dictionary = copy.deepcopy(session['yml'])

    g.path = []
    hide(g.dictionary)

    for key, value in g.keyvaluehide.items():
        value=999999
        setInDict(g.dictionary, key.split(","), value)

    return render_template('editor.html',
                           FIELDS=Markup(g.Fields),
                           TOTAL_LINES=g.Total_Lines,
                           JSONYML=yaml.dump(convert_keys_to_string(yaml.load(yaml.dump(g.dictionary))), default_flow_style=False))


@app.route('/edit', methods=['GET', 'POST'])
def edit():

    initialize()

    session.modified = True

    if request.method == 'POST':

        if request.form['create'].strip() == "True":
            _name = request.form['name'].strip()
            _value = request.form['value'].strip()
            _type = request.form['type'].strip()

        if not _name or not _value or not _type:
            raise Exception("Please enter all the fields.")

        if not re.match("^[a-zA-Z0-9,_.\-]+$", _name):
            raise Exception("format of name is not valid. Please try again.")

        if not re.match("^[a-zA-Z0-9,_=\@\/\:\s\$\.\-]+$", _value):
            raise Exception("format of value is not valid. Please try again.")

        if not any(search in _type for search in ["string", "int", "float", "bool"]):
            raise Exception("please choose the correct type for this field.")

        if _type == "string":
            newInDict(session['yml'],_name.encode('utf-8').split(","), str(_value))
        if _type == "int":
            newInDict(session['yml'],_name.encode('utf-8').split(","), int(_value))
        if _type == "float":
            newInDict(session['yml'], _name.encode('utf-8').split(","), float(_value))
        if _type == "bool":
            if str(_value).lower() == "true":
                newInDict(session['yml'],_name.encode('utf-8').split(","), True)
            elif str(_value).lower() == "false":
                newInDict(session['yml'], _name.encode('utf-8').split(","), False)
            else:
                raise Exception("only true or false for bool")

    try:
        g.dictionary = copy.deepcopy(convert_keys_to_string(session['yml']))
    except KeyError:
        raise Exception("No session! Buy your ticket and came back, I wait for you :)")

    walk(g.dictionary)


    for key, value in sorted(g.keyvalue.items()):

        g.Total_Lines += 1
        if any(search in key for search in g.HiddenFields):
            g.Fields += """ <label for="{0}">{0}:</label>
          <input type="password" style="width:100%" name="{0}" value="sbrubles" disabled>
          <br/>\n""".format(key, value)
        elif type(value) == bool:
            if value:
                g.Fields += """ <label for="{0}">{0}:</label>
                <input type="text" style="width:100%" name="{0}" value="{1}">
                <br/>\n""".format(key, value)
            else:
                g.Fields += """ <label for="{0}">{0}:</label>
                <input type="text" style="width:100%" name="{0}" value="{1}">
                <br/>\n""".format(key, value)
        else:
            g.Fields += """ <label for="{0}">{0}:</label>
          <input type="text" style="width:100%" name="{0}" value="{1}">
          <br/>\n""".format(key, value)

    g.Fields += '<input type="submit" value="Save" />'

    g.path = []
    hide(g.dictionary)
    for key, value in g.keyvaluehide.items():
        value=999999
        setInDict(g.dictionary, key.split(","), value)

    return render_template('editor.html',
                           FIELDS=Markup(g.Fields),
                           TOTAL_LINES=g.Total_Lines,
                           JSONYML=yaml.dump(convert_keys_to_string(yaml.load(yaml.dump(g.dictionary))), default_flow_style=False))


@app.route('/clear')
def clear():
    session.clear()
    return "cleared!"

@app.route('/download', methods=['GET'])
def download():

        if not accept(request.remote_addr):
                return "not authorized", 401

        if not re.match("^[a-fA-F\d]{32}", request.args.get('md5hash') ):
                return "invalid hash", 500

        md5hash    = request.args.get('md5hash')

        try:
                stream = open("basket/" + md5hash, "r")
        except Exception, e:
                return "no such hash" , 200

        return stream.read() , 200, {'Content-Type': 'text/plain; charset=utf-8'}

@app.route('/create')
def create():
    return render_template('create.html')

@app.route('/update/', methods=['POST'])
def update():

    initialize()


    for k, v in request.form.items():
        k.strip()
        v.strip()
        key = k.encode('utf-8').split(",")
        value = v.encode('utf-8').strip()
        if value != "sbrubles":
            setInDict(session['yml'], key, value)

    yml = yaml.dump(convert_keys_to_string(yaml.load(yaml.dump(session['yml']))), default_flow_style=False)

    g.dictionary = copy.deepcopy(convert_keys_to_string(session['yml']))

    g.path = []
    hide(g.dictionary)
    for key, value in g.keyvaluehide.items():
        value=999999
        setInDict(g.dictionary, key.split(","), value)

    md5string =  hashlib.md5(yml).hexdigest()

    # :-)
    with open("basket/" + md5string ,"w") as save:
        save.write(yml)

    return render_template('update.html', YML=yml, MD5=md5string)


if __name__ == '__main__':

    app.run(
        debug = True,
        host="0.0.0.0",
        port=int("8421"),
        processes=5
    )
