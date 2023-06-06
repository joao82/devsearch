import statistics
import json
import jwt
from datetime import datetime
from time import time
from sqlalchemy.sql import func
from webapp import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import current_app


ACCESS = {"guest": 0, "user": 1, "admin": 2}


followers = db.Table(
    "followers",
    db.Column("follower_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("followed_id", db.Integer, db.ForeignKey("user.id")),
)

project_tags = db.Table(
    "tags",
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id")),
    db.Column("project_id", db.Integer, db.ForeignKey("project.id")),
)


class User(db.Model, UserMixin):
    __table_name__ = "user"

    id = db.Column(db.Integer, primary_key=True, unique=True)
    email = db.Column(db.String(80), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(500), nullable=False)
    fullname = db.Column(db.String(80))
    intro = db.Column(db.String(150))
    about_me = db.Column(db.Text)
    profile_pic = db.Column(db.String(10000), nullable=True, default="default_user.png")
    location = db.Column(db.String(150))
    social_github = db.Column(db.String(150))
    social_stakoverflow = db.Column(db.String(150))
    social_twitter = db.Column(db.String(150))
    social_linkedin = db.Column(db.String(150))
    social_website = db.Column(db.String(150))
    access = db.Column(db.Integer)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    last_message_read_time = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    followed = db.relationship(
        "User",
        secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref("followers", lazy="dynamic"),
        lazy="dynamic",
    )

    review = db.relationship("Review", backref="author", lazy="dynamic")
    skills = db.relationship("Skills", backref="author", lazy="dynamic")
    projects = db.relationship("Project", backref="author", lazy="dynamic")
    comments = db.relationship("Comment", backref="author", lazy="dynamic")
    messages_sent = db.relationship("Message", foreign_keys="Message.sender_id", backref="author", lazy="dynamic")
    messages_received = db.relationship(
        "Message", foreign_keys="Message.recipient_id", backref="recipient", lazy="dynamic"
    )
    notifications = db.relationship("Notification", backref="user", lazy="dynamic")

    def __init__(self, username, email, access=ACCESS["user"]):
        self.username = username
        self.email = email
        self.access = access

    def __repr__(self):
        return f"<id: {self.id}, username: {self.username}"

    def json(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "password": self.password,
            "access": self.access,
        }

    def is_admin(self):
        return self.access == ACCESS["admin"]

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method="sha256")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @classmethod
    def find_by_user_id(cls, user_id):
        return cls.query.filter_by(id=user_id).first()

    def save_to_db(self):
        db.session.add(self)
        try:
            db.session.commit()
        except:
            db.session.rollback()
            raise Exception("Error saving user to db")

    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {"reset_password": self.id, "exp": time() + expires_in}, current_app.config["SECRET_KEY"], algorithm="HS256"
        )

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])["reset_password"]
        except:
            return
        return User.query.get(id)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def add_notification(self, name, data):
        self.notifications.filter_by(name=name).delete()
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n

    def new_messages(self):
        last_read_time = self.last_message_read_time or datetime(2010, 1, 1)
        return Message.query.filter_by(recipient=self).filter(Message.created_at > last_read_time).count()

    def unread_messages(self):
        last_read_time = self.last_message_read_time or datetime(2010, 1, 1)
        return Message.query.filter_by(recipient=self).filter(Message.created_at > last_read_time)


class Skills(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    skill = db.Column(db.String(140), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __init__(self, skill, description, user_id):
        self.skill = skill
        self.description = description
        self.user_id = user_id

    def __repr__(self):
        return f"<Skill id: {self.id}, skill: {self.skill}, user id: {self.user_id}>"

    def json(self):
        return {"id": self.id, "skill": self.skill, "description": self.description, "user id": self.user_id}


class Project(db.Model):
    __table_name__ = "project"

    id = db.Column(db.Integer, primary_key=True, unique=True)
    title = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text)
    project_pic = db.Column(db.String(300), nullable=True, default="default_project.jpg")
    rating = db.Column(db.Integer, default=0)
    total_votes = db.Column(db.Integer, default=0)
    positive_votes = db.Column(db.Integer, default=0)
    vote_ratio = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    last_update = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    demo_link = db.Column(db.String(350), nullable=True)
    source_link = db.Column(db.String(350), nullable=True)

    reviewers = db.relationship("Review", backref="project", lazy="dynamic")
    comments = db.relationship("Comment", backref="project", lazy="dynamic")
    tags = db.relationship("Tag", backref="project", lazy="dynamic")

    def __repr__(self):
        return f"<id: {self.id}, title: {self.title}, user id: {self.user_id}"

    def json(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "total_votes": self.total_votes,
            "positive_votes": self.positive_votes,
        }

    def getVoteCount(self):
        reviews = Review.query.filter_by(project_id=self.id)
        upVotes = Review.query.filter_by(project_id=self.id).filter(Review.rating > 2).count()
        totalVotes = reviews.count()

        vote_5 = Review.query.filter_by(project_id=self.id).filter(Review.rating == 5).count()
        vote_4 = Review.query.filter_by(project_id=self.id).filter(Review.rating == 4).count()
        vote_3 = Review.query.filter_by(project_id=self.id).filter(Review.rating == 3).count()
        vote_2 = Review.query.filter_by(project_id=self.id).filter(Review.rating == 2).count()
        vote_1 = Review.query.filter_by(project_id=self.id).filter(Review.rating == 1).count()

        if totalVotes == 0:
            project_rating = 0
        else:
            project_rating = (vote_5 * 5 + vote_4 * 4 + vote_3 * 3 + vote_2 * 2 + vote_1) / totalVotes

        ratio = (upVotes / totalVotes) * 100
        self.total_votes = totalVotes
        self.positive_votes = upVotes
        self.vote_ratio = ratio
        self.rating = project_rating
        db.session.commit()


class Review(db.Model):
    __table_name__ = "review"

    id = db.Column(db.Integer, primary_key=True, unique=True)
    rating = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"))

    def __repr__(self):
        return f"<id: {self.id}, rating: {self.rating}, project id: {self.project_id}, user id: {self.user_id}"


class Tag(db.Model):
    __table_name__ = "tags"

    id = db.Column(db.Integer, primary_key=True, unique=True)
    tag = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"))
    # projects = db.relationship(
    #     'Project', backref='tag', secondary=project_tags, lazy='dynamic')

    def __repr__(self):
        return f"<id: {self.id}, tag: {self.tag}, project id: {self.project_id}"


class Comment(db.Model):
    __table_name__ = "comments"

    id = db.Column(db.Integer, primary_key=True, unique=True)
    content = db.Column(db.Text, unique=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __init__(self, content, project_id, user_id):
        self.content = content
        self.project_id = project_id
        self.user_id = user_id

    def __repr__(self):
        return f"<id: {self.id}, content: {self.content}, project id: {self.project_id}, user id: {self.user_id}"


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(150), nullable=False)
    body = db.Column(db.String(1400), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    recipient_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return "<Message {}>".format(self.body)


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)

    def get_data(self):
        return json.loads(str(self.payload_json))


@login.user_loader
def load_user(id):
    try:
        return User.query.get(int(id))
    except:
        return None
