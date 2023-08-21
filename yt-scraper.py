from time import sleep
from os import path
import re
import csv
import sys
import requests
import datetime


def Channel_Links(search, limit) :

	links = []
	channel_links = set()

	while (len(channel_links) < limit):

		response = requests.get(search)
		channels = re.findall(r'"browseId":"([a-zA-Z0-9_-]+)', response.text)

		channel_links.update(["https://www.youtube.com/channel/" + channel for channel in channels])

		if len(channel_links)/limit < 1.00:
			print(f"Getting Channel Link: {len(channel_links)*100/limit:.0f}% done", end='\r')
		else:
			print(f"Getting Channel Link: 100% done", end='\r')

		sleep(1)

	return list(channel_links)[:limit]


def Channel_Name(page_source):
	try:
		channelName = re.search(r'"channelId":"[a-zA-Z0-9_-]+","title":"(.*)","navigation', page_source).groups()[0]
	except (AttributeError,IndexError):
		print("Couldn't Find Channel Name")
		return "Error"
	else:
		return channelName

def Channel_Email(link):
	link = link + '/about'
	response = requests.get(link)
	email = r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9.-]+)"
	try:
		email = re.findall(email, response.text)[1]
	except (AttributeError,IndexError):
		return "NONE"
	else:
		return email

def Channel_Language(page_source):

	languages = ["tamil", "telegu", 
				 "malayalam", "bengali", 
				 "hindi", "marathi", 
				 "kannada"]
	videoLanguage = ""
	for lang in languages:
		if re.search(lang, page_source, re.IGNORECASE):
			videoLanguage = lang.upper()

	if videoLanguage == "":
		videoLanguage = "English".upper()

	return videoLanguage


def Subscriber_Count(page_source):
	try:
		subscribers = re.findall(r'"subscriberCountText"[a-zA-Z:{".\s}]+([\d.]+)\s?([a-zA-Z]+)', page_source)[0]
	except (AttributeError,IndexError):	
		print("\t\t0 SUBSCRIBERS, Check To Make Sure This Is Correct")
		return (0, None)
	else:
		if subscribers:
			return subscribers
		else:
			print("\t\t0 SUBSCRIBERS, Check To Make Sure This Is Correct")
			return (0, None)


def Last_Uploaded(page_source) :

	return "https://www.youtube.com/watch?v=" + re.search(r'"videoId":"([a-zA-Z0-9_-]+)', page_source).groups()[0]


def Description_Keywords(last_uploaded, description_keywords) :

	response = requests.get(last_uploaded)
	try:
		description = re.search(r'"description":{"simpleText":"(.*)},"lengthSeconds"', response.text).groups()[0]
	except (AttributeError,IndexError):
		return False
	else:
		for keyword in description_keywords:
			if re.search(keyword, description, re.IGNORECASE):
				return True

	return False


def Active_Last(last_uploaded, day_range) :

	response = requests.get(last_uploaded)
	
	upload_date = re.search(r'"uploadDate":"([\d-]+)', response.text).groups()[0]
	upload_date = datetime.datetime.strptime(upload_date, "%Y-%m-%d")
	today = datetime.datetime.now()
	max_last_day = datetime.timedelta(days=day_range)
	
	return (today - max_last_day <= upload_date)


def Save_Data_CSV(file_name, fields, data):

	file_exists = path.isfile(file_name)

	with open(file_name, "a",newline='',encoding='utf-8') as data_file:
	
		writer = csv.DictWriter(data_file, fieldnames=fields, delimiter=",")

		if not file_exists:
			writer.writeheader()

		writer.writerow(data)

def Get_Videos_In_Range(videos_page_link, days_range, max_retry, max_videos):

	today = datetime.datetime.now()
	max_last_day = datetime.timedelta(days=days_range)

	tries = 0
	relevent = []

	while tries < max_retry:
		response = requests.get(videos_page_link)

		ids = re.finditer(r'"videoId":"([a-zA-Z0-9_-]+)","t', response.text)
		ids = [ids.groups()[0] for ids in ids]

		for video_id in ids:
			video_link = "https://www.youtube.com/watch?v=" + video_id
			video_link_response = requests.get(video_link)
			upload_date = re.search(r'"uploadDate":"([\d-]+)"', video_link_response.text).groups()[0]
			upload_date = datetime.datetime.strptime(upload_date, "%Y-%m-%d")

			if (today - max_last_day <= upload_date) :
				relevent.append(video_id)
				if len(relevent) == max_videos:
					break
			else:
				break
		else:
			tries += 1
			continue
		break

	return relevent

