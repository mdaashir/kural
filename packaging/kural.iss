; Unsigned, offline, per-user installation of the verified PyInstaller bundle.
#ifndef AppVersion
  #error AppVersion is required
#endif
[Setup]
AppId={param:AppId|Kural-A5928891-970C-4482-A991-365DA5625B38}
UsePreviousLanguage=no
AppName=Kural
AppVersion={#AppVersion}
DefaultDirName={localappdata}\Programs\Kural
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist
OutputBaseFilename=kural-windows-x64-setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
UninstallDisplayIcon={app}\kural.exe
CreateUninstallRegKey=yes

[Files]
Source: "..\dist\kural\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userprograms}\Kural"; Filename: "{app}\kural.exe"; IconFilename: "{app}\kural.exe"
Name: "{autodesktop}\Kural"; Filename: "{app}\kural.exe"; IconFilename: "{app}\kural.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: checkedonce
