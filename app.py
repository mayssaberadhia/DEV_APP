from flask import Flask, render_template, request, redirect, url_for, flash
from bson import ObjectId
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from pymongo import MongoClient
from flask_pymongo import PyMongo
import secrets

secret_key = secrets.token_hex(24)

app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
app.config['MONGO_URI'] = 'mongodb://localhost:27017/project'
# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017"
client = MongoClient(MONGO_URI)
db = client['project'] 
employees_collection = db['employes']
mongo = PyMongo(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_id, username, password):
        self.id = str(user_id)
        self.username = username
        self.password = password

    @staticmethod
    def check_password(entered_password, stored_password):
        return entered_password == stored_password

    @classmethod
    def get(cls, user_id):
        user_data = db.users.find_one({'_id': user_id})
        if user_data:
            return cls(user_data['_id'], user_data['username'], user_data['password'])
        return None

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)
@app.route('/')
def root():
    return redirect(url_for('login'))
@app.route('/index')

def index():
   
    search_term = request.args.get('search', '')
    search_criteria = request.args.get('criteria', 'nom')  

   
    filter_criteria = {}

    if search_term:
        if search_criteria in ('anciennete', 'prime'):
          
            try:
                search_term = int(search_term)
                filter_criteria[search_criteria] = search_term
            except ValueError:
              
                pass
        else:
            
            filter_criteria[search_criteria] = {"$regex": search_term, "$options": "i"}

    
    employes = employees_collection.find(filter_criteria) if filter_criteria else employees_collection.find()

    return render_template('index.html', employes=employes, current_user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        print(f"Attempting login for user: {username}")

        user_data = db.users.find_one({'username': username})

        if user_data:
            user_obj = User(user_data['_id'], user_data['username'], user_data['password'])
            print("User object created:", user_obj)

            if user_obj and user_obj.check_password(password, user_data['password']):
                print("Password is correct. Logging in...")
                login_user(user_obj)
                print("Redirecting to index...")
                return redirect(url_for('index'))
            else:
                print("Incorrect username or password")
                flash('Incorrect username or password. Please verify your credentials.', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/add', methods=['GET', 'POST'])
def add_employee():
    if request.method == 'POST':
       
        nom = request.form.get('nom')
        prenom = request.form.get('prenom')
        anciennete = int(request.form.get('anciennete'))
        tel = request.form.get('tel')
        rue = request.form.get('rue')
        codepostal = request.form.get('codepostal')
        ville = request.form.get('ville')
        prime = float(request.form.get('prime'))

        # Create a new employee document
        new_employee = {
            'nom': nom,
            'prenom': prenom,
            'anciennete': anciennete,
            'tel': tel,
            'adresse': {
                'rue': rue,
                'codepostal': codepostal,
                'ville': ville
            },
            'prime': prime
        }

        # Insert the new employee into the database
        employees_collection.insert_one(new_employee)

        # Flash a success message
        flash('Employee successfully added!', 'success')

        # Redirect to the index page
        return redirect(url_for('index'))

    return render_template('add_employee.html')

@app.route('/delete/<employee_id>')
def delete_employee(employee_id):
    # Find the employee by ID and delete
    employees_collection.delete_one({'_id': ObjectId(employee_id)})

    # Redirect to the index page
    flash('Employee successfully deleted!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
