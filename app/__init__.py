#!/usr/bin/python
"""
ilmnuri audio website
Api of ilmnuri
"""
from flask import Flask, render_template, jsonify, request
import memcache
import logging
from glob import glob
import os
import sqlite3

app = Flask(__name__)
client = memcache.Client([('127.0.0.1', 11211)])
database = '/usr/share/nginx/html/app/tokens.db'
log_dir = '/var/log/ilmnuri'

if not os.path.exists(log_dir):
    log_dir = '/tmp'

logging.basicConfig(filename='{0}/ilmnuri.log'.format(log_dir),
                    format='%(asctime)s  %(funcName)s: %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)

log = logging.getLogger(__name__)


@app.route('/')
def index():
    log.info('index page rendered.')
    return render_template("index.html")


@app.route('/dars/<teacher>/')
def first(teacher):

    list_items = glob('{0}/*'.format(teacher))
    new_list = []
    for item in list_items:
        s = item.split('/')
        new_list.append(s[1])

    log.info('/dars/{0} page rendered'.format(teacher))

    return render_template('dars.html',
                           new_list=sorted(new_list),
                           teacher=teacher)


@app.route('/dars/<teacher>/<album>/')
def category(teacher, album):

    mobile = None
    user = request.headers.get('User-Agent')
    if 'Mobile' in user:
        mobile = 'mobile'

    list_items = glob('{0}/{1}/*'.format(teacher, album))
    new_list = []
    for item in list_items:
        sz = '{0} MB'.format(os.path.getsize(item) / 1024000)
        s = item.split('/')
        new_list.append((s[2], sz))

    log.info('/dars/{0}/{1} page rendered'.format(teacher, album))

    return render_template('track.html',
                           new_list=sorted(new_list),
                           teacher=teacher,
                           album=album,
                           mobile=mobile)


def insert_token(argument):
    con = sqlite3.connect(database)
    cur = con.cursor()
    cur.execute("INSERT INTO token_table (data) VALUES (?)", (argument,))
    con.commit()
    con.close()


@app.route('/api/v1.0/albums/', methods=['GET'])
def get_tasks():

    albums = []

    if not client.get('album'):
        log.info('Dictionary empty, executing the script.')
        os.system('/usr/share/nginx/html/get_full_list.py')
        dictionary = client.get('album')
    else:
        dictionary = client.get('album')

    for key, value in dictionary.items():
        i = 1
        for k, v in value.items():
            output = {
                'id': i,
                'category': key,
                'album': k,
                'items': sorted(v)
            }
            albums.append(output)
            i += 1
    log.info('Rendering the main albums page.')
    return jsonify({'albums': sorted(albums)})


@app.route('/api/v1.0/albums/<teacher>/', methods=['GET'])
def get_teacher(teacher):

    albums = []

    if not client.get('album'):
        log.info('Dictionary empty, executing the script.')
        os.system('/usr/share/nginx/html/get_full_list.py')
        dictionary = client.get('album')
    else:
        dictionary = client.get('album')

    for key, value in dictionary.items():
        if key == teacher:
            i = 1
            for k, v in value.items():
                output = {
                    'id': i,
                    'category': key,
                    'album': k,
                    'items': sorted(v)
                }
                albums.append(output)
                i += 1

    log.info('Rendering the category {0} page.'.format(teacher))
    return jsonify({'albums': sorted(albums)})


@app.route('/api/ios/albums/<teacher>/', methods=['GET'])
def ios_teacher(teacher):
    
    if not client.get('album'):
        log.info('Dictionary empty, executing the script.')
        os.system('/usr/share/nginx/html/get_full_list.py')
        dictionary = client.get('album')
    else:
        dictionary = client.get('album')
        
    albums = []

    for key, value in dictionary.items():
        if key == teacher:
            i = 1
            for k, v in value.items():
                output = {
                    'id': i,
                    'category': key,
                    'album': k,
                    'items': sorted([{'name': x,
                               'url': 'http://ilmnuri.net/{0}/'
                                      '{1}/{2}'.format(key, k, x)} for x in v])
                }
                albums.append(output)
                i += 1

    log.info('Rendering the category {0} page on ios.'.format(teacher))
    return jsonify({'albums': sorted(albums)})


@app.route('/tokens/<uuid>', methods=['POST'])
def token(uuid):
    token_id = request.json
    insert_token(token_id['data'])
    return jsonify({'uuid': uuid})


if __name__ == '__main__':
    app.run(port=8080, host='0.0.0.0', debug=True)
