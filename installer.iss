#define MyAppName "Web2APK"
#define MyAppVersion "1.0.1"
#define MyAppPublisher "Alex Godly"
#define MyAppExeName "Web2APK.exe"
[Setup]
AppId={{6B2C4DBB-79F0-4F50-B2A9-8DFE74C513A1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\Web2APK
DefaultGroupName=Web2APK
DisableProgramGroupPage=yes
OutputDir=installer
OutputBaseFilename=Web2APK-Setup-v1.0.1
SetupIconFile=web2apk.ico
UninstallDisplayIcon={app}\Web2APK.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
[Files]
Source: "dist\Web2APK.exe"; DestDir: "{app}"; Flags: ignoreversion
[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked
[Icons]
Name: "{autoprograms}\Web2APK"; Filename: "{app}\Web2APK.exe"
Name: "{autodesktop}\Web2APK"; Filename: "{app}\Web2APK.exe"; Tasks: desktopicon
[Run]
Filename: "{app}\Web2APK.exe"; Description: "Launch Web2APK"; Flags: nowait postinstall skipifsilent
