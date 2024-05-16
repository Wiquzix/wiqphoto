from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import os
from PIL import Image, ImageEnhance
import shutil
from instance.DataBase import *
import requests
import os.path
from GPSPhoto import gpsphoto
import cv2
import numpy as np
from art import tprint
import aspose.zip as az
import getpass

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'dng', 'raw', 'ARW', 'mp4', 'avi', 'mov'])
PHOTO_FORMAT = set(['png', 'jpg', 'dng', 'raw', 'ARW'])
VIDEO_FORMAT = set(['mp4', 'avi', 'mov'])

app = Flask(__name__)
app.secret_key = '79d77d1e7f9348c59a384d4376a9e53f'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['UPLOAD_FOLDER'] = 'static/img'
db.init_app(app)
manager = LoginManager(app)


@manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template("index.html")

@app.route('/profile')
def profile():
    user = User.query.get(current_user.id)
    count_files = len(Content.query.filter_by(id_user=current_user.id).all())
    return render_template("profile.html", user=user, count_files=count_files)

@app.route('/profile/<int:id>')
def profile_id(id):
    user = User.query.get(id)
    count_files = len(Content.query.filter_by(id_user=id).all())
    return render_template("profile.html", user=user, count_files=count_files)


# ОПРЕДЕЛЕНИЕ МЕСТА СЪЁМКИ ФОТОГРАФИИ

@app.route('/gps/<int:id>')
def gps(id):
    photo = Content.query.get(id)
    album = Album.query.filter(Album.id == photo.id_album).first()
    fio = User.query.filter(User.id == photo.id_user).first()
    if photo.latitude == '' and photo.longitude == '':
        data = gpsphoto.getGPSData(f'static/img/{photo.name}')
        try:
            photo.latitude = str(data['Latitude'])
            photo.longitude = str(data['Longitude'])
            db.session.commit()
            return render_template("gps.html", latitude=data['Latitude'], longitude=data['Longitude'], photo=photo)
        except:
            flash("У фотографии невозможно определить геопозицию!!!")
            return render_template("photo.html", photo=photo, album=album, fio=fio, format=photo.format, size=photo.size)
    else:
        return render_template("gps.html", latitude=photo.latitude, longitude=photo.longitude, photo=photo)
# СКАЧИВАНИЕ ФОТОГРАФИЙ

cd = 0
@app.route('/download/<int:id>')
def download(id):
    global cd
    content = Content.query.get(id)
    response = requests.get(f"http://127.0.0.1:5000/static/img/{content.name}")
    fio = User.query.filter(User.id == content.id_user).first()
    if response.status_code == 200:
        with open(f'{content.name}', 'wb') as file:
            file.write(response.content)
        if os.path.exists(f'C:/Users/{getpass.getuser()}/Downloads/{content.name[:-4]}(0).{content.name[-3:]}'):
            cd += 1
            shutil.copy2(f'{content.name}', f'C:/Users/{getpass.getuser()}/Downloads/{content.name[:-4]}({cd}).{content.name[-3:]}')
            os.remove(f'{content.name}')
        else:
            shutil.copy2(f'{content.name}', f'C:/Users/{getpass.getuser()}/Downloads/{content.name[:-4]}({cd}).{content.name[-3:]}')
            os.remove(f'{content.name}')
        flash('Файл скачан')
    else:
        flash("Ошибка при скачивании")
    album = Album.query.filter(Album.id == content.id_album).first()
    if content.name[-3:] in PHOTO_FORMAT:
        return render_template("photo.html", photo=content, album=album, fio=fio, format=content.format, size=content.size)
    elif content.name[-3:] in VIDEO_FORMAT:
        return render_template("video.html", video=content, album=album, fio=fio, format=content.format, size=content.size)

