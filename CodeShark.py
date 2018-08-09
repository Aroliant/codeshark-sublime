import sublime
import sublime_plugin
import threading
import json
from os.path import expanduser
try:
    from urllib.request import Request, urlopen  # Python 3
except ImportError:
    from urllib2 import Request, urlopen  # Python 2

API_KEY = ""

class CodeSharkUpdateApiKeyCommand(sublime_plugin.WindowCommand):
	def run(self):
		home = expanduser("~")
		config_file = open(home + "/.codeshark","w") 
		global API_KEY			

		def on_done(key):
			API_KEY = key
			if key != "":
				config_file.write(key)
				config_file.close()
				self.window.status_message("CodeShark : API Key Updated")
			

		self.window.show_input_panel("CodeShark : Enter API Key", "", on_done, None, None)


class CodeSharkInsertCodeCommand(sublime_plugin.TextCommand):
	def run(self, edit,pickedID):
		req = Request("https://api.codeshark.live/api/program/" + pickedID)
		req.add_header('X-API-Key',API_KEY)
		req.get_method = lambda: "POST"
		data = ""
		try: 
			data = urlopen(req).read()
		except urllib2.HTTPError:
			return sublime.message_dialog("HTTP Error occured, Please try again")
		except Exception:
			return sublime.message_dialog("Some problem occured, Try again")
		
		data = data.decode("utf-8") 
		JSONData = json.loads(data)
		if JSONData['success'] == False:			
			return sublime.message_dialog(JSONData['error'])

		code = JSONData['program']['program']
		for selection in self.view.sel():
			self.view.insert(edit, selection.begin(), code)


class CodeSharkSearchCodeCommand(sublime_plugin.WindowCommand):
	def run(self):
		home = expanduser("~")
		config_file = open(home + "/.codeshark","r") 
		global API_KEY
		API_KEY = config_file.readline()		
		config_file.close()
		ListPackagesThread(self.window).start()


class ListPackagesThread(threading.Thread):

	"""
	A thread to prevent the listing of existing packages from freezing the UI
	"""

	def __init__(self, window, filter_function=None):
		self.window = window
		self.filter_function = filter_function
		threading.Thread.__init__(self)
		self.list = []

	def run(self):
		def show_panel():
			self.window.show_quick_panel(self.list,  self.on_done , 0)

		req = Request("https://api.codeshark.live/api/programs/")
		req.add_header('X-API-Key',API_KEY)
		req.get_method = lambda: "POST"
		try: 
			data = urlopen(req).read()
		except urllib2.HTTPError:
			return sublime.message_dialog("HTTP Error occured, Please try again")
		except Exception:
			return sublime.message_dialog("Unable to load programs, Please try again")

		data = data.decode("utf-8") 
		JSONData = json.loads(data)
		if JSONData['success'] == False:
			sublime.message_dialog(JSONData['error'])
			return self.window.run_command('code_shark_update_api_key')
		for program in JSONData['programs']:	
			_program = [program['title'], program['category_name'], str(program["program_id"])]
			self.list.append(_program)
		sublime.set_timeout(show_panel, 10)

	def on_done(self, picked):

		if picked == -1:
			return
		pickedID = self.list[picked][2]

		def insert_code():
			self.window.run_command('code_shark_insert_code', { 'pickedID': pickedID })
			pass
		sublime.set_timeout(insert_code, 10)
