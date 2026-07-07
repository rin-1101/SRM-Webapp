(for %p in (5000 5001 5002 8050 443) do @netstat -ano | findstr ":%p" | findstr "LISTENING")

wmic process where (ProcessId=1234) get ParentProcessId
wmic process where (ProcessId=1234) get CommandLine
for /L %p in (5000,1,5002) do @for /f "tokens=5" %a in ('netstat -ano ^| findstr :%p') do @if not "%a"=="0" taskkill /F /PID %a

@REM import requests
@REM response = requests.get(f"https://srm.okadamanila.com:80/test", timeout=3,verify=False)
@REM response.json()nssm 

(for %p in (443) do @netstat -ano | findstr ":%p" | findstr "LISTENING")