cd_album = 0
@app.route('/download_album/<int:id>')
def download_album(id):
    global cd_album
    content = Content.query.filter(Content.id_album == id).all()
    album = Album.query.filter(Album.id == id).first()
    try:
        with az.Archive() as archive:
            for el in content:
                archive.create_entry(el.name, f'static/img/{el.name}')
            archive.save(f'{album.name}.zip')
        if os.path.exists(f'C:/Users/{getpass.getuser()}/Downloads/{album.name}(0).zip'):
            cd_album += 1
            shutil.copy2(f'{album.name}.zip', f"C:/Users/{getpass.getuser()}/Downloads/{album.name}({cd_album}).zip")
            os.remove(f'{album.name}.zip')
        else:
            shutil.copy2(f'{album.name}.zip', f"C:/Users/{getpass.getuser()}/Downloads/{album.name}({cd_album}).zip")
            os.remove(f'{album.name}.zip')
        flash('Альбом скачан')
    except:
        flash("Ошибка при скачивании")
    album = Album.query.filter(Album.id == id).first()
    fio = User.query.filter(User.id == album.id_user).first()
    len_cont = len(Content.query.filter(Content.id_album == album.id).all())
    content = Content.query.filter(Content.id_album == album.id).all()
    access_list = []
    acc = Access.query.filter_by(id_album=id).all()
    for i in range(len(acc)):
        access_list.append(acc[i].id_user)
    access_list.append(fio.id)
    photo = []
    video = []
    for el in content:
        if el.name[-3:] in PHOTO_FORMAT:
            photo.append(el)
        elif el.name[-3:] in VIDEO_FORMAT:
            video.append(el)
    return render_template("album.html", fio=fio, album=album, len_cont=len_cont,  access_list=access_list, photos=photo, videos=video)

# РЕДАКТИРОВАНИЕ ФОТОГРАФИЙ
@app.route('/t/<int:id>', methods=["POST","GET"])
def t(id):
    photo = Content.query.get(id)
    shutil.copy2(f"static/img/{photo.name}", f"{photo.name}")
    shutil.copy2(f"static/img/{photo.name}", f"r_{photo.name}")
    if request.method == "POST":
        bri = int(request.form.get('brightness'))
        con = int(request.form.get('contrast'))
        b = 1
        c = 1
        if photo.brightness == 100 and bri == 100:
            b = 1
        elif photo.brightness > 100 and bri == 100:
            b = 1 - (((photo.brightness - bri) / 100) / 2)
        elif photo.brightness < 100 and bri == 100:
            b = 1 + ((bri - photo.brightness) / 100)
        elif photo.brightness == 100 and (bri > 100 or bri < 100):
            b = bri / 100
        elif bri > photo.brightness:
            b = 1 + ((bri - photo.brightness) / 100)
        elif bri < photo.brightness:
            b = 1 - (((photo.brightness - bri) / 100) / 2)
        if photo.contrast == 100 and con == 100:
            c = 1
        elif photo.contrast > 100 and con == 100:
            c = 1 - (((photo.contrast - con) / 100) / 2)
        elif photo.contrast < 100 and con == 100:
            c = 1 + ((con - photo.contrast) / 100)
        elif photo.contrast == 100 and (con > 100 or con < 100):
            c = con / 100
        elif con > photo.contrast:
            c = 1 + ((con - photo.contrast) / 100)
        elif con < photo.contrast:
            c = 1 - (((photo.contrast - con) / 100) / 2)
        im = Image.open(f"r_{photo.name}")
        enhancer = ImageEnhance.Brightness(im)
        im2 = enhancer.enhance(b)
        im2.save(f"r_{photo.name}")
        im = Image.open(f"r_{photo.name}")
        enhancer = ImageEnhance.Contrast(im)
        im2 = enhancer.enhance(c)
        im2.save(os.path.join(app.config['UPLOAD_FOLDER'], f"{photo.name}"))
        os.remove(f"r_{photo.name}")
        photo.brightness = bri
        photo.contrast = con
        db.session.commit()
        return render_template("edit.html", photo=photo)

    return render_template("edit.html", photo=photo)

