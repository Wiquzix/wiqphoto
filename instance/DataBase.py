from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    mail = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50), nullable=False)
    fio = db.Column(db.String)
    # description = db.Column(db.String, nullable=False)
    ava = db.Column(db.String, nullable=False)
    count_content = db.Column(db.Integer, default=0)
    '''
    video = db.relationship('Video', backref='User', lazy='dynamic')
    photo = db.relationship('Photo', backref='User', lazy='dynamic')
    album = db.relationship('Album', backref='User', lazy='dynamic')
    access = db.relationship('Access', backref='User', lazy='dynamic')
    '''
    
    '''
    @property
    def dictor(self):
        return {"ID": self.id,
                "login": self.login,
                "password": self.password,
                "FIO": self.fio,
                "age": self.age,
                "balance": self.balance,
                "admin": self.admin
                }  '''


class Content(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    id_user = db.Column(db.Integer, db.ForeignKey('user.id'))
    id_album = db.Column(db.Integer, db.ForeignKey('album.id'))
    tags = db.Column(db.String, default='')
    format = db.Column(db.String, default='')
    size = db.Column(db.Integer)
    brightness = db.Column(db.Integer, default=100)
    contrast = db.Column(db.Integer, default=100)
    latitude = db.Column(db.String, default='')
    longitude = db.Column(db.String, default='')

    # album = db.relationship('Album', backref='Photo', lazy='dynamic')
'''
class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    id_user = db.Column(db.Integer, db.ForeignKey('user.id'))
    id_album = db.Column(db.Integer, db.ForeignKey('album.id'))
    id_tag = db.Column(db.Integer, db.ForeignKey('tag.id'))
    '''
    # album = db.relationship('Album', backref='Video', lazy='dynamic')

class Album(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    id_user = db.Column(db.Integer, db.ForeignKey('user.id'))
    access = db.Column(db.Integer,nullable=False)

    # id_photo = db.Column(db.Integer, db.ForeignKey('photo.id'), nullable=True)
    # id_video = db.Column(db.Integer, db.ForeignKey('video.id'), nullable=True)

    # video = db.relationship('Video', backref='Album', lazy='dynamic')
    # photo = db.relationship('Photo', backref='Album', lazy='dynamic')
    # access = db.relationship('Access', backref='Album', lazy='dynamic')


class Access(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_user = db.Column(db.Integer, db.ForeignKey('user.id'))
    id_album = db.Column(db.Integer, db.ForeignKey('album.id'))

    # album = db.relationship('Access', backref='Access', lazy='dynamic')



class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)

    # photo = db.relationship('Photo', backref='Tag', lazy='dynamic')
    # video = db.relationship('Video', backref='Tag', lazy='dynamic')


