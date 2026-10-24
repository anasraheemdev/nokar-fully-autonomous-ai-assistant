Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = scriptDir

If fso.FileExists(scriptDir & "\.venv\Scripts\pythonw.exe") Then
    WshShell.Run """" & scriptDir & "\.venv\Scripts\pythonw.exe"" """ & scriptDir & "\main.py""", 0, False
ElseIf fso.FileExists(WshShell.ExpandEnvironmentStrings("%LocalAppData%") & "\Programs\Python\Python312\pythonw.exe") Then
    WshShell.Run """" & WshShell.ExpandEnvironmentStrings("%LocalAppData%") & "\Programs\Python\Python312\pythonw.exe"" """ & scriptDir & "\main.py""", 0, False
Else
    WshShell.Run "pythonw """ & scriptDir & "\main.py""", 0, False
End If
