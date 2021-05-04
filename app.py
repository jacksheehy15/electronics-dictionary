import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_items")
def get_items():
    items = list(mongo.db.items.find())
    return render_template("items.html", items=items)


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    items = list(mongo.db.items.find({"$text": {"$search": query}}))
    return render_template("items.html", items=items)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username Already Taken, Try Again!")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("profile", username=session["user"]))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome, {}".format(request.form.get("username")))
                return redirect(url_for(
                    "profile", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from database
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # remove user from session cookie
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_item", methods=["GET", "POST"])
def add_item():
    if request.method == "POST":
        item = {
            "category_name": request.form.get("category_name"),
            "item_name": request.form.get("item_name"),
            "item_description": request.form.get("item_description"),
            "created_by": session["user"]
        }
        mongo.db.items.insert_one(item)
        flash("Item Added to Dictionary")
        return redirect(url_for("get_items"))

    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("add_item.html", categories=categories)


@app.route("/edit_item/<item_id>", methods=["GET", "POST"])
def edit_item(item_id):
    if request.method == "POST":
        submit = {
            "category_name": request.form.get("category_name"),
            "item_name": request.form.get("item_name"),
            "item_description": request.form.get("item_description"),
            "created_by": session["user"]
        }
        mongo.db.items.update({"_id": ObjectId(item_id)}, submit)
        flash("Task Successfully Updated")

    item = mongo.db.items.find_one({"_id": ObjectId(item_id)})
    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("items.html", item=item, categories=categories)


@app.route("/delete_item/<item_id>")
def delete_item(item_id):
    mongo.db.items.remove({"_id": ObjectId(item_id)})
    flash("Item Successfully Deleted!")
    return redirect(url_for("get_items"))


@app.route("/get_categories")
def get_categories():
    categories = list(mongo.db.categories.find().sort("category_name", 1))
    return render_template("categories.html", categories=categories)


@app.route("/delete")
def delete():
    """ Load Delete Account Page """
    if 'user' not in session:
        return redirect(url_for("login"))
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    return render_template("delete_account.html", username=username)


@app.route("/delete_user")
def delete_user():
    """ Delete user from MongoDB """
    if 'user' not in session:
        return redirect(url_for("login"))
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    mongo.db.users.delete_one({"username": username})
    session.clear()
    return render_template("register.html", username=username)


@app.route("/dictionary")
def dictionary():
    dictionary = list(mongo.db.items.find())
    return render_template("items.html", dictionary=dictionary)


@app.route("/add_category", methods=["GET", "POST"])
def add_category():
    if request.method == "POST":
        category = {
            "category_name": request.form.get("category_name")
        }
        mongo.db.categories.insert_one(category)
        flash("You have added a new category successfully!")
        return redirect(url_for("get_categories"))

    return render_template("add_category.html")


@app.route("/edit_category/<category_id>", methods=["GET", "POST"])
def edit_category(category_id):
    if request.method == "POST":
        submit = {
            "category_name": request.form.get("category_name")
        }
        mongo.db.categories.update({"_id": ObjectId(category_id)}, submit)
        flash("You have updated a category successfully!")
        return redirect(url_for("get_categories"))
    category = mongo.db.categories.find_one({"_id": ObjectId(category_id)})
    return render_template("edit_category.html", category=category)


@app.route("/delete_category/<category_id>")
def delete_category(category_id):
    mongo.db.categories.remove({"_id": ObjectId(category_id)})
    flash("You have deleted a category successfully!")
    return redirect(url_for("get_categories"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
