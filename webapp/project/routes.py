import statistics
from flask import Blueprint, session, redirect, render_template, url_for, flash, request, current_app
from flask_login import current_user, login_required
from webapp.models import User, Skills, Project, Comment, Tag, Review
from webapp import db
from .forms import ProjectForm, CommentForm, SearchForm, EmptyForm, VoteForm
from werkzeug.utils import secure_filename
import uuid as uuid
import os

ALLOWED_EXTENSIONS = set(["png", "jpg", "jpeg", "gif"])

bp = Blueprint("project", __name__, template_folder="templates/project", static_folder="static")


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route("/")
@login_required
def projects():
    form = EmptyForm()
    user = User.query.filter_by(id=current_user.id).first()
    projects = Project.query.order_by(Project.created_at.desc())

    page = request.args.get("page")
    if page and page.isdigit():
        page = int(page)
    else:
        page = 1

    pages = projects.paginate(page=page, per_page=current_app.config["POSTS_PER_PAGE"])

    return render_template("project/projects.html", projects=projects, pages=pages, form=form, user=user)


@bp.route("/<int:project_id>", methods=["GET", "POST"])
@login_required
def single_project(project_id):
    project = Project.query.filter_by(id=project_id).first()
    comments = Comment.query.filter_by(project_id=project_id)
    tags = Tag.query.filter_by(project_id=project_id)
    review = Review.query.filter_by(project_id=project_id).filter(Review.user_id == current_user.id).count()

    vote_form = VoteForm()

    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        comment = Comment(content=comment_form.content.data, project_id=project.id, user_id=current_user.id)
        db.session.add(comment)
        db.session.commit()

        project.getVoteCount()

        return redirect(url_for(".single_project", project_id=project.id))

    return render_template(
        "project/single_project.html",
        project=project,
        comments=comments,
        tags=tags,
        comment_form=comment_form,
        review=review,
        vote_form=vote_form,
    )


@bp.route("/add", methods=["GET", "POST"])
@login_required
def add_project():
    user = User.query.filter_by(id=current_user.id).first()

    form = ProjectForm()
    if form.validate_on_submit():
        project = Project(
            title=form.title.data,
            description=form.description.data,
            demo_link=form.demo_link.data,
            source_link=form.source_link.data,
            user_id=current_user.id,
        )

        file = request.files["inputFile"]
        filename = secure_filename(file.filename)
        pic_name = str(uuid.uuid1()) + "_" + filename
        if file and allowed_file(file.filename):
            file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], pic_name))
            project.project_pic = pic_name

        db.session.add(project)
        db.session.commit()

        for tag in form.tag.data:
            tag = Tag(tag=tag, project_id=project.id)
            db.session.add(tag)
            db.session.commit()

        flash("Project added to the user", "success")
        return redirect(url_for("project.projects"))

    return render_template("project/project_form.html", user=user, form=form)


@bp.route("/edit/<int:project_id>", methods=["GET", "POST"])
def edit_project(project_id):
    project = Project.query.filter_by(id=project_id).first()
    tags = Tag.query.filter_by(project_id=project_id)

    form = ProjectForm(obj=project)
    if form.validate_on_submit():
        project.title = form.title.data
        project.description = form.description.data
        project.demo_link = form.demo_link.data
        project.source_link = form.source_link.data

        file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], project.project_pic)
        file = request.files["inputFile"]
        filename = secure_filename(file.filename)
        pic_name = str(uuid.uuid1()) + "_" + filename
        if file and allowed_file(file.filename):
            if os.path.exists(file_path):
                os.remove(file_path)
            file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], pic_name))
            project.project_pic = pic_name

        for tag in form.tag.data:
            if tag in project.tags:
                pass
            else:
                tag = Tag(tag=tag, project_id=project.id)
                db.session.add(tag)
                db.session.commit()

        db.session.commit()
        return redirect(url_for(".single_project", project_id=project.id))

    return render_template("project/project_form.html", project=project, form=form, tags=tags)


