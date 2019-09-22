#!/usr/bin/env python

from flask import Flask, render_template, request, redirect, jsonify, \
    url_for, flash
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Categories, Items, User
from flask import session as login_session
import random
import string
import httplib2
import json
from flask import make_response
from werkzeug.serving import make_ssl_devcert


app = Flask(__name__)


# DATABASE CONNECTION
engine = create_engine('postgres+psycopg2://catalog:catalog@localhost:5432/catalogapp')
Base.metadata.bind = engine

# SESSION CREATION
DBSession = sessionmaker(bind=engine)
session = DBSession()

# CREATE ANTI-FORGERY STATE TOKEN


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits
                                  )
                    for x in xrange(32))
    login_session['state'] = state

    return render_template('login.html', STATE=state)

# CREATE FACEBOOK CONNECTION


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s" % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_secret']

    url = 'https://graph.facebook.com/oauth/access_token?grant_type=\
fb_exchange_token&client_id=%s&client_secret=\
%s&fb_exchange_token=%s' % (app_id, app_secret, access_token)

    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # USE TOKEN TO GET USER INFO FROM API
    userinfo_url = "https://graph.facebook.com/v2.8/me"

    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v2.8/me?access_token=%s&fields\
=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # THE TOKEN MUST BE STORED IN THE login_session IN ORDER TO LOGOUT
    login_session['access_token'] = token

    # GET USER PICTURE
    url = 'https://graph.facebook.com/v2.8/me/picture?access_token=\
%s&redirect=0&height=200&width=200' % token

    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # CHECK THE USER EXISTING
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    flash("Now logged in successfully as %s" % login_session['username'
                                                             ])
    return "you have logged in"

# CREATE FACEBOOK DISCONNECTION


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # THE ACCESS TOKEN MUST BE INCLUDED TO SUCCESSFULLY LOGOUT
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' %\
          (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"

# PROVIDER DISCONNETION


@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('categoriesMenu'))
    else:
        flash("You were not logged in")
        return redirect(url_for('categoriesMenu'))

# USER FUNCTIONS


def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'], picture=login_session
                   ['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']
                                         ).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# SHOW ALL CATEGORIES
@app.route('/')
@app.route('/categories/')
def categoriesMenu():
    categories = session.query(Categories).all()
    lastItems = session.query(Categories, Items).filter(
        Items.categories_id == Categories.id).order_by(desc(
            "createdate")).all()

    if 'username' not in login_session:
        return render_template('GeneralCategories.html',
                               categories=categories,
                               lastItems=lastItems)
    else:
        return render_template('categoriesMenu.html',
                               categories=categories,
                               lastItems=lastItems)

# CREATE NEW CATEGORY
@app.route('/categories/new', methods=['GET', 'POST'])
def newCategory():

    # CHECK IF THE USER LOGGED IN
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        if request.form['name'] != '':
            newCat = Categories(
                name=request.form['name'], user_id=login_session['user_id'])
            session.add(newCat)
            session.commit()
            flash("new category %s has been created!" % (newCat.name))
            return redirect(url_for('categoriesMenu'))
        else:
            flash("Please fill the Category name!")
            return redirect(url_for('categoriesMenu'))
    else:
        return render_template('newCategory.html')


# EDIT EXISTING CATEGORY
@app.route('/categories/<int:category_id>/edit', methods=['GET',
                                                          'POST'])
def editCategory(category_id):

    editCat = session.query(Categories).filter_by(id=category_id)\
        .one()

    # CHECK IF THE USER LOGGED IN
    if 'username' not in login_session:
        return redirect('/login')

    # User Authorization
    if editCat.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not \
                authorized to edit this Category.'); window.location\
                .href = 'items';}</script><body onload='myFunction()'>"

    if request.method == 'POST':
        if request.form['name'] != '':
            editCat.name = request.form['name']
            session.add(editCat)
            session.commit()
            flash('Category %s has been edited' % (editCat.name))
            return redirect(url_for('categoryItems', category_id=editCat
                                .id))
        else:
            flash("!!!!!! Fill please new name for the Category !!!!!!")
            return redirect(url_for('categoryItems', category_id=editCat
                                .id))    
    else:
        return render_template('editCategory.html', categ=editCat,
                               category_id=editCat.id)

# DELETE EXISTING CATEGORY


@app.route('/categories/<int:category_id>/delete', methods=['GET',
                                                            'POST'])
