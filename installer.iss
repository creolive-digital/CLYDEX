; Inno Setup 6 script for CLYDEX
; Requires both PyInstaller builds to be present under dist\ before running.

[Setup]
AppName=CLYDEX
AppVersion=1.0
AppPublisher=CLYDEX
AppPublisherURL=https://github.com/
DefaultDirName={autopf}\CLYDEX
DefaultGroupName=CLYDEX
OutputBaseFilename=CLYDEX_Setup
OutputDir=installer_out
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\clydex_widget.exe
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
SetupIconFile=
InfoAfterFile=INSTALLER_NOTES.txt

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut for the CLYDEX widget"; \
  GroupDescription: "Additional icons:"; Flags: checked

[Files]
; --- Widget (exe + _widget internal folder + studio_ui fonts/assets) ---
Source: "dist\clydex_widget\clydex_widget.exe";   DestDir: "{app}"; Flags: ignoreversion
Source: "dist\clydex_widget\_widget\*";            DestDir: "{app}\_widget";   Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\clydex_widget\studio_ui\*";          DestDir: "{app}\studio_ui"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\clydex_widget\clydex_hologram.png";  DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "dist\clydex_widget\clydex_projection.png"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

; --- Voice agent (exe + _agent internal folder; studio_ui shared from above) ---
Source: "dist\clydex_voice_agent\clydex_voice_agent.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\clydex_voice_agent\_agent\*";               DestDir: "{app}\_agent"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\CLYDEX Widget";       Filename: "{app}\clydex_widget.exe"
Name: "{group}\CLYDEX Voice Agent";  Filename: "{app}\clydex_voice_agent.exe"
Name: "{group}\Uninstall CLYDEX";    Filename: "{uninstallexe}"
Name: "{autodesktop}\CLYDEX Widget"; Filename: "{app}\clydex_widget.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\clydex_widget.exe"; \
  Description: "Launch CLYDEX Widget now"; \
  Flags: nowait postinstall skipifsilent
