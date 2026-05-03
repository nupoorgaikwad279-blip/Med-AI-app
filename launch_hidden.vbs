Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "python run_permanently.py", 0, False
WScript.Sleep 2000
WshShell.Run "cmd /c start http://localhost:5000", 0, False
