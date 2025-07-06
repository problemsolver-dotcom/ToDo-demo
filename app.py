from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Change this for production

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///todo.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    todos = db.relationship('Todo', backref='user', lazy=True)


# Todo model
class Todo(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.String(500), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


@app.route("/", methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        return redirect("/login")

    if request.method == "POST":
        title = request.form.get('title', '').strip()
        desc = request.form.get('desc', '').strip()
        if title and desc:
            todo = Todo(title=title, desc=desc, user_id=session['user_id'])
            db.session.add(todo)
            db.session.commit()

    user_todos = Todo.query.filter_by(user_id=session['user_id']).all()
    return render_template('index.html', allTodo=user_todos)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        if User.query.filter_by(username=username).first():
            flash("Username already exists.")
            return redirect("/register")

        hashed_password = generate_password_hash(password)
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful. Please log in.")
        return redirect("/login")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash("Logged in successfully.")
            return redirect("/")
        else:
            flash("Invalid username or password.")
            return redirect("/login")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop('user_id', None)
    flash("You have been logged out.")
    return redirect("/login")


@app.route("/update/<int:sno>", methods=['GET', 'POST'])
def update(sno):
    if 'user_id' not in session:
        return redirect("/login")

    todo = Todo.query.filter_by(sno=sno, user_id=session['user_id']).first()
    if not todo:
        flash("Todo not found.")
        return redirect("/")

    if request.method == 'POST':
        title = request.form['title'].strip()
        desc = request.form['desc'].strip()
        if title and desc:
            todo.title = title
            todo.desc = desc
            db.session.commit()
            flash("Todo updated successfully.")
            return redirect("/")
    return render_template('update.html', todo=todo)


@app.route("/delete/<int:sno>")
def delete(sno):
    if 'user_id' not in session:
        return redirect("/login")

    todo = Todo.query.filter_by(sno=sno, user_id=session['user_id']).first()
    if todo:
        db.session.delete(todo)
        db.session.commit()
        flash("Todo deleted.")
    return redirect("/")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8000)
