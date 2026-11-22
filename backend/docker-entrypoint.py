import os
import sys
import time
import subprocess
import config
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

url = make_url(config.DB_URL).set(database=None)

print("Aguardando o banco de dados...", flush=True)

for tentativa in range(60):
    engine = create_engine(url)

    try:
        with engine.connect():
            print("Banco de dados conectado!", flush=True)
        break
    except Exception:
        if tentativa == 59:
            raise
        time.sleep(2)
    finally:
        engine.dispose()

print("Preparando o banco de dados...", flush=True)

subprocess.run(
    [sys.executable, "db/criar_banco.py"],
    check=True
)

print("Iniciando a aplicação...", flush=True)

os.execv(
    sys.executable,
    [sys.executable, "api/api.py"]
)