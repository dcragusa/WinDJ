# WinDJ - David Ragusa
# Refer to the LICENSE file.

import os
import re
import sys
import pafy
import html
import queue
import requests
import threading
import pyWinhook
import tkinter as tk
import multiprocessing
from configparser import ConfigParser
from helper import errorbox, resource_path

try:
    import vlc
except (ImportError, OSError):
    errorbox('VLC is not installed.')


class AttrDict(dict):
    # access data by dot notation e.g. {'a': 1} -> d.a = 1
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self

    def __getattr__(self, name):
        return self.get(name, None)


if not os.path.isfile('config.cfg'):
    errorbox('Missing configuration file.\nconfig.cfg should be in this folder.')

config = ConfigParser(inline_comment_prefixes=(';',))
config.read('config.cfg')

if config.has_section('Folders'):
    folders = config.items('Folders')
    if not folders:
        errorbox('Incorrect configuration file.\nYou must have at least one folder!')
else:
    errorbox('Incorrect configuration file.\nMake sure there is a [Folders] section.')


def get_setting_from_config(name, type_, default):
    if config.has_option('Settings', name):
        setting = config.get('Settings', name)
        if type_ is bool:
            if setting.lower() == 'true':
                return True
            elif setting.lower() == 'false':
                return False
            else:
                errorbox(f'Invalid setting for {name}:\n{setting}')
        elif type_ is int:
            try:
                return int(setting)
            except ValueError:
                errorbox(f'Invalid number for {name}:\n{setting}')
        elif type_ is str:
            return setting
    else:
        return default


def get_control_from_config(name):
    if config.has_option('Controls', name):
        return config.get('Controls', name)
    else:
        errorbox(f'Missing \'{name}\' control.')


Settings = AttrDict({
    'hide_on_play': get_setting_from_config('hide_on_play', bool, True),
    'show_on_stop': get_setting_from_config('show_on_stop', bool, True),
    'fixed_position': get_setting_from_config('fixed_position', bool, True),
    'hor_size': get_setting_from_config('hor_size', int, 220),
    'ver_size': get_setting_from_config('ver_size', int, 550),
    'hor_offset': get_setting_from_config('hor_offset', int, 1620),
    'ver_offset': get_setting_from_config('ver_offset', int, 100),
    'scroll_step': get_setting_from_config('scroll_step', int, 5),
    'controls_captured': get_setting_from_config('controls_captured', bool, False),
    'output_device': get_setting_from_config('output_device', str, None)
})

Controls = AttrDict({
    'reset': get_control_from_config('reset'),
    'toggle_show': get_control_from_config('toggle_show'),
    'quit': get_control_from_config('quit'),
    'toggle_play': get_control_from_config('toggle_play'),
    'vol_up': get_control_from_config('vol_up'),
    'vol_down': get_control_from_config('vol_down'),
    'nav_up': get_control_from_config('nav_up'),
    'nav_down': get_control_from_config('nav_down'),
    'nav_mult_up': get_control_from_config('nav_mult_up'),
    'nav_mult_down': get_control_from_config('nav_mult_down'),
    'search': get_control_from_config('search'),
    'yt_mode': get_control_from_config('yt_mode')
})

# necessary as tk can't display chars outside of BMP
non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)


