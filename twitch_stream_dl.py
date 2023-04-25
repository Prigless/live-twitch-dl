import streamlink
from subprocess import call
import requests
import time
from datetime import datetime
import traceback
import os
import uuid
import logging
from urllib.parse import urlencode

from google.cloud import storage # google-cloud-storage

from dotenv import load_dotenv # python-dotenv
load_dotenv() #? first it looks for .env,   use this func or manually load .env file

# var2= str(date).encode('utf-8')
# hashed_var = hashlib.md5(var).hexdigest()

def basic_logger():
    logging.basicConfig(
        filename='logs/twitch_stream_dl.log',
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


def send_pushsafer_notification(msg):
    post_fields = {
    "t" : 'Live Twitch DL',
    "m" : msg,
    "d" : PUSHSAFER_TARGET_DEVICE,
    "k" : PUSHSAFER_PRIVATE_KEY
    }
    res = requests.get('https://www.pushsafer.com/api/?'+urlencode(post_fields))
    logger.info(res.text)


def check_if_file_exists(name): #? on bucket, on given path
    bucket = storage_client.bucket(BUCKET_NAME)
    stats = storage.Blob(bucket=bucket, name=name).exists(storage_client)
    if stats:
        logger.warning('File DOES Exist On Bucket')
    return stats


def upload_to_bucket(blob_name, file_path):
    try:
        my_bucket = storage_client.get_bucket(BUCKET_NAME)
        blob = my_bucket.blob(blob_name)
        blob.upload_from_filename(file_path)
        return True
    except Exception as e:
        error_data = traceback.format_exc()
        logger.error(error_data)
        return False


def get_info_stream(STREAM_NICK): #? getting info about stream, lastBroadcast_id -- unique ID of stream, lastBroadcast_title -- title of stream, lastBroadcast_gameName -- current game/category on stream
    payload = "[{\"variables\":{\"channelLogin\":\""+STREAM_NICK+"\"},\"extensions\":{\"persistedQuery\":{\"version\":1,\"sha256Hash\":\"5ab2aee4bf1e768b9dc9020a9ae7ccf6f30f78b0a91d5dad504b29df4762c08a\"}}}]"
    headers = {'Accept': '*/*','Accept-Language': 'cs-CZ','Cache-Control': 'no-cache','Client-Id': 'kimne78kx3ncx6brgo4mv6wki5h1ko','Client-Integrity': 'v4.public.eyJjbGllbnRfaWQiOiJraW1uZTc4a3gzbmN4NmJyZ280bXY2d2tpNWgxa28iLCJjbGllbnRfaXAiOiI4OS4xMDMuODcuMTciLCJkZXZpY2VfaWQiOiJHVzVhTm1jYWZhbjk3TllqcWVGUENGMnQ3aWtjem5WZyIsImV4cCI6IjIwMjItMTItMTVUMDc6NDI6MzJaIiwiaWF0IjoiMjAyMi0xMi0xNFQxNTo0MjozMloiLCJpc19iYWRfYm90IjoiZmFsc2UiLCJpc3MiOiJUd2l0Y2ggQ2xpZW50IEludGVncml0eSIsIm5iZiI6IjIwMjItMTItMTRUMTU6NDI6MzJaIiwidXNlcl9pZCI6IiJ9ogV-0YcEjNVYGLF02_vHx7AxDHvte8nLBu9Y6ib66PF7aTvZvK9EU5qOEG7ya90zddOpix08Ui0dqJKnWqckCg','Client-Session-Id': '72215249ba171ab8','Client-Version': '917a4d53-fed7-4621-bdcc-b05309c6b96b','Connection': 'keep-alive','Content-Type': 'text/plain;charset=UTF-8','Origin': 'https://www.twitch.tv','Pragma': 'no-cache','Referer': 'https://www.twitch.tv/','Sec-Fetch-Dest': 'empty','Sec-Fetch-Mode': 'cors','Sec-Fetch-Site': 'same-site','User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36','X-Device-Id': 'GW5aNmcafan97NYjqeFPCF2t7ikcznVg','sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"','sec-ch-ua-mobile': '?0','sec-ch-ua-platform': '"Windows"'}
    res = requests.post('https://gql.twitch.tv/gql', headers=headers, data=payload)
    
    #? cannot get realiable(in sense I would by certain it wont change) video id, with twitch api it would be easy,   now Im using  lastBroadcast_id  - its used in "animatedPreviewURL" and "previewThumbnailURL"
    lastBroadcast_id=res.json()[0]['data']['user']['lastBroadcast']['id'] #? id of the current whole live stream, can raise 40240342120(format) or None, or TypeError: 'NoneType' object is not subscriptable
    lastBroadcast_title=res.json()[0]['data']['user']['lastBroadcast']['title'] #? current title on stream
    lastBroadcast_gameName=res.json()[0]['data']['user']['lastBroadcast']['game']['name'] #? current category on stream (game, just chatting)
    return lastBroadcast_id, lastBroadcast_title, lastBroadcast_gameName


def main(STREAM_NICK):
    stream_dl_url = None

    lastBroadcast_id = None
    lastBroadcast_id_OLD = None

    check_for_upload = True 

    if not os.path.exists('db'):
        logger.info(f'creating db/ folder')
        os.makedirs('db')


    logger.info(f'starting while True loop')
    while True:

        #! upload non-uploaded videos
        if check_for_upload and GOOGLE_CLOUD_STORAGE_ENABLED:
            print('')
            logger.info(f'check_for_upload == True, checking for non-uploaded videos')

            check_for_upload = False #? check only one time if all videos are uploaded per stream
            logger.info(f'folders_to_check: {os.listdir("db")}')
            for folder in os.listdir('db'): #? os.listdir('db')=['22_12_13', '22_12_13_2', '22_12_14]
                files_to_check = os.listdir('db/'+folder) #? files_to_check=['details.txt', 'video.mkv']
                logger.debug(f'files_to_check: {files_to_check}')

                for file in files_to_check:
                    if file.split('.')[-1] == 'mkv': #? will be check if the VIDEO exists on the bucket
                        logger.info(f'mkv file found: {file}')

                        path_of_video = 'db/'+folder+'/'+file #? this is the VIDEO
                        logger.debug(f'path_of_video: {path_of_video}')
                        path_of_dir = 'db/'+folder #? THIS will be uploaded if the VIDEO does NOT exist on the bucket
                        logger.debug(f'path_of_dir: {path_of_dir}')
                        if check_if_file_exists(path_of_video) == False: #? check if the VIDEO exists on the bucket, if not upload whole folder with everything in it
                            start_time = datetime.utcnow()
                            logger.info(f'uploading(txt, mkv) and deleting(mkv) folder: {path_of_dir} // {start_time}')

                            for e in files_to_check: #? this is the way for uploading whole folder
                                logger.debug(f'upload_to_bucket({path_of_dir}/{e}, {path_of_dir}/{e})')
                                if upload_to_bucket(path_of_dir+'/'+e, path_of_dir+'/'+e): #? if all is uploaded, delete local VIDEO for space, im leaving the directory and details.txt in it
                                    if e.split('.')[-1] == 'mkv':
                                        logger.info(f'deleting mkv: {path_of_dir}/{e}')
                                        os.remove(path_of_dir+'/'+e)
                                else:
                                    logger.error('probably tried to upload details.txt when it already existed on the bucket (there is no check for that)')
                                    if NOTIFICATIONS_ENABLED:
                                        send_pushsafer_notification('error while uploading to bucket')
                                        
                            end_time = datetime.utcnow()
                            logger.info(f'uploading and deleting done: {end_time-start_time}')
                            
                        else: #? if uploaded video (or part of it) has not been delete (im using permissions that dont allow replacing files on bucket (plus im not tring to do it anyway) so manual intervention is needed)
                            logger.error('mkv file has not been deleted automaticky! (this can lead to not downloading new stream due to low storage space)')
                            if NOTIFICATIONS_ENABLED:
                                send_pushsafer_notification('mkv file has not been deleted automaticky!')


            logger.info('uploading done, waiting for new stream')
            print('')

        try:
            #* new
            try:
                session = streamlink.Streamlink()
                session.set_option('http-headers', {'Authorization': f'OAuth {TWITCH_OAUTH_TOKEN}'})
                stream_dl_url = session.streams(f'https://www.twitch.tv/{STREAM_NICK}')['best'].url #? url for dl of the stream, it changes 
            except: #? if OAuth token (the user it belongs to) has a problem, it will not work, so next try is without OAuth token  (downloading does not require OAuth token but I wont get ads if I use them (+ I dont need any checks if the cookies is ok (the user it belongs to) it will donwload ok either way))
                logger.error('user with OAuth token has thrown an error')
                if NOTIFICATIONS_ENABLED:
                    send_pushsafer_notification('user with OAuth token has thrown an error')
                stream_dl_url = streamlink.streams(f'https://www.twitch.tv/{STREAM_NICK}')['best'].url #? url for dl of the stream, it changes     
            #* new

            time.sleep(2)
            lastBroadcast_id, lastBroadcast_title, lastBroadcast_gameName = get_info_stream(STREAM_NICK)
        except Exception as e: #(KeyError, TypeError)
            logger.error('both user with OAuth token and without has thrown an error')
            if NOTIFICATIONS_ENABLED:
                send_pushsafer_notification('both user with OAuth token and without has thrown an error')

            error_data = traceback.format_exc()
            if str(e) != "'best'": #? if stream is offline or not found -- streamlink.streams() raises:  KeyError: 'best'
                logger.error(f'str(e) != "best": {error_data}')
                if NOTIFICATIONS_ENABLED:
                    send_pushsafer_notification(f'str(e) != "best": {error_data}')

            else:
                logger.debug('stream is offline')

            

        if lastBroadcast_id != lastBroadcast_id_OLD: #? detecting new stream
            lastBroadcast_id_OLD = lastBroadcast_id
            print('')
            logger.info('new stream detected')

            logger.debug(f'stream_dl_url: {stream_dl_url}, lastBroadcast_id: {lastBroadcast_id}, lastBroadcast_title: {lastBroadcast_title}, lastBroadcast_gameName: {lastBroadcast_gameName}')
            

            if NOTIFICATIONS_ENABLED:
                send_pushsafer_notification(f'Stream UP! {STREAM_NICK}')



            check_for_upload = True
            date_now = datetime.utcnow()

            
            os.chdir(f'db')

            original_dir_name = datetime.utcnow().strftime('%y_%m_%d')
            dir_name = original_dir_name

            num = 1
            while True: #? one stream a day dir_name:22_12_13    multiple:22_12_13_2
                if not os.path.exists(dir_name):
                    logger.debug(f'creating dir: {dir_name}')
                    os.makedirs(dir_name)
                    break
                else:
                    num+=1
                    dir_name=original_dir_name+'_'+str(num)
            os.chdir(dir_name)



            date=date_now.strftime('%m/%d/%Y, %H:%M:%S')
            with open('details.txt', 'w', encoding="utf-8") as file:
                file.write(
                    f'DATE: {date}\n'
                    f'lastBroadcast_id: {lastBroadcast_id}\n'
                    f'lastBroadcast_title: {lastBroadcast_title}\n'
                    f'lastBroadcast_gameName: {lastBroadcast_gameName}\n'
                    f'.m3u8: {stream_dl_url}\n'
                )


            lastBroadcast_title=''.join([x if x.isalnum() else '_' for x in lastBroadcast_title]) #? ascii safe title
            call_process = call(['streamlink', '-o', f'{lastBroadcast_title+"_"+uuid.uuid4().hex[0:12]}.mkv', stream_dl_url, 'best', '--twitch-api-header', f'"Authorization=OAuth {TWITCH_OAUTH_TOKEN}"']) 
            #? subprocess.call() is blocking, so it will wait for the stream to end to continue with the code
            #? --twitch-api-header with OAuth is ONLY for non ad stream, I can download subonly streams without it,      only for stream_dl_url is needed OAuth token

            logger.info('stream has ended')
            os.chdir(f'..')
            os.chdir(f'..')

        else:
            logger.debug('no new stream detected, waiting')
            time.sleep(120)
        time.sleep(2)

logger = basic_logger()
logger.debug('basic_logger() initialized')

STREAM_NICK = os.getenv('STREAM_NICK')
TWITCH_OAUTH_TOKEN = os.getenv('TWITCH_OAUTH_TOKEN')

GOOGLE_CLOUD_STORAGE_ENABLED = bool(os.getenv('GOOGLE_CLOUD_STORAGE_ENABLED'))

if GOOGLE_CLOUD_STORAGE_ENABLED:
    BUCKET_NAME = os.getenv('BUCKET_NAME')
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    storage_client = storage.Client()

NOTIFICATIONS_ENABLED = bool(os.getenv('NOTIFICATIONS_ENABLED'))
if NOTIFICATIONS_ENABLED:
    logger.debug('notifications are enabled')
    PUSHSAFER_USER = os.getenv('PUSHSAFER_USER')
    PUSHSAFER_PRIVATE_KEY = os.getenv('PUSHSAFER_PRIVATE_KEY')
    PUSHSAFER_TARGET_DEVICE = os.getenv('PUSHSAFER_TARGET_DEVICE')

logger.debug(f'all env variables loaded to vars: {os.environ}')
if __name__ == '__main__':
    logger.info(f'starting main({STREAM_NICK})')
    main(STREAM_NICK)

    