import subprocess

ports = [5000, 5001, 5002]  # Define ports

processes = []
for port in ports:
    p = subprocess.Popen(["python", "app.py", str(port)])
    processes.append(p)

try:
    for p in processes:
        p.wait()  # Keep processes running
except KeyboardInterrupt:
    for p in processes:
        p.terminate()  # Terminate all processes on exit
