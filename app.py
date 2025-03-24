from flask import Flask,request,flash,render_template,url_for,redirect,session,send_file
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager,UserMixin,login_user,login_required,logout_user,current_user
import os
from werkzeug.utils import secure_filename
import cv2
from PIL import Image
from io import BytesIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
UPLOAD_FOLDER = '/Users/ricardjossemeyer/Documents/python/Training project/Image processing service/static'
app.config['UPLOAD_FOLDER'] = os.path.join('static')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
class User(db.Model,UserMixin):
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(20),unique=True,nullable=False)
    email = db.Column(db.String(120),unique=True,nullable=False)
    password = db.Column(db.String(60),nullable=False)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
@app.route('/register',methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        hashed_password =  bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username,email=email,password=hashed_password)
        db.session.add(user)
        db.session.commit()
        print('Account created successfully')
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password,password):
            login_user(user)
            print('Login successful')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            print('Fail to log in')
            flash('Login failed. Check your email and password', 'danger')
    return render_template('login.html')
@app.route('/home')
@login_required
def home():
    logo_image = session.get('uploaded_logo')
    uploaded_image = session.get('uploaded_image')
    return render_template('home.html', logo_image=logo_image,uploaded_image=uploaded_image)
ALLOWED_EXTENSIONS = {'png','jpg','jpeg'}
@app.route('/upload',methods=['POST'])
def upload_photo():
    if request.method == 'POST':
        if 'photo' not in request.files:
            print('No file part')
            return redirect(request.url)
        file = request.files['photo']
        if file.filename == '':
            print('No selected file')
            return redirect(request.url)
        if file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'],'uploads', filename)
            file.save(file_path)
            print('File successfully uploaded')
            session['uploaded_image'] = f'uploads/{filename}'
            return redirect(url_for('home'))
        else:
            print('Allowed files are png, jpg, jpeg')
            return redirect(url_for('home'))
@app.route('/upload_logo',methods=['POST'])
def upload_logo():
    if request.method == 'POST':
        if 'logo' not in request.files:
            print('No file_logo part')
            return redirect(request.url)
        file = request.files['logo']
        if file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'],'Logos', filename)
            file.save(file_path)
            print('Logo successfully uploaded')
            session['uploaded_logo'] = f'Logos/{filename}'
            return redirect(url_for('home'))
        else:
            return redirect(url_for('home'))

@app.route('/resize',methods=['POST'])
def resize():
    logo_image = session.get('uploaded_logo')
    if request.method == 'POST':
        width = int(request.form.get('width'))
        height = int(request.form.get('height'))
        uploaded_image = session.get('uploaded_image')
        if not uploaded_image:
            print('No uploaded image found in session')
            return redirect(url_for('home'))
        image_path = os.path.join(app.config['UPLOAD_FOLDER'],uploaded_image)
        image = cv2.imread(image_path)
        if image is None:
            print('Error loading image')
            return redirect(request.url)
        resized_image = cv2.resize(image, (width, height))
        resized_filename = 'resized_' + os.path.basename(uploaded_image)
        resized_image_path = os.path.join(app.config['UPLOAD_FOLDER'],'uploads', resized_filename)
        cv2.imwrite(resized_image_path,resized_image)
        print('Image resized successfully')
        session['uploaded_image'] = f'uploads/{resized_filename}'
        return render_template('home.html', logo_image = logo_image, uploaded_image=f'uploads/{resized_filename}')
@app.route('/crop',methods=['POST'])
def crop():
    logo_image = session.get('uploaded_logo')
    if request.method == 'POST':
        x1 = int(request.form.get('x1'))
        y1 = int(request.form.get('y1'))
        x2 = int(request.form.get('x2'))
        y2 = int(request.form.get('y2'))    
        uploaded_image = session.get('uploaded_image')
        if not uploaded_image:
            print('No uploaded image found in session')
            return redirect(url_for('home'))
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_image)
        image = cv2.imread(image_path)
        if image is None:
            print('Error loading image')
        height,width,_ = image.shape
        if x1 < 0 or y1 < 0 or x2 > width or y2 > height or x1 >= x2 or y1 >= y2:
            print('Invalid crop coordinates')
            return redirect(request.url)
        cropped_image = image[y1:y2,x1:x2]
        cropped_filename = 'cropped_' + os.path.basename(uploaded_image)
        cropped_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'uploads',cropped_filename)
        cv2.imwrite(cropped_image_path, cropped_image)
        print('Image cropped successfully')
        session['uploaded_image'] = f'uploads/{cropped_filename}'
        return render_template('home.html', logo_image = logo_image, uploaded_image=f'uploads/{cropped_filename}')