@bp.route("/delete/<int:project_id>", methods=["GET", "POST"])
def delete_project(project_id):
    project = Project.query.filter_by(id=project_id).first()

    db.session.delete(project)
    db.session.commit()
    flash("The project has been deleted", "success")
    return redirect(url_for("user.account"))


@bp.route("/<int:project_id>/delete/tag/<int:tag_id>", methods=["GET", "POST"])
def delete_tag(tag_id, project_id):
    tag = Tag.query.filter_by(id=tag_id).first()

    db.session.delete(tag)
    db.session.commit()
    return redirect(url_for(".edit_project", project_id=project_id))


@bp.route("/<int:project_id>/add/comment", methods=["GET", "POST"])
def add_comment(project_id):
    user = User.query.filter_by(id=current_user.id).first()
    project = Project.query.filter_by(id=project_id).first()

    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(content=form.content.data, project_id=project.id, user_id=user.id)
        db.session.add(comment)
        db.session.commit()
        return redirect(url_for(".single_project", project_id=project.id))


@bp.route("/<int:project_id>/edit/comment/<int:comment_id>", methods=["GET", "POST"])
def edit_comment(comment_id, project_id):
    project = Project.query.filter_by(id=project_id).first()
    comments = Comment.query.filter_by(project_id=project_id)
    tags = Tag.query.filter_by(project_id=project_id)
    review = Review.query.filter_by(project_id=project_id).filter(Review.user_id == current_user.id).count()
    comment = Comment.query.filter_by(id=comment_id).first()

    vote_form = VoteForm()

    comment_form = CommentForm(obj=comment)
    if comment_form.validate_on_submit():
        comment.content = comment_form.content.data
        db.session.commit()
        return redirect(url_for(".single_project", project_id=project.id))

    return render_template(
        "project/single_project.html",
        comment=comment,
        project=project,
        comments=comments,
        tags=tags,
        comment_form=comment_form,
        review=review,
        vote_form=vote_form,
    )


@bp.route("/<int:project_id>/delete/comment/<int:comment_id>", methods=["GET", "POST"])
def delete_comment(comment_id, project_id):
    comment = Comment.query.filter_by(id=comment_id).first()

    db.session.delete(comment)
    db.session.commit()
    flash("The comment has been deleted", "success")
    return redirect(url_for(".single_project", project_id=project_id))


@bp.route("/search", methods=["POST"])
@login_required
def search():
    form = SearchForm()
    projects = Project.query
    if form.validate_on_submit():
        single_project.searched = form.searched.data
        projects = projects.filter(
            Project.description.like("%" + single_project.searched + "%")
            | Project.title.like("%" + single_project.searched + "%")
            | Project.description.like("%" + single_project.searched + "%")
        )
        projects = projects.order_by(Project.title).all()

    return render_template("project/search.html", form=form, searched=single_project.searched, projects=projects)


@bp.route("/<int:project_id>/rate/", methods=["GET", "POST"])
@login_required
def rate_project(project_id):
    project = Project.query.get_or_404(project_id)
    comments = Comment.query.filter_by(project_id=project_id)
    tags = Tag.query.filter_by(project_id=project_id)
    review = Review.query.filter_by(user_id=current_user.id).filter(Review.project_id == project_id)
    comment_form = CommentForm()

    vote_form = VoteForm()
    if vote_form.validate_on_submit():
        rating = Review(rating=vote_form.review.data, user_id=current_user.id, project_id=project_id)
        db.session.add(rating)
        db.session.commit()

        project.getVoteCount()

        return redirect(url_for(".single_project", project_id=project.id))

    return render_template(
        "project/single_project.html",
        vote_form=vote_form,
        comments=comments,
        tags=tags,
        review=review,
        comment_form=comment_form,
        project=project,
    )


@bp.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


@bp.route("/", defaults={"path": ""})
@bp.route("/<path:path>")
def catch_all(path):
    return render_template("errors/404.html"), 404
