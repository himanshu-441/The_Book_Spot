from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import pickle
import numpy as np
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
    current_user,
    logout_user,
    login_required,
)



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
    
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), unique=True)
    password_hash = db.Column(db.String())
 
    def set_password(self,password):
        self.password_hash = generate_password_hash(password)
     
    def check_password(self,password):
        return check_password_hash(self.password_hash,password)
    
    
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

    
@app.before_first_request
def create_tables():
    db.create_all()


@app.route('/books_category', methods=['POST', 'GET'])
def category():
    if request.method == 'POST':
        category = request.form['category']
        books=Books.query.filter(Books.category==category).all()
        return render_template("books.html", books=books)
    
    else:
        return render_template("books.html")


@app.route('/books', methods=['POST', 'GET'])
def books():
    user=current_user
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
        return redirect("/books", user=user)
    else:
        return render_template("books.html", user=user)


@app.route("/")
def home():
    books=Books.query.all()
    new_arrival=Books.query.filter(Books.arrival>=2022).all()
    user=current_user
    return render_template('index.html',
                           book_name=list(popular_df['Book-Title'].values),
                           author=list(popular_df['Book-Author'].values),
                           image=list(popular_df['book-path'].values),
                           votes=list(popular_df['num_ratings'].values),
                           rating=list(popular_df['avg_ratings'].values),
                           link=list(popular_df['book-link'].values)
                           , books=books, new_arrival=new_arrival, user=user)
                           
@app.route("/recommender")
def post():
    user=current_user
    return render_template('recommender.html', user=user)



@app.route("/recommend_books", methods=["POST"])
def recommend():
    data = []
    user_input = request.form.get('user_input')
    if user_input in pt.index:       
        index = np.where(pt.index == user_input)[0][0]  
        similar_items = sorted(list(enumerate(similarity_scores[index])), key=lambda x: x[1], reverse=True)[
                    0:6]  # similarity of 1984 book with other books

        
        for i in similar_items:
            item = []
            temp_df = books2[books2['Book-Title'] == pt.index[i[0]]]
            item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Title'].values))
            item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Author'].values))
            item.extend(list(temp_df.drop_duplicates('Book-Title')['Image-URL-M'].values))
            item.extend(list(temp_df.drop_duplicates('Book-Title')['book-link'].values))

            data.append(item)
    user=current_user
    
    return render_template('recommender.html',data=data, user=user)

@app.route("/register", methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        password_hash = generate_password_hash(password)
        user=User(email=email, password_hash=password_hash)
        db.session.add(user)
        db.session.commit()
        return redirect("/")
    
    return render_template('register.html')


@app.route('/login', methods = ['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect('/')
     
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email = email).first()
        if user is not None and user.check_password(request.form['password']):
            login_user(user)
            user=current_user
            return render_template('index.html', user=user)
        else:
            print('user not found')
            return redirect('/')
     
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template('index.html')

@app.route('/profile')
@login_required
def profile():
    user=current_user
    data=[]
    data.append(user)

    return render_template('profile.html', data=data)
    


if __name__ =="__main__":
    app.run(debug=True, port=8000)