@app.route('/rotate',methods=['POST'])
def rotate():
    logo_image = session.get('uploaded_logo')
    if request.method == 'POST':
        angle = int(request.form.get('angle'))
        uploaded_image = session.get('uploaded_image')
        if not uploaded_image:
            print('No uploaded image found in session')
            return redirect(url_for('home'))
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_image)
        image = cv2.imread(image_path)
        if image is None:
            print('Error loading image')
            return redirect(request.url)
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated_image = cv2.warpAffine(image, M, (w, h))
        rotated_filename = 'rotated_' + os.path.basename(uploaded_image)
        rotated_image_path = os.path.join(app.config['UPLOAD_FOLDER'],'uploads', rotated_filename)
        cv2.imwrite(rotated_image_path, rotated_image)
        print('Image rotated successfully')
        session['uploaded_image'] = f'uploads/{rotated_filename}'
        return render_template('home.html', logo_image = logo_image, uploaded_image=f'uploads/{rotated_filename}')  
@app.route('/watermark',methods=['POST'])
def watermark():
    logo_filename = session.get('uploaded_logo')
    image_filename = session.get('uploaded_image')
    if logo_filename and image_filename:
        logo_path = os.path.join(app.config['UPLOAD_FOLDER'], logo_filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'],image_filename)
        logo = cv2.imread(logo_path)
        image = cv2.imread(image_path)
        if logo is None or image is None:
            print('Error loading logo or image')
            return redirect(request.url)
        h_logo,w_logo,_ = logo.shape
        h_image,w_image,_ = image.shape
        center_x,center_y = (w_image // 2, h_image // 2)
        top_y = center_y-int(h_logo/2)
        left_x = center_x-int(w_logo/2)
        bottom_y = top_y + h_logo  
        right_x = left_x + w_logo
        destination = image[top_y:bottom_y,left_x:right_x]
        result = cv2.addWeighted(destination,1,logo,0.5,0)
        image[top_y:bottom_y,left_x:right_x] = result
        watermarked_filename = 'watermarked_' + os.path.basename(image_filename)
        watermarked_image_path = os.path.join(app.config['UPLOAD_FOLDER'],'uploads', watermarked_filename)
        cv2.imwrite(watermarked_image_path, image)
        print('Watermark added successfully')
        session['uploaded_image'] = f'uploads/{watermarked_filename}'
        return render_template('home.html', logo_image = logo_filename, uploaded_image=f'uploads/{watermarked_filename}')
    print('No logo or image found in session')
    return redirect(url_for('home'))
@app.route('/flip',methods=['POST'])
def flip():
    image_filename = session.get('uploaded_image')
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
    if not image_filename:
        print('No uploaded image found in session')
        return
    if request.method == 'POST':
        image = cv2.imread(image_path)
        flipped_image = cv2.flip(image, 0) 
        flipped_filename = 'flipped_' + os.path.basename(image_filename)
        flipped_image_path = os.path.join(app.config['UPLOAD_FOLDER'],'uploads', flipped_filename)
        cv2.imwrite(flipped_image_path, flipped_image)
        print('Image flipped successfully')
        session['uploaded_image'] = f'uploads/{flipped_filename}'
        return render_template('home.html', logo_image = session.get('uploaded_logo'), uploaded_image=f'uploads/{flipped_filename}')
@app.route('/mirror',methods=['POST'])
def mirror():
    image_filename = session.get('uploaded_image')
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
    if not image_filename:
        print('No uploaded image found in session')
        return
    if request.method == 'POST':
        image = cv2.imread(image_path)
        mirrored_image = cv2.flip(image, 1) 
        mirrored_filename = 'flipped_' + os.path.basename(image_filename)
        mirrored_image_path = os.path.join(app.config['UPLOAD_FOLDER'],'uploads', mirrored_filename)
        cv2.imwrite(mirrored_image_path, mirrored_image)
        print('Image flipped successfully')
        session['uploaded_image'] = f'uploads/{mirrored_filename}'
        return render_template('home.html', logo_image = session.get('uploaded_logo'), uploaded_image=f'uploads/{mirrored_filename}')
@app.route('/convert',methods=['POST'])
def convert():
    image_filename = session.get('uploaded_image')
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
    if not image_filename:
        print('No uploaded image found in session')
        return
    format_selected = request.form['format'].lower()
    image = Image.open(image_path)
    img_io = BytesIO()
    image.save(img_io,format=format_selected.upper())
    img_io.seek(0)
    return send_file(img_io, mimetype=f'image/{format_selected}', as_attachment=True, download_name=f'converted_image.{format_selected}')
@app.route('/greyscale',methods=['POST'])
def greyscale():
    image_filename = session.get('uploaded_image')
    if not image_filename:
        print('No uploaded image found in session')
    if request.method == 'POST':
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
        image = cv2.imread(image_path)
        greyscaled_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        greyscaled_filename = 'greyscaled_' + os.path.basename(image_filename)
        greyscaled_image_path = os.path.join(app.config['UPLOAD_FOLDER'],'uploads', greyscaled_filename)
        cv2.imwrite(greyscaled_image_path, greyscaled_image)
        session['uploaded_image'] = f'uploads/{greyscaled_filename}'
        print('Image converted to greyscale successfully')
        return render_template('home.html', logo_image = session.get('uploaded_logo'), uploaded_image=f'uploads/{greyscaled_filename}')
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
@app.route('/')
def start():
    return render_template('register.html')
if __name__ == '__main__':
    app.run(debug=True)