@app.route('/save/<int:id>')
def save(id):
    photo = Content.query.get(id)
    album = Album.query.filter(Album.id == photo.id_album).first()
    fio = User.query.filter(User.id == photo.id_user).first()
    os.remove(f"{photo.name}")
    photo.brightness = 100
    photo.contrast = 100
    db.session.commit()
    return render_template("photo.html", photo=photo, album=album, fio=fio, format=photo.format, size=photo.size)

@app.route('/cancel/<int:id>')
def cancel(id):
    photo = Content.query.get(id)
    album = Album.query.filter(Album.id == photo.id_album).first()
    fio = User.query.filter(User.id == photo.id_user).first()
    shutil.copy2(f"{photo.name}", f"static/img/{photo.name}")
    os.remove(f"{photo.name}")
    photo.brightness = 100
    photo.contrast = 100
    db.session.commit()
    return render_template("photo.html", photo=photo, album=album, fio=fio, format=photo.format, size=photo.size)


count = 0
@app.route('/edit/<int:id>', methods=["POST","GET"])
def edit(id):
    photo = Content.query.get(id)
    shutil.copy2(f"static/img/{photo.name}", f"{photo.name}")
    shutil.copy2(f"static/img/{photo.name}", f"r_{photo.name}")
    if request.method == "GET":
        global count
        count += 1
        im = Image.open(f"r_{photo.name}")
        if count == 1:
            im2 = im.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.ROTATE_90)
            im2.save(os.path.join(app.config['UPLOAD_FOLDER'], f"{photo.name}"))
        elif count == 2:
            im2 = im.transpose(Image.FLIP_TOP_BOTTOM).transpose(Image.ROTATE_90)
            im2.save(os.path.join(app.config['UPLOAD_FOLDER'], f"{photo.name}"))
        elif count == 3:
            im2 = im.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.ROTATE_90)
            im2.save(os.path.join(app.config['UPLOAD_FOLDER'], f"{photo.name}"))
        elif count == 4:
            im2 = im.transpose(Image.FLIP_TOP_BOTTOM).transpose(Image.ROTATE_90)
            im2.save(os.path.join(app.config['UPLOAD_FOLDER'], f"{photo.name}"))
            count = 0
        os.remove(f"r_{photo.name}")
        return render_template("edit.html", photo=photo)
    bri = int(request.form.get('brightness'))
    con = int(request.form.get('contrast'))
    b = 1
    c = 1
    if photo.brightness == 100 and bri == 100:
        b = 1
    elif photo.brightness > 100 and bri == 100:
        b = 1 - (((photo.brightness - bri) / 100) / 2)
    elif photo.brightness < 100 and bri == 100:
        b = 1 + ((bri - photo.brightness) / 100)
    elif photo.brightness == 100 and (bri > 100 or bri < 100):
        b = bri / 100
    elif bri > photo.brightness:
        b = 1 + ((bri - photo.brightness) / 100)
    elif bri < photo.brightness:
        b = 1 - (((photo.brightness - bri) / 100) / 2)
    if photo.contrast == 100 and con == 100:
        c = 1
    elif photo.contrast > 100 and con == 100:
        c = 1 - (((photo.contrast - con) / 100) / 2)
    elif photo.contrast < 100 and con == 100:
        c = 1 + ((con - photo.contrast) / 100)
    elif photo.contrast == 100 and (con > 100 or con < 100):
        c = con / 100
    elif con > photo.contrast:
        c = 1 + ((con - photo.contrast) / 100)
    elif con < photo.contrast:
        c = 1 - (((photo.contrast - con) / 100) / 2)
    im = Image.open(f"r_{photo.name}")
    enhancer = ImageEnhance.Brightness(im)
    im2 = enhancer.enhance(b)
    im2.save(f"r_{photo.name}")
    im = Image.open(f"r_{photo.name}")
    enhancer = ImageEnhance.Contrast(im)
    im2 = enhancer.enhance(c)
    im2.save(os.path.join(app.config['UPLOAD_FOLDER'], f"{photo.name}"))
    os.remove(f"r_{photo.name}")
    photo.brightness = bri
    photo.contrast = con
    db.session.commit()
    return render_template("edit.html", photo=photo)

