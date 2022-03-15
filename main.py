from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, HiddenField, FloatField
from wtforms.validators import DataRequired, NumberRange
import requests
import os

# set up the flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///extra-books-collection.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
Bootstrap(app)

DB_SITE_API_KEY = os.environ['API_KEY']
DB_SITE_SEARCH = "https://api.themoviedb.org/3/search/movie?"


# Movie database model
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    title = db.Column(db.String(255), nullable=False)
    year = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    ranking = db.Column(db.Integer, nullable=False)
    review = db.Column(db.String(255), nullable=False)
    img_url = db.Column(db.String(255), nullable=False)


# form to edit review and rating
class MovieReviewForm(FlaskForm):
    Rating = FloatField('Your Rating out of 10 e.g 8.5',
                        validators=[DataRequired(),
                                    NumberRange(min=0, max=10, message="please enter a number between 0 and 10")])
    Review = StringField('Your Review', validators=[DataRequired()])
    submit = SubmitField('Done')


# form to search for new movies to add
class SearchMovie(FlaskForm):
    New_movie = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')


# Home page
@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()
    i = len(all_movies)
    for movie in all_movies:
        movie.ranking = i
        i -= 1
    db.session.commit()

    return render_template("index.html", movies=all_movies)


# edit rating and review page
@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = MovieReviewForm()
    if form.validate_on_submit():
        movie_id = request.args.get("id")
        movie_to_update = Movie.query.get(movie_id)
        movie_to_update.rating = form.data.get("Rating")
        movie_to_update.review = form.data.get("Review")
        db.session.commit()
        return redirect(url_for("home"))

    return render_template("edit.html", form=form)


# delete movie
@app.route("/delete", methods=["GET", "POST"])
def delete():
    movie_id = request.args.get("id")
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()

    return redirect(url_for("home"))


# add new movie
@app.route("/add", methods=["GET", "POST"])
def add():
    form = SearchMovie()
    if form.validate_on_submit():
        search_parameters = {
            "api_key": DB_SITE_API_KEY,
            "query": form.data.get("New_movie")
        }
        response = requests.get(url=DB_SITE_SEARCH, params=search_parameters)
        search_result = response.json()
        results = (search_result["results"])

        return render_template("select.html", results=results)

    return render_template("add.html", form=form)


# select
@app.route("/select/<int:num>", methods=["GET", "POST"])
def select(num):
    movie_site_url = f"https://api.themoviedb.org/3/movie/{num}?api_key={DB_SITE_API_KEY}&language=en-US"
    response = requests.get(url=movie_site_url).json()
    title = response["original_title"]
    img_url = response["poster_path"]
    year = response["release_date"].split("-")[0]
    description = response["overview"]

    new_movie = Movie(
        title=title,
        year=year,
        description=description,
        rating=0,
        ranking=1,
        review="None",
        img_url=f"https://image.tmdb.org/t/p/w500/{img_url}")

    db.session.add(new_movie)
    db.session.commit()

    current_movie = Movie.query.filter_by(title=new_movie.title).first()

    return redirect(url_for('edit', id=current_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
