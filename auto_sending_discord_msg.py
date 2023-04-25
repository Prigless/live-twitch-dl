import requests
import traceback
import os
import re
import pytz #pip install pytz
from datetime import datetime


import discord #discord.py
from discord.ext import commands
from discord.ext import tasks

# from urllib.parse import urlencode #? for dict
from urllib.parse import quote_plus #? for str

from google.cloud import storage

from dotenv import load_dotenv # python-dotenv
load_dotenv() #? first it looks for .env,   use this func or manually load .env file

import logging

def basic_logger(): #? everything to file and info and higher print to console
	logging.basicConfig(
		filename='logs/discord_bot.log',
		level=logging.DEBUG, 
		format= '%(lineno)d;%(asctime)s - %(name)s - %(levelname)s - %(message)s'
		# datefmt='%H:%M:%S'
	)
	console = logging.StreamHandler()
	console.setLevel(logging.INFO)
	formatter = logging.Formatter('%(message)s')
	console.setFormatter(formatter)
	# add the handler to the root logger
	logging.getLogger('').addHandler(console)
	logger = logging.getLogger(__name__)
	return logger

def get_properties_and_values_of_object(objs):
	for obj in objs:
		for attr in dir(obj):
			print(attr)
			# print("obj.%s = %r" % (attr, getattr(obj, attr))) #? this gets like everything
			# x.append("obj.%s = %r" % (attr, getattr(obj, attr))) 

def list_all_details_BUCKET(already_sent_msg_ids):
	try:
		my_bucket = storage_client.get_bucket(BUCKET_NAME)
		blobs_all = list(my_bucket.list_blobs(prefix='db/')) #? list all bucket obejcts with prefix 'db/'  ->  details.txt, stream.mkv, db/(it gets the folder itself)  ->  then use regex to filter it out
		
		logger.debug(f'all files - blobs_all: {blobs_all[0:50]}')

		num = 0
		#? this removes everyting from blobs_all except  db/23_01_13/details.txt  objects, these obejcts (details.txt) will be appended with all information needed
		for index, blob in enumerate(blobs_all[:]): #? every thing thats inside /db, so all .mkv, details.txt, and somtimes then folder blobs too (manualy created blos yes but uploaded through .py script not?? )
			logger.debug(f'index: {index} num: {num} blob: {blob}')
			#* its depended on the scructure: db/date_folder/details.txt+.mkv  ,  every date_folder (23_01_01) has to have details.txt
			#* to this to work .mkv and details.txt are in same folder together wiht \d\d_\d\d_\d* structure
			
			# note:   db/23_02_04_2/ <-- I once created folder manualy and it behaves different.    Every strem/video.mkv with details.txt has a folder object, but this one is the only one showing when I list over them.
			#                          db/ 23  _02  _05   _2<- sometimes there are multuple streams per one date     /.{1} <-- 
			folder__regex = re.match(r"db/(\d\d_\d\d_\d\d(_\d+)?)/details.txt", blob.name) #? /(\d\d_\d\d_\d\d(_\d+)?)/  is the folder, I will extract it few lines down
			if bool(folder__regex) == False: #? every details.txt should have its own folder it is in with .mkv,     so I look only for details.txt and extract the folder it lives in
				blobs_all.remove(blob)
			else:
				folder = folder__regex.group(1)
				folder_blobs = list(my_bucket.list_blobs(prefix=f'db/{folder}/'))
				for e in folder_blobs: #? for all things in folder - details.txt, .mkv
					if str(e.name)[-4::] == '.mkv':
						num += 1 
						logger.debug(f'.mkv detected, index: {index} num: {num} blob: {blob} folder_blobs: {folder_blobs}')

						metadata = {}
						#? Im not using mediaLink(blob.media_link)/selfLink(blob.self_link) bcs it is not recomended(dunno why) https://cloud.google.com/storage/docs/request-endpoints#json-api
						# metadata['mkv_dl_url'] = e.public_url #? this is ok?
						metadata['mkv_dl_url'] = f'https://storage.googleapis.com/download/storage/v1/b/{BUCKET_NAME}/o/{quote_plus(str(e.name))}?alt=media'
						msg_already_sent = False
						for msg_id in already_sent_msg_ids: #? already_sent_msg_ids are all msgs that are already in discord channel
							if msg_id == f'[link]({metadata["mkv_dl_url"]})':
								blobs_all.remove(blob) #? remove the details.txt with all the data for sending msg
								msg_already_sent = True
								break
						if msg_already_sent != True:
							logger.info(f'new msg to send DETECTED, index: {index} num: {num} e.name: {e.name}')
							
							metadata['blob_folder'] = folder

							metadata['downloaded_content'] = blob.download_as_string() #? it can by crlf/lf
							metadata['downloaded_content'] = metadata['downloaded_content'].decode('utf-8') #? little history: I had multiple problems with manually uplading details.txt, didnt do it right with the encodings and I got some blob of nonsence that couldn't be decoded  23_01_25

							
							def get_data_from_downloaded_content(metadata, regex, name):
								regex=re.search(regex, metadata['downloaded_content'], flags=re.MULTILINE)
								if bool(regex) == True: #? if it exists in the content
									metadata[name] = regex.group(1)
									return metadata, True #? found, and set the metadata[name]
								else:
									metadata[name] = None #? not found, and set the metadata[name] to None
									return metadata, False

							metadata, found = get_data_from_downloaded_content(metadata, r"^DATE: (.*)$", 'date')
							metadata, found = get_data_from_downloaded_content(metadata, r"^lastBroadcast_id: (\d{11})$", 'lastBroadcast_id')
							metadata, found = get_data_from_downloaded_content(metadata, r"^lastBroadcast_title: (.*)$", 'lastBroadcast_title')
							if found == False: #? is for old version of details.txt
								metadata, found = get_data_from_downloaded_content(metadata, r"^TITLE: (.*)$", 'lastBroadcast_title')
								
							metadata, found = get_data_from_downloaded_content(metadata, r"^dev_note: (.*)$", 'dev_note')

							logger.debug(metadata)

							blob.local_metadata = metadata #? append the blob object with the metadata

		return blobs_all
	except Exception as e:
		error_data = traceback.format_exc()
		logger.error(error_data)
		return False