#ОБРЕЗКА
"""
@app.route('/c/<int:id>')
def c(id):
    photo = Content.query.get(id)
    shutil.copy2(f"static/img/{photo.name}", f"{photo.name}")
    return render_template("c.html", photo=photo)

@app.route('/cropping/<int:id>')
def cropping(id):
    photo = Content.query.get(id)
    #shutil.copy2(f"static/img/{photo.name}", f"{photo.name}")
    im = Image.open(f"{photo.name}")
    im2 = im.crop((200, 200, 500, 500))
    im2.save(os.path.join(app.config['UPLOAD_FOLDER'], f"{photo.name}"))
    im2.save("1.jpg")
    return render_template("c.html", photo=photo)
"""


# АЛЬБОМЫ

@app.route('/album/<int:id>')
def album(id):
    album = Album.query.filter(Album.id == id).first()
    fio = User.query.filter(User.id == album.id_user).first()
    len_cont = len(Content.query.filter(Content.id_album == album.id).all())
    content = Content.query.filter(Content.id_album == album.id).all()
    access_list = []
    acc = Access.query.filter_by(id_album = id).all()
    for i in range(len(acc)):
        access_list.append(acc[i].id_user)
    access_list.append(fio.id)
    photo = []
    video = []
    for el in content:
        if el.name[-3:] in PHOTO_FORMAT:
            photo.append(el)
        elif el.name[-3:] in VIDEO_FORMAT:
            video.append(el)
    return render_template("album.html", fio=fio, album=album, len_cont=len_cont,  access_list=access_list, photos=photo, videos=video)


@app.route('/add_album', methods=["POST","GET"])     # доступ не зареганым, зареганым, только владельцу, только конкретные по емаил
def add_album():
    if request.method == "GET":
        return render_template("add_album.html")

    name = request.form.get('name')
    access = request.form.get('access')

    if access == '0' or access == '1' or access == '-1':
        try:
            album = Album(name=name, id_user=current_user.id, access=int(access))
            db.session.add(album)
            db.session.commit()
            return redirect("/")
        except:
            flash("Возникла ошибка при создании альбома")
            return render_template("/add_album.html")

    elif access.count('@') == 1:
        try:
            user = User.query.filter(User.mail==access).first()
            album = Album(name=name, id_user=current_user.id, access=2)
            al_id = Album.query.order_by(Album.id).all()[-1].id + 1
            access = Access(id_user=user.id, id_album=al_id)
            db.session.add(access)
            db.session.add(album)
            db.session.commit()
            return redirect("/")
        except:
            flash("Возникла ошибка при создании альбома")
            return render_template("/add_album.html")

    elif access.count('@') > 1:
        try:
            acc = access.split()
            album = Album(name=name, id_user=current_user.id, access=2)
            al_id = Album.query.order_by(Album.id).all()[-1].id + 1

            for i in range(access.count('@')):
                user = User.query.filter(User.mail == acc[i]).first()
                access = Access(id_user=user.id, id_album=al_id)
                db.session.add(access)

            db.session.add(album)

            db.session.commit()
            return redirect("/")
        except:
            flash("Возникла ошибка при создании альбома")
            return render_template("/add_album.html")

    else:
        flash("Выберите: доступ правильно доступ")


@app.route('/albums')
def albums():
    album = Album.query.filter(Album.id_user == current_user.id).all()
    len_cont = []
    for i in album:
        len_cont.append(len(Content.query.filter(Content.id_album==i.id).all()))
    return render_template("albums.html", albums=album, len_cont=len_cont)

