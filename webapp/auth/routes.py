from flask import Blueprint, redirect, url_for, request, render_template, flash, abort, current_app
from flask_login import login_user, logout_user, current_user

from webapp import db
from webapp.models import User
from webapp.auth.email import send_password_reset_email
from .forms import RegistrationForm, LoginForm, ResetPasswordRequestForm, ResetPasswordForm


bp = Blueprint("auth", __name__, template_folder="templates/auth", static_folder="static")


@bp.route("/register", methods=["POST", "GET"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("user.index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        try:
            db.session.commit()
            flash(message="Congratulations, you are now a registered user!", category="success")
            return redirect(url_for("auth.login"))
        except Exception as e:
            db.session.rollback()
            current_app.logger.critical(f"Something went wrong: {e}")
            current_app.logger.exception(e)
            flash(message=f"Something went wrong: {e}", category="danger")
            return redirect(url_for("auth.register"))

    return render_template("auth/register.html", title="Register", form=form)


@bp.route("/login", methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        redirect(url_for("user.index", user_id=current_user.id))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password", "danger")
            return redirect(url_for("auth.login"))
        login_user(user, remember=True)
        return redirect(url_for("user.index"))

    return render_template("auth/login.html", form=form)


@bp.route("/logout")
def logout():
    logout_user()
    flash("Your are logged out", "info")

    return redirect(url_for("auth.login"))


@bp.route("/reset_password_request", methods=["GET", "POST"])
def reset_pwd_request():
    if current_user.is_authenticated:
        redirect(url_for("user.index"))

    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
            return redirect(url_for("auth.reset_pwd_sent"))
        else:
            flash("You are not yet an user. Please register", "error")
            abort(404)
    return render_template("auth/reset_password_request.html", title="Reset Password", form=form)


@bp.route("/reset_password_sent")
def reset_pwd_sent():
    return render_template("auth/reset_password_sent.html")


@bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_pwd(token):
    if current_user.is_authenticated:
        redirect(url_for("user.index"))

    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for("user.index"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        if form.password.data != form.confirm_password.data:
            flash("Your passwords does not match", "error")
        else:
            user.set_password(form.password.data)
            try:
                db.session.commit()
                flash(message="Your password has been reset.", category="success")
                return redirect(url_for("auth.reset_pwd_complete"))
            except Exception as e:
                db.session.rollback()
                current_app.logger.critical(f"Something went wrong: {e}")
                current_app.logger.exception(e)
                flash(message=f"Something went wrong: {e}", category="danger")
                return redirect(url_for("auth.reset_pwd", token=token))

    return render_template("auth/reset_password.html", form=form)


@bp.route("/reset_password_complete")
def reset_pwd_complete():
    return render_template("auth/reset_password_complete.html")


@bp.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404
