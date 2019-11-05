# WinDJ Helper - David Ragusa
# Refer to the LICENSE file.

import os
import sys
import queue
import threading
import pyWinhook
import tkinter as tk
import multiprocessing
from tkinter import font


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class ErrorBox:

    def __init__(self, msg):
        root = self.root = tk.Tk()
        self.root.iconbitmap(resource_path('favicon.ico'))
        root.title('WinDJ')
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(size=14)
        root.option_add("*Font", default_font)
        # main frame
        frame = tk.Frame(root)
        frame.pack(ipadx=2, ipady=2)
        # message
        message = tk.Label(frame, text=msg)
        message.pack(padx=16, pady=6)
        # buttons
        ok = tk.Button(frame, width=8, text='OK', command=self.dismiss)
        ok.pack(side=tk.TOP)
        ok.focus_set()
        ok.bind('<KeyPress-Return>', func=self.dismiss)
        root.update_idletasks()
        # centre screen
        xp = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
        yp = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
        geom = (root.winfo_width(), root.winfo_height(), xp, yp)
        root.geometry('{0}x{1}+{2}+{3}'.format(*geom))

    def dismiss(self):
        self.root.quit()


def errorbox(msg):
    msgbox = ErrorBox(msg)
    msgbox.root.mainloop()
    msgbox.root.destroy()
    sys.exit(0)


try:
    import vlc
except (ImportError, OSError):
    errorbox('VLC is not installed.')


class HelperBox:

    def __init__(self, root):
        self.root = root
        self.root.iconbitmap(resource_path('favicon.ico'))
        self.root.title('WinDJHelper')
        default_font = font.nametofont('TkDefaultFont')
        default_font.configure(size=14)
        self.root.option_add('*Font', default_font)
        self.root.bind('<<keypressed>>', self.button_press)

        self.player = vlc.Instance().media_player_new()

        result = []
        mods = self.player.audio_output_device_enum()

        if mods:
            mod = mods
            while mod:
                mod = mod.contents
                result.append((mod.description.decode('ascii'), mod.device.decode('ascii')))
                mod = mod.next

        vlc.libvlc_audio_output_device_list_release(mods)

        devices = ''
        max_device_len = 0
        for index, value in enumerate(result):
            device_str = f'{value[0]}: {value[1]}'
            devices += device_str
            if len(device_str) > max_device_len:
                max_device_len = len(device_str)
            if index != len(result)-1:
                devices += '\n'

        self.title = tk.Label(root, text='DEVICES:')
        self.title.grid(row=0, padx=5, pady=(5, 0))

        self.label1 = tk.Text(self.root, height=len(result), width=max_device_len)
        self.label1.insert(1.0, devices)
        self.label1.configure(state='disabled', bg=root.cget('bg'), relief=tk.FLAT)
        self.label1.grid(row=1, padx=5, pady=5)

        self.scancodeval = tk.StringVar()
        self.scancodeval.set('KEY CODES:\n')
        self.label2 = tk.Label(self.root, textvariable=self.scancodeval)
        self.label2.grid(row=2, padx=5, pady=5)

        # buttons
        ok = tk.Button(self.root, width=8, text='OK', command=self.dismiss)
        ok.grid(row=3, padx=5, pady=(0, 5))
        ok.focus_set()

    def button_press(self, _):
        if not queue.empty():
            self.handle_button(queue.get())

    def handle_button(self, key):
        self.scancodeval.set(f'KEY CODES:\n{str(key)}')

    def dismiss(self):
        self.root.quit()


if __name__ == '__main__':

    multiprocessing.freeze_support()

    root = tk.Tk()

    queue = queue.Queue()
    p_read, p_write = multiprocessing.Pipe(duplex=False)

    def start_pipe_loop():
        while True:
            if p_read.poll(0.2):
                _ = p_read.recv()
                root.event_generate('<<keypressed>>', when='mark')

    def pyhook_keypress(event):
        queue.put(event.Key)
        p_write.send(1)
        return True

    # poll the keyboard hook
    pipeloop = threading.Thread(target=start_pipe_loop)
    pipeloop.daemon = True
    pipeloop.start()

    # hook the keyboard
    obj = pyWinhook.HookManager()
    obj.KeyDown = pyhook_keypress
    obj.HookKeyboard()

    # main gui loop
    WinDJHelper = HelperBox(root)
    root.mainloop()