@app.route('/edit_album/<int:id>', methods=["POST","GET"])
def edit_album(id):
    album = Album.query.filter_by(id=id).first()
    ac2 = []
    if album.access == 2:
        ac = Access.query.filter(Access.id_album == id).all()
        for i in ac:
            ac1 = User.query.filter(User.id == i.id_user).all()
            for j in ac1:
                ac2.append(j.mail)
        ac2 = set(ac2)
        if len(ac2) > 1:
            ac = ' '.join(ac2)
        else:
            ac = list(ac2)[0]
    else:
        ac = album.access
    if current_user.is_authenticated and current_user.id == album.id_user:
        if request.method == "GET":
            return render_template("edit_album.html", album=album, ac=ac)
        if request.method == "POST":

            name = request.form.get('name')
            access = request.form.get('access')

            if access in ['-1', '0', '1'] and album.access == 2:
                ac = Access.query.filter(Access.id_album == id).all()
                for i in ac:
                    db.session.delete(i)
                    db.session.commit()

            if access == "-1" or access == '0' or access == '1':
                try:

                    album.name = name
                    album.access = access
                    db.session.commit()
                    flash("Альбом изменён")
                    return redirect(f'/album/{id}')
                except:
                    flash("Возникла ошибка при изменении альбома")
                    return render_template("/edit_album.html")
            elif access.count('@') == 1:
                try:
                    if access != ac:
                        album.access = 2
                    if name != album.name:
                        album.name = name

                    user = User.query.filter(User.mail == access).first()
                    access = Access(id_user=user.id, id_album=album.id)

                    db.session.add(access)
                    db.session.commit()
                    flash("Альбом изменён")
                    return redirect(f'/album/{id}')
                except:
                    flash("Возникла ошибка при изменении альбома")
                    return render_template("/edit_album.html")
            elif access.count('@') > 1:
                try:
                    acc = access.split()
                    if access != ac:
                        album.access = 2
                    if name != album.name:
                        album.name = name
                    for i in range(access.count('@')):
                        user = User.query.filter(User.mail == acc[i]).first()
                        access = Access(id_user=user.id, id_album=album.id)
                        db.session.add(access)
                    db.session.commit()
                    flash("Альбом изменён")
                    return redirect(f'/album/{id}')
                except:
                    flash("Возникла ошибка при редактировании альбома")
                    return render_template("/edit_album.html")
            else:
                flash("некорректный доступ")
                return redirect('/')
        return render_template("edit_album.html", album=album, ac=ac)
    else:
        flash('Нет доступа')
        return redirect('/')

@app.route('/delete_album/<int:id>')
def del_album(id):
    album = Album.query.filter_by(id=id).first()
    if current_user.is_authenticated and current_user.id == album.id_user:
        try:
            if album.access == 2:
                access = Access.query.filter(Access.id_album == id).all()
                if len(access) > 1:
                    for i in access:
                        db.session.delete(i)
                else:
                    db.session.delete(access[0])
            db.session.delete(album)
            db.session.commit()
            flash('Альбом удалён!')
            return redirect("/")
        except:
            flash('Ошибка при удалении')
            return redirect("/")
    else:
        flash('Нет доступа')
        return redirect("/")


# ФОТОГРАФИИ И ВИДЕО

@app.route('/add_content', methods=["POST","GET"])
def add_photo():
    if request.method == "GET":
        return render_template("add_content.html")
    user = User.query.get(current_user.id)
    file = request.files['file']
    photos = Content.query.filter_by(id_user=current_user.id).all()
    if not allowed_file(file.filename):
        flash("Неподходящий формат!")
        return render_template('add_content.html')
    name = f'u{current_user.id}_p{user.count_content + 1}.{file.filename[-3:]}'
    content = Content.query.filter_by(name=name).first()
    if content is None:
        file.save(os.path.join('static/img', name))
    else:
        name = f'u{current_user.id}_p{user.count_content + 2}.{file.filename[-3:]}'
        file.save(os.path.join('static/img', name))
    try:
        db.session.add(Content(name=name, id_user=current_user.id, id_album=-1, format=name[-3:], size=os.stat(f"static/img/{name}").st_size))
        if content is None:
            user.count_content += 1
        else:
            user.count_content += 2
        db.session.commit()
        return redirect("/")
    except:
        flash("Возникла ошибка при добавлении фотографии(ий) или видео")
        return render_template("/add_content.html")

