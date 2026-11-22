"""Worker responsável pelo processamento das análises com YOLO26."""

import logging
import time

import config
from db import repositorio as repo
from visao.detector import DetectorPlacas
from visao import pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

log = logging.getLogger(__name__)


def iniciar():
    config.STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    log.info("Aguardando conexão com o banco de dados...")

    while True:
        try:
            repo.verificar_conexao()
            break
        except Exception:
            log.warning("Banco indisponível. Tentando novamente em 5 segundos.")
            time.sleep(5)

    log.info("Banco conectado!")

    repo.redefinir_processamentos_interrompidos()

    log.info("Carregando modelo YOLO26...")

    detector = DetectorPlacas(
        config.MODELO_PESOS,
        config.DISPOSITIVO
    )

    log.info("Modelo carregado: %s", detector.versao)

    while True:
        id_proc = repo.proximo_processamento_pendente()

        if id_proc is None:
            time.sleep(3)
            continue

        log.info("Iniciando processamento %s", id_proc)

        try:
            pipeline.processar(id_proc, detector)
        except Exception:
            log.exception("Erro no processamento %s", id_proc)


if __name__ == "__main__":
    iniciar()
