import subprocess
import sys
import os

# Define a porta e o endereço que o Streamlit irá usar. 
# 127.0.0.1 garante que ele abre apenas localmente.
STREAMLIT_COMMAND = [
    sys.executable, 
    "-m", 
    "streamlit", 
    "run", 
    "app.py",
    "--browser.serverAddress", "127.0.0.1", 
    "--server.port", "8501" # Porta fixa para evitar conflitos
]

# A pasta temporária é o local onde o PyInstaller extrai o pacote
# Este é o caminho onde o 'app.py' estará após a execução
if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
    # Garante que o app.py é encontrado no caminho de extração
    STREAMLIT_COMMAND[-3] = os.path.join(application_path, "app.py")

# Executa o Streamlit
subprocess.call(STREAMLIT_COMMAND)import subprocess
import sys
import os

# Define a porta e o endereço que o Streamlit irá usar. 
# 127.0.0.1 garante que ele abre apenas localmente.
STREAMLIT_COMMAND = [
    sys.executable, 
    "-m", 
    "streamlit", 
    "run", 
    "app.py",
    "--browser.serverAddress", "127.0.0.1", 
    "--server.port", "8501" # Porta fixa para evitar conflitos
]

# A pasta temporária é o local onde o PyInstaller extrai o pacote
# Este é o caminho onde o 'app.py' estará após a execução
if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
    # Garante que o app.py é encontrado no caminho de extração
    STREAMLIT_COMMAND[-3] = os.path.join(application_path, "app.py")

# Executa o Streamlit
subprocess.call(STREAMLIT_COMMAND)