def list_all_details_TWITCH():
	payload = "[{\"operationName\":\"FilterableVideoTower_Videos\",\"variables\":{\"limit\":30,\"channelOwnerLogin\":\""+STREAM_NICK+"\",\"broadcastType\":\"ARCHIVE\",\"videoSort\":\"TIME\"},\"extensions\":{\"persistedQuery\":{\"version\":1,\"sha256Hash\":\"a937f1d22e269e39a03b509f65a7490f9fc247d7f83d6ac1421523e3b68042cb\"}}}]"
	headers = {'Accept': '*/*','Accept-Language': 'cs-CZ','Cache-Control': 'no-cache','Client-Id': 'kimne78kx3ncx6brgo4mv6wki5h1ko','Client-Integrity': 'v4.public.eyJjbGllbnRfaWQiOiJraW1uZTc4a3gzbmN4NmJyZ280bXY2d2tpNWgxa28iLCJjbGllbnRfaXAiOiI4OS4xMDMuODcuMTciLCJkZXZpY2VfaWQiOiJHVzVhTm1jYWZhbjk3TllqcWVGUENGMnQ3aWtjem5WZyIsImV4cCI6IjIwMjItMTItMTVUMDc6NDI6MzJaIiwiaWF0IjoiMjAyMi0xMi0xNFQxNTo0MjozMloiLCJpc19iYWRfYm90IjoiZmFsc2UiLCJpc3MiOiJUd2l0Y2ggQ2xpZW50IEludGVncml0eSIsIm5iZiI6IjIwMjItMTItMTRUMTU6NDI6MzJaIiwidXNlcl9pZCI6IiJ9ogV-0YcEjNVYGLF02_vHx7AxDHvte8nLBu9Y6ib66PF7aTvZvK9EU5qOEG7ya90zddOpix08Ui0dqJKnWqckCg','Client-Session-Id': '72215249ba171ab8','Client-Version': '917a4d53-fed7-4621-bdcc-b05309c6b96b','Connection': 'keep-alive','Content-Type': 'text/plain;charset=UTF-8','Origin': 'https://www.twitch.tv','Pragma': 'no-cache','Referer': 'https://www.twitch.tv/','Sec-Fetch-Dest': 'empty','Sec-Fetch-Mode': 'cors','Sec-Fetch-Site': 'same-site','User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36','X-Device-Id': 'GW5aNmcafan97NYjqeFPCF2t7ikcznVg','sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"','sec-ch-ua-mobile': '?0','sec-ch-ua-platform': '"Windows"'}
	#? make a post req to twitch to get last 30ish videos from selectd chanenel (longer that +-30days, twitch deletes the videos)
	try:
		res = requests.post('https://gql.twitch.tv/gql', headers=headers, data=payload)
		logger.debug(f'{res.status_code}{res.content[0:500]}')
		all_details_videos = [e for e in res.json()[0]['data']['user']['videos']['edges']] #? get all details the all videos from the response
		logger.debug(f'all_details_videos: {all_details_videos[0:1]}')

		for index, e in enumerate(all_details_videos):
			#? "animatedPreviewURL": "https://dgeft87wbj63p.cloudfront.net/bf15d33829e49de7b8ae_agraelus_      --> 40438512728 <-- (this should by same as lastBroadcast_id)         _1675538290/storyboards/1728239184-strip-0.jpg",
			#? only "previewThumbnailURL" and "animatedPreviewURL" has the lastBroadcast_id in them      but "previewThumbnailURL": "https://vod-secure.twitch.tv/_404/404_processing_320x180.png"     ---  404_processing so I can only use  "animatedPreviewURL"
			all_details_videos[index]['node']['lastBroadcast_id'] = str(e['node']['animatedPreviewURL']).split(f'_{STREAM_NICK}_')[1][:11]
			logger.debug(f'all_details_videos[index]["node"]["lastBroadcast_id"]: {all_details_videos[index]["node"]["lastBroadcast_id"]}')

		return all_details_videos
	except Exception as e:
		error_data = traceback.format_exc()
		logger.error(error_data)
		return False

