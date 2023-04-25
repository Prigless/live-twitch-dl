# Live Twitch Stream Downloader
With this tool you can download live Twitch streams.


## Additional Features:


- Twitch chat can be downloaded as well, but only raw data. With help of: https://github.com/xenova/chat-downloader.
```json
{"author": {"badges": [{"badge": {"name": "subscriber", "id": "X", "title": "4-Year Subscriber", "description": "4-Year Subscriber"}}, {"badge": {"name": "premium", "id": "X", "title": "Prime Gaming", "description": "Prime Gaming"}}], "name": "X", "display_name": "X", "id": "X", "is_moderator": false, "is_subscriber": true}, "channel_id": "X", "message_id": "X", "timestamp": 0, "message": "Despair"}
```

- There is an option to automatically send finished download to discord channel.

![Discord Embed Example](https://user-images.githubusercontent.com/89812657/232319096-5c16be2c-e806-4f32-b8dc-8e069ad103db.png)

- You can also easily send finished download to Google Storage.


## How To Run:
1. Download repository, it is intended to be used on Linux OS.
2. Install the newest Python, tmux and jq. If you do not wish to use tmux, you can manually run .py files.
3. Initiate venv with `python -m venv .venv`
4. Activate venv `. .venv/bin/activate`
5. Install required dependencies `pip install -r requirements.txt`
6. Edit .env-template and rename it to .env
6. Run `RUN.sh` (you may need to run `chmod +x RUN.sh`)

## If You Want To Use Google Storage:
1. Create a project in Google Cloud Platform.
3. Create a bucket with "db/" folder.
2. Create a service account and download the json file to the root of the project.
3. Edit GOOGLE_APPLICATION_CREDENTIALS in .env-template.




## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.