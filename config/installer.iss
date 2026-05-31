#define AppName "Koyfin Scraper"
#define AppVersion "1.0"
#define AppPublisher "Min Wai"
#define AppExeName "KoyfinScraper.exe"

[Setup]
AppId={{7D16DD91-13EB-4BF2-A6FC-1DA3ED1161B9}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
OutputDir=..\dist\installer
OutputBaseFilename=KoyfinScraperSetup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
; The built app directory from PyInstaller
Source: "..\dist\KoyfinScraper\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; The data folder (companies.json)
Source: "..\data\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs
; The trust certificate — installed automatically during setup
Source: "..\KoyfinScraper.cer"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
; Automatically import your certificate into Trusted Publishers when installing
; This is the one-time trust step — colleague doesn't need to do it manually
Filename: "certutil.exe"; Parameters: "-addstore TrustedPublisher ""{tmp}\KoyfinScraper.cer"""; \
    Flags: runhidden; StatusMsg: "Configuring security trust..."
; Launch app after install
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
