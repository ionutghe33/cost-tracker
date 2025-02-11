from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cost_tracker.db'
app.config['SECRET_KEY'] = 'secretkey'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "home"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Model User
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)

# Model Expense
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)

# Model Budget
class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_budget = db.Column(db.Float, nullable=False, default=0)

# Creare tabele dacă nu există
with app.app_context():
    db.create_all()

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        action = request.form.get("action")
        username = request.form["username"]
        password = request.form["password"]

        if action == "register":
            if User.query.filter_by(username=username).first():
                flash("Numele de utilizator este deja folosit.", "danger")
            else:
                hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
                new_user = User(username=username, password=hashed_password)
                db.session.add(new_user)
                db.session.commit()
                flash("Cont creat cu succes! Te poți autentifica acum.", "success")

        elif action == "login":
            user = User.query.filter_by(username=username).first()
            if user and bcrypt.check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for("dashboard"))
            else:
                flash("Login invalid. Verifică datele introduse.", "danger")

    return render_template("index.html")

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    budget = Budget.query.filter_by(user_id=current_user.id).first()
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    total_expenses = sum(exp.amount for exp in expenses)
    budget_remaining = (budget.total_budget - total_expenses) if budget else 0

    if request.method == "POST":
        action = request.form.get("action")

        if action == "set_budget":
            total_budget = float(request.form["total_budget"])
            if budget:
                budget.total_budget = total_budget
            else:
                budget = Budget(user_id=current_user.id, total_budget=total_budget)
                db.session.add(budget)
            db.session.commit()
            flash("Buget actualizat!", "success")
            return redirect(url_for("dashboard"))

        elif action == "add_expense":
            name = request.form["name"]
            amount = float(request.form["amount"])
            category = request.form["category"]
            new_expense = Expense(user_id=current_user.id, name=name, amount=amount, category=category)
            db.session.add(new_expense)
            db.session.commit()
            flash("Cheltuială adăugată!", "success")
            return redirect(url_for("dashboard"))

    return render_template("dashboard.html", budget=budget, expenses=expenses, budget_remaining=budget_remaining)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Te-ai deconectat cu succes.", "info")
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