class WinDJ:
    def __init__(self, root):

        # class init
        self.root = root
        self.root.title('WinDJ')
        self.root.bind('<<keypressed>>', self.button_press)

        # WinDJ init
        self.visible = True
        self.playing = False
        self.search_open = False
        self.search_string = ''
        self.saved_volume = 50
        self.playing_name = ''
        self.play_lock = False
        self.youtube_mode = False
        self.youtube_thread = None

        # song list
        self.song_list = None  # will be populated line below
        self.populate_song_list()
        self.youtube_list = []

        # initialise vlc
        self.instance = vlc.Instance('--no-video')
        self.p = self.instance.media_player_new()

        # searches and labels
        self.search = tk.StringVar()
        self.search_box = tk.Label(self.root, textvariable=self.search)
        self.search_box.grid(row=0, columnspan=2)
        self.song_name = tk.StringVar()
        self.label_songname = tk.Label(self.root, textvariable=self.song_name, anchor=tk.W)
        self.label_songname.grid(row=2, columnspan=2)
        self.timer = tk.StringVar()
        self.label_timer = tk.Label(self.root, textvariable=self.timer, anchor=tk.W)
        self.label_timer.grid(row=3, columnspan=2)
        self.status = tk.StringVar()
        self.label_status = tk.Label(self.root, textvariable=self.status)
        self.label_status.grid(row=4, columnspan=2)
        self.button_youtube = tk.Button(self.root, text='Youtube', command=self.toggle_youtube_mode)
        self.button_youtube.grid(row=5, columnspan=2)
        self.search_box.grid_remove()

        # scrollbar and listbox
        self.scrollbar = tk.Scrollbar(self.root)
        self.scrollbar.grid(row=1, column=0, sticky=(tk.N, tk.S))
        self.listbox = tk.Listbox(self.root, yscrollcommand=self.scrollbar.set, selectmode=tk.BROWSE)
        self.populate_listbox()
        self.listbox.grid(row=1, column=1, sticky=(tk.N, tk.S, tk.W, tk.E))
        self.scrollbar.config(command=self.listbox.yview)

        # ignore double controls on listbox
        self.listbox.bind('<Down>', self.ignore_event)
        self.listbox.bind('<Up>', self.ignore_event)
        self.listbox.bind('<Left>', self.ignore_event)
        self.listbox.bind('<Right>', self.ignore_event)
        self.listbox.bind('<Next>', self.ignore_event)
        self.listbox.bind('<Prior>', self.ignore_event)

        # bind clicks
        self.listbox.bind('<Button-1>', self.click)
        self.listbox.bind('<Double-Button-1>', self.double_click)

        # select first item
        self.listbox.selection_set(0)

        # topmost window
        self.root.wm_attributes('-topmost', True)
        self.ensure_top()

        # set up labels
        self.update_labels()
        self.update_timer()

        # configure sizing
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(1, weight=1)

    def ensure_top(self):
        self.root.lift()
        self.root.after(5000, self.ensure_top)

    def ignore_event(self, _):
        return 'break'

    def button_press(self, _):
        if not queue.empty():
            self.handle_button(queue.get())

    def populate_song_list(self):
        song_list = []
        index = 0
        for folder in folders:
            value, path = folder
            try:
                filenames = sorted(os.listdir(path))
            except OSError:
                errorbox(f'You have specified an invalid folder:\n{path}')
                sys.exit(0)
            for filename in filenames:
                display = os.path.splitext(filename)[0]
                song_list.append({'index': index, 'path': path, 'filename': filename, 'display': display})
                index += 1
        if not song_list:
            errorbox('There are no files in the folders selected.')
        self.song_list = song_list

    @property
    def selected(self):
        return self.listbox.curselection()[0] if self.listbox.curselection() else 0

    def release_play_lock(self):
        self.play_lock = False

    def click(self, event):
        idx = self.listbox.nearest(event.y)
        self.set_selection(idx)

    def double_click(self, event):
        self.click(event)
        self.play()

    def set_selection(self, idx):
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(idx)
        self.listbox.activate(idx)
        self.listbox.see(idx)

    def handle_button(self, key):
        if self.search_open:
            process = False
            if key in Controls.values():
                # controls override search
                pass
            elif len(key) == 1:
                # not control character
                self.search_string += key.lower()
                process = True
            elif key == 'Space':
                self.search_string += ' '
                process = True
            elif key == 'Back':
                self.search_string = self.search_string[:-1]
                process = True
            if process:
                self.search.set(self.search_string)
                if self.youtube_mode:
                    # debounce the youtube search on a 0.5s timer
                    if self.youtube_thread:
                        self.youtube_thread.cancel()
                    self.youtube_thread = threading.Timer(0.5, self.search_youtube)
                    self.youtube_thread.daemon = True
                    self.youtube_thread.start()
                else:
                    self.search_songlist()

        if key == Controls.toggle_play:
            if not self.play_lock:
                self.play_lock = True  # when no lock, holding play gives crashes
                self.root.after(400, self.release_play_lock)
                self.toggle_play()
        elif key == Controls.nav_up:
            if self.selected > 0:
                self.set_selection(self.selected - 1)
        elif key == Controls.nav_down:
            if self.selected < self.listbox.size() - 1:
                self.set_selection(self.selected + 1)
        elif key == Controls.nav_mult_up:
            if self.selected >= Settings.scroll_step - 1:
                self.set_selection(self.selected - Settings.scroll_step)
            else:
                self.set_selection(0)
        elif key == Controls.nav_mult_down:
            if self.selected <= self.listbox.size() - 1 - Settings.scroll_step:
                self.set_selection(self.selected + Settings.scroll_step)
            else:
                self.set_selection(self.listbox.size() - 1)
        elif key == Controls.vol_up:
            if self.saved_volume < 100:
                self.saved_volume += 1
                self.p.audio_set_volume(self.saved_volume * 2)
                self.update_labels()
        elif key == Controls.vol_down:
            if self.saved_volume > 0:
                self.saved_volume -= 1
                self.p.audio_set_volume(self.saved_volume * 2)
                self.update_labels()
        elif key == Controls.search:
            self.toggle_search()
        elif key == Controls.yt_mode:
            self.toggle_youtube_mode()
        elif key == Controls.toggle_show:
            self.toggle_show()
        elif key == Controls.reset:
            self.reset()
        elif key == Controls.quit:
            self.root.quit()
            self.root.destroy()

    def toggle_search(self):
        self.hide_search() if self.search_open else self.show_search()

    def show_search(self):
        self.search_open = True
        self.search_box.grid()
        self.show()
        self.search_string = ''
        self.search.set(self.search_string)
        self.set_selection(0)

    def hide_search(self):
        self.search_open = False
        self.search_box.grid_remove()
        index = self.song_list[self.selected]['index'] if self.song_list else 0
        self.populate_listbox()
        self.set_selection(index)

    def toggle_youtube_mode(self):
        self.youtube_mode_off() if self.youtube_mode else self.youtube_mode_on()

    def youtube_mode_on(self):
        self.youtube_mode = True
        self.show_search()
        self.song_list = []
        self.populate_listbox()
        self.button_youtube.config(relief=tk.SUNKEN)

    def youtube_mode_off(self):
        self.youtube_mode = False
        self.hide_search()
        self.populate_song_list()
        self.populate_listbox()
        self.button_youtube.config(relief=tk.RAISED)

    def toggle_play(self):
        self.listbox.focus_set()
        self.stop() if self.playing else self.play()

    def play(self):
        self.playing = True
        entry = self.song_list[self.selected]

        if 'path' in entry:
            # play from file
            path = entry['path'] + '/' + entry['filename']
            path = path.replace('\\', '\\\\')
        else:
            # play from youtube - get audio stream url
            vid = pafy.new(f'https://www.youtube.com{entry["url"]}')
            path = vid.getbestaudio().url

        self.p.set_media(self.instance.media_new(path))
        self.playing_name = entry['display']
        self.p.play()
        self.root.after(350, self.set_device)  # hackery for some reason...

        if Settings.hide_on_play:
            self.hide()
        if self.search_open:
            self.hide_search()
        self.update_labels()

    def stop(self):
        self.playing = False
        self.p.stop()
        self.instance = vlc.Instance()
        self.p = self.instance.media_player_new()
        if Settings.show_on_stop:
            self.show()
        self.update_labels()

    def set_device(self):
        self.p.audio_output_device_set(None, Settings.output_device)
        self.p.pause()
        self.root.after(10)
        self.p.pause()

    def toggle_show(self):
        self.hide() if self.visible else self.show()

    def hide(self):
        self.visible = False
        self.root.withdraw()

    def show(self):
        self.visible = True
        self.root.update()
        self.root.deiconify()

    def update_labels(self):
        if self.playing:
            playing = 'Playing'
            songname = self.playing_name
        else:
            playing = 'Stopped'
            songname = '-'

        self.song_name.set(songname)
        self.status.set(f'{playing} | Volume: {self.saved_volume}')

    def update_timer(self):
        if self.playing:
            curtime = '%d:%02d' % divmod(round(self.p.get_time()/1000), 60)
            tottime = '%d:%02d' % divmod(round(self.p.get_length()/1000), 60)
            self.timer.set(f'{curtime} / {tottime}')
        else:
            self.timer.set('-')
        self.root.after(500, self.update_timer)

    def populate_listbox(self):
        self.listbox.delete(0, tk.END)
        for entry in self.song_list:
            self.listbox.insert(tk.END, entry['display'])

    def search_songlist(self):
        self.song_list = [entry for entry in self.song_list if self.search_string in entry['display'].lower()]
        self.populate_listbox()
        self.set_selection(0)

    def search_youtube(self):
        self.listbox.delete(0, tk.END)
        # sp searches for videos only
        payload = {'search_query': self.search_string, 'sp': 'EgIQAQ%3D%3D'}
        resp = requests.get('http://www.youtube.com/results', params=payload).text
        search_results = re.findall(r'<h3.+?href="(.+?)".+?title="(.+?)"', resp)
        self.song_list = []
        for idx, result in enumerate(search_results):
            display = html.unescape(result[1].translate(non_bmp_map))
            self.song_list.append({'index': idx, 'url': result[0], 'display': display})
            self.listbox.insert(tk.END, display)
        self.set_selection(0)

    def reset(self):
        self.stop()
        self.hide_search()
        self.youtube_mode_off()
        self.set_selection(0)
        self.show()


