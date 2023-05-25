import os
import uuid as uuid
from time import time
from datetime import datetime

from flask import Blueprint, session, redirect, render_template, url_for, flash, request, jsonify, current_app
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from webapp import db
from webapp.models import User, Skills, Project, Message, Notification
from .forms import UserForm, SkillForm, EmptyForm, MessageForm, SearchForm


ALLOWED_EXTENSIONS = set(["png", "jpg", "jpeg", "gif"])


bp = Blueprint("user", __name__, template_folder="templates/user", static_folder="static")


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route("/")
def index():
    form = EmptyForm()
    q = request.args.get("q")
    if q:
        users = User.query.filter(single_user.title.contains(q) | User.body.contains(q))
    else:
        users = User.query.order_by(User.created_at.desc())
    page = request.args.get("page")
    if page and page.isdigit():
        page = int(page)
    else:
        page = 1
    pages = users.paginate(page=page, per_page=current_app.config["POSTS_PER_PAGE"])
    return render_template("user/index.html", users=users, form=form, pages=pages)


@bp.route("/user/<int:user_id>")
@login_required
def single_user(user_id):
    form = EmptyForm
    user = User.query.filter_by(id=user_id).first()
    skills = Skills.query.filter_by(user_id=user.id)
    projects = Project.query.filter_by(user_id=user.id)

    return render_template("user/single_user.html", user=user, skills=skills, projects=projects, form=form)


@bp.route("/user")
@login_required
def account():
    skills = Skills.query.filter_by(user_id=current_user.id)
    projects = Project.query.filter_by(user_id=current_user.id)

    return render_template("user/account.html", skills=skills, projects=projects, user=current_user)


@bp.route("/edit/", methods=["GET", "POST"])
@login_required
def edit_user():
    user = User.query.filter_by(id=current_user.id).first()

    form = UserForm(obj=user)
    if form.validate_on_submit():
        user.fullname = form.fullname.data
        user.intro = form.intro.data
        user.about_me = form.about_me.data
        user.location = form.location.data
        user.social_github = form.social_github.data
        user.social_stakoverflow = form.social_stakoverflow.data
        user.social_twitter = form.social_twitter.data
        user.social_linkedin = form.social_linkedin.data
        user.social_website = form.social_website.data

        file = request.files["inputFile"]
        filename = secure_filename(file.filename)
        pic_name = str(uuid.uuid1()) + "_" + filename
        if file and allowed_file(file.filename):
            file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], pic_name))
            user.profile_pic = pic_name

        db.session.commit()
        return redirect(url_for(".account"))

    return render_template("user/edit_user.html", user=user, form=form)


@bp.route("/add/skill/", methods=["GET", "POST"])
@login_required
def add_skill():
    user = User.query.filter_by(id=current_user.id).first()

    form = SkillForm()
    if form.validate_on_submit():
        skill = Skills(skill=form.skill.data, description=form.description.data, user_id=user.id)
        db.session.add(skill)
        db.session.commit()

        return redirect(url_for(".account"))

    return render_template("user/skill_form.html", user=user, form=form)


@bp.route("/edit/skill/<int:skill_id>", methods=["GET", "POST"])
@login_required
def edit_skill(skill_id):
    skill = Skills.query.filter_by(id=skill_id).first()

    form = SkillForm(obj=skill)
    if form.validate_on_submit():
        skill.skill = form.skill.data
        skill.description = form.description.data

        db.session.commit()
        return redirect(url_for(".account"))

    return render_template("user/skill_form.html", form=form)


@bp.route("/delete/<int:skill_id>", methods=["GET", "POST"])
@login_required
def delete_skill(skill_id):
    skill = Skills.query.filter_by(id=skill_id).first()

    db.session.delete(skill)
    db.session.commit()
    flash("The skill has been deleted", "success")
    return redirect(url_for(".account"))


@bp.route("/follow/username", methods=["POST"])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            return redirect(url_for(".index"))
        if user == current_user:
            return redirect(url_for(".single_user", user_id=user.id))
        current_user.follow(user)
        db.session.commit()
        return redirect(url_for(".single_user", user_id=user.id))
    else:
        return redirect(url_for(".single_user", user_id=user.id))


@bp.route("/unfollow/<int:user_id>", methods=["POST"])
@login_required
def unfollow(user_id):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            return redirect(url_for(".single_user", user_id=user.id))
        if user == current_user:
            return redirect(url_for(".single_user", user_id=user.id))
        current_user.unfollow(user)
        db.session.commit()
        return redirect(url_for("user.single_user", user_id=user.id))
    else:
        return redirect(url_for("user.single_user", user_id=user.id))


@bp.route("/send_message/<recipient>", methods=["GET", "POST"])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm(obj=user)
    if form.validate_on_submit():
        msg = Message(subject=form.subject.data, body=form.body.data, sender_id=current_user.id, recipient_id=user.id)
        db.session.add(msg)
        user.add_notification("unread_message_count", user.new_messages())
        db.session.commit()
        flash("Your message has been sent.", "success")
        return redirect(url_for("user.single_user", user_id=user.id))
    return render_template("user/message_form.html", form=form, user=user)


@bp.route("/inbox/")
@login_required
def messages():
    unread_messages = current_user.unread_messages()
    unreadCount = unread_messages.count()
    messages = current_user.messages_received.order_by(Message.created_at.desc())
    return render_template(
        "user/inbox.html", messages=messages, unreadCount=unreadCount, unread_messages=unread_messages
    )


@bp.route("/inbox/message/<int:message_id>")
@login_required
def single_message(message_id):
    unread_messages = current_user.unread_messages()
    unreadCount = unread_messages.count() - 1
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification("unread_message_count", unreadCount)
    db.session.commit()
    message = Message.query.filter_by(id=message_id).first_or_404()

    return render_template(
        "user/message.html", message=message, unreadCount=unreadCount, unread_messages=unread_messages
    )


@bp.route("/delete/<int:message_id>", methods=["GET", "POST"])
@login_required
def delete_message(message_id):
    message = Message.query.filter_by(id=message_id).first_or_404()
    db.session.delete(message)
    db.session.commit()
    flash("The message has been deleted!", "success")
    return redirect(url_for("profile.messages"))


@bp.route("/notifications")
@login_required
def notifications():
    since = request.args.get("since", 0.0, type=float)
    notifications = current_user.notifications.filter(Notification.created_at > since).order_by(
        Notification.created_at.asc()
    )
    return jsonify([{"name": n.name, "data": n.get_data(), "created_at": n.created_at} for n in notifications])


@bp.route("/search", methods=["POST"])
@login_required
def search():
    form = SearchForm()
    users = User.query
    if form.validate_on_submit():
        single_user.searched = form.searched.data
        users = users.filter(
            User.about_me.like("%" + single_user.searched + "%")
            | User.fullname.like("%" + single_user.searched + "%")
            | User.about_me.like("%" + single_user.searched + "%")
            | User.intro.like("%" + single_user.searched + "%")
        )
        users = users.order_by(User.fullname).all()

    return render_template("user/search.html", form=form, searched=single_user.searched, users=users)


@bp.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


@bp.get("/toggle-theme")
def toggle_theme():
    current_theme = session.get("theme")
    if current_theme == "dark":
        session["theme"] = "light"
    else:
        session["theme"] = "dark"

    return redirect(request.args.get("current_page"))


@bp.route("/", defaults={"path": ""})
@bp.route("/<path:path>")
def catch_all(path):
    return render_template("errors/404.html"), 404
