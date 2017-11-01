from flask import Flask,session, redirect, url_for, render_template, request
from flask_socketio import SocketIO, send,emit, join_room, leave_room
from flask_wtf import Form
from wtforms.fields import StringField, SubmitField,PasswordField
from wtforms.validators import Required

class LoginForm(Form):
    """Accepts a nickname and a password."""
    name = StringField('Name', validators=[Required()])
    password = PasswordField('Password', validators=[Required()])
    submit = SubmitField('Sign in')

class ChannelForm(Form):
    """Accepts a nickname and a password."""
    channel_name = StringField('Channel Name', validators=[Required()])
    nickname = StringField('Nick Name', validators=[Required()])
    submit = SubmitField('Join')


app = Flask(__name__)
app.config['SECRET_KEY'] = 'ChannelX'
socketio = SocketIO(app)
"""
@socketio.on('message')
def handleMessage(msg):
	print('Message: ' + msg)
	send(msg, broadcast=True)

@socketio.on('join')
def join()
"""

@app.route('/',methods=['GET','POST'])
def get_login():
    print("Get Login")
    form = LoginForm()
    if form.validate_on_submit():
        session['name'] = form.name.data
        session['password'] = form.password.data
        return redirect('/get_user_panel')
    elif request.method == 'GET':
        form.name.data = session.get('name', '')
        form.password.data = session.get('password', '')
    return render_template('login.html', form=form)

@app.route('/get_user_panel',methods=['GET','POST'])
def get_user_panel():
    print("Get User Panel")
    form=ChannelForm()
    if form.validate_on_submit():
		session['channel_name']=form.channel_name.data
		session['nickname']=form.nickname.data
		return redirect(url_for('get_channel'))
    return render_template('user_panel.html',form=form)

@app.route('/channel',methods=['GET','POST'])
def get_channel():
    print("Get Channel")
    nickname = session.get('nickname', '')
    channel_name = session.get('channel_name', '')
    return render_template('channel.html', nickname=nickname, channel_name=channel_name)


@socketio.on('joined',namespace='/channel')
def joined(message):
    """Sent by clients when they enter a room.
    A status message is broadcast to all people in the room."""
    print("Message joined: ")
    print(message)
    channel_name = session.get('channel_name')
    nickname=session.get('nickname')
    join_room(channel_name)
    emit('status', {'msg': nickname + ' has entered the room.'}, room=channel_name)


@socketio.on('text',namespace='/channel')
def text(message):
    """Sent by a client when the user entered a new message.
    The message is sent to all people in the room."""
    print("Message is ")
    print(message)
    channel_name = session.get('channel_name')
    nickname=session.get('nickname')
    emit('message', {'msg': nickname + ':' + message['msg']}, room=channel_name)


@socketio.on('left',namespace='/channel')
def left(message):
    """Sent by clients when they leave a room.
    A status message is broadcast to all people in the room."""
    print("Leaving room")
    channel_name = session.get('channel_name')
    leave_room(channel_name)
    emit('status', {'msg': session.get('nickname') + ' has left the room.'}, room=channel_name)

if __name__ == '__main__':
	socketio.run(app)