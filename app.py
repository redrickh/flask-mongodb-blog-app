from flask import Flask, render_template, request, url_for, redirect, session
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId
import bcrypt
import credentials

# Create a new client and connect to the server
client = MongoClient(credentials.uri, server_api=ServerApi('1'))
# add your mongodb uri to your credentials.py file!
# uri = "your_mongo_db_uri"

db = client.Cluster0
product = db.product
user_log = db.login
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'testing'


@app.route('/', methods=("GET", "POST"))
def index():
    if request.method == 'POST':
        render_template('posts.html')
        print("test")

    all_posts = product.find()

    return render_template('index.html', product=all_posts)


@app.route('/admin', methods=("GET", "POST"))
def admin():
    if 'username' in session:
        if request.method == 'POST':
            content = request.form['name']
            degree = request.form['content']
            product.insert_one({'name': content, 'content': degree})
            return redirect(url_for('admin'))

        all_posts = product.find()
        return render_template('admin.html', product=all_posts, username=session['username'])

    else:
        return redirect(url_for('login'))


@app.route("/posts", methods=("GET", "POST"))
def posts():
    name = request.args.get('name')
    query = {"name": name}
    content = product.find(query)
    print(query)
    search_results = [result for result in content]
    return render_template('posts.html', search_results=search_results)


@app.route('/<id>/delete/', methods=("GET", "POST"))
def delete(id):
    product.delete_one({"_id": ObjectId(id)})
    return redirect(url_for('admin'))


@app.route('/<id>/edit/', methods=("GET", "POST"))
def edit(id):
    name = request.form['name']
    content = request.form['content']
    product.update_one({"_id": ObjectId(id)}, {'$set': {'name': name, 'content': content}})
    return redirect(url_for('admin'))


@app.route('/process', methods=['POST'])
def process():
    find = request.form.get('search_query')
    query = {"name": find}
    results = product.find(query)

    search_results = [result for result in results]

    return render_template('search_results.html', search_results=search_results)


def create_hashed_password(password):
    encoded = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(encoded, salt)
    return hashed


@app.route('/login', methods=("GET", "POST"))
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        decoding = password.encode('utf-8')
        stored_password = user_log.find_one({'username': username})

        if stored_password and bcrypt.checkpw(decoding, stored_password['password']):
            print("match")
            session['username'] = username
            return redirect(url_for('admin'))
        else:
            print("does not match")
            return render_template('login.html')

    else:
        return render_template('login.html')


@app.route('/signup', methods=("GET", "POST"))
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if len(password) >= 7:
            hashed = create_hashed_password(password)
            print(hashed)
            user_log.insert_one({'username': username, 'password': hashed})
            return redirect(url_for('admin'))
        else:
            return render_template('signup.html')
    else:
        return render_template('signup.html')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run()
