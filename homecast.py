import time
from pychromecast import *
from tkinter import *

from pychromecast.controllers.media import MediaController


class Player:
    def __init__(self):
        self.chromecasts = None
        self.device_names = []
        self.chosen_device_name = ""
        self.media_url = "https://storage.googleapis.com/hafnium/video/Real%20McCoy%20-%20Another%20Night%20(" \
                         "Official%20Video)-opt.mp4"
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

    def play_media(self):
        self.media_controller = self.chosen_device.media_controller
        self.media_controller.play_media(self.media_url, "video/mp4")
        self.media_controller.block_until_active()

    def pause(self):
        self.media_controller.pause()

    def resume(self):
        self.media_controller.play()

    def stop(self):
        self.media_controller.stop()

    def disconnect(self):
        self.chosen_device.quit_app()


top = Tk()
player = Player()
player.retrieve_all_chromecasts_and_set_device_names()
device_listbox = Listbox(top)
device_index = 1
for device_name in player.get_device_names():
    device_listbox.insert(device_index, device_name)
    device_index = device_index + 1
device_listbox.pack()
chosen_device_label = Label(top, text=player.get_chosen_device_name())
chosen_device_label.pack()


def choose_device_button_clicked():
    items = device_listbox.curselection()
    items = [player.get_device_names()[int(item)] for item in items]
    chosen_device_name = items[0]
    player.set_chosen_device_name_and_connect(chosen_device_name)
    chosen_device_label.config(text=player.get_chosen_device_name())


choose_device_button = Button(top, text="Choose Device", command=choose_device_button_clicked)
choose_device_button.pack()
url_entry = Entry(top)
url_entry.insert(0, player.get_media_url())
url_entry.pack()


# https://storage.googleapis.com/hafnium/video/Real%20McCoy%20-%20Another%20Night%20(Official%20Video)-opt.mp4
def play_url_button_clicked():
    media_url = url_entry.get()
    player.set_media_url(media_url)
    player.play_media()


play_url_button = Button(top, text="Play URL", command=play_url_button_clicked)
play_url_button.pack()


def pause_button_clicked():
    player.pause()


pause_button = Button(top, text="Pause", command=pause_button_clicked)
pause_button.pack()


def resume_button_clicked():
    player.resume()


resume_button = Button(top, text="Resume", command=resume_button_clicked)
resume_button.pack()


def stop_button_clicked():
    player.stop()


stop_button = Button(top, text="Stop", command=stop_button_clicked)
stop_button.pack()


def disconnect_button_clicked():
    player.disconnect()


disconnect_button = Button(top, text="Disconnect", command=disconnect_button_clicked)
disconnect_button.pack()
top.mainloop()
