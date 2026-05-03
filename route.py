from flask import Blueprint, render_template, request, redirect, session
from auth import register_user

# Create the Blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route("/signup", methods=["POST"])
def signup():
    user = request.form.get("username")
    pwd = request.form.get("password")
    
    if not user or not pwd:
        return render_template("login.html", error="Username and password are required.", show_signup=True)
        
    success, msg = register_user(user, pwd)
    if success:
        return render_template("login.html", success="Registration successful! You can now log in.")
    else:
        return render_template("login.html", error=msg, show_signup=True)

@main_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/")