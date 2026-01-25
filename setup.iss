[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}AppName=Devalaya Billing System
AppVersion=1.6.0
AppPublisher=TheAgg
AppPublisherURL=https://github.com/theagg-18/devalaya-pro
AppSupportURL=https://github.com/theagg-18/devalaya-pro
AppUpdatesURL=https://github.com/theagg-18/devalaya-pro
DefaultDirName={autopf}\Devalaya Billing System
DisableProgramGroupPage=yes
; "ArchitecturesInstallIn64BitMode=x64" requests that the install be
; done in "64-bit mode" on x64, meaning it should use the native
; 64-bit Program Files directory and the 64-bit view of the registry.
ArchitecturesInstallIn64BitMode=x64
LicenseFile=LICENSE
; PrivilegesRequired=lowest ensures installation to User Profile (AppData)
; This avoids permission issues when writing to temple.db next to the exe.
PrivilegesRequired=lowest
OutputDir=Output
OutputBaseFilename=DevalayaBillingSetup_v1.6.0
SetupIconFile=static\favicon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; The main executable
Source: "dist\DevalayaBilling.exe"; DestDir: "{app}"; Flags: ignoreversion
; NOTE: We do NOT include temple.db here because we don't want to overwrite user data.
; The application creates it automatically if missing.
; We can include a default config if really needed, but generally unnecessary.
; Copy LICENSE
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Devalaya Billing System"; Filename: "{app}\DevalayaBilling.exe"
Name: "{autodesktop}\Devalaya Billing System"; Filename: "{app}\DevalayaBilling.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\DevalayaBilling.exe"; Description: "{cm:LaunchProgram,Devalaya Billing System}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up backups and logs, but maybe ask first?
; Standard uninstaller removes files it installed.
; Generated files (temple.db, backups) are usually left behind unless specified.
; We will leave them to be safe.
; Type: files; Name: "{app}\temple.db" 
; Type: filesandordirs; Name: "{app}\backups"
