Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Get current directory
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = currentDir

' Function to run hidden command
Function RunHidden(cmd)
    WshShell.Run cmd, 0, True
End Function

' Check if first launch (no venv)
venvPath = currentDir & "\venv"
If Not fso.FolderExists(venvPath) Then
    ' Run setup with progress visibly
    setupBat = currentDir & "\setup_with_progress.bat"
    If fso.FileExists(setupBat) Then
        WshShell.Run """" & setupBat & """", 1, True
    Else
        ' Fallback: original silent install
        On Error Resume Next
        WshShell.Run "python --version", 0, True
        If Err.Number <> 0 Then
            WshShell.Run "winget install Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements", 0, True
            WshShell.Run "set PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%", 0, True
            WScript.Sleep 5000
        End If
        On Error Goto 0
        If Not fso.FolderExists(venvPath) Then
            WshShell.Run "python -m venv venv", 0, True
        End If
        pip = venvPath & "\Scripts\pip.exe"
        If fso.FileExists(pip) Then
            WshShell.Run """" & pip & """ install -r requirements.txt", 0, True
        End If
    End If
End If

' Check config to decide what to run
configPath = currentDir & "\config\config.json"
runScript = "launcher.py"
port = "8501"

If fso.FileExists(configPath) Then
    Set configFile = fso.OpenTextFile(configPath, 1)
    configContent = configFile.ReadAll
    configFile.Close
    ' Check if google_sheets is enabled and sheet_id is filled
    If InStr(configContent, """enabled"": true") > 0 And InStr(configContent, """sheet_id""") > 0 And InStr(configContent, "1wMDIgZgrQt") > 0 Then
        runScript = "app.py"
        port = "8502"
    End If
End If

' Run Streamlit hidden with pythonw
pythonw = venvPath & "\Scripts\pythonw.exe"
If Not fso.FileExists(pythonw) Then
    pythonw = "pythonw.exe"
End If

' Kill existing Streamlit processes to avoid duplicate windows
WshShell.Run "taskkill /f /im streamlit.exe >nul 2>&1", 0, True

cmd = """" & pythonw & """ -m streamlit run " & runScript & " --server.port " & port & " --server.headless true --server.address 0.0.0.0"
WshShell.Run cmd, 0, False

' Wait and open browser (only one window)
WScript.Sleep 5000
If runScript = "app.py" Then
    WshShell.Run "http://localhost:" & port, 1, False
Else
    WshShell.Run "http://localhost:" & port, 1, False
End If
