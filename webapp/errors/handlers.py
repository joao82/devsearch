from flask import Blueprint

bp = Blueprint("errors", __name__, template_folder="templates/errors", static_folder="static")


def wants_json_response():
    return request.accept_mimetypes["application/json"] >= request.accept_mimetypes["text/html"]


@bp.app_errorhandler(404)
def not_found_error(error):
    if wants_json_response():
        return api_error.response(404)
    return render_template("errors/404.html"), 404


@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if wants_json_response():
        return api_error.response(500)
    return render_template("errors/500.html"), 500


@bp.app_errorhandler(403)
def page_forbidden(error):
    if wants_json_response():
        return api_error.response(403)
    return render_template("errors/403.html"), 500
