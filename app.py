from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import boto3
from botocore.exceptions import NoCredentialsError
import secrets
import string

def random_string(length):
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

s3 = boto3.client('s3', aws_access_key_id=os.environ.get('ACCESS_KEY'), aws_secret_access_key=os.environ.get('SECRET_ACCESS_KEY'))

app = Flask(__name__)
app.config['S3_BUCKET_NAME'] = os.environ.get('BUCKET_NAME')
app.secret_key = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] =  os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')

db = SQLAlchemy(app)

def upload_to_s3(file, bucket_name, filename):
    imageName =  f"{filename}-{random_string(10)}"
    print(imageName)

    try:
        s3.upload_fileobj(file, bucket_name, imageName)
        url = f"https://{bucket_name}.s3.amazonaws.com/{imageName}"
        return url
    except NoCredentialsError:
        print("Error: Invalid AWS credentials")
        return None
    except Exception as e:
        print("Error: ", e)
        return None

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
        image_url = upload_to_s3(image, 'date-app', filename)

        if not image_url:
            flash('An error occurred while uploading the image to S3.', 'error')
            return render_template('add_location.html')

        new_location = Location(name=name, address=address, rating=rating, image=image_url, latitude=latitude, longitude=longitude)
        db.session.add(new_location)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('add_location.html', GOOGLE_MAPS_API_KEY=GOOGLE_MAPS_API_KEY)

@app.route('/location_details/<int:location_id>')
def location_details(location_id):
    location = Location.query.get_or_404(location_id)
    return render_template('location_details.html', location=location, location_id=location_id,GOOGLE_MAPS_API_KEY=GOOGLE_MAPS_API_KEY)

@app.route('/edit_location/<int:location_id>', methods=['GET', 'POST'])
def edit_location(location_id):
    location = Location.query.get_or_404(location_id)
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        rating = request.form['rating']
        image = request.files['image']
        latitude = float(request.form['latitude'])
        longitude = float(request.form['longitude'])
        filename = secure_filename(image.filename)

        if image:
            image_url = upload_to_s3(image, os.environ.get('BUCKET_NAME'), filename)
            if not image_url:
                flash('An error occurred while uploading the image to S3.', 'error')
                return render_template('edit_location.html', location=location, location_id=location_id,GOOGLE_MAPS_API_KEY=GOOGLE_MAPS_API_KEY)
        else:
            image_url = location.image

        location.name = name
        location.address = address
        location.rating = int(rating)
        location.image = image_url
        location.latitude = latitude
        location.longitude = longitude

        db.session.commit()

        return redirect(url_for('location_details', location_id=location_id))

    return render_template('edit_location.html', location=location, location_id=location_id)

@app.route('/delete_location/<int:location_id>', methods=['POST'])
def delete_location(location_id):
    location = Location.query.get_or_404(location_id)
    if location:
        db.session.delete(location)
        db.session.commit()
        flash('Lokalizacja została usunięta.', 'success')
    else:
        flash('Lokalizacja nie istnieje.', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)