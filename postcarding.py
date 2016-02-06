import os
from flask import Flask
from flask import render_template, url_for, redirect, session, request, jsonify
import pymongo
import json
import datetime
import random

app = Flask(__name__)
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['DEBUG'] = True

conn = pymongo.Connection(os.environ['OPENSHIFT_MONGODB_DB_URL'])
db = conn['postcards']


def get_index(alist, element):
    return alist.index(element)


@app.route('/no_text', methods = ['GET', 'POST'])
def add_numbers():
    if request.method == 'POST':
        no_text = request.json['hasText']
        card_id = request.json['cardId']
        result = db['cards'].find_one({'img_id': card_id})
        if result:
            result = db['cards'].update({"img_id": card_id},{"$set": {"no_text": True}})
            return 'Postkaart uuendatud'
        else:
            return 'Postkaari ei ole uuendatud'
    else:
        return ''


@app.route("/")
def front():
    pages = []
    pages_list = db['cards'].find({ "no_text" : { "$exists" : False }})
    for page in pages_list:
        pages.append(page['img_id'])

    random_page = "00" + pages[random.randrange(len(pages))]

    return render_template('front.html', random_page = random_page)

@app.route("/item/00<card_id>", methods=['GET', 'POST'])
def digar_cards(card_id):

    pages = []
    pages_list = db['cards'].find({ "no_text" : { "$exists" : False } })
    for page in pages_list:
        pages.append(page['img_id'])

    random_page = random.randrange(len(pages))

    result = db['cards'].find_one({'img_id': card_id})

    if result and not 'no_text' in result:
        postcard = {}
        postcard['front_img'] = result['front']
        postcard['back_img'] = result['back']
        postcard['previous'] = "00" + pages[get_index(pages, card_id)-1]
        postcard['next'] = "00" + pages[get_index(pages, card_id)+1]
        postcard['text'] = ''
        postcard['card_id'] = card_id
        postcard['random_page'] = "00" + pages[random_page]
    elif result and 'no_text' in result:
        postcard = {}
        postcard['front_img'] = result['front']
        postcard['back_img'] = result['back']
        postcard['text'] = ''
        postcard['card_id'] = card_id
        postcard['random_page'] = "00" + pages[random_page]
    else:
        return 'Vabandame, sellist postkaarti ei ole.'
        

    commented = db['comments'].find({'img_id': card_id}).sort('date', pymongo.DESCENDING)
    comments = []
    if commented:
        for i in commented:
            comments.append(i['comment'])
        if len(comments) > 0:
            postcard['text'] = comments[-1]
  
    if request.method == 'POST':
        if len(request.form['comment']) > 0:
            db['comments'].insert({'img_id': card_id, 'comment': request.form['comment'], 'time': datetime.datetime.utcnow()})
            return redirect(url_for('digar_cards', card_id=card_id))

    if result and not 'no_text' in result:
        return render_template('index.html', postcard = postcard)
    else:
        return render_template('notext.html', postcard = postcard)

if __name__ == "__main__":
    app.run()