if __name__ == '__main__':

    multiprocessing.freeze_support()

    window = tk.Tk()
    window.resizable(width=False, height=False)
    window.lift()
    window.attributes('-topmost', True)
    window.iconbitmap(resource_path('favicon.ico'))
    window.geometry(f'{Settings.hor_size}x{Settings.ver_size}+{Settings.hor_offset}+{Settings.ver_offset}')
    if Settings.fixed_position:
        window.overrideredirect(True)
    WinDJ = WinDJ(window)

    queue = queue.Queue()
    p_read, p_write = multiprocessing.Pipe(duplex=False)

    def start_pipe_loop():
        while True:
            if p_read.poll(0.2):
                _ = p_read.recv()
                window.event_generate('<<keypressed>>', when='mark')

    def pyhook_keypress(event):
        queue.put(event.Key)
        p_write.send(1)
        # controls captured by WinDJ and not passed through
        return not (Settings.controls_captured and event.Key in Controls.values())

    # poll the keyboard hook
    pipeloop = threading.Thread(target=start_pipe_loop)
    pipeloop.daemon = True
    pipeloop.start()

    # hook the keyboard
    obj = pyWinhook.HookManager()
    obj.KeyDown = pyhook_keypress
    obj.HookKeyboard()

    # main gui loop
    window.mainloop()
