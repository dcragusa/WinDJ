# Python
import multiprocessing
import threading
import Queue

# Tkinter
from Tkinter import *
import tkFont

queue = Queue.Queue()
pread, pwrite = multiprocessing.Pipe(duplex=False)

try:
    import pyHook
except ImportError:
    errorbox('The pyHook module is not installed.')

try:
    import vlc
except ImportError:
    errorbox('The vlc module is not installed.')

try:
    x, x = vlc.find_lib()
except:
    errorbox('VLC is not installed.')


class MessageBox(object):

    def __init__(self, root):
        self.root = root
        self.root.iconbitmap('favicon.ico')
        self.root.title('WinDJHelper')
        default_font = tkFont.nametofont("TkDefaultFont")
        default_font.configure(size=14)
        self.root.option_add("*Font", default_font)
        self.root.bind('<<keypressed>>', self.ButtonPress)

        # message

        self.Instance = vlc.Instance()
        self.player = self.Instance.media_player_new()

        result = []
        mods = self.player.audio_output_device_enum()

        if mods:
            mod = mods
            while mod:
                mod = mod.contents
                result.append((mod.description, mod.device))
                mod = mod.next

        vlc.libvlc_audio_output_device_list_release(mods)

        devices = ''
        for index, value in enumerate(result):
            devices += '%s: %s' % (value[0], value[1])
            if index != len(result)-1:
                devices += '\n'

        self.title = Label(root, text='DEVICES:')
        self.title.grid(row=0, padx=5, pady=(5,0))

        self.label1 = Text(self.root, height=len(result))
        self.label1.insert(1.0, devices)
        self.label1.configure(state="disabled")
        self.label1.configure(bg=root.cget('bg'), relief=FLAT)
        self.label1.grid(row=1, padx=5, pady=5)

        self.scancodeval = StringVar()
        self.scancodeval.set('KEY CODES:\n')
        self.label2 = Label(self.root, textvariable=self.scancodeval)
        self.label2.grid(row=2, padx=5, pady=5)

        # buttons
        ok = Button(self.root, width=8, text='OK', command=self.dismiss)
        ok.grid(row=3, padx=5, pady=(0,5))
        ok.focus_set()

    def ButtonPress(self, event):
        if not queue.empty():
            scancode, ascii = queue.get()
            self.ButtonHandle(scancode, ascii)

    def ButtonHandle(self, scancode, ascii):
        self.scancodeval.set('KEY CODES:\n%s' % str(scancode))

    def dismiss(self):
        self.root.quit()

root = Tk()

def startPipeLoop(root=root, pipe=pread):
    while True:
        if pipe.poll(0.2):
            x = pipe.recv()
            root.event_generate('<<keypressed>>', when='mark')

def pyHookKeypress(event, pipe=pwrite):
    if event.Ascii == 8:
        key = 'BackSpace'
    elif event.Ascii == 32:
        key = 'Space'
    else:
        key = chr(event.Ascii)
    queue.put((event.ScanCode, key))
    pipe.send(1)
    return True

if __name__ == '__main__':

    multiprocessing.freeze_support()

    pipeloop = threading.Thread(target=startPipeLoop)
    pipeloop.daemon = True
    pipeloop.start()

    obj = pyHook.HookManager()
    obj.KeyDown = pyHookKeypress
    obj.HookKeyboard()

    # main gui loop

    msgbox = MessageBox(root)
    root.mainloop()
