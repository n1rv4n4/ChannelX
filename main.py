from flask import Flask,session, redirect, url_for, render_template, request
from flask_socketio import SocketIO, send,emit, join_room, leave_room
from flask_wtf import Form
from wtforms.fields import StringField, SubmitField,PasswordField
from wtforms.validators import Required
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager,UserMixin,login_user,login_required,logout_user



class LoginForm(Form):
    """Accepts a name and a password."""
    name = StringField('Name', validators=[Required()])
    password = PasswordField('Password', validators=[Required()])
    submit = SubmitField('Sign in')

class ChannelForm(Form):
    """Accepts a channel_name and a nickname."""
    channel_name = StringField('Channel Name', validators=[Required()])
    nickname = StringField('Nick Name', validators=[Required()])
    submit = SubmitField('Join')


app = Flask(__name__)
app.config['SECRET_KEY'] = 'ChannelX'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:////home/ubuntu/Desktop/ChannelX/login.db'
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

socketio = SocketIO(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/',methods=['GET','POST'])
def get_login():
    print("Get Login")
    form = LoginForm()
    if form.validate_on_submit():
        user=User.query.filter_by(username=form.name.data).first()
        print("username"+str(user))
        if not user:
            new_user=User(username=form.name.data,password=form.password.data)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
        else:
            if user.password != form.password.data:
                print("Wrong Password")
                return redirect('/')
            login_user(user)
        session['name'] = form.name.data
        session['password'] = form.password.data
        return redirect('/get_user_panel')
    elif request.method == 'GET':
        form.name.data = session.get('name', '')
        form.password.data = session.get('password', '')
    return render_template('login.html', form=form)

@app.route('/log_out')
@login_required
def log_out():
    logout_user()
    return 'Logged out'


@app.route('/get_user_panel',methods=['GET','POST'])
@login_required
def get_user_panel():
    print("Get User Panel")
    username=session['name']
    channels=ChannelHistory.query.filter_by(username=username)
    form=ChannelForm()
    if form.validate_on_submit():
        if channels:
            flag=False
            for channel in channels:
                if channel.channel_name == form.channel_name.data:
                    flag=True
                    session['channel_name']=channel.channel_name
                    session['nickname']=channel.nickname
            if not flag:
                new_channel=ChannelHistory(channel_name=form.channel_name.data,nickname=form.nickname.data,username=username)
                db.session.add(new_channel)
                db.session.commit()
                session['channel_name']=form.channel_name.data
                session['nickname']=form.nickname.data
        else:
            new_channel=ChannelHistory(channel_name=form.channel_name.data,nickname=form.nickname.data,username=username)
            db.session.add(new_channel)
            db.session.commit()
            session['channel_name']=form.channel_name.data
            session['nickname']=form.nickname.data
        return redirect(url_for('get_channel'))
    return render_template('user_panel.html',form=form,channels=[channel.channel_name for channel in channels])

@app.route('/channel',methods=['GET','POST'])
@login_required
def get_channel():
    print("Get Channel")
    nickname = session.get('nickname', '')
    channel_name = session.get('channel_name', '')
    return render_template('channel.html', nickname=nickname, channel_name=channel_name)


@socketio.on('joined',namespace='/channel')
def joined(message):
    """Sent by clients when they enter a channel.
    A status message is broadcast to all people in the channel."""
    print("Message joined: ")
    print(message)
    channel_name = session.get('channel_name')
    nickname=session.get('nickname')
    join_room(channel_name)
    emit('status', {'msg': nickname + ' has entered the channel.'}, room=channel_name)


@socketio.on('text',namespace='/channel')
def text(message):
    """Sent by a client when the user entered a new message.
    The message is sent to all people in the channel."""
    print("Message is ")
    print(message)
    channel_name = session.get('channel_name')
    nickname=session.get('nickname')
    emit('message', {'msg': nickname + ':' + message['msg']}, room=channel_name)


@socketio.on('left',namespace='/channel')
def left(message):
    """Sent by clients when they leave a channel.
    A status message is broadcast to all people in the channel."""
    print("Leaving channel")
    channel_name = session.get('channel_name')
    leave_room(channel_name)
    emit('status', {'msg': session.get('nickname') + ' has left the channel.'}, room=channel_name)

if __name__ == '__main__':
	socketio.run(app)