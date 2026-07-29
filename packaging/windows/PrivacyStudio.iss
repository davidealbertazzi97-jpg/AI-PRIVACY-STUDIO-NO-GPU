#define AppName "AI Privacy Studio (No GPU)"
#define AppVersion "1.0.0"
#ifndef SourceRoot
  #error SourceRoot must point to the checked-out repository
#endif
#ifndef OutputRoot
  #define OutputRoot "."
#endif

[Setup]
AppId={{94A1D499-A1B5-4E34-980F-4A6EC2B434CC}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Privacy Studio contributors
DefaultDirName={localappdata}\Programs\AI Privacy Studio
DefaultGroupName=AI Privacy Studio
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir={#OutputRoot}
OutputBaseFilename=AI-Privacy-Studio-Setup-{#AppVersion}-windows-x86_64
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
LicenseFile={#SourceRoot}\LICENSE
InfoBeforeFile={#SourceRoot}\packaging\INSTALLER_NOTICE.en-it.txt
UninstallDisplayName={#AppName}
SetupLogging=yes
CloseApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"

[Files]
Source: "{#SourceRoot}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: ".git\*,.github\*,.venv\*,.tools\*,bin\*,models\*,build\*,dist\*,__pycache__\*,*.pyc,*.log,*.sqlite*,*.pcv"

[Icons]
Name: "{group}\AI Privacy Studio"; Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoLogo -NoProfile -ExecutionPolicy Bypass -File ""{app}\start.ps1"""; WorkingDir: "{app}"
Name: "{userdesktop}\AI Privacy Studio"; Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoLogo -NoProfile -ExecutionPolicy Bypass -File ""{app}\start.ps1"""; WorkingDir: "{app}"; Tasks: desktopicon
Name: "{group}\Uninstall AI Privacy Studio"; Filename: "{uninstallexe}"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut / Crea un collegamento sul desktop"; GroupDescription: "Shortcuts / Collegamenti:"

[Run]
Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoLogo -NoProfile -ExecutionPolicy Bypass -File ""{app}\install.ps1"""; WorkingDir: "{app}"; Description: "Download and install local engines / Scarica e installa i motori locali"; Flags: postinstall skipifsilent waituntilterminated runasoriginaluser
