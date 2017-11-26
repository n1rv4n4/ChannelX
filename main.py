from flask import Flask, session, redirect, url_for, render_template, request
from flask_socketio import SocketIO, send,emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import os

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
	Channel_Name=db.Column(db.String(20))
	Channel_Password=db.Column(db.String(20))
	Username=db.Column(db.String(20))
	Nickname=db.Column(db.String(20))

socketio = SocketIO(app, async_mode='gevent')	# Working with gevent mode provides keyboard interrupt with CTRL+C.
db.create_all()		# Creates DB.

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/terms_and_conditions', methods=['GET'])
def terms_and_conditions():
    return render_template('terms_and_conditions.html')

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
		    username_failure = "Username already exists choose another one."
		    return render_template('sign_up.html', username_failure = username_failure)
		else:
			if Password == Confirm:
				new_user = User(Name = Name, Username = Username, Password = Password, Email = Email)
				db.session.add(new_user)
				db.session.commit()
				login_user(new_user)
				session['Name'] = Name
				session['Username'] = Username
				return redirect('/user_panel')
			else:
				password_match = "Passwords are not same!"
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
				session['Name'] = usr.Name
				session['Username'] = usr.Username
				return redirect('/user_panel')
			else:
			    password_failure = "Password failure!"
			    return render_template('/login.html', password_failure = password_failure)
		else:
			name_failure = "Username not found!"
			return render_template('/login.html', name_failure = name_failure)

@app.route('/join',methods=['GET','POST'])
def join():
	if request.method == 'GET':
		return render_template('join.html')
	else:
		Channel_Name = request.form['Channel_Name']
		Channel_Password = request.form['Channel_Password']
		Nickname = request.form['Nickname']
		session['Channel_Name'] = Channel_Name
		session['Nickname'] = Nickname

		chnn = Channel.query.filter_by(Channel_Name=Channel_Name).first()
		if not chnn:
			ChannelName_failure = "Sorry, channel name is not found!"
			return render_template('join.html', ChannelName_failure = ChannelName_failure)

		if chnn.Channel_Password != Channel_Password:
			ChannelPassword_failure = "Channel name and password could not match!"
			return render_template('join.html', ChannelPassword_failure = ChannelPassword_failure)

		nick = Channel.query.filter_by(Nickname=Nickname).first()
		if nick:
			Nickname_failure = "This nickname is already being used!"
			return render_template('join.html', Nickname_failure = Nickname_failure)

		return redirect('/channel')

@app.route('/log_out')
@login_required
def log_out():
	logout_user()
	print(session.get('Name') + " has logged out.")
	return 'Logged out.'

@app.route('/user_panel',methods=['GET','POST'])
@login_required
def user_panel():
	if request.method == 'GET':
		return render_template('user_panel.html')
	else:
		Name = session['Name']
		User = session['Username']
		Channel_Name = request.form['Channel_Name']
		Nickname = request.form['Nickname']
		Channel_Password = request.form['Channel_Password']
		chn = Channel.query.filter_by(Channel_Name=Channel_Name).first()
		if chn:
			ChannelName_failure = "Channel is already exists please choose another."
			return render_template('user_panel.html', ChannelName_failure = ChannelName_failure)

		nick = Channel.query.filter_by(Nickname=Nickname).first()
		if nick:
			NickName_failure = "Nickname is already being used now try something else."
			return render_template('user_panel.html',NickName_failure = NickName_failure)
		new_channel = Channel(Username = User, Nickname = Nickname, Channel_Name = Channel_Name, Channel_Password = Channel_Password)
		session['Nickname'] = Nickname
		session['Channel_Name'] = Channel_Name
		db.session.add(new_channel)
		db.session.commit()
		return redirect('/channel')

@app.route('/channel',methods=['GET','POST'])
@login_required
def channel():
    print(session.get('Nickname') + " created channel " + session.get('Channel_Name'))
    Nickname = session.get('Nickname')
    Channel_Name = session.get('Channel_Name')
    return render_template('channel.html', Nickname=Nickname, Channel_Name=Channel_Name)

@socketio.on('joined',namespace='/channel')
def joined(message):
    print(session.get('Nickname') + " entered the channel " + session.get('Channel_Name'))
    Channel_Name = session.get('Channel_Name')
    Nickname=session.get('Nickname')
    join_room(Channel_Name)
    emit('status', {'msg': Nickname + ' has entered the channel.'}, room=Channel_Name)

@socketio.on('text',namespace='/channel')
def text(message):
    print("Sent message by " + session.get('Nickname') + ": " + message['msg'])
    Channel_Name = session.get('Channel_Name')
    Nickname=session.get('Nickname')
    emit('message', {'msg': Nickname + ': ' + message['msg']}, room=Channel_Name)

@socketio.on('left',namespace='/channel')
def left(message):
    print(session.get('Nickname') + " leaved the channel " + session.get('Channel_Name'))
    Channel_Name = session.get('Channel_Name')
    leave_room(Channel_Name)
    emit('status', {'msg': session.get('Nickname') + ' has left the channel.'}, room=Channel_Name)

if __name__ == '__main__':
	socketio.run(app)
