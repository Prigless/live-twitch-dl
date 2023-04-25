from chat_downloader import ChatDownloader # chat-downloader
import json

import logging
def basic_logger():
	logging.basicConfig(
		filename='logs/twitch_chat_dl.log',
		level=logging.DEBUG, 
		format= '%(lineno)d;%(asctime)s - %(name)s - %(levelname)s - %(message)s'
		#  datefmt='%H:%M:%S'
	)
	console = logging.StreamHandler()
	console.setLevel(logging.INFO)
	formatter = logging.Formatter('%(message)s')
	console.setFormatter(formatter)
	# add the handler to the root logger
	logging.getLogger('').addHandler(console)
	logger = logging.getLogger(__name__)
	return logger

logging.getLogger("urllib3").disabled = True #? [DEBUG] Total number of messages: X  -- this was spamming console and log
logger = basic_logger()
logger.debug('basic_logger() initialized')

url = 'twitch.tv/haiset'
chat = ChatDownloader().get_chat(url, output='test.json', message_types=['text_message']) # create a generator
print('running')
for index, original_message in enumerate(chat): # iterate over new messages
	print(f'msg num: {index}', end='\r') # print the progress indicator on a single line and overwrite the previous line
	# chat.print_formatted(original_message)    # print the formatted message

	try:
		msg = {}
		msg['author'] = {}
		msg_badges = []
		if 'badges' in original_message['author']:
			for all_badge_info in original_message['author']['badges']:
				msg_badge = {}
				msg_badge['badge'] = {}
				msg_badge['badge']['name'] = all_badge_info['name']
				msg_badge['badge']['id'] = all_badge_info['id'] #? NEW
				msg_badge['badge']['title'] = all_badge_info['title']
				msg_badge['badge']['description'] = all_badge_info['description']
				msg_badges.append(msg_badge)
			msg['author']['badges'] = msg_badges


		msg['author']['name'] = original_message['author']['name']
		msg['author']['display_name'] = original_message['author']['display_name']
		msg['author']['id'] = original_message['author']['id']
		msg['author']['is_moderator'] = original_message['author']['is_moderator']
		msg['author']['is_subscriber'] = original_message['author']['is_subscriber']        

		msg['channel_id'] = original_message['channel_id']
		msg['message_id'] = original_message['message_id']
		msg['timestamp'] = original_message['timestamp']

		try:msg['message'] = original_message['message'] #todo problem, there is no 'message'    subscription_gift?
		except:logger.warning(f'original_message["message"] PROBLEM      {original_message}')



		try:msg['time_in_seconds'] = original_message['time_in_seconds'] #? NEW
		except:pass #? not always present
		try:msg['is_bot'] = original_message['is_bot'] #? NEW
		except:pass #? not always present
	except Exception as e:
		logger.error(f'ERROR:  {e}  {original_message}')
		
		

			


	# with open('chat_own.json', 'r', encoding='utf-8') as f:
	#     my_list = [json.loads(line) for line in f]
	# print(json.dumps(my_list, indent=4))

	with open('twitch_chat_dl.json', 'a', encoding='utf-8') as f:
		f.write(json.dumps(msg))
		f.write('\n')