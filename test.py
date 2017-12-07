from main import app,db,User
import unittest

class BaseTestCase(unittest.TestCase):
	def setUp(self):
		db.create_all()
		db.session.add(User(id = 1, Name = "",Email = "admin@hotmail.com",Username = "admin", 
			Password = "password"))
		db.session.commit()
	def tearDown(self):
		db.session.remove()
		db.drop_all()

class FlaskTestCase(BaseTestCase):

	#ensure that the index page loads correctly
	def test_index_load(self):
		tester = app.test_client(self)
		response = tester.get('/',content_type = 'html/text')
		self.assertEqual(response.status_code, 200)
		print("testing that the index page loads correctly")
		
	#ensure that the sign_up page loads correctly
	def test_sign_up_load(self):
		tester = app.test_client(self)
		response = tester.get('/sign_up',content_type = 'html/text')
		self.assertEqual(response.status_code, 200)
		print("testing that the sign_up page loads correctly")
	
	#ensure sign_up behaves correctly
	def test_correct_sign_up(self):
		tester = app.test_client(self)
		response = tester.post('/sign_up',data = dict(Name = "",Email = "admin@hotmail.com",Username = "newuser", 
			Password = "password",Confirm = "password"),follow_redirects = True)
		self.assertIn(b'Create Channel',response.data)
		print("testing that sign_up behaves correctly")
	
	#ensure sign_up behaves correctly for password confirmation
	def test_wrong_confirmation_sign_up(self):
		tester = app.test_client(self)
		response = tester.post('/sign_up',data = dict(Name = "",Email = "admin@hotmail.com",Username = "newuser", 
			Password = "password",Confirm = "wrong"),follow_redirects = True)
		self.assertIn(b'Passwords are not same!',response.data)
		print("testing that sign_up behaves correctly for password confirmation")
	
	#ensure sign_up behaves correctly given the username that already exists
	def test_exists_username_sign_up(self):
		tester = app.test_client(self)
		response = tester.post('/sign_up',data = dict(Name = "",Email = "admin@hotmail.com",Username = "admin", 
			Password = "password",Confirm = "password"),follow_redirects = True)
		self.assertIn(b'Username already exists choose another one.',response.data)
		print("testing that sign_up behaves correctly given the username that already exists")
	
	#ensure that the login page loads correctly
	def test_login_load(self):
		tester = app.test_client(self)
		response = tester.get('/login',content_type = 'html/text')
		self.assertEqual(response.status_code, 200)
		print("testing that the login page loads correctly")
	
	#ensure login behaves correctly given the correct credential
	def test_correct_login(self):
		tester = app.test_client(self)
		response = tester.post('/login',data = dict(Username = "admin", Password = "password"),follow_redirects = True)
		self.assertIn(b'Create Channel',response.data)
		print("testing that login behaves correctly given the correct credential")
	
	#ensure login behaves correctly given the incorrect Username
	def test_false_username_login(self):
		tester = app.test_client(self)
		response = tester.post('/login',data = dict(Username = "deneme", 
			Password = "password"),follow_redirects = True)
		self.assertIn(b'Username not found!',response.data)
		print("testing that login behaves correctly given the incorrect Username")
		
	#ensure login behaves correctly given the incorrect Password
	def test_false_password(self):
		tester = app.test_client(self)
		response = tester.post('/login',data = dict(Username = "admin", 
			Password = "wrong"),follow_redirects = True)
		self.assertIn(b'Password failure!',response.data)
		print("testing that login behaves correctly given the incorrect Password")
		
	#ensure channel creation is done correctly
	def test_correct_create_channel(self):
		weekday=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
		tester = app.test_client(self)
		tester.post('/login',data = dict(Username = "admin", Password = "password"),follow_redirects = True)
		response = tester.post('/user_panel',
			data = dict(Nickname = "admin", Channel_Name = "NewChannel",
			Channel_Password = "asdfgh",Start_Time = "00:01",End_Time = "23:59",
			days=",".join(weekday)),follow_redirects = True
		)
		self.assertIn(b'Leave this channel!',response.data)
		print("testing that channel creation is done correctly")
		
	#ensure that users cannot reach unauthorized user_panel
	def test_Unauthorized_user_panel(self):
		tester = app.test_client(self)
		response = tester.get('/user_panel',content_type = 'html/text')
		self.assertEqual(response.status_code, 401)
		print("testing that users cannot reach unauthorized user_panel")
		
	#ensure that users cannot reach unauthorized channel
	def test_Unauthorized_channel(self):
		tester = app.test_client(self)
		response = tester.get('/channel',content_type = 'html/text')
		self.assertEqual(response.status_code, 401)
		print("testing that users cannot reach unauthorized channel")
		
if __name__ == '__main__':
	unittest.main()