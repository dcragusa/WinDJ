# WinDJ - David Ragusa
# Refer to the LICENSE file.

# Python
import multiprocessing
import ConfigParser
import threading
import Queue
import sys
import os

# Tkinter
from Tkinter import *
import tkFont


### Error Box
class MessageBox(object):

    def __init__(self, msg):
        root = self.root = Tk()
        root.iconbitmap('favicon.ico')
        root.title('WinDJ')
        default_font = tkFont.nametofont("TkDefaultFont")
        default_font.configure(size=14)
        root.option_add("*Font", default_font)
        # main frame
        frame = Frame(root)
        frame.pack(ipadx=2, ipady=2)
        # message
        message = Label(frame, text=msg)
        message.pack(padx=16, pady=6)
        # buttons
        ok = Button(frame, width=8, text='OK', command=self.dismiss)
        ok.pack(side=TOP)
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
    msgbox = MessageBox(msg)
    msgbox.root.mainloop()
    msgbox.root.destroy()
    # exit after error
    sys.exit(0)


try:
    import pyHook
except ImportError:
    errorbox('The pyHook module is not installed.')

try:
    import vlc
except ImportError:
    errorbox('VLC or the vlc module are not installed.')

try:
    x, x = vlc.find_lib()
except:
    errorbox('VLC or the vlc module are not installed.')


if not os.path.isfile('config.cfg'):
    errorbox('Missing configuration file.\nconfig.cfg should be in this folder.')

config = ConfigParser.RawConfigParser()
config.read('config.cfg')

if not config.has_section('Folders'):
    errorbox('Incorrect configuration file.\nMake sure there is a [Folders] section.')
else:
    folders = config.items('Folders')

if not folders:
    errorbox('Incorrect configuration file.\nYou must have at least one Folders!')


### Settings
if config.has_option('Settings', 'hideonplay'):
    option = config.get('Settings', 'hideonplay')
    if option.lower() == 'true':
        hideonplay = True
    elif option.lower() == 'false':
        hideonplay = False
    else:
        errorbox('Invalid option for hideonplay:\n%s' % option)
else:
    hideonplay = True

if config.has_option('Settings', 'showonstop'):
    option = config.get('Settings', 'showonstop')
    if option.lower() == 'true':
        showonstop = True
    elif option.lower() == 'false':
        showonstop = False
    else:
        errorbox('Invalid option for showonstop:\n%s' % option)
else:
    showonstop = True

if config.has_option('Settings', 'fixedonscreen'):
    option = config.get('Settings', 'fixedonscreen')
    if option.lower() == 'true':
        fixed = True
    elif option.lower() == 'false':
        fixed = False
    else:
        errorbox('Invalid option for fixedonscreen:\n%s' % option)
else:
    fixed = False

if config.has_option('Settings', 'horsize'):
    option = config.get('Settings', 'horsize')
    try:
        horsize = int(option)
    except ValueError:
        errorbox('Invalid number for horsize:\n%s' % option)
else:
    horsize = 200

if config.has_option('Settings', 'versize'):
    option = config.get('Settings', 'versize')
    try:
        versize = int(option)
    except ValueError:
        errorbox('Invalid number for versize:\n%s' % option)
else:
    versize = 550

if config.has_option('Settings', 'horoffset'):
    option = config.get('Settings', 'horoffset')
    try:
        horoffset = int(option)
    except ValueError:
        errorbox('Invalid number for horoffset:\n%s' % option)
else:
    horoffset = 1300

if config.has_option('Settings', 'veroffset'):
    option = config.get('Settings', 'veroffset')
    try:
        veroffset = int(option)
    except ValueError:
        errorbox('Invalid number for veroffset:\n%s' % option)
else:
    veroffset = 100

if config.has_option('Settings', 'scrolljump'):
    option = config.get('Settings', 'scrolljump')
    try:
        scrolljump = int(option)
    except ValueError:
        errorbox('Invalid number for scrolljump:\n%s' % option)
else:
    scrolljump = 5

if config.has_option('Settings', 'controlsoversearch'):
    option = config.get('Settings', 'controlsoversearch')
    if option.lower() == 'true':
        c_over_s = True
    elif option.lower() == 'false':
        c_over_s = False
    else:
        errorbox('Invalid option for controlsoversearch:\n%s' % option)
else:
    c_over_s = True

if config.has_option('Settings', 'audiodevice'):
    audiodevice = config.get('Settings', 'audiodevice')
else:
    audiodevice = None


### Controls
controls = {}

if config.has_option('Controls', 'reset'):
    option = config.get('Controls', 'reset')
    try:
        reset = int(option)
    except ValueError:
        errorbox('Invalid number for \'reset\' control:\n%s' % option)
    controls['reset'] = reset