@app.route('/album/add_content/<int:id>', methods=["POST","GET"])
def add_content(id):
    album = Album.query.filter(Album.id == id).first()
    if request.method == "GET":
        return render_template("add_content.html")
    user = User.query.get(current_user.id)
    file = request.files['file']
    photos = Content.query.filter_by(id_user=current_user.id).all()
    if not allowed_file(file.filename):
        flash("Неподходящий формат!")
        return render_template('add_content.html')
    name = f'u{current_user.id}_p{user.count_content + 1}.{file.filename[-3:]}'
    content = Content.query.filter_by(name=name).first()
    if content is None:
        file.save(os.path.join('static/img', name))
    else:
        name = f'u{current_user.id}_p{user.count_content + 2}.{file.filename[-3:]}'
        file.save(os.path.join('static/img', name))
    try:
        db.session.add(Content(name=name, id_user=current_user.id, id_album=album.id, format=name[-3:], size=os.stat(f"static/img/{name}").st_size))
        if content is None:
            user.count_content += 1
        else:
            user.count_content += 2
        db.session.commit()
        return redirect("/")
    except:
        flash("Возникла ошибка при добавлении фотографии(ий) или видео в альбом")
        return render_template("/add_content.html")

@app.route('/add_to_album/<int:id>', methods=["POST","GET"])
def add_to_album(id):
    photo = Content.query.get(id)
    if request.method == "GET":
        return render_template("add_to_album.html")
    name = request.form.get('name')
    album = Album.query.filter(Album.name == name).first()
    try:
        photo.id_album = album.id
        db.session.commit()
        return redirect("/")
    except:
        flash("Возникла ошибка при добавлении фотографии(ий) или видео в альбом")
        return render_template("add_to_album.html")

@app.route('/tags/<int:id>', methods=["POST","GET"])
def tags(id):
    if current_user == None:
        flash("Войдите в аккаунт")
        return redirect('/')
    photo = Content.query.get(id)
    album = Album.query.filter(Album.id == photo.id_album).first()
    fio = User.query.filter(User.id == photo.id_user).first()
    if request.method == "GET":
        return render_template("tags.html", photo=photo, album=album, fio=fio, format=photo.format, size=photo.size)
    tags = request.form.get('tags')
    t = tags.split(", ")
    len_tags = len(Tag.query.all())+1
    try:
        for el in range(len(t)):
            tag = Tag(name=t[el])
            db.session.add(tag)
            photo.tags = photo.tags + ", " + str(len_tags+el) + ", "
            photo.tags = photo.tags[:-2]
        if photo.tags!=None:
            if photo.tags[:2] == ', ':
                photo.tags = photo.tags[2:]
        db.session.commit()
        flash("Теги успешно добавлены")
        return render_template("photo.html", photo=photo, album=album, fio=fio, format=photo.format, size=photo.size)
    except:
        flash("Возникла ошибка при добавлении тегов")
        return render_template("photo.html", photo=photo, album=album)


@app.route('/delete_photo/<int:id>')
def delete_photo(id):
    user = User.query.get(current_user.id)
    photo = Content.query.get(id)
    db.session.delete(photo)
    user.count_content -= 1
    db.session.commit()
    try:
        os.remove(f'static/img/{photo.name}')
        flash('Фотография удалена!')
        return redirect('/')
    except:
        flash("Ошибка при удалении фотографии!")
        photos = Content.query.filter_by(id_user=current_user.id).all()
        return render_template("photos.html", photos=photos)

