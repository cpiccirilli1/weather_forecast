#!/usr/bin/python3
import requests
from pathlib import Path
from xml.etree import ElementTree as ET
import json
import argparse
import platform
import os, sys
from time import sleep
import datetime as dt
from writer import Writer as ww

class geonames:
	def __init__(self, zip_code=None, geo_acct=None):
		self.zip_code =zip_code
		self.geo_acct = geo_acct	
	
	def _country_val(self, tree):
		validate = None

		for child in tree.iter():
			if child.tag == 'countryCode': 
				if child.text == 'US': 
					validate = True
				else:
					validate = False

		return validate

	def api_call(self):
		'''
		Makes a call to geonames api using a pre-made username.
		'''
		url_str = 'http://api.geonames.org/postalCodeSearch?postalcode={0}&maxRows=1&username={1}'.format(self.zip_code, self.geo_acct)
		req = requests.get(url_str)
		tree = ET.fromstring(req.text)
		return tree

	def info_parse(self, tree):
		info_dic = {}
		validate = self._country_val(tree)


		if validate:			
			for child in tree.iter():
				if child.tag == "postalcode": info_dic[child.tag] = child.text
				if child.tag == "name": info_dic[child.tag] = child.text
				if child.tag == "countryCode": info_dic[child.tag] = child.text
				if child.tag == "lat": info_dic[child.tag] = child.text
				if child.tag == "lng": info_dic[child.tag] = child.text
				if child.tag == "adminCode1": info_dic["state_code"] = child.text
				if child.tag == "adminName2": info_dic['county'] = child.text	
		else:
			pass		
			
		return info_dic		


class nws_api:
	def __init__(self, lat=None, lng=None):
		self.lat = lat
		self.lng = lng

	def api_call(self):
		url = "https://api.weather.gov/points/{0},{1}".format(self.lat, self.lng)
		req = requests.get(url)
		data = req.json()
		sleep(1)
		forecast = requests.get(data["properties"]['forecast'])
		new_cast = forecast.json()
		if new_cast.get('title', 'Not existant') == 'Data Unavailable For Requested Point':
			print(new_cast['title'])
			sys.exit()
		else:	
			periods = new_cast['properties']['periods']
			return periods

	def write_json(self, file):
		data = self.api_call()	
		with open(file, 'w+') as weather:
			json.dump(data, weather)

	def read_json(self, file):
		with open(file, 'r') as weather:
			w = json.load(weather)	
		return w	
	
	def _day_ident(self, forecast_range, conn):
		day_parts = ['This Afternoon', 'Tonight', 'Today']
		day_times = []
		forecast_range = int(forecast_range)
		if forecast_range == 1:
			if not conn:
				day_times = [str(dt.datetime.strftime(dt.datetime.now(),"%A"))]
			else:	
				day_times += day_parts #returns day_parts if no other is required
			return day_times		
		elif forecast_range > 1:
			if not conn:
				day_times = self._no_network_day_comp(forecast_range)
			else:	
				custom  = self._day_comp(forecast_range)
				
				day_times += custom + day_parts
			return day_times	
		else:
			print('Please use one of the presets or the -day flag for any day seven or lower')
			print ('weather -day <int>')	

	
	def _day_comp(self, f_range):
		incrimentor = dt.timedelta(days=1) #sets the delta to incriment the days
		today = dt.datetime.now() #todays day.
		comprehension = [str(dt.datetime.strftime(today+(incrimentor*i), '%A')) for i in range(1, f_range+1)]
		return comprehension

	def _no_network_day_comp(self, f_range):
		incrimentor = dt.timedelta(days=1) #sets the delta to incriment the days
		today = dt.datetime.now() #todays day.
		comprehension = [str(dt.datetime.strftime(today, '%A'))]
		comprehension += [str(dt.datetime.strftime(today+(incrimentor*i), '%A')) for i in range(1, f_range+1)]
		return comprehension

	def weather_parse(self, f_range):
		internet = internet_conn(timeout=3)
		if internet:
			periods = self.api_call()
		else:
			print('No internet connection available. Using data from last connection.')
			periods=self.read_json('weather.txt')

		forecasts = self._day_ident(f_range, internet) #loads number of days forecasts 
		tup = tuple()

		for en, p in enumerate(periods):
			for f in forecasts:
				if f in p['name']:
					tup += ([p, en],)
		return tup
	
	def forecast(self, tup):			
		for i in tup:
			print(
'''
[{7}] {0}:
Temperature: {1} {2}
Wind Speed: {3} {4} 
Short Forecast: {5}

{6}
'''.format(i[0]['name'], i[0]['temperature'], i[0]['temperatureUnit'], i[0]['windSpeed'], i[0]['windDirection'], i[0]['shortForecast'], i[0]['detailedForecast'], i[1])
			)
			print ("*" * 50)	