def Count_Keywords(video_ids, keyword):

	count = 0

	for vid in video_ids:
		video_link = "https://www.youtube.com/watch?v=" + vid
		video_page = requests.get(video_link)
		try:
			description = re.search(r'"description":{"simpleText":"(.*)},"lengthSeconds"', video_page.text).groups()[0]
		except AttributeError:
			pass
		else:
			if re.search(keyword, description, re.IGNORECASE):
				count += 1

	return count


def Key_Count(videos_page_link, keyword, days_range, max_retry, max_videos):
	
	range_ids = Get_Videos_In_Range(videos_page_link, days_range, max_retry, max_videos)

	count = Count_Keywords(range_ids, keyword)

	return count

def Get_All_Data(file_name, limit, 
				  channel_links, days_range, 
				  fields, description_keywords,
				  avg_of, key_count_keyword
				  ):

	for i in range(limit):

		print("{}. Saving Details For: {}".format(i+1, channel_links[i]))
		progress = 1;steps=9

		videos_page = channel_links[i] + '/videos'
		response = requests.get(videos_page)
		data = dict()

		print("\tSTARTED",end='\r')

		if(response.status_code == 200):

			last_uploaded = Last_Uploaded(response.text)
			print(f"\tProgress: {progress*100/steps:.0f}%", end='\r');progress += 1

			channel_name = Channel_Name(response.text)
			print(f"\tProgress: {progress*100/steps:.0f}%", end='\r');progress += 1
			channel_lang = Channel_Language(response.text)
			print(f"\tProgress: {progress*100/steps:.0f}%", end='\r');progress += 1
			channel_email = Channel_Email(channel_links[i])
			print(f"\tProgress: {progress*100/steps:.0f}%", end='\r');progress += 1

			subs = Subscriber_Count(response.text)
			print(f"\tProgress: {progress*100/steps:.0f}%", end='\r');progress += 1
			subscriber_count, subscriber_unit = subs[0], subs[1]

			description_keywords_present = "Present" if Description_Keywords(last_uploaded, description_keywords) else "NOT PRESENT"
			print(f"\tProgress: {progress*100/steps:.0f}%", end='\r');progress += 1

			active = "Active" if Active_Last(last_uploaded, days_range) else "NOT ACTIVE"
			print(f"\tProgress: {progress*100/steps:.0f}%", end='\r');progress += 1

			if key_count_keyword.strip() != '':
				day_range_key = 30
				max_retries = 3
				max_videos = 40
				key_count = Key_Count(videos_page, key_count_keyword, day_range_key, max_retries, max_videos)
				print(f"\tProgress: {progress*100/steps:.0f}%", end='\r');progress += 1
		
		sleep(1)

		data_recieved = [channel_links[i], channel_name, channel_lang, 
						 channel_email, subscriber_count, subscriber_unit,
						 description_keywords_present, active,
						 ]
		field = fields

		if key_count_keyword.strip() != '':
			if key_count not in data_recieved:
				data_recieved.append(key_count)
			if "Count of {}".format(key_count_keyword if key_count_keyword != '' else 'NONE') not in field:
				field.append("Count of " + key_count_keyword)

		data = { 
				key : value for key,value in list(zip(field, data_recieved))
				}

		print('\tCompleted')
		Save_Data_CSV(file_name, field, data)


def main(search_query, limit, key_count_keyword):

	search_query_format:str = "https://www.youtube.com/results?search_query="

	search = search_query_format + search_query
	# Get channel links found on search result
	channel_links = Channel_Links(search, limit)
	
	file_name = search_query.replace("+", " ") + ".csv"
	day_range: int = 30 	# last upload day to consider for activeness
	avg_of = 10

	fields: list = ["Channel Link",
					"Channel Name",
					"Channel Language",
					"Channel Email",
					"Sub Count", 
					"Sub Unit", 
					"Key Present", 
					"Active or not in {} Days".format(day_range),
					]
	description_keywords: list = ["purchase", 
								  "coupon", 
								  "discount", 
								  "buy", 
								  "Off",
								  ]
	Get_All_Data(file_name, limit, channel_links, day_range, fields, description_keywords, avg_of, key_count_keyword)

	print("DONE!!!")

if __name__ == "__main__":
	print("\t\tALL INPUT FIELDS SHOULD BE ,(COMMA) SEPARATED")
	search_query = [ item.strip().replace(' ','+') for item in input("Enter search queries: \n").split(',') ]
	limits = list(map( int ,[item.strip() for item in input("Enter corresponding max limits: \n").split(",")] ))
	keywords = [ item.strip() for item in input("Enter corresponding keywords to look for: \n").split(",") ]
	
	if len(search_query) == len(limits) == len(keywords):
		for k,v in enumerate(search_query):
			main(v, limits[k], keywords[k])
	else:
		sys.exit("Mismatched Input Data")