else:
    errorbox('Missing \'reset\' control.')

if config.has_option('Controls', 'showhide'):
    option = config.get('Controls', 'showhide')
    try:
        showhide = int(option)
    except ValueError:
        errorbox('Invalid number for \'showhide\' control:\n%s' % option)
    controls['showhide'] = showhide
else:
    errorbox('Missing \'showhide\' control.')

if config.has_option('Controls', 'quit'):
    option = config.get('Controls', 'quit')
    try:
        quit = int(option)
    except ValueError:
        errorbox('Invalid number for \'quit\' control:\n%s' % option)
    controls['quit'] = quit
else:
    errorbox('Missing \'quit\' control.')

if config.has_option('Controls', 'playstop'):
    option = config.get('Controls', 'playstop')
    try:
        playstop = int(option)
    except ValueError:
        errorbox('Invalid number for \'playstop\' control:\n%s' % option)
    controls['playstop'] = playstop
else:
    errorbox('Missing \'playstop\' control.')

if config.has_option('Controls', 'volup'):
    option = config.get('Controls', 'volup')
    try:
        volup = int(option)
    except ValueError:
        errorbox('Invalid number for \'volup\' control:\n%s' % option)
    controls['volup'] = volup
else:
    errorbox('Missing \'volup\' control.')

if config.has_option('Controls', 'voldown'):
    option = config.get('Controls', 'voldown')
    try:
        voldown = int(option)
    except ValueError:
        errorbox('Invalid number for \'voldown\' control:\n%s' % option)
    controls['voldown'] = voldown
else:
    errorbox('Missing \'voldown\' control.')

if config.has_option('Controls', 'navup'):
    option = config.get('Controls', 'navup')
    try:
        navup = int(option)
    except ValueError:
        errorbox('Invalid number for \'navup\' control:\n%s' % option)
    controls['navup'] = navup
else:
    errorbox('Missing \'navup\' control.')

if config.has_option('Controls', 'navdown'):
    option = config.get('Controls', 'navdown')
    try:
        navdown = int(option)
    except ValueError:
        errorbox('Invalid number for \'navdown\' control:\n%s' % option)
    controls['navdown'] = navdown
else:
    errorbox('Missing \'navdown\' control.')

if config.has_option('Controls', 'multup'):
    option = config.get('Controls', 'multup')
    try:
        multup = int(option)
    except ValueError:
        errorbox('Invalid number for \'multup\' control:\n%s' % option)
    controls['multup'] = multup
else:
    errorbox('Missing \'multup\' control.')

if config.has_option('Controls', 'multdown'):
    option = config.get('Controls', 'multdown')
    try:
        multdown = int(option)
    except ValueError:
        errorbox('Invalid number for \'multdown\' control:\n%s' % option)
    controls['multdown'] = multdown
else:
    errorbox('Missing \'multdown\' control.')

if config.has_option('Controls', 'search'):
    option = config.get('Controls', 'search')
    try:
        search = int(option)
    except ValueError:
        errorbox('Invalid number for \'search\' control:\n%s' % option)
    controls['search'] = search
else:
    errorbox('Missing \'search\' control.')


# Find songs
def populatesongs():
    songlist = []
    index = 0
    for folder in folders:
        value, path = folder
        try:
            filenames = sorted(os.listdir(path))
        except OSError:
            errorbox('You have specified an invalid folder:\n%s' % path)
        for filename in filenames:
            display = os.path.splitext(filename)[0]
            songlist.append({'index': index, 'path': path, 'filename': filename, 'display': display})
            index += 1

    return songlist

songlist = populatesongs()
print songlist[0]
if not songlist:
    errorbox('There are no files in the folders selected.')

queue = Queue.Queue()
pread, pwrite = multiprocessing.Pipe(duplex=False)


