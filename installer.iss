; Inno Setup 6 script for CLYDEX
; Requires both PyInstaller builds to be present under dist\ before running.

[Setup]
AppName=CLYDEX
AppVersion=1.0
AppPublisher=CLYDEX
AppPublisherURL=https://github.com/creolive-digital/CLYDEX
DefaultDirName={autopf}\CLYDEX
DefaultGroupName=CLYDEX
OutputBaseFilename=CLYDEX_Setup
OutputDir=installer_out
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\widget\clydex_widget.exe
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
SetupIconFile=
InfoAfterFile=INSTALLER_NOTES.txt

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut for the CLYDEX widget"; \
  GroupDescription: "Additional icons:"

[Files]
; Widget — full dist folder goes into widget\
Source: "dist\clydex_widget\*"; DestDir: "{app}\widget"; Flags: ignoreversion recursesubdirs createallsubdirs

; Voice agent — full dist folder goes into agent\
Source: "dist\clydex_voice_agent\*"; DestDir: "{app}\agent"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\CLYDEX Widget";       Filename: "{app}\widget\clydex_widget.exe"
Name: "{group}\CLYDEX Voice Agent";  Filename: "{app}\agent\clydex_voice_agent.exe"
Name: "{group}\Uninstall CLYDEX";    Filename: "{uninstallexe}"
Name: "{autodesktop}\CLYDEX Widget"; Filename: "{app}\widget\clydex_widget.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\widget\clydex_widget.exe"; \
  Description: "Launch CLYDEX Widget now"; \
  Flags: nowait postinstall skipifsilent
