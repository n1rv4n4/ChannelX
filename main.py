from flask import Flask,session, redirect, url_for, render_template, request
from flask_socketio import SocketIO, send,emit, join_room, leave_room
from flask_wtf import FlaskForm		# Using FlaskForm rather than form eliminates deprecation warning.
from wtforms.fields import StringField, SubmitField,PasswordField
from wtforms.validators import Required
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager,UserMixin,login_user,login_required,logout_user
import os

basedir = os.path.abspath(os.path.dirname(__file__))	# Relative path for SQLAlchemy database file.

RECAPTCHA_PUBLIC_KEY = '6Ld9yzgUAAAAABhNSebzM2V1ZDn9j5eb1iWhlOma'
RECAPTCHA_PRIVATE_KEY = '6Ld9yzgUAAAAAO75KNjOiT4QH5uCbn6sl_WzdHHU'

class LoginForm(FlaskForm):
    """ Accepts a name and a password. """
    name = StringField('User Name', validators=[Required()])
    password = PasswordField('Password', validators=[Required()])
    submit = SubmitField('Sign In')

class ChannelForm(FlaskForm):
    """ Accepts a channel_name and a nickname. """
    channel_name = StringField('Channel Name', validators=[Required()])
    nickname = StringField('Nickname', validators=[Required()])
    submit = SubmitField('Join!')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ChannelX!^+%&/(()=?798465312-_*'	# Random complex key for CSRF security.
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']= False				# Eliminates SQLAlchemy deprecation warning.
app.config['SQLALCHEMY_DATABASE_URI']= 'sqlite:///' + os.path.join(basedir, 'login.db')
db=SQLAlchemy(app)
login_manager=LoginManager()
login_manager.init_app(app)

class User(UserMixin,db.Model):
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(20),unique=True)
    password=db.Column(db.String(20))

class ChannelHistory(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    channel_name=db.Column(db.String(20))
    username=db.Column(db.String(20))
    nickname=db.Column(db.String(20))

socketio = SocketIO(app, async_mode='gevent')	# Working with gevent mode provides keyboard interrupt with CTRL+C.
db.create_all()		# Creates DB.

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/',methods=['GET','POST'])
def get_login():
	FlaskForm = LoginForm()
	if FlaskForm.validate_on_submit():
		print("Someone in login panel.")
		user=User.query.filter_by(username=FlaskForm.name.data).first()
		if not user:
			new_user=User(username=FlaskForm.name.data,password=FlaskForm.password.data)
			db.session.add(new_user)
			db.session.commit()
			login_user(new_user)
			print(FlaskForm.name.data + " has logged in.")
		else:
			if user.password != FlaskForm.password.data:
				print("Someone tried to log in with wrong password!")
				return redirect('/')
			login_user(user)
		session['name'] = FlaskForm.name.data
		session['password'] = FlaskForm.password.data
		return redirect('/get_user_panel')
	elif request.method == 'GET':
		FlaskForm.name.data = session.get('name')
		FlaskForm.password.data = session.get('password')
	return render_template('login.html', FlaskForm=FlaskForm)

@app.route('/log_out')
@login_required
def log_out():
	logout_user()
	print(session.get('name') + " has logged out.")
	return 'Logged out.'


@app.route('/get_user_panel',methods=['GET','POST'])
@login_required
def get_user_panel():
    print(session.get('name') + " in user panel.")
    username=session['name']
    channels=ChannelHistory.query.filter_by(username=username)
    FlaskForm=ChannelForm()
    if FlaskForm.validate_on_submit():
        if channels:
            flag=False
            for channel in channels:
                if channel.channel_name == FlaskForm.channel_name.data:
                    flag=True
                    session['channel_name']=channel.channel_name
                    session['nickname']=channel.nickname
            if not flag:
                new_channel=ChannelHistory(channel_name=FlaskForm.channel_name.data,nickname=FlaskForm.nickname.data,username=username)
                db.session.add(new_channel)
                db.session.commit()
                session['channel_name']=FlaskForm.channel_name.data
                session['nickname']=FlaskForm.nickname.data
                print(session.get('name') + " selected a nickname " + session.get('nickname'))
        else:
            new_channel=ChannelHistory(channel_name=FlaskForm.channel_name.data,nickname=FlaskForm.nickname.data,username=username)
            db.session.add(new_channel)
            db.session.commit()
            session['channel_name']=FlaskForm.channel_name.data
            session['nickname']=FlaskForm.nickname.data
        return redirect(url_for('get_channel'))
    return render_template('user_panel.html',FlaskForm=FlaskForm,channels=[channel.channel_name for channel in channels])

@app.route('/channel',methods=['GET','POST'])
@login_required
def get_channel():
    print(session.get('nickname') + " created channel " + session.get('channel_name'))
    nickname = session.get('nickname')
    channel_name = session.get('channel_name')
    return render_template('channel.html', nickname=nickname, channel_name=channel_name)


@socketio.on('joined',namespace='/channel')
def joined(message):
    """ Sent by clients when they enter a channel.
    A status message is broadcast to all people in the channel. """
    print(session.get('nickname') + " entered the channel " + session.get('channel_name'))
    channel_name = session.get('channel_name')
    nickname=session.get('nickname')
    join_room(channel_name)
    emit('status', {'msg': nickname + ' has entered the channel.'}, room=channel_name)


@socketio.on('text',namespace='/channel')
def text(message):
    """ Sent by a client when the user entered a new message.
    The message is sent to all people in the channel. """
    print("Sent message by " + session.get('nickname') + ": " + message['msg'])
    channel_name = session.get('channel_name')
    nickname=session.get('nickname')
    emit('message', {'msg': nickname + ': ' + message['msg']}, room=channel_name)


@socketio.on('left',namespace='/channel')
def left(message):
    """ Sent by clients when they leave a channel.
    A status message is broadcast to all people in the channel. """
    print(session.get('nickname') + " leaved the channel " + session.get('channel_name'))
    channel_name = session.get('channel_name')
    leave_room(channel_name)
    emit('status', {'msg': session.get('nickname') + ' has left the channel.'}, room=channel_name)

if __name__ == '__main__':
	socketio.run(app)
