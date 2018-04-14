from datetime import datetime, date

from flask import Flask, abort, request, jsonify
from flask.views import MethodView
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound


app = Flask('revolut-hello')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config.from_envvar('FLASK_CONFIG')
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    dob = db.Column(db.DateTime, nullable=False)


class UserView(MethodView):

    def get(self, name):
        try:
            user = User.query.filter_by(name=name).one()
        except NoResultFound:
            abort(404)

        today = date.today()
        bday = user.dob.date().replace(year=today.year)
        if bday < today:
            bday = bday.replace(year=today.year + 1)

        if bday == today:
            message = 'Hello, {name}! Happy birthday!'.format(name=name)
        else:
            days = bday - today
            message = 'Hello, {name}! Your birthday is in {days} days'.format(name=name, days=days.days)

        return jsonify(message=message)

    def put(self, name):
        try:
            dob = datetime.strptime(request.get_json()['dateOfBirth'], '%Y-%m-%d').date()
        except (KeyError, ValueError):
            app.logger.warning('Invalid PUT data', exc_info=True)
            abort(400)

        try:
            user = User.query.filter_by(name=name).one()
        except NoResultFound:
            user = User(name=name)
            db.session.add(user)

        user.dob = dob
        db.session.commit()
        return '', 201


@app.route('/healthcheck')
def healthcheck():
    return 'ALIVE'


app.add_url_rule('/hello/<name>', view_func=UserView.as_view('hello'))
