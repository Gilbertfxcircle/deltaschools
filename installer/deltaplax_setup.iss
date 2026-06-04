; Inno Setup script for the Delta Plax Education Suite local installer (section 13).
; Compile with the Inno Setup Compiler (ISCC.exe) after building the EXE with
; PyInstaller. Produces a Windows installer that registers the server as a
; background service and adds a Start Menu entry.

#define AppName "Delta Plax Education Suite"
#define AppVersion "0.1.0"
#define AppPublisher "Delta Plax Technologies"
#define AppExeName "Delta Plax Education Suite Server.exe"

[Setup]
AppId={{C0FFEE00-DE17-4A11-9E55-DELTAPLAX0001}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\DeltaPlax\EducationSuite
DefaultGroupName={#AppName}
OutputDir=output
OutputBaseFilename=DeltaPlaxEducationSuiteSetup
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\.env.example"; DestDir: "{app}"; DestName: ".env"; Flags: onlyifdoesntexist

[Icons]
Name: "{group}\Open Delta Plax Dashboard"; Filename: "http://localhost:3000"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"

[Run]
; Register the bundled server as an auto-start Windows service.
Filename: "{sys}\sc.exe"; \
  Parameters: "create DeltaPlaxSuite binPath= ""{app}\{#AppExeName}"" start= auto DisplayName= ""{#AppName}"""; \
  Flags: runhidden
Filename: "{sys}\sc.exe"; Parameters: "start DeltaPlaxSuite"; Flags: runhidden

[UninstallRun]
Filename: "{sys}\sc.exe"; Parameters: "stop DeltaPlaxSuite"; Flags: runhidden
Filename: "{sys}\sc.exe"; Parameters: "delete DeltaPlaxSuite"; Flags: runhidden