def deleteCategory(category_id):
    deleteCat = session.query(Categories).filter_by(id=category_id)\
        .one()
    itemsToDelete = session.query(Items).filter_by(
        categories_id=category_id).all()

    # CHECK IF THE USER LOGGED IN
    if 'username' not in login_session:
        return redirect('/login')

    # User Authorization
    if deleteCat.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not \
                authorized to delete this Category.'); window.location\
                .href = 'items';}</script><body onload='myFunction()'>"

    if request.method == 'POST':

        # DELETE ITEMS FOR THE CATEGORY FIRST
        for items in itemsToDelete:
            session.delete(items)

        # DELETE THE CATEGORY
        session.delete(deleteCat)
        session.commit()
        flash('Category %s has been deleted' % (deleteCat.name))
        return redirect(url_for('categoriesMenu'))
    else:
        return render_template('deleteCategory.html', deleteCategory=deleteCat)


# SHOW CATEGORY ITEMS
@app.route('/categories/<int:category_id>/')
@app.route('/categories/<int:category_id>/items/')
def categoryItems(category_id):
    CatOne = session.query(Categories).filter_by(id=category_id).one()
    items = session.query(Items).filter_by(categories_id=category_id)
    countItems = list(items)
    creatorID = getUserInfo(CatOne.user_id)

    # CHECK IF THE USER LOGGED IN & CATEGORIESITEMS OWNER
    if 'username' not in login_session or creatorID.id != login_session[
                                                          'user_id']:
        return render_template('Generalitems.html', categ=CatOne,
                               items=items, countItems=len(
                                   countItems))
    else:
        return render_template('itemsMenu.html', categ=CatOne,
                               items=items, countItems=len(countItems))

# ADD ITEM
@app.route('/categories/<int:category_id>/items/new', methods=['GET',
                                                               'POST'])
def newCategoryItem(category_id):
    CatOne = session.query(Categories).filter_by(id=category_id).one()

    # CHECK IF THE USER LOGGED IN
    if 'username' not in login_session:
        return redirect('/login')

    if request.method == 'POST':
        # CHECK FILEDS IF THEY ARE EMPTY
        if request.form['name'] and request.form['description'] and \
           request.form['price'] and request.form['manufacture'] != '':
            newItem = Items(name=request.form['name'],
                            description=request.form['description'],
                            price=request.form['price'],
                            manufacture=request.form['manufacture'],
                            categories_id=category_id)
            session.add(newItem)
            session.commit()
            flash('New Menu %s Item Successfully created' % (newItem
                                                             .name))
            return redirect(url_for('categoryItems', category_id=CatOne.id))
        else:
            flash("!!!!!! Fill please all new item fields !!!!!!")
            return redirect(url_for('categoryItems', category_id=CatOne.id))
    else:
        return render_template('newItem.html', category_id=CatOne.id,
                               categ=CatOne)

# EDIT ITEM


@app.route('/categories/<int:category_id>/items/<int:item_id>/edit',
           methods=['GET', 'POST'])
def editCategoryItem(category_id, item_id):
    CatOne = session.query(Categories).filter_by(id=category_id).one()
    editedItem = session.query(Items).filter_by(id=item_id).one()

    # CHECK IF THE USER LOGGED IN
    if 'username' not in login_session:
        return redirect('/login')

    # USER AUTHORIZATION
    if CatOne.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not \
                authorized to edit this Item.');window.location.href =\
                '/';}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        # CHECK FILEDS IF THEY ARE EMPTY
        if request.form['name'] and request.form['description'] and \
           request.form['price'] and request.form['manufacture'] != '':
            editedItem.name = request.form['name']
            editedItem.description = request.form['description']
            editedItem.price = request.form['price']
            editedItem.manufacture = request.form['manufacture']
            session.add(editedItem)
            session.commit()
            flash('Menu %s Item Successfully edited' % (editedItem.name))
            return redirect(url_for('categoryItems', category_id=CatOne.id
                                ))
        else:
            flash("!!!!!! Fill please all new item fields !!!!!!")
            return redirect(url_for('categoryItems', category_id=CatOne.id
                                ))
    else:
        return render_template('editItem.html', categ=CatOne, item=editedItem)


# DELETE ITEM
@app.route('/categories/<int:category_id>/items/<int:item_id>/delete',
           methods=['GET', 'POST'])