STREAM_NICK = os.getenv('STREAM_NICK')
BUCKET_NAME = os.getenv('BUCKET_NAME')
CHANNEL_ID = os.getenv('CHANNEL_ID')
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
storage_client = storage.Client()


logger = basic_logger()
logger.debug('basic_logger() initialized')




# with open('blobs_all.txt', 'w', encoding='utf-8') as f:
# 	f.write(str(blobs_all))

# with open('res_twitch.json', 'w') as f:
# 	f.write(json.dumps(all_details_videos, indent=4, sort_keys=True))


def get_twitch_video_data(all_details_videos, lastBroadcast_id): #? list over all twitch videos, if cant find a video, then  return None
	for video in all_details_videos:
		if video['node']['lastBroadcast_id'] == lastBroadcast_id:
			return video
	return None #? stream has been deleted by streamer, or I have an error in my code





intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(intents=intents, command_prefix='?', help_command=None)

# @tasks.loop(seconds=30)
@tasks.loop(minutes=20)
async def mytask():
	logger.debug('running mytask()')

	all_details_videos = list_all_details_TWITCH()

	channel = client.get_channel(int(CHANNEL_ID))


	already_sent_msg_ids = []
	async for msg in channel.history(limit=None):#* old are first
		
		# print(message.embeds[0].to_dict())
		if msg.embeds: #? ignores msgs that are not embeds, so I can still write in the channel
			already_sent_msg_ids.append(msg.embeds[0].fields[0].value)

	blobs_all = list_all_details_BUCKET(already_sent_msg_ids)
	logger.debug(f'blobs_all: {blobs_all}')


	if bool(blobs_all) == False: #? if no new videos are found, then dont continue bcs it can cause errors
		return 0
	
	for blob in blobs_all: #? blobs_all are only details.txt blobs with all info
		print(blob)
		try: #? having problem with blob.local_metadata['XX'] -- AttributeError: 'Blob' object has no attribute 'local_metadata'
			if bool(blob.local_metadata['lastBroadcast_id']) == False: #! not sure what it does but sometimes I have an error: AttributeError: 'Blob' object has no attribute 'local_metadata'    so not all files has not been yet uploaded by RUN.py?
				logger.info("bool(blob.local_metadata['lastBroadcast_id']) == False")
				raise("bool(blob.local_metadata['lastBroadcast_id']) == False")
		except:
			logger.info("if bool(blob.local_metadata['lastBroadcast_id']) -- ERROR")

		else:
			twitch_video_data=get_twitch_video_data(all_details_videos, blob.local_metadata['lastBroadcast_id'])


			#* TITLE
			blob_title = blob.local_metadata['lastBroadcast_title']
			logger.debug(f'blob_title {blob_title}')
			if bool(twitch_video_data): #? with TWITCH data (video NOT deleted by streamer or 30days passed) 
				twitch_title = twitch_video_data["node"]["title"]
				logger.debug(f'twitch_title {twitch_title}')
				
				
				if blob_title == twitch_title: #? if title is still the same, then I will show only title from blob(its same)
					embed = discord.Embed(description=blob_title)
				else: #? if title was edited by streamer, then I will show both titles
					embed = discord.Embed(description=f'{blob_title}\n\n{twitch_title}')

			else:
				embed = discord.Embed(description=f'{blob_title}')

			logger.debug(f'embed.description (title to display) {embed.description}')

			#* TITLE




			def convert_date(date): #? from CET to Etc/UTC and format
				logger.debug(f'START convert_date(date) {date}')

				local_timezone = pytz.timezone('CET') #? timezone Im in, or users are
				remote_timezone = pytz.timezone('Etc/UTC') #? remote server timezone


				date = datetime.strptime(date, '%m/%d/%Y, %H:%M:%S')
				date = remote_timezone.localize(date)#strftime
				logger.debug(f'MID convert_date(date) {date}')

				#? "%-d" (mac, linux)  OR  "%#d" (windows)  OR  ".replace('X0', '').replace('X', '')" (mac, linux, windows)
				#?  -->  '21.8.23. 21:30'
				date = date.astimezone(local_timezone).strftime('X%d.X%m.%y %H:%M').replace('X0', '').replace('X', '')
				#? this take into account daylight savings plus the conversion between timezones
				#? and converts to time format I want
				
				logger.debug(f'END convert_date(date) {date}')
				return date

			date = convert_date(blob.local_metadata['date']) #? '08/21/2023, 19:30:50'
			#? small picture in left top corner with text
			embed.set_author(name=date, icon_url="https://yt3.googleusercontent.com/ytc/AL5GRJWKzPR4MITG6vAwTWc99a1Q0BHFxc6CVAgE0wJHjA=s88-c-k-c0x00ffffff-no-rj")
			#todo custom icon for each streamer







			embed.add_field(name="Bucket Link", value=f"[link]({blob.local_metadata['mkv_dl_url']})", inline=True)
			if bool(twitch_video_data): #? with TWITCH data (video NOT deleted by streamer or 30days passed) 
				embed.add_field(name="Twitch Link", value=f"[link](https://www.twitch.tv/videos/{twitch_video_data['node']['id']})", inline=True)
			else:
				embed.add_field(name="Twitch Link", value="**N/A**", inline=True)

			dev_note = blob.local_metadata['dev_note']
			if bool(dev_note):
				embed.set_footer(text=dev_note) #? footer is at the bottom of the embed (small text)
			


			if bool(twitch_video_data):
				embed.set_image(url=twitch_video_data["node"]["previewThumbnailURL"]) #? big image at the bottom of the embed
			else:
				# embed.set_image(url="https://static-cdn.jtvnw.net/cf_vods/dgeft87wbj63p/f4033d08b96158310ec0_agraelus_40469973016_1676231128//thumb/thumb0-320x180.jpg") #? big image at the bottom of the embed
				embed.set_image(url="https://vod-secure.twitch.tv/_404/404_processing_320x180.png") #? big image at the bottom of the embed






			logger.info('sending embed')
			logger.debug(f'embed: {embed.to_dict()}')
			await channel.send(embed=embed)



@client.event
async def on_ready():
	logger.info(f'We have logged in as {client.user}')
	mytask.start()

client.run(os.getenv('DISCORD_TOKEN'))