### Main GUI
class WinDJ:
    def __init__(self, root, hideonplay, showonstop, scrolljump, audiodevice, c_over_s, controls):

        # class init
        self.root = root
        self.hideonplay = hideonplay
        self.showonstop = showonstop
        self.scrolljump = scrolljump
        self.audiodevice = audiodevice
        self.controls = controls
        self.c_over_s = c_over_s
        self.root.title('WinDJ')
        self.root.bind('<<keypressed>>', self.ButtonPress)

        # WinDJ init
        self.visible = True
        self.playing = False
        self.selected = 0
        self.searching = False
        self.searchstring = ''
        self.searchresult = ''
        self.savedvolume = 100
        self.playingname = ''
        self.playlock = False

        # song list
        self.songlist = populatesongs()

        # initialise vlc
        self.instance = vlc.Instance()
        self.p = self.instance.media_player_new()

        # bottom labels
        self.songname = StringVar()
        self.label1 = Label(root, textvariable=self.songname, anchor=W)
        self.label1.grid(row=2, columnspan=2)
        self.timer = StringVar()
        self.label2 = Label(root, textvariable=self.timer, anchor=W)
        self.label2.grid(row=3, columnspan=2)
        self.status = StringVar()
        self.label3 = Label(root, textvariable=self.status)
        self.label3.grid(row=4, columnspan=2)
        self.search = StringVar()
        self.searchbox = Label(root, textvariable=self.search)
        self.searchbox.grid(row=0, columnspan=2)
        self.searchbox.grid_remove()

        # scrollbar and listbox
        self.scrollbar = Scrollbar(root)
        self.scrollbar.grid(row=1, column=0, sticky=(N,S))
        self.listbox = Listbox(root, yscrollcommand=self.scrollbar.set, selectmode=BROWSE)
        self.PopulateListBox()
        self.listbox.grid(row=1, column=1, sticky=(N,S,W,E))
        self.scrollbar.config(command=self.listbox.yview)

        # ignore double controls on listbox
        self.listbox.bind("<Down>", self.Ignore)
        self.listbox.bind("<Up>", self.Ignore)
        self.listbox.bind("<Left>", self.Ignore)
        self.listbox.bind("<Right>", self.Ignore)
        self.listbox.bind("<Next>", self.Ignore)
        self.listbox.bind("<Prior>", self.Ignore)

        # select first item
        self.listbox.selection_set(0)

        # bind to click too
        self.listbox.bind('<<ListboxSelect>>', self.OnClick)

        # topmost window
        self.root.wm_attributes("-topmost", True)
        self.EnsureTop()

        # set up labels
        self.UpdateLabels()
        self.UpdateTimer()

        # configure sizing
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(1, weight=1)

    def Ignore(self, event):
        return 'break'

    def EnsureTop(self):
        self.root.lift()
        self.root.after(5000, self.EnsureTop)

    def ReleaseLock(self):
        self.playlock = False

    def ButtonPress(self, event):
        if not queue.empty():
            scancode, ascii = queue.get()
            self.ButtonHandle(scancode, ascii)

    def SetSelection(self):
        self.listbox.selection_set(self.selected)
        self.listbox.activate(self.selected)
        self.listbox.see(self.selected)

    def ButtonHandle(self, scancode, ascii):
        if self.searching:
            process = False
            if self.c_over_s and scancode in self.controls.values(): # controls override search
                pass
            elif len(ascii) == 1 and ascii != '\x00': # not control character
                self.searchstring += ascii
                process = True
            elif ascii == 'Space':
                self.searchstring += ' '
                process = True
            elif ascii == 'BackSpace':
                self.searchstring = self.searchstring[:-1]
                process = True
            if process:
                self.search.set(self.searchstring)
                self.SearchListBox(self.searchstring)

        if scancode == self.controls['playstop']:     # play/stop
            if not self.playlock:
                self.playlock = True # when no lock, holding play gives crashes
                self.root.after(400, self.ReleaseLock)
                self.PlayStop()
        elif scancode == self.controls['navup']:      # nav up
            if self.selected > 0:
                self.listbox.selection_clear(self.selected)
                self.selected -= 1
            self.SetSelection()
        elif scancode == self.controls['navdown']:    # nav down
            if self.selected < self.listbox.size()-1:
                self.listbox.selection_clear(self.selected)
                self.selected += 1
            self.SetSelection()
        elif scancode == self.controls['multup']:      # mult up
            self.listbox.selection_clear(self.selected)
            if self.selected >= self.scrolljump-1:
                self.selected -= self.scrolljump
            else:
                self.selected = 0
            self.SetSelection()
        elif scancode == self.controls['multdown']:    # mult down
            self.listbox.selection_clear(self.selected)
            if self.selected <= self.listbox.size()-1-self.scrolljump:
                self.selected += self.scrolljump
            else:
                self.selected = self.listbox.size()-1
            self.SetSelection()
        elif scancode == self.controls['volup']:      # vol inc
            if self.p.audio_get_volume() <= 198:
                self.p.audio_set_volume(self.p.audio_get_volume()+2)
                self.UpdateLabels()
                self.savedvolume += 2
        elif scancode == self.controls['voldown']:    # vol dec
            if self.p.audio_get_volume() >= 2:
                self.p.audio_set_volume(self.p.audio_get_volume()-2)
                self.UpdateLabels()
                self.savedvolume -= 2
        elif scancode == self.controls['search']:     # search
            if self.searching:
                self.HideSearch()
            else:
                self.ShowSearch()
        elif scancode == self.controls['showhide']:   # show/hide
            self.ShowHide()
        elif scancode == self.controls['reset']:      # reset
            self.Reset()
        elif scancode == self.controls['quit']:       # exit
            self.root.quit()
            self.root.destroy()

    def HideSearch(self):
        self.searchbox.grid_remove()
        self.searching = False
        self.PopulateListBox()
        for entry in self.songlist:
            if self.searchresult == entry['display']:
                self.selected = entry['index']
        self.SetSelection()
        self.searchresult = ''

    def ShowSearch(self):
        self.searchbox.grid()
        self.searching = True
        self.Show()
        self.searchstring = ''
        self.search.set(self.searchstring)
        self.selected = 0

    def PlayStop(self):
        self.listbox.focus_set()
        if self.playing:
            self.playing = False
            self.savedvolume = self.p.audio_get_volume()
            self.p.stop()
            self.instance = vlc.Instance()
            self.p = self.instance.media_player_new()
            if self.showonstop:
                self.Show()
            self.UpdateLabels()
        else:
            self.playing = True
            song = self.listbox.get(ACTIVE)
            for entry in self.songlist:
                if song == entry['display']:
                    path = entry['path'] + '/' + entry['filename']
                    path = path.replace('\\','\\\\').decode('unicode-escape') # allows unicode chars
                    self.Media = self.instance.media_new(path)
                    self.p.set_media(self.Media)
                    self.playingname = entry['display']
                    self.p.play()
                    self.root.after(350, self.DeviceSet) # hackery for some reason...
                    break
            if self.hideonplay:
                self.Hide()
            if self.searching:
                self.HideSearch()
            self.UpdateLabels(firstplay=True)

    def DeviceSet(self):
        self.p.audio_output_device_set(None, self.audiodevice)
        self.p.pause()
        self.root.after(10)
        self.p.pause()

    def ShowHide(self):
        if self.visible:
            self.Hide()
        else:
            self.Show()

    def Hide(self):
        self.root.withdraw()
        self.visible = False

    def Show(self):
        self.root.update()
        self.root.deiconify()
        self.visible = True

    def OnClick(self, event):
        w = event.widget
        try:
            index = int(w.curselection()[0])
        except IndexError:
            return
        self.selected = index
        self.listbox.activate(index)

    def UpdateLabels(self, firstplay=False):
        if self.playing:
            playing = 'Playing'
            songname = self.playingname
        else:
            playing = 'Stopped'
            songname = '-'

        if firstplay:
            vol = str(self.savedvolume/2)
        else:
            vol = str(self.p.audio_get_volume()/2)
        volume = ' | Volume: ' + vol

        self.status.set(playing + volume)
        self.songname.set(songname)

    def UpdateTimer(self):
        if self.playing:
            curtime = str(self.p.get_time()/1000)
            tottime = str(self.p.get_length()/1000)
            self.timer.set(curtime + '/' + tottime)
        else:
            self.timer.set('-')
        self.root.after(1000, self.UpdateTimer)

    def PopulateListBox(self):
        self.listbox.delete(0, END)
        for entry in self.songlist:
            self.listbox.insert(END, entry['display'])

    def SearchListBox(self, searchstring):
        searchresults = [entry for entry in self.songlist if searchstring in entry['display'].lower()]
        self.listbox.delete(0, END)
        for entry in searchresults:
            self.listbox.insert(END, entry['display'])
        self.listbox.selection_set(0)
        self.listbox.activate(0)
        self.listbox.see(0)
        self.searchresult = self.listbox.get(ACTIVE)
        print self.searchresult

    def Reset(self):
        self.p.stop()
        self.playing = False
        self.songlist = populatesongs()
        self.PopulateListBox()
        self.SetSelection()
        self.UpdateLabels()
        self.Show()


root = Tk()
root.resizable(width=False, height=False)
root.lift()
root.attributes('-topmost', True)
root.iconbitmap('favicon.ico')
root.geometry('%sx%s+%s+%s' % (horsize, versize, horoffset, veroffset))

if fixed:
    root.overrideredirect(True)
WinDJ = WinDJ(root, hideonplay, showonstop, scrolljump, audiodevice, c_over_s, controls)

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

    # poll the keyboard hook
    pipeloop = threading.Thread(target=startPipeLoop)
    pipeloop.daemon = True
    pipeloop.start()

    # hook the keyboard
    obj = pyHook.HookManager()
    obj.KeyDown = pyHookKeypress
    obj.HookKeyboard()

    # main gui loop
    root.mainloop()
