import subprocess, sys, pathlib
root=pathlib.Path(__file__).resolve().parent
subprocess.run([sys.executable,'-m','py_compile',str(root/'server.py')],check=True)
print('Python syntax PASS')
