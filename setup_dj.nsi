SilentInstall silent
RequestExecutionLevel user
OutFile "WinDJ.exe"

;!include MUI2.nsh
;!define MUI_ICON "favicon.ico"

;!insertmacro MUI_PAGE_WELCOME ; Commenting out this line has no effect on the icon nor UAC elevation
;!insertmacro MUI_PAGE_INSTFILES
;!insertmacro MUI_LANGUAGE English

Section
InitPluginsDir
SetOutPath $PLUGINSDIR
File /r "setup_dj\*"
CopyFiles /silent $EXEDIR\config.cfg $PLUGINSDIR\config.cfg
ExecWait $PLUGINSDIR\dj.exe ; Double quotes on the path
SetOutPath $Temp ; SetOutPath locks the directory and we don't want to lock $PluginsDir
SectionEnd
