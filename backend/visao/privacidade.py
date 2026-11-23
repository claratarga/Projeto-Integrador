
from pathlib import Path

import cv2
from ultralytics import YOLO


class Anonimizador:

    def __init__(self):

        pasta_modelos = (
            Path(__file__).resolve().parents[1] / "modelos"
        )

        # Modelo de detecção de rostos
        self.detector_rostos = cv2.FaceDetectorYN.create(
            str(pasta_modelos / "detector_rostos.onnx"),
            "",
            (640, 640),
            0.55,
            0.3,
            5000
        )

        # Modelo de detecção de placas veiculares
        self.detector_placas = YOLO(
            str(
                pasta_modelos
                / "detector_placas_openvino_model"
            ),
            task="detect"
        )

    @staticmethod
    def _pixelizar(frame, x, y, w, h, margem):

        altura, largura = frame.shape[:2]

        margem_x = int(w * margem)
        margem_y = int(h * margem)

        x1 = max(0, int(x - margem_x))
        y1 = max(0, int(y - margem_y))

        x2 = min(largura, int(x + w + margem_x))
        y2 = min(altura, int(y + h + margem_y))

        if x2 <= x1 or y2 <= y1:
            return

        regiao = frame[y1:y2, x1:x2]

        pequeno = cv2.resize(
            regiao,
            (3, 3),
            interpolation=cv2.INTER_AREA
        )

        frame[y1:y2, x1:x2] = cv2.resize(
            pequeno,
            (x2 - x1, y2 - y1),
            interpolation=cv2.INTER_NEAREST
        )

    def detectar_rostos(self, frame):

        altura, largura = frame.shape[:2]

        escala = min(1.0, 960 / largura)

        nova_largura = round(largura * escala)
        nova_altura = round(altura * escala)

        imagem = cv2.resize(
            frame,
            (nova_largura, nova_altura)
        )

        self.detector_rostos.setInputSize(
            (nova_largura, nova_altura)
        )

        _, rostos = self.detector_rostos.detect(imagem)

        regioes = []

        if rostos is not None:

            for rosto in rostos:

                x, y, w, h = [
                    int(valor / escala)
                    for valor in rosto[:4]
                ]

                regioes.append((x, y, w, h))

        return regioes

    def detectar_placas(self, frame):

        resultado = self.detector_placas.predict(
            source=frame,
            imgsz=640,
            conf=0.25,
            device="cpu",
            verbose=False
        )[0]

        regioes = []

        if resultado.boxes is not None:

            for caixa in resultado.boxes.xyxy.cpu().numpy():

                x1, y1, x2, y2 = map(int, caixa)

                regioes.append((
                    x1,
                    y1,
                    x2 - x1,
                    y2 - y1
                ))

        return regioes

    def aplicar(self, frame):

        # Detectar antes de modificar a imagem
        rostos = self.detectar_rostos(frame)
        placas = self.detectar_placas(frame)

        # Pixelizar rostos
        for x, y, w, h in rostos:

            self._pixelizar(
                frame,
                x, y, w, h,
                margem=0.30
            )

        # Pixelizar placas veiculares
        for x, y, w, h in placas:

            self._pixelizar(
                frame,
                x, y, w, h,
                margem=0.20
            )

        return frame
