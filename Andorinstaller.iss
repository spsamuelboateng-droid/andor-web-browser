[Setup]
AppName=Andor
AppVersion=1.0
DefaultDirName={pf}\Andor
DefaultGroupName=Andor
OutputBaseFilename=AndorSetup
SetupIconFile=browser.ico
UninstallDisplayIcon={app}\browser.exe
Compression=lzma
SolidCompression=yes

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; Flags: unchecked

[Files]
Source: "dist\Andor.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "browser.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Andor"; Filename: "{app}\Andor.exe"
Name: "{userdesktop}\Andor"; Filename: "{app}\Andor.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\browser.exe"; Description: "Launch Andor now"; Flags: nowait postinstall skipifsilent


