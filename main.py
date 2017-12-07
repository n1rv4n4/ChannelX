from flask import Flask, session, redirect, url_for, render_template, request
from flask_socketio import SocketIO, send,emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import os
import datetime

basedir = os.path.abspath(os.path.dirname(__file__))	# Relative path for SQLAlchemy database file.
app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = 'ChannelX!^+%&/(()=?798465312-_*'	# Random complex key for CSRF security.
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']= False				# Eliminates SQLAlchemy deprecation warning.
app.config['SQLALCHEMY_DATABASE_URI']= 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['DEBUG'] = True
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'computerprojecttwo@gmail.com'
app.config['MAIL_PASSWORD'] = 'CProje2..'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True


mail = Mail(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
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
	Chat_Admin=db.Column(db.String(20))
	Start_Time=db.Column(db.String(20))
	End_Time=db.Column(db.String(20))
	days=db.Column(db.String(100))


class Nickname(db.Model):
	id=db.Column(db.Integer,primary_key=True)
	nickname=db.Column(db.String(20))
	username=db.Column(db.String(20))
	channel_name=db.Column(db.String(20))


class Message(db.Model):
	id=db.Column(db.Integer,primary_key=True)
	sender=db.Column(db.String(20))
	channel_name=db.Column(db.String(20))
	content=db.Column(db.String(200))
	date=db.Column(db.DateTime, default=datetime.datetime.utcnow)

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
		user = User.query.filter_by(Username = Username).first()
		if user:
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
		user = User.query.filter_by(Username = Username).first()
		if user:
			if user.Password == Password:
				login_user(user)
				session['Name'] = user.Name
				session['Username'] = user.Username
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
		nick = request.form['Nickname']
		session['Channel_Name'] = Channel_Name
		session['Nickname'] = nick

		chnn = Channel.query.filter_by(Channel_Name=Channel_Name).first()
		if not chnn:
			ChannelName_failure = "Sorry, channel name is not found!"
			return render_template('join.html', ChannelName_failure = ChannelName_failure)

		if chnn.Channel_Password != Channel_Password:
			ChannelPassword_failure = "Channel name and password could not match!"
			return render_template('join.html', ChannelPassword_failure = ChannelPassword_failure)

		weekday=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"][datetime.datetime.today().weekday()]
		if weekday not in chnn.days.split(','):
			ChannelName_failure = "Channel is not available today!"
			return render_template('join.html', ChannelName_failure = ChannelName_failure)

		now = datetime.datetime.now()
		now=int(now.hour)*60+int(now.minute)
		start_hour,start_min=chnn.Start_Time.split(':')
		end_hour,end_min=chnn.End_Time.split(':')
		if int(start_hour)*60+int(start_min) <= now < int(end_hour)*60+int(end_min):
			pass
		else:
			ChannelName_failure = "Channel is not available at this time!"
			return render_template('join.html', ChannelName_failure = ChannelName_failure)



		nicknames=Nickname.query.filter_by(channel_name=Channel_Name).all()
		nickname_matched=False
		for nickname in nicknames:
			if nickname.nickname == nick:
				if nickname.username == session['Username']:
					nickname_matched=True
					break
				else:
					Nickname_failure = "This nickname is already being used by another user!"
					return render_template('join.html', Nickname_failure = Nickname_failure)
			elif nickname.username == session['Username']:
				Nickname_failure = "You already have another nickname for this channel!"
				return render_template('join.html', Nickname_failure = Nickname_failure)

		if not nickname_matched:
			new_nickname = Nickname(nickname = nick, username = session['Username'], channel_name = Channel_Name)
			db.session.add(new_nickname)
			db.session.commit()
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
            uname=session['Username']
            print (uname, "uname")
            channels=Channel.query.filter_by(Chat_Admin=uname).all()
            print (channels, "eklendi")
            return render_template('user_panel.html', channels=channels)
        else:
            Name = session['Name']
            User = session['Username']
            Channel_Name = request.form['Channel_Name']
            nickname = request.form['Nickname']
            Channel_Password = request.form['Channel_Password']
            Start_Time=request.form['Start_Time']
            End_Time=request.form['End_Time']
            days=request.form.getlist('days')
            #print(Start_Time,type(Start_Time))
            #print(End_Time,type(End_Time))
            #print(days)

        chn = Channel.query.filter_by(Channel_Name=Channel_Name).first()
        if chn:
            ChannelName_failure = "Channel is already exists please choose another."
            return render_template('user_panel.html', ChannelName_failure = ChannelName_failure)
        new_channel = Channel(Channel_Name = Channel_Name, Channel_Password = Channel_Password, Chat_Admin=nickname,Start_Time=Start_Time,End_Time=End_Time,days=",".join(days))
        new_nickname = Nickname(nickname = nickname, username = User, channel_name = Channel_Name)
        db.session.add(new_nickname)
        db.session.commit()
        session['Nickname'] = nickname
        session['Channel_Name'] = Channel_Name
        db.session.add(new_channel)
        db.session.commit()
        return redirect('/channel')


@app.route('/channel',methods=['GET','POST'])
def channel():
    Nickname = session.get('Nickname')
    Channel_Name = session.get('Channel_Name')
    chn = Channel.query.filter_by(Channel_Name=Channel_Name).first()
    days_channel_available=chn.days.split(',')
    start_hour,start_min=chn.Start_Time.split(':')
    start_hour,start_min=int(start_hour),int(start_min)
    current_date=datetime.datetime.now()
    days=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    start_date=datetime.datetime(current_date.year,current_date.month,current_date.day-(datetime.datetime.today().weekday()-days.index(days_channel_available[0])),start_hour,start_min)
    messages=Message.query.filter_by(channel_name=Channel_Name).all()
    messages=[str(message.date)+" "+message.sender+": "+message.content for message in messages if start_date <= message.date]
    return render_template('channel.html', Nickname=Nickname, Channel_Name=Channel_Name, messages="\n".join(messages)+"\n")

@app.route("/email",methods=['GET','POST'])
def index():
    MsgBody = "This mail is send automatically."
    fromMsg = ('ChannelX','computerprojecttwo@gmail.com')
    subject = 'ChannelX - New Messages'
    
    emails = User.query.all()
    for email in emails:
        toMsg = "['" + email + "']"
        msg = Message(subject, sender = fromMsg, recipients = toMsg)
        msg.body = MsgBody
        mail.send(msg)
        return render_template('channel.html')

@socketio.on('joined',namespace='/channel')
def joined(message):
	Channel_Name = session.get('Channel_Name')
	Nickname=session.get('Nickname')
	new_message=Message(sender='Server',channel_name=Channel_Name,content=Nickname + ' has entered the channel.')
	db.session.add(new_message)
	db.session.commit()
	print(new_message.content +" "+ Channel_Name)
	join_room(Channel_Name)
	emit('status', {'msg': str(new_message.date)+" "+new_message.sender+": "+new_message.content}, room=Channel_Name)

@socketio.on('text',namespace='/channel')
def text(message):
	Channel_Name=session['Channel_Name']
	chnn = Channel.query.filter_by(Channel_Name=Channel_Name).first()
	now = datetime.datetime.now()
	now=int(now.hour)*60+int(now.minute)
	start_hour,start_min=chnn.Start_Time.split(':')
	end_hour,end_min=chnn.End_Time.split(':')
	if int(start_hour)*60+int(start_min) <= now < int(end_hour)*60+int(end_min):
		print("Sent message by " + session.get('Nickname') + ": " + message['msg'])
	else:
		print("Channel is closed")
		return 
	Channel_Name = session.get('Channel_Name')
	Nickname=session.get('Nickname')
	new_message=Message(sender=Nickname,channel_name=Channel_Name,content=message['msg'])
	db.session.add(new_message)
	db.session.commit()
	emit('message', {'msg': str(new_message.date)+" "+new_message.sender+": "+new_message.content}, room=Channel_Name)
	
@socketio.on('left',namespace='/channel')
def left(message):
	Channel_Name = session.get('Channel_Name')
	Nickname=session.get('Nickname')
	new_message=Message(sender='Server',channel_name=Channel_Name,content=Nickname + ' has left the channel.')
	db.session.add(new_message)
	db.session.commit()
	print(new_message.content+ " " + Channel_Name)
	leave_room(Channel_Name)
	emit('status', {'msg': str(new_message.date)+" "+new_message.sender+": "+new_message.content}, room=Channel_Name)
	
if __name__ == '__main__':
	socketio.run(app)
