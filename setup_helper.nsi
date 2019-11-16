SilentInstall silent
RequestExecutionLevel user
OutFile "WinDJHelper.exe"
Icon "favicon.ico"

Section
InitPluginsDir
SetOutPath $PLUGINSDIR
File /r "setup_helper\*"
ExecWait $PLUGINSDIR\helper.exe ; Double quotes on the path
SetOutPath $Temp ; SetOutPath locks the directory and we don't want to lock $PluginsDir
SectionEnd
