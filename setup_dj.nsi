SilentInstall silent
RequestExecutionLevel user
OutFile "WinDJ.exe"
Icon "favicon.ico"

Section
InitPluginsDir
SetOutPath $PLUGINSDIR
File /r "setup_dj\*"
CopyFiles /silent $EXEDIR\config.cfg $PLUGINSDIR\config.cfg
ExecWait $PLUGINSDIR\dj.exe ; Double quotes on the path
SetOutPath $Temp ; SetOutPath locks the directory and we don't want to lock $PluginsDir
SectionEnd
