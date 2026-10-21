; Installer for DashAI (Windows). Based on PyInstaller one-dir portable executable
; ---------------------------------------------
; Command to generate the executable:
; pyinstaller -D -n dashAI-launcher-cpu --clean --add-data "DashAI/front/build;DashAI/front/build" --add-data "%CONDA_PREFIX%\Lib\site-packages\transformers;transformers" --add-binary "%CONDA_PREFIX%\Lib\site-packages\llama_cpp\lib\*;llama_cpp/lib" --additional-hooks-dir=hooks DashAI/__main__.py

; The release workflow passes the version from pyproject.toml with
; ISCC /DAppVersion=<version>. The fallback only applies to local builds.
#ifndef AppVersion
  #define AppVersion "0.0.0-dev"
#endif

[Setup]
; Inno Setup recognises a previous install by AppId, so a new installer
; upgrades in place only while this value stays the same. Releases built
; without an explicit AppId used the AppName as their id, so it must stay
; "dashAI" or existing installs end up duplicated.
AppId=dashAI
AppName=dashAI
AppVersion={#AppVersion}
AppPublisher=DashAI Software
AppPublisherURL=https://dash-ai.com
DefaultDirName={pf}\dashAI
DefaultGroupName=dashAI
OutputDir=.
OutputBaseFilename=dashAI-Installer
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
SetupIconFile=dashAI.ico

[InstallDelete]
; Installing over a previous version does not remove its files, so the old
; *.dist-info folders would stay next to the new ones and importlib.metadata
; (and pip, for plugins) could read the old version. User data and plugins
; live in %USERPROFILE%\.DashAI, never in {app}.
Type: filesandordirs; Name: "{app}\_internal"

[Files]
; Copy all files from PyInstaller onedir output
Source: "..\dist\dashAI-launcher-cpu\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\dashAI"; Filename: "{app}\dashAI-launcher-cpu.exe"
Name: "{commondesktop}\dashAI"; Filename: "{app}\dashAI-launcher-cpu.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; Flags: unchecked

[Run]
Filename: "{app}\dashAI-launcher-cpu.exe"; Description: "Launch dashAI"; Flags: postinstall nowait skipifsilent
; The in-app updater runs this installer silently with /RELAUNCH=1, so the
; entry above is skipped. Start dashAI again in that case only: an admin
; deploying silently to many machines does not want it to open. It runs as
; the user who started the update, not as the elevated installer.
Filename: "{app}\dashAI-launcher-cpu.exe"; Flags: nowait runasoriginaluser; Check: RelaunchRequested

[Code]
function RelaunchRequested: Boolean;
begin
  Result := ExpandConstant('{param:RELAUNCH|0}') = '1';
end;
