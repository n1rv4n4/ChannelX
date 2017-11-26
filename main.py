from flask import Flask, session, redirect, url_for, render_template, request
from flask_socketio import SocketIO, send,emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import os, datetime

basedir = os.path.abspath(os.path.dirname(__file__))	# Relative path for SQLAlchemy database file.
app = Flask(__name__)

app.config['SECRET_KEY'] = 'ChannelX!^+%&/(()=?798465312-_*'	# Random complex key for CSRF security.
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']= False				# Eliminates SQLAlchemy deprecation warning.
app.config['SQLALCHEMY_DATABASE_URI']= 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['DEBUG'] = True

db=SQLAlchemy(app)
login_manager=LoginManager()
login_manager.init_app(app)

class User(UserMixin, db.Model):
	id=db.Column(db.Integer,primary_key=True)
	Username=db.Column(db.String(20),unique=True)
	Password=db.Column(db.String(20))
	Name=db.Column(db.String(50))
	Email=db.Column(db.String(20))

class Channel(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    channel_name=db.Column(db.String(20))
    Username=db.Column(db.String(20))
    nickname=db.Column(db.String(20))

socketio = SocketIO(app, async_mode='gevent')	# Working with gevent mode provides keyboard interrupt with CTRL+C.
db.create_all()		# Creates DB.

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/', methods=['GET'])
def home_page():
    now = datetime.datetime.now()
    return render_template('index.html')

@app.route('/sign_up', methods = ['GET','POST'])
def sign_up():
	if request.method == 'POST':
		Name = request.form['Name']
		Username = request.form['Username']
		Password = request.form['Password']
		Email = request.form['Email']
		Confirm = request.form['Confirm']
		usr = User.query.filter_by(Username = Username).first()
		if usr:
		    username_error = "Username already exists choose another one."
		    return render_template('sign_up.html', username_error = username_error)
		else:
			if Password == Confirm:
				new_user = User(Name = Name, Username = Username, Password = Password, Email = Email)
				db.session.add(new_user)
				db.session.commit()
				login_user(new_user)
				session['name'] = Name
				session['UserName'] = Username
				return redirect('/user_panel')
			else:
				password_match = "Passwords could not match!"
				return render_template('/sign_up.html', password_match = password_match)
	else:
	    return render_template('sign_up.html')

@app.route('/login',methods=['GET','POST'])
def login():
	if request.method == 'GET':
		return render_template('login.html')
	else:
		Username = request.form['Username']
		Password = request.form['Password']
		usr = User.query.filter_by(Username = Username).first()
		if usr:
			if usr.Password == Password:
				login_user(usr)
				session['name'] = usr.Name
				session['UserName'] = usr.Username
				return redirect('/user_panel')
			else:
			    password_failure = "Password failure!"
			    return render_template('/login.html',password_failure = password_failure)
		else:
			name_error = "Username not found!"
			return render_template('/login.html',name_error = name_error)

@app.route('/join',methods=['GET','POST'])
def join():
	if request.method == 'GET':
		return render_template('join.html')
	else:
		channel_name = request.form['channel_name']
		nickname = request.form['NickName']
		session['channel_name'] = channel_name
		session['nickname'] = nickname
		chnn = Channel.query.filter_by(channel_name=channel_name).first()
		if not chnn:
			ChannelName_error = "Sorry, channel name is not found!"
			return render_template('join.html',ChannelName_error = ChannelName_error)
		nick = Channel.query.filter_by(nickname=nickname).first()
		if nick:
			NickName_failure = "This nickname is already being used!"
			return render_template('join.html',NickName_failure = NickName_failure)
		return redirect(url_for('channel'))

@app.route('/log_out')
@login_required
def log_out():
	logout_user()
	print(session.get('name') + " has logged out.")
	return 'Logged out.'

@app.route('/user_panel',methods=['GET','POST'])
@login_required
def user_panel():
	if request.method == 'GET':
		return render_template('user_panel.html')
	else:
		name = session['name']
		user = session['UserName']
		channel_name = request.form['Channel_Name']
		nickname = request.form['NickName']
		chn = Channel.query.filter_by(channel_name=channel_name).first()
		if chn:
			ChannelName_error = "Channel is already exists please choose another."
			return render_template('user_panel.html', ChannelName_error = ChannelName_error)

		nick = Channel.query.filter_by(nickname=nickname).first()
		if nick:
			NickName_failure = "Nickname is already being used now try something else."
			return render_template('user_panel.html',NickName_failure = NickName_failure)
		new_channel = Channel(Username = user, nickname = nickname,channel_name = channel_name)
		session['nickname'] = nickname
		session['channel_name'] = channel_name
		db.session.add(new_channel)
		db.session.commit()
		return redirect(url_for('channel'))

@app.route('/channel',methods=['GET','POST'])
def channel():
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
