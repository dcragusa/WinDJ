# WinDJ
WinDJ is an unobtrusive media player for Windows based on VLC. You can use it for micspam too!

## Features:
- High quality music on any server or game with mic input. No need for server settings like sv_allow_voice_from_file or sv_use_steam_voice!
- Easy setup. Just add a folder with music in, tweak some settings (if you want) and go!
- Minimalist window that you can hide and use while hidden
- Intuitive default control scheme based on the numpad - but completely customisable controls too
- Volume control
- Search function - just type in a few letters and watch your songlist narrow down 
- Scrollable and clickable songlist
- Many program settings can be customised
- Plays damn near every format - no need to convert any of your files
- VAC-safe
- Free and Open Source! 

## Setup
1. Install VLC from [here](https://www.videolan.org/vlc/index.html)

2. Extract the latest zip from the release page [here](https://github.com/dcragusa/WinDJ/releases) to wherever you want

3. Open `config.cfg` and give it a folder with some music in it, like the example

4. Edit the rest of the config file if you wish - further details are in the Config section below

5. Launch WinDJ!
 
If you want to micspam, there are additional steps.

1. Install VB-Audio Virtual Cable, available as donationware from [here](https://www.vb-audio.com/Cable/) (the orange download button)

2. Open WinDJHelper and find the long code for the device called CABLE Input (VB-Audio Virtual Cable). 
 
3. Open `config.cfg`, remove the `;` from in front of the audiodevice setting, and paste your code in there. 
It should look something like `output_device: {0.0.0.00000000}.{9bfca61f-07f6-49b0-9313-35cd914fa71a}`.
 
4. Set VB Cable as the mic input to whatever program you want to micspam for. 
Unfortunately Source games do not allow you to set a mic input and you will therefore need to make VB Cable your default system mic.

5. Make sure you are using either bordered or borderless window for whatever it is you want to micspam in

6. For Source games like TF2, you'll need to paste the following bind into your autoexec file:

        // Micspam toggle
        alias micspamEnable "voice_loopback 1; +voicerecord; unbind v; alias micspamToggle micspamDisable"
        alias micspamDisable "-voicerecord; bind v +voicerecord; voice_loopback 0; alias micspamToggle micspamEnable"
        alias micspamToggle micspamEnable
        bind KP_5 micspamToggle
        
You must have the same key for WinDJ play/stop and the bind (in this case 5 on the keypad).

## Config
Under the `[Folders]` section goes a numbered list of folders that contain the music you want WinDJ to be able to play.
There can be any number of folders in separate places on your PC and they will all be merged into WinDJ's songlist.
There needs to be at least one folder in here (obviously :P).

- `hide_on_play` and `show_on_stop` tell the program how to show and hide itself. 
By default, the program hides itself when playing and shows itself when stopped.
You could change `hide_on_play` to `false` if you wanted WinDJ to stay on top of other windows.
- `hor_size` and `ver_size` are the size of the WinDJ window in pixels.
- `hor_offset` and `ver_offset` are the location of the WinDJ window from the top left of the screen, in pixels.
- `scroll_step` is how many items the `nav_mult_up` and `nav_mult_down` scroll by. 
You can increase this if you have a huge songlist, for example.
- `fixed_position` is whether the WinDJ window is fixed on the screen, or draggable. 
If it fixed it has no title bar and is therefore slightly smaller.
- `controls_captured` is whether WinDJ controls will be captured (invisible to other programs) or not.
If you wish to micspam as in the instructions above, this must be false to allow the game to register the micspam toggle button.
- `output_device` is the device code that WinDJ will output audio to. 
You can comment this out with a `;` if you want WinDJ to output over your default sound output.

## Controls
Most of the controls are self-explanatory. Below are the more complex ones.
- `reset` stops any songs, and refreshes the songlist. 
Helpful if for some reason the ingame miscpam toggle and WinDJ get out of sync.
- `search` opens a search box at the top of the songlist that you can type into. 
You can exit the search by pressing the same button again, or it will exit automatically if you play a song.
