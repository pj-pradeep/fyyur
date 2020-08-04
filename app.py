#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json, sys
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from sqlalchemy import func
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


from models import *

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  venues = Venue.query.all()
  cities = set()
  for venue in venues:
    cities.update([venue.city])

  data = []
  for city in cities:
    venue_by_city = {'city': city, 'venues': []}
    for venue in venues:
      if venue.city.lower() == city.lower():
        venue_by_city.update({'state': venue.state})
        upcoming_shows_at_venue = Show.query.filter(Show.venue_id == venue.id).filter(Show.start_time > datetime.now()).all()
        
        venue_by_city['venues'].append({
          "id": venue.id,
          "name": venue.name,
          "num_upcoming_shows": len(upcoming_shows_at_venue)
        })
    data.append(venue_by_city)          

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_str = request.form.get('search_term', '')
  search_format = "%{}%".format(search_str.lower())
  search_results = Venue.query.filter(func.lower(Venue.name).like(search_format)).all()

  data = []
  for venue in search_results:
    upcoming_shows_at_venue = Show.query.filter(Show.venue_id == venue.id).filter(Show.start_time > datetime.now()).all()
    data.append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": len(upcoming_shows_at_venue)
    })

  response = {
    "count": len(search_results),
    "data": data
  }
  
  return render_template('pages/search_venues.html', results=response, search_term=search_str)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  
  venue = Venue.query.get(venue_id)
  data = {}
  if venue:
    # retrieve shows for the venue
    query = db.session.query(Show, Artist).filter(Show.venue_id == venue.id).filter(Artist.id == Show.artist_id).all()
    
    upcoming_shows = [
      {
        "artist_id": rec.Artist.id,
        "artist_name": rec.Artist.name,
        "artist_image_link": rec.Artist.image_link,
        "start_time": rec.Show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      }
      for rec in query if rec.Show.start_time > datetime.now()
    ]
    past_shows = [
      {
        "artist_id": rec.Artist.id,
        "artist_name": rec.Artist.name,
        "artist_image_link": rec.Artist.image_link,
        "start_time": rec.Show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      }
      for rec in query if rec.Show.start_time <= datetime.now()
    ]
       

    data = {
      "id": venue.id,
      "name": venue.name,
      "genres": [genre.name for genre in venue.genres],
      "address": venue.address,
      "city": venue.city,
      "state": venue.state,
      "phone": venue.phone,
      "website": venue.website,
      "facebook_link": venue.facebook_link,
      "seeking_talent": True if venue.seeking_talent else False,
      "image_link": venue.image_link,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows)
    }
       
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = VenueForm(request.form)
  error = False
  
  # For genres, check if exists in genre table. Use id if exists
  # If genre doesnt exist, add it to the genre table
  # insert venue and genre to venue_genre table
  try:
      venue = Venue(
        name = form.name.data,
        city = form.city.data,
        state = form.state.data,
        address = form.address.data,
        phone = form.phone.data,
        image_link = form.image_link.data,
        facebook_link = form.facebook_link.data,
        seeking_talent = True if form.seeking_talent.data else False,
        seeking_description = form.seeking_description.data,
        website = form.website.data
      )

      db.session.add(venue)
      db.session.flush()

      for name in form.genres.data:
        #genre = db.session.query(Genre).filter_by(name=genre_name)
        genre = Genre.query.filter_by(name = name).first()
        print(genre)
        if genre is None:
          # insert into Genre table
          genre = Genre(name = name)
          db.session.add(genre)
          db.session.flush()
        
        add_venue_genre = venue_genre.insert().values(
          venue_id = venue.id,
          genre_id = genre.id
        )

        db.session.execute(add_venue_genre)        

      db.session.commit()
  except Exception as e:
      db.session.rollback()
      error = True
      print(sys.exc_info())
      print(e)
  finally:
      db.session.close()

  # on successful db insert, flash success
  #flash('Venue ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  if error:
    flash('An error occurred. Venue ' + request.form['name']+ ' could not be listed.')
  else:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  
  all_artists = Artist.query.all()

  data = [
    {
      "id": artist.id,
      "name": artist.name,
    }
    for artist in all_artists
  ]

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  
  search_str = request.form.get('search_term', '')
  search_format = "%{}%".format(search_str.lower())
  search_results = Artist.query.filter(func.lower(Artist.name).like(search_format)).all()

  data = []
  for artist in search_results:
    upcoming_shows_for_artist = Show.query.filter(Show.artist_id == artist.id).filter(Show.start_time > datetime.now()).all()
    data.append({
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": len(upcoming_shows_for_artist)
    })

  response = {
    "count": len(search_results),
    "data": data
  }
  
  return render_template('pages/search_artists.html', results=response, search_term=search_str)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id  
  artist = Artist.query.get(artist_id)
  data = {}
  if artist:
    # retrieve shows for the venue
    query = db.session.query(Show, Venue).filter(Show.artist_id == artist.id).filter(Venue.id == Show.venue_id).all()
    
    upcoming_shows = [
      {
        "venue_id": rec.Venue.id,
        "venue_name": rec.Venue.name,
        "venue_image_link": rec.Venue.image_link,
        "start_time": rec.Show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      }
      for rec in query if rec.Show.start_time > datetime.now()
    ]
    past_shows = [
      {
        "venue_id": rec.Venue.id,
        "venue_name": rec.Venue.name,
        "venue_image_link": rec.Venue.image_link,
        "start_time": rec.Show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      }
      for rec in query if rec.Show.start_time <= datetime.now()
    ]       

    data = {
      "id": artist.id,
      "name": artist.name,
      "genres": [genre.name for genre in artist.genres],
      "city": artist.city,
      "state": artist.state,
      "phone": artist.phone,
      "website": artist.website,
      "facebook_link": artist.facebook_link,
      "seeking_venue": True if artist.seeking_venue else False,
      "seeking_description": artist.seeking_description,
      "image_link": artist.image_link,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows)
    }
 
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)

  if artist:
    form.name.data = artist.name
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.image_link.data = artist.image_link
    form.genres.data = [genre.name for genre in artist.genres]
    form.facebook_link.data = artist.facebook_link
    form.website.data = artist.website
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description

  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  form = ArtistForm(request.form)
  artist = Artist.query.get(artist_id)

  if artist:
    artist.name = form.name.data
    artist.city = form.city.data
    artist.phone = form.phone.data
    artist.state = form.state.data
    artist.image_link = form.image_link.data
    artist.facebook_link = form.facebook_link.data
    artist.website = form.website.data
    artist.seeking_venue = True if form.seeking_venue else False
    artist.seeking_description = form.seeking_description.data

    db.session.add(artist)
    db.session.flush()

    # delete all genres for the artist in artist_genre table and recreate them
    # not ideal, but easiest solution
    delete_artist_genre = artist_genre.delete().where(artist_genre.c.artist_id == artist_id)
    db.session.execute(delete_artist_genre)

    for name in form.genres.data:
      genre = Genre.query.filter_by(name = name).first()
      print(genre)
      if genre is None:
        # insert into Genre table
        genre = Genre(name = name)
        db.session.add(genre)
        db.session.flush()
      
      add_artist_genre = artist_genre.insert().values(
        artist_id = artist.id,
        genre_id = genre.id
      )

      db.session.execute(add_artist_genre)

    db.session.commit()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)

  if venue:
    # populate form for loading the UI
    form.name.data = venue.name
    form.phone.data = venue.phone
    form.state.data = venue.state
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description
    form.website.data = venue.website
    form.address.data = venue.address
    form.city.data = venue.city
    form.facebook_link.data = venue.facebook_link
    form.image_link.data = venue.image_link
    form.genres.data = [genre.name for genre in venue.genres]
  
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  form = VenueForm(request.form)
  venue = Venue.query.get(venue_id)

  if venue:
    # update venue object with form data
    venue.name = form.name.data
    venue.city = form.city.data
    venue.state = form.state.data
    venue.address = form.address.data
    venue.phone = form.phone.data
    venue.image_link = form.image_link.data
    venue.facebook_link = form.facebook_link.data
    venue.seeking_talent = form.seeking_talent.data
    venue.seeking_description = form.seeking_description.data
    venue.website = form.website.data
    
    
    db.session.add(venue)
    db.session.flush()

    # delete all genres for the venue in venue_genre table and recreate them
    # not ideal, but easiest solution
    delete_venue_genre = venue_genre.delete().where(venue_genre.c.venue_id == venue_id)
    db.session.execute(delete_venue_genre)

    for name in form.genres.data:
      #genre = db.session.query(Genre).filter_by(name=genre_name)
      genre = Genre.query.filter_by(name = name).first()
      print(genre)
      if genre is None:
        # insert into Genre table
        genre = Genre(name = name)
        db.session.add(genre)
        db.session.flush()
      
      add_venue_genre = venue_genre.insert().values(
        venue_id = venue.id,
        genre_id = genre.id
      )

      db.session.execute(add_venue_genre)

    db.session.commit()
    
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = ArtistForm(request.form)
  error = False
  
  artist = Artist(
      name = form.name.data,
      city = form.city.data,
      state = form.state.data,
      phone = form.phone.data,
      image_link = form.image_link.data,
      facebook_link = form.facebook_link.data,
      website = form.website.data,
      seeking_venue = True if form.seeking_venue.data else False,
      seeking_description = form.seeking_description.data
    )

  try:
    db.session.add(artist)
    db.session.flush()

    for name in form.genres.data:
      genre = Genre.query.filter_by(name = name).first()
      print(genre)
      if genre is None:
        # insert into Genre table
        genre = Genre(name = name)
        db.session.add(genre)
        db.session.flush()
      
      add_artist_genre = artist_genre.insert().values(
        artist_id = artist.id,
        genre_id = genre.id
      )

      db.session.execute(add_artist_genre) 
    
    db.session.commit()
      
  except Exception as e:
    db.session.rollback()
    error = True
    print(sys.exc_info())
    print(e)
  finally:
    db.session.close()
  # on successful db insert, flash success
  # flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')

  if error:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  else:
    flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  shows = Show.query.all()
  data = []
  
  for show in shows:
    artist = Artist.query.get(show.artist_id)
    venue = Venue.query.get(show.venue_id)
    data.append({
      "venue_id": venue.id,
      "venue_name": venue.name,
      "artist_id": artist.id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  if len(data) == 0:
    flash("There are no shows to list.")

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  form = ShowForm(request.form)

  # Query DB if the provided artist and venue exist
  venue = Venue.query.get(form.venue_id.data)
  artist = Artist.query.get(form.artist_id.data)

  if venue and artist:
    show = Show(
      artist_id = form.artist_id.data,
      venue_id = form.venue_id.data,
      start_time = form.start_time.data
    )

    db.session.add(show)
    db.session.commit()

    flash('Show was successfully listed!')
  else:
    flash('An error occurred. Show could not be listed.')
  # on successful db insert, flash success
  
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
