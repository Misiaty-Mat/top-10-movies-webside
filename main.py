from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask_wtf import FlaskForm
from wtforms import  validators
from wtforms import StringField, SubmitField
from html import unescape
import requests

# Api key for themoviedb API
api_key = "themoviedb API KEY"

# Flask setup
app = Flask(__name__)
app.config["SECRET_KEY"] = "KEY TO THE APP"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///top-10-movies.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
Bootstrap(app)

# database setup
db = SQLAlchemy(app)

class Movies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    rating = db.Column(db.Float)
    review = db.Column(db.String(250))
    img_url = db.Column(db.String(250), nullable=False)


# uncomment the line bellow to create new databese
# db.create_all()

# Edit form structure
class EditMoveForm(FlaskForm):
    rating = StringField(label="Your rating out of 10", validators=[validators.DataRequired()])
    review = StringField(label="Your review", validators=[validators.DataRequired()])
    
    submit = SubmitField(label="Done")
    
# Add movie form structure
class AddMoveForm(FlaskForm):
    title = StringField(label="Title of the movie", validators=[validators.DataRequired()])
    submit = SubmitField(label="Done")


# Home page
# Returning database records by descending rating
@app.route("/")
def home():
    all_movies = Movies.query.order_by(desc("rating"))
    return render_template("index.html", all_movies=all_movies)

# Edit page
# Creates new form to edit some data which is sended to the databese
@app.route("/edit/<int:movie_id>", methods=["GET", "POST"])
def edit(movie_id):
    edit_form = EditMoveForm()
    if edit_form.validate_on_submit():
        movie = Movies.query.get(movie_id)
        
        movie.rating = edit_form.rating.data
        movie.review = edit_form.review.data
        
        db.session.commit()  
        
        return redirect(url_for("home"))
    else:
        return render_template("edit.html", movie_id=movie_id, form=edit_form)


# Delete mechanisim to delete specific record from database
@app.route("/delete/<int:movie_id>")
def delete(movie_id):
    movie_to_delete = Movies.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    
    return redirect(url_for("home"))

# Add page
# Creates new form and getting data from it
# Imported data is used to find film in themoviedb endpoint and send it to the select page
@app.route("/add", methods=["GET", "POST"])
def add():
    add_form = AddMoveForm()
    
    if add_form.validate_on_submit():
        movie_title = add_form.title.data
        
        params = {
            "api_key": api_key,
            "query": movie_title
        }
        
        response = requests.get("https://api.themoviedb.org/3/search/movie", params=params)
        response.raise_for_status()
        movies_data = response.json()
        movies_required_data = []
        
        for movie in movies_data["results"]:
            movies_required_data.append([movie["id"], movie["title"], movie["release_date"]])
        
        
        return render_template("select.html", movies=movies_required_data)
    
    return render_template("add.html", form=add_form)


# Select  page
# Renders all possible films that user was looking for
# On click API send all needed info of the film and gathered data is sended to the database
@app.route("/select/<int:movie_id>")
def select(movie_id):
    params = {
            "api_key": api_key
    }
    
    response = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}", params=params)
    data = response.json()
    
    new_movie = Movies(
    id = movie_id,
    title=data["title"],
    year=int(data["release_date"][:4]),
    description=unescape(data["overview"]),
    img_url=f"https://image.tmdb.org/t/p/original{data['poster_path']}"
    )

    db.session.add(new_movie)
    db.session.commit()
    
    
    return redirect(url_for("edit", movie_id=movie_id))


# Run Flask app on start
if __name__ == '__main__':
    app.run(debug=True)
