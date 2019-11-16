# WinDJ - David Ragusa
# Refer to the LICENSE file.

import os
import queue
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
    'show_hide': get_control_from_config('show_hide'),
    'quit': get_control_from_config('quit'),
    'play_stop': get_control_from_config('play_stop'),
    'vol_up': get_control_from_config('vol_up'),
    'vol_down': get_control_from_config('vol_down'),
    'nav_up': get_control_from_config('nav_up'),
    'nav_down': get_control_from_config('nav_down'),
    'nav_mult_up': get_control_from_config('nav_mult_up'),
    'nav_mult_down': get_control_from_config('nav_mult_down'),
    'search': get_control_from_config('search')
})


# Find songs
def populate_songs():
    song_list = []
    index = 0
    for folder in folders:
        value, path = folder
        try:
            filenames = sorted(os.listdir(path))
        except OSError:
            errorbox(f'You have specified an invalid folder:\n{path}')
        for filename in filenames:
            display = os.path.splitext(filename)[0]
            song_list.append({'index': index, 'path': path, 'filename': filename, 'display': display})
            index += 1
    if not song_list:
        errorbox('There are no files in the folders selected.')
    return song_list


class WinDJ:
    def __init__(self, root):

        # class init
        self.root = root
        self.root.title('WinDJ')
        self.root.bind('<<keypressed>>', self.button_press)

        # WinDJ init
        self.visible = True
        self.playing = False
        self.selected = 0
        self.searching = False
        self.searchstring = ''
        self.searchresult = ''
        self.saved_volume = 50
        self.playingname = ''
        self.playlock = False

        # song list
        self.song_list = populate_songs()

        # initialise vlc
        self.instance = vlc.Instance()
        self.p = self.instance.media_player_new()

        # bottom labels
        self.song_name = tk.StringVar()
        self.label1 = tk.Label(self.root, textvariable=self.song_name, anchor=tk.W)
        self.label1.grid(row=2, columnspan=2)
        self.timer = tk.StringVar()
        self.label2 = tk.Label(self.root, textvariable=self.timer, anchor=tk.W)
        self.label2.grid(row=3, columnspan=2)
        self.status = tk.StringVar()
        self.label3 = tk.Label(self.root, textvariable=self.status)
        self.label3.grid(row=4, columnspan=2)
        self.search = tk.StringVar()
        self.search_box = tk.Label(self.root, textvariable=self.search)
        self.search_box.grid(row=0, columnspan=2)
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

    def ignore_event(self, _):
        return 'break'

    def ensure_top(self):
        self.root.lift()
        self.root.after(5000, self.ensure_top)

    def release_lock(self):
        self.playlock = False

    def button_press(self, _):
        if not queue.empty():
            self.handle_button(queue.get())

    def set_selection(self):
        self.listbox.selection_set(self.selected)
        self.listbox.activate(self.selected)
        self.listbox.see(self.selected)

    def handle_button(self, key):
        if self.searching:
            process = False
            if key in Controls.values():
                # controls override search
                pass
            elif len(key) == 1:
                # not control character
                self.searchstring += key.lower()
                process = True
            elif key == 'Space':
                self.searchstring += ' '
                process = True
            elif key == 'Back':
                self.searchstring = self.searchstring[:-1]
                process = True
            if process:
                self.search.set(self.searchstring)
                self.search_listbox(self.searchstring)

        if key == Controls.play_stop:
            if not self.playlock:
                self.playlock = True  # when no lock, holding play gives crashes
                self.root.after(400, self.release_lock)
                self.play_stop()
        elif key == Controls.nav_up:
            if self.selected > 0:
                self.listbox.selection_clear(self.selected)
                self.selected -= 1
            self.set_selection()
        elif key == Controls.nav_down:
            if self.selected < self.listbox.size()-1:
                self.listbox.selection_clear(self.selected)
                self.selected += 1
            self.set_selection()
        elif key == Controls.nav_mult_up:
            self.listbox.selection_clear(self.selected)
            if self.selected >= Settings.scroll_step - 1:
                self.selected -= Settings.scroll_step
            else:
                self.selected = 0
            self.set_selection()
        elif key == Controls.nav_mult_down:
            self.listbox.selection_clear(self.selected)
            if self.selected <= self.listbox.size() - 1 - Settings.scroll_step:
                self.selected += Settings.scroll_step
            else:
                self.selected = self.listbox.size()-1
            self.set_selection()
        elif key == Controls.vol_up:
            self.saved_volume += 1
            self.p.audio_set_volume(self.saved_volume * 2)
            self.update_labels()
        elif key == Controls.vol_down:
            self.saved_volume -= 1
            self.p.audio_set_volume(self.saved_volume * 2)
            self.update_labels()
        elif key == Controls.search:
            self.hide_search() if self.searching else self.show_search()
        elif key == Controls.show_hide:
            self.show_hide()
        elif key == Controls.reset:
            self.reset()
        elif key == Controls.quit:
            self.root.quit()
            self.root.destroy()

    def hide_search(self):
        self.search_box.grid_remove()
        self.searching = False
        self.populate_listbox()
        for entry in self.song_list:
            if self.searchresult == entry['display']:
                self.selected = entry['index']
        self.set_selection()
        self.searchresult = ''

    def show_search(self):
        self.search_box.grid()
        self.searching = True
        self.show()
        self.searchstring = ''
        self.search.set(self.searchstring)
        self.selected = 0

    def play_stop(self):
        self.listbox.focus_set()
        self.stop() if self.playing else self.play()

    def play(self):
        self.playing = True
        song = self.listbox.get(tk.ACTIVE)
        for entry in self.song_list:
            if song == entry['display']:
                path = entry['path'] + '/' + entry['filename']
                path = path.replace('\\', '\\\\')
                self.p.set_media(self.instance.media_new(path))
                self.playingname = entry['display']
                self.p.play()
                self.root.after(350, self.set_device)  # hackery for some reason...
                break
        if Settings.hide_on_play:
            self.hide()
        if self.searching:
            self.hide_search()
        self.update_labels()

    def stop(self):
        self.playing = False
        self.saved_volume = int(self.p.audio_get_volume() / 2)
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

    def show_hide(self):
        self.hide() if self.visible else self.show()

    def hide(self):
        self.root.withdraw()
        self.visible = False

    def show(self):
        self.root.update()
        self.root.deiconify()
        self.visible = True

    def update_labels(self):
        if self.playing:
            playing = 'Playing'
            songname = self.playingname
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

    def search_listbox(self, searchstring):
        searchresults = [entry for entry in self.song_list if searchstring in entry['display'].lower()]
        self.listbox.delete(0, tk.END)
        for entry in searchresults:
            self.listbox.insert(tk.END, entry['display'])
        self.listbox.selection_set(0)
        self.listbox.activate(0)
        self.listbox.see(0)
        self.searchresult = self.listbox.get(tk.ACTIVE)

    def reset(self):
        self.p.stop()
        self.playing = False
        self.song_list = populate_songs()
        self.populate_listbox()
        self.set_selection()
        self.update_labels()
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
