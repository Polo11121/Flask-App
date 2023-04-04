from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

def __init__(self, name, address, rating, image, latitude, longitude):
    self.name = name
    self.address = address
    self.rating = rating
    self.image = image
    self.latitude = latitude
    self.longitude = longitude

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    locations = Location.query.all()
    return render_template('index.html', locations=locations)

@app.route('/add_location', methods=['GET', 'POST'])
def add_location():
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        rating = int(request.form['rating'])
        image = request.files['image']
        filename = secure_filename(image.filename)
        latitude = float(request.form['latitude'])
        longitude = float(request.form['longitude'])

        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_location = Location(name=name, address=address, rating=rating, image=filename, latitude=latitude, longitude=longitude)
        db.session.add(new_location)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('add_location.html')

@app.route('/location_details/<int:location_id>')
def location_details(location_id):
    location = Location.query.get_or_404(location_id)
    return render_template('location_details.html', location=location, location_id=location_id)

@app.route('/edit_location/<int:location_id>', methods=['GET', 'POST'])
def edit_location(location_id):
    location = Location.query.get_or_404(location_id)
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        rating = request.form['rating']
        image = request.files['image']
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        latitude = float(request.form['latitude'])
        longitude = float(request.form['longitude'])

        location.name = name
        location.address = address
        location.rating = int(rating)
        location.image = filename
        location.latitude = latitude
        location.longitude = longitude

        db.session.commit()

        return redirect(url_for('location_details', location_id=location_id))

    return render_template('edit_location.html', location=location, location_id=location_id)

@app.route('/delete_location/<int:location_id>', methods=['POST'])
def delete_location(location_id):
    location = Location.query.get_or_404(location_id)
    if location:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], location.image))
        db.session.delete(location)
        db.session.commit()
        flash('Lokalizacja została usunięta.', 'success')
    else:
        flash('Lokalizacja nie istnieje.', 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)