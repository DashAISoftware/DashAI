; Installer for DashAI (Windows). Based on PyInstaller one-dir portable executable
; ---------------------------------------------
; Command to generate the executable:
; pyinstaller -D -n dashAI-launcher-cpu --clean --add-data "DashAI/front/build;DashAI/front/build" --add-data "%CONDA_PREFIX%\Lib\site-packages\transformers;transformers" --add-binary "%CONDA_PREFIX%\Lib\site-packages\llama_cpp\lib\*;llama_cpp/lib" --additional-hooks-dir=hooks DashAI/__main__.py
[Setup]
AppName=dashAI
AppVersion=0.9.3
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