@app.route('/photos/<sort>', methods=["POST", "GET"])
def photos(sort):
    if current_user == None:
        flash("Войдите в аккаунт")
        return redirect('/')
    status = False
    content = []
    formats = {}
    photo = []
    video = []
    if request.method == "POST":
        sort = ""
        tag = request.form.get('tag')
        contents = Content.query.filter_by(id_user=current_user.id).all()
        for el in contents:
            if el.tags == '':
                continue
            else:
                for t in el.tags.split(", "):
                    tags = Tag.query.filter(Tag.id == t).first()
                    if tag in tags.name:
                        content.append(el)
        status = True
    if sort == "def":
        content = Content.query.filter_by(id_user=current_user.id).all()
    elif sort == "size_up":
        content = Content.query.filter_by(id_user=current_user.id).order_by(Content.size)
    elif sort == "size_down":
        content = Content.query.filter_by(id_user=current_user.id).order_by(desc(Content.size))
    elif sort == "format":
        content = Content.query.filter_by(id_user=current_user.id).all()
        for el in content:
            if el.format in list(formats.keys()):
                formats[el.format] += [el]
            else:
                formats[el.format] = [el]
    if sort != "format":
        for el in content:
            if el.name[-3:] in PHOTO_FORMAT:
                """# if el.name[-3:] == "dng":
                #     el.name = el.name[:-3] + 'png'
                #     photo.append(el)
                #     print(el.name)
                #     shutil.copy2(f'static/img/{el.name[:-3] + "dng"}', f'static/img/{el.name}')
                #     os.remove(f"static/img/{el.name[:-3] + 'dng'}")
                #     db.session.commit()
                # elif el.name[-3:] == "ARW":
                #     shutil.copy2(f"static/img/{el.name}", f"{el.name}")
                #     im = Image.open(f"{el.name}")
                #     rgb_im = im.convert('RGB')
                #     rgb_im.save(f'{el.name[:-3]}jpg')
                #     shutil.copy2(f'{el.name[:-3]}jpg', f"static/img/{el.name[:-3]}jpg")
                #     os.remove(f"{el.name[:-3]}jpg")
                #     el.name = f"{el.name[:-3]}jpg"
                #     db.session.commit()
                # else:"""
                photo.append(el)
            elif el.name[-3:] in VIDEO_FORMAT:
                video.append(el)
    return render_template("photos.html", photos=photo, videos=video, formats=formats, status=status)


@app.route('/photo/<int:id>')
def photo(id):
    if current_user == None:
        flash("Войдите в аккаунт")
        return redirect('/')
    photo = Content.query.get(id)
    album = Album.query.filter(Album.id == photo.id_album).first()
    fio = User.query.filter(User.id == photo.id_user).first()
    return render_template("photo.html", photo=photo, album=album, fio=fio, format=photo.format, size=photo.size)

@app.route('/video/<int:id>')
def video(id):
    if current_user == None:
        flash("Войдите в аккаунт")
        return redirect('/')
    video = Content.query.get(id)
    album = Album.query.filter(Album.id == video.id_album).first()
    fio = User.query.filter(User.id == video.id_user).first()
    return render_template("video.html", video=video, album=album, fio=fio, format=video.format, size=video.size)


@app.route('/delete_from_album/<int:id>')
def delete_from_album(id):
    content = Content.query.get(id)
    content.id_album = -1
    db.session.commit()
    try:
        flash("Файл удален из альбома")
        album = Album.query.filter(Album.id == content.id_album).first()
        fio = User.query.filter(User.id == content.id_user).first()
        if content.name[-3:] in PHOTO_FORMAT:
            return render_template("photo.html", photo=content, album=album, fio=fio, format=content.format, size=content.size)
        elif content.name[-3:] in VIDEO_FORMAT:
            return render_template("video.html", video=content, album=album, fio=fio, format=content.format, size=content.size)
    except:
        flash("Ошибка при удалении из альбома")
        return redirect("/")

# РЕГИСТРАЦИЯ И ВХОД