class location_info:
	def __init__(self, args):
		self.args = args

	def get_loc_data(self):
		file_path = os.path.join(str(Path.home()),'.zip_code')
		
		
		if self.args.zip_code: #zip code from argparse
			if not self.args.username: 
				print('You will need a username at http://geonames.org to set up this program.')
				return
			else:	
				geo = geonames(self.args.zip_code, self.args.username) 
				#api.geonames.org call returns {'county': 'Paulding', 'postalcode': '30157', 'countryCode': 'US', 'name': 'Dallas', 'state_code': 'GA', 'lng': '-84.86214', 'lat': '33.90448'}		
			info = geo.info_parse(geo.api_call())
			data = (self.args.zip_code, info["lat"], info['lng'], self.args.username)
			self.zip_info_store(file_path=file_path, info=data)
			#self.alias_append()
			return data			
		else:
		
			loc_data = self.loc_data(file_path)
			return loc_data
			
	def zip_info_store(self, file_path, info):		
		zip_dict = dict()
		zip_list= ['zip', 'lat', 'lng', 'user']
		for en, z in enumerate(zip_list):			
			zip_dict[z]=info[en]

		print(zip_dict)	
		if not os.path.isfile(file_path): #creates a dot file if none.
			with open(file_path, 'w+') as file_info:
				json.dump(zip_dict, file_info)					
		else:
			pass
					
			
	def alias_append(self):	
		bash_alias = os.path.join(str(Path.home()),'.bash_aliases') #path to aliases list
		if platform.system() == "Linux": #checks if linux system
			if os.path.isfile('weather.py') and not os.path.isfile('.bash_aliases'):
				f_path = os.getcwd()+'/weather.py' #path to program
				alias = ww(title=bash_alias) #homebrewed textwriter module
				alias.txtWriter(mode='a', text='alias weather="python3 {}"\n'.format(f_path))
			else:
				pass		
		else:
			print('You have a non-posix system where aliases are not used')


	def loc_data(self, file_path):
		try:
			with open(file_path, 'r') as zip_f:
				data = json.load(zip_f)
				return data
		except FileNotFoundError:
			print("It's a mystery")						

def internet_conn(url='http://www.google.com', timeout=3):
	try:
		inet_conn = requests.get(url, timeout=timeout)
		return True
	except requests.ConnectionError:
		
		return False		

def weather_get(arg_com, nws):
	parse = nws.weather_parse(f_range=arg_com)
	nws.forecast(parse)


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-z', dest='zip_code')
	parser.add_argument('-user', type=str, dest='username')
	parser.add_argument('-today', const=1, dest='now', type=int, nargs="?")
	parser.add_argument('-three', dest='three',const=3, type=int, nargs="?")
	parser.add_argument('-seven', const=7, dest = 'seven', nargs='?', type=int)
	parser.add_argument('-day', const=5, nargs='?', dest='custom', type=int)
	parser.add_argument('-test', action='store_true')
	args = parser.parse_args()
	start = dt.datetime.now()
	internet = internet_conn('http://www.google.com', timeout=3)
	
	if internet:
		location = location_info(args)
		if args.zip_code:
			zip_location, lat, lng, username = location.get_loc_data()
			sleep(1)
		else:
			local = location.get_loc_data()
			zip_location, lat, lng, username =local['zip'], local['lat'], local['lng'], local['user']	
		nws = nws_api(lat=lat, lng=lng)	
		nws.write_json('weather.txt')
		if args.now:
			weather_get(args.now, nws)
		elif args.three:
			weather_get(args.three, nws)
		elif args.seven:
			weather_get(args.seven, nws)
		elif args.custom:
			weather_get(args.custom, nws)
		else:
			weather_get(args.custom, nws)						

		print(dt.datetime.now() - start)

	elif args.test:
				
		test = nws_api()
		parse = test.weather_parse(f_range=args.custom)
		test.forecast(parse)
		print(dt.datetime.now() - start)
	else:
		print('Unable to comply.')	


if __name__ == "__main__":
	main()