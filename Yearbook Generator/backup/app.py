from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import os
from fpdf import FPDF
from flask_mysqldb import MySQL

app = Flask(__name__)

# Configurations
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure the upload directory exists

# MySQL Config
app.config['MYSQL_HOST'] = '127.0.0.1'  # Use 127.0.0.1 instead of 'localhost'
app.config['MYSQL_USER'] = 'root'  # Replace with your MySQL username
app.config['MYSQL_PASSWORD'] = '1234'  # Replace with your MySQL password
app.config['MYSQL_DB'] = 'yearbook_db'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# PDF Generation Class
class YearbookPDF(FPDF):
    def header(self):
        self.set_font("Arial", style='B', size=16)
        self.cell(0, 10, "Yearbook", ln=True, align='C')
        self.ln(10)

    def add_photo_page(self, img_path, description):
        self.add_page()
        if os.path.exists(img_path):
            self.image(img_path, x=50, y=40, w=100)
        self.set_xy(20, 150)
        self.set_font("Arial", size=12)
        self.multi_cell(0, 10, description, align='C')

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        try:
            cursor = mysql.connection.cursor()

            # Correct SQL query with proper placeholders
            query = "SELECT * FROM users WHERE username = %s AND password = %s AND email = %s"
            cursor.execute(query, (username, password, email))

            user = cursor.fetchone()  # Fetch the user data if found
            cursor.close()

            if user:
                return render_template('signed_index.html', username=username)
            else:
                return render_template('Error.html', message="Invalid credentials. Please try again.")

        except Exception as e:
            return f"Database error: {str(e)}"

    return render_template('login.html')



@app.route('/signup', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        try:
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()

            if user:
                cursor.close()
                return render_template('Error1.html', username=username)
            else:
                cursor.execute("INSERT INTO users (username,password,email) VALUES (%s, %s,%s)", (username, password,email))
                mysql.connection.commit()
                cursor.close()
                return render_template('Registered.html', username=username)
        except Exception as e:
            return f"Database error: {str(e)}"

    return render_template('signup.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        new_password = request.form['new_password']

        try:
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()

            if user:
                cursor.execute("UPDATE users SET password = %s WHERE username = %s", (new_password, username))
                mysql.connection.commit()
                cursor.close()
                return redirect(url_for('signin'))
            else:
                cursor.close()
                return render_template('Error2.html', message="Username not found.")
        except Exception as e:
            return f"Database error: {str(e)}"

    return render_template('forgot_password.html')

@app.route('/view_yearbook')
def view_yearbook():
    yearbook_data = {}
    upload_dir = 'uploads'

    if os.path.exists(upload_dir):
        for month in os.listdir(upload_dir):
            month_dir = os.path.join(upload_dir, month)
            if os.path.isdir(month_dir):
                photos = [f'/uploads/{month}/{photo}' for photo in os.listdir(month_dir)]
                yearbook_data[month] = photos

    return render_template('view_yearbooks.html', yearbook_data=yearbook_data)

@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/create_yearbook', methods=['GET', 'POST'])
def create_yearbook():
    if request.method == 'POST':
        template = request.form.get('template')

        months_photos = {}
        months_descriptions = {}

        months = [
            "January", "February", "March", "April", "May", "June", 
            "July", "August", "September", "October", "November", "December"
        ]

        for month in months:
            months_photos[month] = request.files.getlist(f"photos_{month}")
            months_descriptions[month] = request.form.get(f"highlights_{month}", "")

        pdf = YearbookPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        for month in months:
            description = months_descriptions[month]

            for photo in months_photos[month][:10]:  # Limit to 10 photos per month
                if photo.filename and allowed_file(photo.filename):
                    filename = secure_filename(photo.filename)
                    month_folder = os.path.join(UPLOAD_FOLDER, month)
                    os.makedirs(month_folder, exist_ok=True)
                    img_path = os.path.join(month_folder, filename)
                    photo.save(img_path)
                    pdf.add_photo_page(img_path, description)

        pdf_path = os.path.join(UPLOAD_FOLDER, "yearbook.pdf")
        pdf.output(pdf_path)

        return render_template('YearbookCreated.html', pdf_path=pdf_path)

    return render_template('book_input_display.html')

@app.route('/book')
def book():
    return render_template('book.html')

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