def deleteCategoryItem(category_id, item_id):
    CatOne = session.query(Categories).filter_by(id=category_id).one()
    itemToDelete = session.query(Items).filter_by(id=item_id).one()

    # CHECK IF THE USER LOGGED IN
    if 'username' not in login_session:
        return redirect('/login')

    # USER AUTHORIZATION
    if CatOne.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not \
                 authorized to delete this Item.');window.location.href\
                 = '/';}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Menu %s Item Successfully deleted' % (itemToDelete.name))
        return redirect(url_for('categoryItems', category_id=CatOne.id
                                ))
    else:
        return render_template('deleteItem.html', categ=CatOne,
                               itemToDelete=itemToDelete)

# SHOW ITEM DESCRIPTION

@app.route('/categories/<int:category_id>/items/<int:item_id>/ \
            description')
def showItemDescription(category_id, item_id):
    category = session.query(Categories).filter_by(id=category_id)\
        .one()
    itemDesc = session.query(Items).filter_by(id=item_id).one()
    creatorID = getUserInfo(category.user_id)

    # CHECK IF THE USER LOGGED IN & CategoryItems Owner
    if 'username' not in login_session or creatorID.id != login_session[
                                                          'user_id']:
        return render_template('GeneralDescription.html', itemDesc=itemDesc,
                               categ=category)
    else:
        return render_template('itemDescription.html', categ=category,
                               itemDesc=itemDesc)


# EDIT ITEM DESCRIPTION
@app.route('/categories/<int:category_id>/items/<int:item_id>/ \
             description/edit', methods=['GET', 'POST'])
def editItemDescription(category_id, item_id):
    itemDescToEditCat = session.query(
        Categories).filter_by(id=category_id).one()
    itemDescToEdit = session.query(Items).filter_by(id=item_id)\
        .one()

    # CHECK IF THE USER LOGGED IN
    if 'username' not in login_session:
        return redirect('/login')

    # USER AUTHORIZATION
    if itemDescToEditCat.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not\
                authorized to edit this Item description.');window\
                .location.href = '/'; }</script><body onload=\
                'myFunction()'>"

    if request.method == 'POST':
        if request.form['description'] != '':
            itemDescToEdit.description = request.form['description']
            session.commit()
            flash('Menu %s Item description Successfully edited' %
                  (itemDescToEdit.name))
            return redirect(url_for('showItemDescription',
                                category_id=itemDescToEditCat.id,
                                item_id=itemDescToEdit.id))
        else:
            flash("!!!!!! Fill please item description field !!!!!!")
            return redirect(url_for('showItemDescription',
                                category_id=itemDescToEditCat.id,
                                item_id=itemDescToEdit.id))
    else:
        return render_template('editDescription.html',
                               category=itemDescToEditCat,
                               itemDescToEdit=itemDescToEdit)


# DELETE ITEM DESCRIPTION
@app.route('/categories/<int:category_id>/items/<int:item_id>/ \
            description/delete', methods=['GET', 'POST'])
def deleteItemDescription(category_id, item_id):
    itemDescToDeleteCat = session.query(
        Categories).filter_by(id=category_id).one()
    itemDescToDelete = session.query(Items).filter_by(id=item_id)\
        .one()

    # CHECK IF THE USER LOGGED IN
    if 'username' not in login_session:
        return redirect('/login')

    # USER AUTHORIZATION
    if itemDescToDeleteCat.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not \
                authorized to delete this Item description.');window\
                .location.href = '/';}</script><body onload=\
                'myFunction()'>"

    if request.method == 'POST':
        itemDescToDelete.description = ''
        session.commit()
        flash('Menu %s Item description Successfully deleted' %
              (itemDescToDelete.name))
        return redirect(url_for('categoriesMenu',
                                category_id=itemDescToDeleteCat.id))
    else:
        return render_template('deleteDescription.html',
                               itemDescToDeleteCat=itemDescToDeleteCat,
                               itemDescToDelete=itemDescToDelete)


# ADD JSON API
@app.route('/categories.JSON')
def CategoriesJSON():
    category = session.query(Categories).all()

    # CHECK IF THE USER LOGGED IN
    if 'username' not in login_session:
        return redirect('/login')

    return jsonify(categories=[c.serialize for c in category])

@app.route('/categories/<int:category_id>/items/<int:item_id>/JSON')
def ArbitraryItemJSON(category_id, item_id):
    #categroy = session.query(Categories).filter_by(
                        #id=category_id).one()
    item = session.query(Items).filter_by(categories_id=category_id).filter_by(id=item_id).all()

    # CHECK IF THE USER LOGGED IN
    if 'username' not in login_session:
        return redirect('/login')

    return jsonify(item=[i.serialize for i in item])


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    make_ssl_devcert('key', host='localhost')
    app.run(host='0.0.0.0', port=80, ssl_context=('key.crt', 'key.key'))