@app.route('/sign-up', methods=["POST", "GET"])
def sign_up():
    if request.method == "GET":
        return render_template("sign-up.html")
    mail = request.form.get('mail')
    password = request.form.get('password')
    password2 = request.form.get('password2')
    #description = request.form.get('description')
    fio = request.form.get('F') + " " + request.form.get('I') + " " + request.form.get('O')
    #age = request.form.get('age')
    user = User.query.filter_by(mail=mail).first()
    file = request.files['file']
    file.save(os.path.join('static/img', file.filename))
    if len(mail) > 50:
        flash("Слишком длинный логин")
        return render_template("sign-up.html")
    if user is not None:
        flash('Имя пользователя занято!')
        return render_template("sign-up.html")

    if password != password2:
        flash("Пароли не совпадают!")
        return render_template("sign-up.html")
    try:
        hash_pwd = generate_password_hash(password)
        new_user = User(mail=mail, password=hash_pwd, fio=fio, ava=file.filename)
        db.session.add(new_user)
        db.session.commit()
        return redirect("/")

    except:
        flash("Возникла ошибка при регистрации")
        return render_template("sign-up.html")


@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        mail = request.form.get('mail')
        password = request.form.get('password')
        user = User.query.filter_by(mail=mail).first()
        if user is not None:
            if check_password_hash(user.password, password):
                login_user(user)
                return redirect('/')
            else:
                flash('Неверный логин или пароль')
        else:
            flash('Такого пользователя не существует')
    return render_template("login.html")


@app.route('/logout')
def logout():
    logout_user()
    return redirect("/")

# РАСПОЗНОВАНИЕ ОБЪЕКТОВ НА ФОТО

def apply_yolo_object_detection(image_to_process):
    height, width, _ = image_to_process.shape
    blob = cv2.dnn.blobFromImage(image_to_process, 1 / 255, (608, 608), (0, 0, 0), swapRB=True, crop=False)
    net.setInput(blob)
    outs = net.forward(out_layers)

    class_indexes, class_scores, boxes = ([] for i in range(3))
    objects_count = 0
    objects_found = {}

    for out in outs:
        for obj in out:
            scores = obj[5:]
            class_index = np.argmax(scores)
            class_score = scores[class_index]

            if class_score > 0:
                center_x = int(obj[0] * width)
                center_y = int(obj[1] * height)
                obj_width = int(obj[2] * width)
                obj_height = int(obj[3] * height)
                box = [center_x - obj_width // 2, center_y - obj_height // 2, obj_width, obj_height]
                boxes.append(box)
                class_indexes.append(class_index)
                class_scores.append(float(class_score))
                objects_count += 1

                # Сохраняем типы найденных объектов
                class_name = classes[class_index]
                if class_name in objects_found:
                    objects_found[class_name] += 1
                else:
                    objects_found[class_name] = 1

    return objects_count, objects_found

@app.route('/objects/<int:id>')
def objects(id):
    photo = Content.query.get(id)
    image_path = f"static/img/{photo.name}"
    image = cv2.imread(image_path)
    objects_count, objects_found = apply_yolo_object_detection(image)
    obj = []
    for obj_type, count in objects_found.items():
        obj.append(obj_type)
    len_tags = len(Tag.query.all())+1
    try:
        for el in range(len(obj)):
            tag = Tag(name=obj[el])
            db.session.add(tag)

            photo.tags = photo.tags + ", " + str(len_tags+el)
        if photo.tags != '':
            if photo.tags[:2] == ', ':
                photo.tags = photo.tags[2:]
        db.session.commit()
        return render_template("objects.html", obj=obj, photo=photo)
    except:
        flash("Не удалось добавить теги в базу данных")
        return render_template("objects.html", obj=obj, photo=photo)



if __name__ == "__main__":
    net = cv2.dnn.readNetFromDarknet("Resources/yolov4-tiny.cfg", "Resources/yolov4-tiny.weights")
    layer_names = net.getLayerNames()
    out_layers_indexes = net.getUnconnectedOutLayers()
    out_layers = [layer_names[index - 1] for index in out_layers_indexes]
    with open("Resources/coco.names.txt") as file:
        classes = file.read().split("\n")
    with app.app_context():
        db.create_all()
    app.run()

