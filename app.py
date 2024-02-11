from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import pickle
import numpy as np
import json
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
    current_user,
    logout_user,
    login_required,
    AnonymousUserMixin
)
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand





popular_df = pickle.load(open('popular.pkl','rb'))
pt = pickle.load(open('pts1.pkl','rb'))
books2 = pickle.load(open('books1.pkl','rb'))
similarity_scores =  pickle.load(open('similarity_scores1.pkl','rb'))


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///the-book-spot.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "My Secret key"

#app.config["SQLALCHEMY_DATABASE_URI"] = "postgres://mthwnkvmlsvjzp:ec522ca94a36167296640a3c861dc957da3d0ea3a5f41ee1d63dc5bc73807d89@ec2-44-205-177-160.compute-1.amazonaws.com:5432/d19lnnc3bfcl9n"
db = SQLAlchemy(app)


migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.session_protection = "strong"
login_manager.login_view = "login"
login_manager.login_message_category = "info"




class Books(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    language = db.Column(db.String(50), nullable=False)
    arrival = db.Column(db.Integer, nullable=False)
    link = db.Column(db.String(200), nullable=True)
    image = db.Column(db.String(200), nullable=True)


    def __repr__(self) -> str:
        return f"{self.sno} - {self.name} - {self.author}"
    
class User1(UserMixin, db.Model):
    __tablename__ = 'users1'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=True)
    second_name = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(80), unique=True)
    password_hash = db.Column(db.String())
 
    def set_password(self,password):
        self.password_hash = generate_password_hash(password)
     
    def check_password(self,password):
        return check_password_hash(self.password_hash,password)
    
@app.before_first_request
def create_tables():
    db.create_all()
    
    
@login_manager.user_loader
def load_user(user_id):
    return User1.query.get(user_id)

    



@app.route('/books_category', methods=['POST', 'GET'])
def category():
    user=True
    if current_user.is_anonymous:
        user=False
    if request.method == 'POST':
        category = request.form['category']
        books=Books.query.filter(Books.category==category).all()
        return render_template("books.html", books=books, user=user)
    
    else:
        return render_template("books.html", user=user)


@app.route('/books', methods=['POST', 'GET'])
def books():

    user=True
    user_name=""
    if current_user.is_anonymous:
        user=False
    
    else:
        user_name=current_user.first_name
    if request.method == 'POST':
        book_name = request.form['name']
        book_author = request.form['author']
        category = request.form['category']
        language = request.form['language']
        arrival = request.form['arrival']
        link = request.form['link']
        image = request.form['image']
        book=Books(name=book_name, author=book_author, category=category, language=language, link=link,arrival= arrival, image=image)
        db.session.add(book)
        db.session.commit()
        return redirect("/books", user=user, user_name=user_name)
    else:
        return render_template("books.html", user=user, user_name=user_name)


@app.route("/", methods=['POST', 'GET'])
def home():
    if request.method=='POST':
        search=[]
        searched_data=[]
        api_key = 'AIzaSyCm1hhYNPWjjL39pZwlPTckHcuHhpSIJjw'  # Replace with your Google Books API key
        url = f'https://www.googleapis.com/books/v1/volumes?q=orderBy=newest&key={api_key}&maxResults=20'
        response = requests.get(url)

        user_input=request.form['user_input']
        url = f'https://www.googleapis.com/books/v1/volumes?q={user_input}&key={api_key}&maxResults=5'
        res=requests.get(url)
        search_results={}
        if res.status_code == 200:
            search_results = json.loads(res.text)
        
    
        if search_results and 'items' in search_results:
                    for item in search_results['items']:
                        book_info = {
                            'title': item['volumeInfo']['title'],
                            'authors': item['volumeInfo'].get('authors', []),
                            'image_url': item['volumeInfo'].get('imageLinks', {}).get('thumbnail', ''),
                            'google_books_link': item['volumeInfo'].get('infoLink', ''),
                            'description': item['volumeInfo'].get('description', '')
                            
                        }
                        search.append(book_info)


        user=True
        if current_user.is_anonymous:
            user=False

        search_results={}
        if response.status_code == 200:
            search_results = json.loads(response.text)
            
        
        if search_results and 'items' in search_results:
                    for item in search_results['items']:
                        book_info = {
                            'title': item['volumeInfo']['title'],
                            'authors': item['volumeInfo'].get('authors', []),
                            'image_url': item['volumeInfo'].get('imageLinks', {}).get('thumbnail', ''),
                            'google_books_link': item['volumeInfo'].get('infoLink', ''),
                            'description': item['volumeInfo'].get('description', '')
                            
                        }
                        searched_data.append(book_info)
        return render_template('index.html',
                            book_name=list(popular_df['Book-Title'].values),
                            author=list(popular_df['Book-Author'].values),
                            image=list(popular_df['book-path'].values),
                            votes=list(popular_df['num_ratings'].values),
                            rating=list(popular_df['avg_ratings'].values),
                            link=list(popular_df['book-link'].values)
                            , searched_data=searched_data, search=search, user=user)
    else:
        searched_data=[]
        api_key = 'AIzaSyCm1hhYNPWjjL39pZwlPTckHcuHhpSIJjw'  # Replace with your Google Books API key
        url = f'https://www.googleapis.com/books/v1/volumes?q=orderBy=newest&key={api_key}&maxResults=20'
        response = requests.get(url)
        
        user=True
        if current_user.is_anonymous:
            user=False

        search_results={}
        if response.status_code == 200:
            search_results = json.loads(response.text)
            
        
        if search_results and 'items' in search_results:
                    for item in search_results['items']:
                        book_info = {
                            'title': item['volumeInfo']['title'],
                            'authors': item['volumeInfo'].get('authors', []),
                            'image_url': item['volumeInfo'].get('imageLinks', {}).get('thumbnail', ''),
                            'google_books_link': item['volumeInfo'].get('infoLink', ''),
                            'description': item['volumeInfo'].get('description', '')
                            
                        }
                        searched_data.append(book_info)
        return render_template('index.html',
                            book_name=list(popular_df['Book-Title'].values),
                            author=list(popular_df['Book-Author'].values),
                            image=list(popular_df['book-path'].values),
                            votes=list(popular_df['num_ratings'].values),
                            rating=list(popular_df['avg_ratings'].values),
                            link=list(popular_df['book-link'].values)
                            , searched_data=searched_data, user=user)

                           
