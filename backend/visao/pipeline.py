
"""Processamento completo de uma análise: vídeo enviado -> modelo -> banco + vídeo anotado.

Passos (para o processamento id_proc):
 1. converte o vídeo enviado para MP4 H.264;
 2. lê TODOS os frames e passa cada um pelo modelo;
 3. pixeliza rostos detectados, desenha as caixas e grava o vídeo anotado;
 4. guarda no banco o frame com rostos pixelizados e as detecções;
 5. grava as métricas e o status final em processamentos.
"""

import logging
import time
from pathlib import Path

import cv2

import config
from db import repositorio as repo
from visao.detector import desenhar
from visao.privacidade import Anonimizador
from visao.video import EscritorVideo, converter_h264, ler_info

log = logging.getLogger(__name__)

LOTE_FRAMES = 10
ATUALIZAR_A_CADA = 15


def _relativo(caminho: Path) -> str:
    return caminho.resolve().relative_to(
        config.STORAGE_DIR.resolve()
    ).as_posix()


def processar(id_proc, detector):
    dados = repo.dados_processamento(id_proc)

    if dados is None:
        log.warning(
            "Processamento %s não existe mais.", id_proc
        )
        return

    id_video = dados["id_video"]
    inicio = time.time()
    escritor = None

    try:
        repo.iniciar_processamento(id_proc, id_video)

        # 1) Converter vídeo para MP4 H.264
        enviado = config.STORAGE_DIR / dados["caminho_arquivo"]
        original = enviado.with_name("original.mp4")

        if enviado != original or not original.is_file():
            converter_h264(enviado, original)

            if enviado != original:
                enviado.unlink(missing_ok=True)

        info = ler_info(original)

        repo.atualizar_video(
            id_video,
            caminho_arquivo=_relativo(original),
            info=info
        )

        # 2) Configurar leitura dos frames
        fps = info["fps"]
        total = info["total_frames"]

        passo = max(
            1,
            round(
                float(
                    dados["intervalo_extracao_segundos"] or 1
                ) * fps
            )
        )

        anotado = (
            config.STORAGE_DIR
            / "processamentos"
            / str(id_proc)
            / "anotado.mp4"
        )

        escritor = EscritorVideo(
            anotado,
            info["largura"],
            info["altura"],
            fps
        )

        # Inicializar detector YuNet uma vez por vídeo
        anonimizador = Anonimizador()

        cap = cv2.VideoCapture(str(original))

        lote, n, total_det, frames_com_placa = [], 0, 0, 0

        try:
            while True:

                ok, frame = cap.read()

                if not ok:
                    break

                n += 1

                # Detectar placas de trânsito com YOLO
                caixas = detector.detectar(frame)

                # Detectar e pixelizar rostos com YuNet
                anonimizador.aplicar(frame)

                # Guardar frame com rostos pixelizados no banco
                if (n - 1) % passo == 0:

                    ok_jpg, jpg = cv2.imencode(
                        ".jpg",
                        frame,
                        [
                            cv2.IMWRITE_JPEG_QUALITY,
                            config.QUALIDADE_JPEG
                        ]
                    )

                    if not ok_jpg:
                        raise RuntimeError(
                            f"Falha ao codificar o frame {n}."
                        )

                    lote.append({
                        "numero": n,
                        "tempo": (n - 1) / fps,
                        "jpeg": jpg.tobytes(),
                        "caixas": caixas
                    })

                    total_det += len(caixas)
                    frames_com_placa += bool(caixas)

                    if len(lote) >= LOTE_FRAMES:

                        repo.salvar_frames(
                            id_video, id_proc, lote
                        )

                        lote = []

                # Gravar vídeo anotado com rostos pixelizados
                escritor.escrever(
                    desenhar(frame, caixas)
                )

                # Atualizar progresso
                if n % ATUALIZAR_A_CADA == 0:

                    repo.atualizar_progresso(
                        id_proc,
                        min(0.99, n / total)
                    )

        finally:
            cap.release()

        if lote:
            repo.salvar_frames(id_video, id_proc, lote)

        if n == 0:
            raise RuntimeError(
                "Nenhum frame foi lido do vídeo."
            )

        escritor.fechar()
        escritor = None

        # Finalizar processamento
        repo.concluir_processamento(
            id_proc,
            caminho_anotado=_relativo(anotado),
            total_deteccoes=total_det,
            frames_com_placa=frames_com_placa
        )

        log.info(
            "Análise %s concluída: %d frames, "
            "%d detecções nos frames guardados, %.1fs",
            id_proc,
            n,
            total_det,
            time.time() - inicio
        )

    except Exception as erro:

        log.exception(
            "Falha no processamento %s", id_proc
        )

        if escritor is not None:
            escritor.abortar()

        repo.falhar_processamento(id_proc, erro)
