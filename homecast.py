import time
from pychromecast import *
from tkinter import *
import os
from requests import get
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from pychromecast.controllers.media import MediaController


class MediaFile:
    def __init__(self):
        self.name = ""
        self.mime_type = ""
        self.url = ""

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def set_mime_type(self, mime_type):
        self.mime_type = mime_type

    def get_mime_type(self):
        return self.mime_type

    def set_url(self, url):
        self.url = url

    def get_url(self):
        return self.url


class Drive:
    def __init__(self):
        # If modifying these scopes, delete the file token.pickle.
        SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']
        """Shows basic usage of the Drive v3 API.
            Prints the names and ids of the first 10 files the user has access to.
            """
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(os.environ.get("GOOGLE_DRIVE_CLIENT_SECRETS_PATH"),
                                                                 SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.drive_service = build('drive', 'v3', credentials=creds)
        self.drive_media_files = []

    def retrieve_media_files(self):
        page_token = None
        while True:
            response = self.drive_service.files().list(q="mimeType contains 'audio' or mimeType contains 'video'",
                                                       spaces='drive',
                                                       fields='files(id,mimeType,name,webContentLink),nextPageToken',
                                                       pageToken=page_token).execute()
            for file in response.get('files', []):
                # Process change
                drive_media_file = MediaFile()
                drive_media_file.set_name(file.get('name'))
                drive_media_file.set_mime_type(file.get('mimeType'))
                drive_media_file.set_url(file.get('webContentLink'))
                self.drive_media_files.append(drive_media_file)
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
        return self.drive_media_files

    def get_media_files(self):
        if len(self.drive_media_files) == 0:
            return self.retrieve_media_files()
        else:
            return self.drive_media_files


class Player:
    def __init__(self):
        self.chromecasts = None
        self.device_names = []
        self.chosen_device_name = ""
        self.media_url = ""
        self.media_mime_type = "video/mp4"
        self.chosen_device = None
        self.media_controller = None

    def get_device_names(self):
        return self.device_names

    def retrieve_all_chromecasts_and_set_device_names(self):
        self.chromecasts = get_chromecasts()
        for cc in self.chromecasts:
            self.device_names.append(cc.device.friendly_name)

    def get_chosen_device_name(self):
        return self.chosen_device_name

    def set_chosen_device_name_and_connect(self, chosen_device_name):
        self.chosen_device_name = chosen_device_name
        self.chosen_device = next(cc for cc in self.chromecasts if cc.device.friendly_name == self.chosen_device_name)
        self.chosen_device.wait()

    def get_media_url(self):
        return self.media_url

    def set_media_url(self, media_url):
        self.media_url = media_url

    def get_media_mime_type(self):
        return self.media_mime_type

    def set_media_mime_type(self, media_mime_type):
        self.media_mime_type = media_mime_type

    def play_media(self):
        self.media_controller = self.chosen_device.media_controller
        self.media_controller.play_media(self.media_url, self.media_mime_type)
        self.media_controller.block_until_active()

    def pause(self):
        self.media_controller.pause()

    def resume(self):
        self.media_controller.play()

    def stop(self):
        self.media_controller.stop()

    def disconnect(self):
        self.chosen_device.quit_app()

    def test_speech(self):
        self.media_controller.play_media()

def synthesize_text_with_audio_profile(text):
    """Synthesizes speech from the input string of text."""
    from google.cloud import texttospeech

    client = texttospeech.TextToSpeechClient()

    input_text = texttospeech.types.SynthesisInput(text=text)

    # Note: the voice can also be specified by name.
    # Names of voices can be retrieved with client.list_voices().
    voice = texttospeech.types.VoiceSelectionParams(language_code='en-US')

    # Note: you can pass in multiple effects_profile_id. They will be applied
    # in the same order they are provided.
    audio_config = texttospeech.types.AudioConfig(
        audio_encoding=texttospeech.enums.AudioEncoding.MP3,
        effects_profile_id=['handset-class-device'])

    response = client.synthesize_speech(input_text, voice, audio_config)

    # The response's audio_content is binary.
    speech_data_filename = 'speech_data.mp3'
    with open(speech_data_filename, 'wb') as speech_data:
        pickle.dump(response.audio_content, speech_data)
        print('Audio content written to file "%s"' % speech_data_filename)

    if os.path.exists(speech_data_filename):
        with open(speech_data_filename, 'rb') as speech_data:
            my_speech_data = pickle.load(speech_data)


synthesize_text_with_audio_profile("Hello.")
top = Tk()
top.configure(background="floral white")
top.title("HomeCast")
top.minsize(500, -1)
player = Player()
drive = Drive()
drive.get_media_files()
media_files = drive.get_media_files()
media_listbox = Listbox(top, background="lavender")
media_index = 1
for media_file in media_files:
    media_listbox.insert(media_index, "{} ({})".format(media_file.get_name(), media_file.get_mime_type()))
    media_index = media_index + 1
media_listbox.pack(fill=BOTH, expand=1)
url_entry = Entry(top)
url_entry.insert(0, player.get_media_url())
url_entry.pack(fill=BOTH, expand=1)
mime_type_entry = Entry(top)
mime_type_entry.insert(0, player.get_media_mime_type())
mime_type_entry.pack(fill=BOTH, expand=1)


def choose_file_button_clicked():
    items = media_listbox.curselection()
    items = [drive.get_media_files()[int(item)] for item in items]
    chosen_file_url = items[0].get_url()
    chosen_file_mime_type = items[0].get_mime_type()
    player.set_media_url(chosen_file_url)
    player.set_media_mime_type(chosen_file_mime_type)
    url_entry.delete(0, END)
    url_entry.insert(0, player.get_media_url())
    mime_type_entry.delete(0, END)
    mime_type_entry.insert(0, player.get_media_mime_type())


choose_file_button = Button(top, text="Choose File", command=choose_file_button_clicked,
                            highlightbackground="CadetBlue1")
choose_file_button.pack(fill=BOTH, expand=1)
player.retrieve_all_chromecasts_and_set_device_names()
device_listbox = Listbox(top, background="lavender")
device_index = 1
for device_name in player.get_device_names():
    device_listbox.insert(device_index, device_name)
    device_index = device_index + 1
device_listbox.pack(fill=BOTH, expand=1)
chosen_device_label = Label(top, text=player.get_chosen_device_name())
chosen_device_label.pack(fill=BOTH, expand=1)


def choose_device_button_clicked():
    items = device_listbox.curselection()
    items = [player.get_device_names()[int(item)] for item in items]
    chosen_device_name = items[0]
    player.set_chosen_device_name_and_connect(chosen_device_name)
    chosen_device_label.config(text=player.get_chosen_device_name())


choose_device_button = Button(top, text="Choose Device", command=choose_device_button_clicked,
                              highlightbackground="light goldenrod")
choose_device_button.pack(fill=BOTH, expand=1)


def play_media_button_clicked():
    media_url = url_entry.get()
    media_mime_type = mime_type_entry.get()
    player.set_media_url(media_url)
    player.set_media_mime_type(media_mime_type)
    player.play_media()


play_media_button = Button(top, text="Play Media", command=play_media_button_clicked,
                           highlightbackground="LavenderBlush2")
play_media_button.pack(side=LEFT, expand=1)


def pause_button_clicked():
    player.pause()


pause_button = Button(top, text="Pause", command=pause_button_clicked, highlightbackground="aquamarine")
pause_button.pack(side=LEFT, expand=1)


def resume_button_clicked():
    player.resume()


resume_button = Button(top, text="Resume", command=resume_button_clicked, highlightbackground="burlywood1")
resume_button.pack(side=LEFT, expand=1)


def stop_button_clicked():
    player.stop()


stop_button = Button(top, text="Stop", command=stop_button_clicked, highlightbackground="DarkOliveGreen1")
stop_button.pack(side=LEFT, expand=1)


def disconnect_button_clicked():
    player.disconnect()


disconnect_button = Button(top, text="Disconnect", command=disconnect_button_clicked, highlightbackground="plum1")
disconnect_button.pack(side=LEFT, expand=1)

def test_speech_button_clicked():
    print("To be done...")


test_speech_button = Button(top, text="Test Speech", command=test_speech_button_clicked, highlightbackground="plum1")
test_speech_button.pack(side=LEFT, expand=1)
top.mainloop()