@app.route("/recommender")
def post():
    user=True
    if current_user.is_anonymous:
        user=False
    return render_template('recommender.html', user=user)

def search_books(query):
    api_key = 'AIzaSyCm1hhYNPWjjL39pZwlPTckHcuHhpSIJjw'  # Replace with your Google Books API key
    url = f'https://www.googleapis.com/books/v1/volumes?q={query}&key={api_key}&maxResults=1'
    response = requests.get(url)
    if response.status_code == 200:
        data = json.loads(response.text)
        return data
    else:
        return None

@app.route("/recommend_books", methods=["POST", "GET"])
def recommend():
    if request.method=='POST':
        recommended_data=[]
        searched_data=[]
        user_input = request.form.get('user_input')
        if user_input in pt.index:       
            index = np.where(pt.index == user_input)[0][0]  
            similar_items = sorted(list(enumerate(similarity_scores[index])), key=lambda x: x[1], reverse=True)[
                        0:6]  # similarity of 1984 book with other books


            user_input = user_input.replace(' ', '+')
            search_results = search_books(user_input)
            if search_results and 'items' in search_results:
                for item in search_results['items']:
                    book_info = {
                        'title': item['volumeInfo']['title'],
                        'authors': item['volumeInfo'].get('authors', []),
                        'image_url': item['volumeInfo'].get('imageLinks', {}).get('thumbnail', ''),
                        'google_books_link': item['volumeInfo'].get('infoLink', ''),
                        'description': item['volumeInfo'].get('description', '')
                        
                    }
                    searched_data.append(book_info)
            
            for i in similar_items:
                book = []
                temp_df = books2[books2['Book-Title'] == pt.index[i[0]]]
            
                related_book=temp_df.drop_duplicates('Book-Title')['Book-Title'].values
                print(related_book)
                related_book=str(related_book)
                related_book = related_book.replace(' ', '+')
                search_results = search_books(related_book)
                if search_results and 'items' in search_results:
                    for item in search_results['items']:
                        book_info = {
                            'title': item['volumeInfo']['title'],
                            'authors': item['volumeInfo'].get('authors', []),
                            'image_url': item['volumeInfo'].get('imageLinks', {}).get('thumbnail', ''),
                            'google_books_link': item['volumeInfo'].get('infoLink', ''),
                            'description': item['volumeInfo'].get('description', '')
                            
                        }
                        book.append(book_info)
                recommended_data.append(book)
                
        user=True
        
        if current_user.is_anonymous:
            user=False

        
        return render_template('recommender.html',data=[],recommended_data=recommended_data, user=user, searched_data=searched_data)
    else:
        return render_template('recommender.html')

@app.route("/register", methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        first_name = request.form['first_name']
        second_name=request.form['second_name']
        password = request.form['password']
        password_hash = generate_password_hash(password)
        user=User1(email=email, password_hash=password_hash, first_name=first_name, second_name=second_name)
        db.session.add(user)
        db.session.commit()
        return redirect("/")
    
    return render_template('register.html')


@app.route('/login', methods = ['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return render_template('index.html', user=True)
     
    if request.method == 'POST':
        email = request.form['email']
        user = User1.query.filter_by(email = email).first()
        if user is not None and user.check_password(request.form['password']):
            login_user(user)
            user=True
            if current_user.is_anonymous:
                user=False
            return render_template('index.html', user=user)
        else:
            print('user not found')
            return redirect('/')
     
    return render_template('index.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template('index.html')

@app.route('/profile')
@login_required
def profile():
    user=current_user
    

    return render_template('profile.html', user=user)
    


if __name__ =="__main__":
    app.run(debug=True, port=8080)