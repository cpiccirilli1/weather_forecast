#!/usr/bin/python3
import requests
from pathlib import Path
from xml.etree import ElementTree as ET
import json
import argparse
import platform
import os
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
		forecast = requests.get(data["properties"]['forecast'])
		new_cast = forecast.json()
		periods = new_cast['properties']['periods']
		print(periods)
		return periods

	def write_json(self, file):
		data = self.api_call()
		with open(file, 'w+') as weather:
			json.dump(data, weather)

	def read_json(self, file):
		with open(file, 'r') as weather:
			w = json.load(weather)

		periods = w['properties']['periods']	
		return periods	
	
	def _day_ident(self, forecast_range, conn):
		day_parts = ['This Afternoon', 'Tonight', 'Today']
		day_times = []

		if forecast_range == 1:
			if not conn:
				day_times = [str(dt.datetime.strftime(dt.datetime.now(),"%A"))]
			else:	
				day_times += day_parts #returns day_parts if no other is required
		elif forecast_range:
			if not conn:
				day_times = self._no_network_day_comp(forecast_range)
			else:	
				custom  = self._day_comp(forecast_range)
				
				day_times += custom + day_parts
		else:
			print('Please use one of the presets or the -day flag for any day seven or lower')
			print ('weather -day <int>')	
		print(day_times)	
		return day_times 
	
	def _day_comp(self, f_range):
		incrimentor = dt.timedelta(days=1) #sets the delta to incriment the days
		today = dt.datetime.now() #todays day.
		print(today)
		comprehension = [str(dt.datetime.strftime(today+(incrimentor*i), '%A')) for i in range(1, f_range+1)]
		print(comprehension)
		return comprehension

	def _no_network_day_comp(self, f_range):
		incrimentor = dt.timedelta(days=1) #sets the delta to incriment the days
		today = dt.datetime.now() #todays day.
		comprehension = [str(dt.datetime.strftime(today+(incrimentor*i), '%A')) for i in range(1, f_range+1)]
		comprehension += [str(dt.datetime.strftime(today, '%A'))]
		print (comprehension)
		return comprehension

	def weather_parse(self, f_range):
		internet = internet_conn(timeout=1)
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
		loc_data = self.loc_data(file_path)
		
		if self.args.zip_code: #zip code from argparse
			if not self.args.username: 
				print('You will need a username at http://geonames.org to set up this program.')
				return
			else:	
				geo = geonames(self.args.zip_code, self.args.username) 
				#api.geonames.org call returns {'county': 'Paulding', 'postalcode': '30157', 'countryCode': 'US', 'name': 'Dallas', 'state_code': 'GA', 'lng': '-84.86214', 'lat': '33.90448'}		
			info = geo.info_parse(geo.api_call())
			

			print(info)
			return (self.args.zip_code, info["lat"], info['lng'], self.args.username)
			'''
			if not os.path.isfile(file_path): #creates a dot file if none.
				with open(file_path, 'w+') as zip_f: 
					info_tup = (self.args.zip_code, info["lat"], info['lng'], self.args.username)
					zip_f.write(info_tup)
					return info_tup	
			else:
				pass
			
		else:
			return loc_data
			'''	

	def alias_append(self):
		pass	
		'''	
		bash_alias = os.path.join(str(Path.home()),'.bash_aliases') #path to aliases list
		if platform.system() == "Linux": #checks if linux system
			f_path = os.getcwd()+'/weather.py' #path to program
			alias = ww(title=bash_alias) #homebrewed textwriter module
			lines = alias.txtReader(mode='r')
			if f_path not in lines:
				alias.txtWriter(mode='a', text='alias pod="python3 {}"'.format(f_path))
			else:
				pass
		else:
			pass
		'''

	def loc_data(self, file_path):
		try:
			with open(file_path, 'r') as zip_f:
				data = zip_f.readline()
				return data
		except FileNotFoundError:
			with open(file_path, 'w+') as new_file:
				new_file.write(self.args.zip_code)						

def internet_conn(url='http://www.google.com', timeout=3):
	try:
		inet_conn = requests.get(url, timeout=timeout)
		return True
	except requests.ConnectionError:
		
		return False		


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-z', dest='zip_code')
	parser.add_argument('-user', type=str, dest='username')
	parser.add_argument('-today', default=1, dest='today', type=int)
	parser.add_argument('-3day', default=3, dest='three', type=int)
	parser.add_argument('-7day', default=7, dest = 'seven', type=int)
	parser.add_argument('-day', default=5, dest='custom', type=int)
	parser.add_argument('-test', action='store_true')
	args = parser.parse_args()

	start = dt.datetime.now()
	internet = internet_conn('http://www.google.com', timeout=3)
	
	if internet:
		location = location_info(args)
		zip_location, lat, lng, username = location.get_loc_data()
		sleep(1)
		nws = nws_api(lat=lat, lng=lng)	
		nws.write_json('weather.txt')
		if args.today:
			parse = nws.weather_parse(f_range=args.today)
			nws.forecast(parse)
		elif args.three:
			parse = nws.weather_parse(f_range=args.three)
			nws.forecast(parse)
		elif args.seven:
			parse = nws.weather_parse(f_range=args.seven)
			nws.forecast(parse)
		else:
			pass						

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