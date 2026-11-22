
# 🚦 Monitoramento de Vias Públicas de Londrina

![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)

Sistema que recebe vídeos gravados no trânsito de Londrina, detecta **placas de trânsito** com visão computacional (YOLO26) e realiza a **anonimização de rostos e placas veiculares**, preservando a privacidade das pessoas presentes nas gravações.

Permite consultar o vídeo processado, comparar frames sem rotulação com suas versões rotuladas e revisar as detecções da inteligência artificial.

Projeto Integrador de Visão Computacional — Universidade Tecnológica Federal do Paraná (UTFPR), campus Londrina, sob orientação do professor Danilo.

---

## 📋 Sumário

- [Como funciona](#-como-funciona)
- [Anonimização de rostos e placas veiculares](#-anonimização-de-rostos-e-placas-veiculares)
- [Treinamento e avaliação do modelo](#-treinamento-e-avaliação-do-modelo)
- [Documentação](#-documentação)
- [Estrutura do repositório](#-estrutura-do-repositório)
- [Como executar (Windows)](#-como-executar-windows)
- [Usando o sistema](#-usando-o-sistema)
- [Privacidade e limitações](#-privacidade-e-limitações)
- [Problemas comuns](#-problemas-comuns)
- [Tecnologias](#-tecnologias)
- [Equipe](#-equipe)
- [Como contribuir](#-como-contribuir)

---

## 🔄 Como funciona

```mermaid
flowchart LR
    U(["👤 Usuário"]) --> F["🖥️ Front-end"]
    F -- "HTTP / JSON" --> A["🔌 API Flask"]
    A --> W["⚙️ Worker de processamento"]

    W --> M["YOLO26n - Sinalização"]
    W --> R["YuNet - Rostos"]
    W --> P["YOLO26n + OpenVINO - Placas veiculares"]

    M --> V["Processamento OpenCV"]
    R --> V
    P --> V

    V --> S[("💾 Vídeos processados")]
    V --> D[("🐬 MySQL")]
    A -- SQL --> D
    A --> S
```

1. O usuário envia um vídeo (10–40 s) com o **local**, a **data** e o **horário** da gravação.
2. A API cadastra o vídeo no banco e o coloca na fila de processamento.
3. O worker realiza a leitura dos frames do vídeo.
4. O modelo YOLO26 identifica as placas de trânsito.
5. O YuNet detecta os rostos presentes nas imagens.
6. Um segundo modelo YOLO26n, exportado para OpenVINO, detecta as placas veiculares.
7. O OpenCV aplica a pixelização nas regiões de rostos e placas veiculares detectadas.
8. O sistema gera o **vídeo anotado e anonimizado** e armazena **1 frame por segundo** para consulta, juntamente com suas detecções.
9. O front-end mostra o progresso e, ao terminar, disponibiliza a análise, a consulta de frames e a revisão das detecções.

---

## 🔒 Anonimização de rostos e placas veiculares

A funcionalidade de anonimização foi desenvolvida para reduzir a exposição de informações pessoais presentes nos vídeos de trânsito.

O processamento ocorre automaticamente durante a análise do vídeo, sem necessidade de intervenção manual.

### Detecção de rostos

A detecção de rostos utiliza o modelo **YuNet**, disponibilizado pelo OpenCV Zoo.

Características:

- Modelo pré-treinado.
- Arquitetura leve.
- Execução em CPU.
- Formato ONNX.
- Não necessita de treinamento adicional.

Arquivo utilizado:

```text
backend/modelos/detector_rostos.onnx
```

Fonte: [OpenCV Zoo — YuNet](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet).

### Detecção de placas veiculares

A identificação de placas veiculares utiliza um modelo **YOLO26n**, treinado especificamente para essa finalidade.

O modelo é independente do detector de placas de trânsito, preservando o funcionamento da sinalização original.

Características:

- Treinamento com imagens de placas veiculares brasileiras.
- Uma classe de detecção: `plate`.
- Resolução de entrada de 640 × 640 pixels.
- Exportação para OpenVINO.
- Execução otimizada em CPU.

Arquivos utilizados:

```text
backend/modelos/detector_placas.pt
backend/modelos/detector_placas_openvino_model/
```

### Pixelização

Após identificar os rostos e as placas veiculares, o OpenCV realiza a pixelização das regiões detectadas.

Configuração utilizada:

| Parâmetro | Valor |
|---|---|
| Confiança mínima — rostos | 55% |
| Confiança mínima — placas veiculares | 25% |
| Margem adicional — rostos | 30% |
| Margem adicional — placas veiculares | 20% |
| Resolução da pixelização | 3 × 3 |
| Dispositivo de processamento | CPU |

A pixelização é aplicada em todos os frames processados, mantendo as sinalizações de trânsito disponíveis para análise.

### Otimização com OpenVINO

O modelo de placas veiculares foi exportado para o formato OpenVINO, buscando reduzir o custo computacional da inferência em processadores Intel.

Essa abordagem permite executar a funcionalidade sem depender de uma GPU dedicada.

Fonte: [Documentação Ultralytics — OpenVINO](https://docs.ultralytics.com/integrations/openvino/).

---

## 📊 Treinamento e avaliação do modelo

### Dataset

O treinamento do detector de placas veiculares utilizou o dataset público **Brazil Plates Detector — versão 2**, disponibilizado pelo Roboflow Universe.

| Conjunto | Imagens |
|---|---:|
| Treinamento | 1.207 |
| Validação | 62 |
| Teste | 177 |
| **Total** | **1.446** |

- Classe: `plate`.
- Licença do dataset: CC BY 4.0.
- Plataforma: Roboflow Universe.

Fonte: [Brazil Plates Detector v2](https://universe.roboflow.com/brazilplatedetector/brazil-plates-detector/dataset/2).

### Configurações do treinamento

| Configuração | Valor |
|---|---|
| Modelo | YOLO26n |
| Plataforma | Google Colab |
| GPU | NVIDIA Tesla T4 |
| Épocas configuradas | 100 |
| Épocas realizadas | 92 |
| Melhor época | 72 |
| Batch size | 16 |
| Resolução | 640 × 640 |
| Otimizador | AdamW |
| Patience | 20 |
| Tempo de treinamento | Aproximadamente 34 minutos |

O treinamento foi encerrado automaticamente pelo mecanismo de Early Stopping após 20 épocas sem melhoria no desempenho.

### Resultados no conjunto de teste

A avaliação foi realizada nas 177 imagens reservadas para teste.

| Métrica | Resultado |
|---|---:|
| Precisão | 99,40% |
| Recall | 100% |
| mAP50 | 99,49% |
| mAP50-95 | 90,53% |

Os resultados demonstram um bom desempenho no conjunto de teste utilizado.

Entretanto, essas métricas não garantem a identificação de todas as placas em condições reais de trânsito.

### Exportação do modelo

Após o treinamento e a avaliação, o melhor modelo (`best.pt`) foi exportado para OpenVINO.

| Informação | Resultado |
|---|---|
| Formato | OpenVINO |
| Tamanho | 9,5 MB |
| Tempo de exportação | 8 segundos |
| Resolução | 640 × 640 |
| Dispositivo | CPU |

O modelo original no formato `.pt` também foi preservado para avaliações futuras e possíveis alterações.

---

## 📚 Documentação

| Documento | Conteúdo |
|---|---|
| [🗺️ Arquitetura visual](docs/01_ARQUITETURA_VISUAL.md) | Como as partes se encaixam, com diagramas — **comece por aqui** |
| [▶️ Manual de execução](docs/02_MANUAL_DE_EXECUCAO.md) | Passo a passo completo para rodar na sua máquina e usar a página |
| [🐬 Banco de dados](docs/03_BANCO_DE_DADOS.md) | Tabelas, relacionamentos e operações no banco |
| [🔌 API](docs/04_API.md) | Rotas, formatos JSON, modelos e pipeline |
| [🖥️ Front-end](docs/05_FRONTEND.md) | As telas e como conversam com a API |

---

## 📁 Estrutura do repositório

```text
├── frontend/                         # Interface web
├── backend/
│   ├── api/                          # API Flask
│   ├── db/                           # Conexão MySQL e consultas
│   ├── visao/
│   │   ├── detector.py              # Detecção de sinalizações
│   │   ├── pipeline.py              # Processamento dos vídeos
│   │   └── privacidade.py           # Anonimização de rostos e placas
│   ├── modelos/
│   │   ├── detector_v1.pt           # Modelo de sinalizações
│   │   ├── detector_rostos.onnx     # Modelo YuNet
│   │   ├── detector_placas.pt       # Modelo veicular original
│   │   └── detector_placas_openvino_model/
│   │       ├── best.xml             # Estrutura do modelo
│   │       ├── best.bin             # Pesos do modelo
│   │       └── metadata.yaml        # Metadados
│   ├── storage/                     # Vídeos enviados e processados
│   ├── worker.py                    # Worker de processamento
│   ├── requirements-backend.txt
│   ├── requirements-processamento.txt
│   ├── config.py
│   └── .env.example
├── database/
│   ├── migracoes/                   # Scripts de migração
│   └── exemplos/                    # Consultas e revisões
├── notebooks/                       # Treinamentos
├── docs/                            # Documentação
├── compose.yaml
└── README.md
```

---

## 🚀 Como executar (Windows)

O sistema pode ser executado localmente utilizando MySQL, API Flask, worker de processamento e front-end.

### Pré-requisitos

- [Python 3.10 ou mais recente](https://www.python.org/downloads/) — marque a opção *Add Python to PATH*.
- [MySQL Server 8.4 LTS](https://dev.mysql.com/downloads/mysql/).
- Git.
- Visual Studio Code (opcional).

Não é necessário possuir uma GPU dedicada nem instalar o FFmpeg manualmente.

### 1. Clonar e criar o ambiente Python

```bash
git clone https://github.com/libinayantonini-sketch/Integrative-Project-1.git
```

```bash
cd Integrative-Project-1
```

```bash
python -m venv venv
```

```cmd
venv\Scripts\activate
```

Instale as dependências da API:

```bash
pip install -r backend/requirements-backend.txt
```

Instale as dependências do processamento:

```bash
pip install -r backend/requirements-processamento.txt
```

A primeira instalação baixa o PyTorch e outras bibliotecas, podendo demorar alguns minutos.

No Linux/macOS, utilize `source venv/bin/activate` para ativar o ambiente virtual.

### 2. Verificar os modelos

Antes de executar o sistema, confira se os seguintes arquivos estão presentes:

```text
backend/modelos/detector_v1.pt
backend/modelos/detector_rostos.onnx
backend/modelos/detector_placas.pt
backend/modelos/detector_placas_openvino_model/best.xml
backend/modelos/detector_placas_openvino_model/best.bin
backend/modelos/detector_placas_openvino_model/metadata.yaml
```

Os arquivos internos da pasta OpenVINO devem permanecer juntos.

### 3. Configurar o ambiente

Copie `backend/.env.example` para `backend/.env`:

```cmd
copy backend\.env.example backend\.env
```

Configure a conexão com o MySQL:

```env
DB_URL=mysql+pymysql://root:SUA_SENHA@localhost:3306/projeto_sinalizacoes
```

Altere o usuário, senha e nome do banco conforme sua instalação.

### 4. Criar o banco de dados

Com o MySQL ligado, execute:

```bash
python backend/db/criar_banco.py
```

Essa etapa deve ser realizada na primeira configuração.

### 5. Iniciar a API — Terminal 1

Com o ambiente virtual ativado:

```bash
python backend/api/api.py
```

Endereço da API:

```text
http://127.0.0.1:8000
```

### 6. Iniciar o worker — Terminal 2

Abra outro terminal e ative o ambiente virtual:

```cmd
venv\Scripts\activate
```

Execute:

```bash
python backend/worker.py
```

O worker será responsável por:

- Processar os vídeos enviados.
- Detectar placas de trânsito.
- Detectar rostos.
- Detectar placas veiculares.
- Aplicar a pixelização.
- Gerar os vídeos processados.
- Registrar as informações no banco de dados.

### 7. Iniciar o front-end — Terminal 3

Abra outro terminal e execute:

```bash
python -m http.server 5500 --directory frontend
```

Acesse:

```text
http://127.0.0.1:5500
```

Também é possível utilizar a extensão Live Server do VS Code.

Mantenha os três terminais abertos durante a utilização do sistema.

---

## 🖥️ Usando o sistema

| Tela | O que faz |
|---|---|
| **Vídeos → Nova análise** | Envia o vídeo com local, data, horário e observações |
| **Análises** | Lista as análises com busca e filtros |
| **Detalhe da análise** | Exibe o vídeo processado, com sinalizações rotuladas e regiões detectadas anonimizadas |
| **Consulta de frames** | Permite consultar frames por número, tempo ou miniatura |
| **Revisão de detecções** | Permite confirmar, rejeitar ou corrigir as detecções |
| **Visão geral / Relatórios** | Apresenta totais, gráficos, detecções por classe e exportação CSV |

A extração de frames ocorre a cada segundo, conforme a configuração `INTERVALO_EXTRACAO_S`.

Caso o frame solicitado não esteja armazenado, o sistema apresenta o mais próximo.

A anonimização é realizada automaticamente durante o processamento, sem necessidade de configuração adicional pelo usuário.

---

## 🛡️ Privacidade e limitações

A identificação automática de rostos e placas veiculares busca reduzir a exposição de informações pessoais.

Entretanto, algumas condições podem dificultar a detecção:

- Objetos muito distantes.
- Baixa iluminação.
- Imagens com baixa resolução.
- Movimentos rápidos.
- Rostos parcialmente encobertos.
- Placas veiculares sujas ou parcialmente ocultas.

O Recall de 100% obtido no conjunto de teste não garante a anonimização integral de todos os vídeos reais.

O vídeo original enviado ao sistema permanece armazenado sem pixelização. Portanto, seu acesso deve ser restrito a pessoas autorizadas.

Recomenda-se revisar os vídeos processados antes de sua divulgação pública.

A implementação contribui para a proteção da privacidade, mas não garante, isoladamente, conformidade integral com a LGPD.

---

## 🧯 Problemas comuns

| Mensagem ou problema | Solução |
|---|---|
| `Não foi possível conectar ao MySQL` | Inicie o serviço MySQL e confira as credenciais em `backend/.env` |
| `Unknown database 'projeto_sinalizacoes'` | Execute `python backend/db/criar_banco.py` |
| `Modelo não encontrado` | Confira os arquivos em `backend/modelos/` |
| `ModuleNotFoundError` | Ative o ambiente virtual e instale as dependências |
| `FaceDetectorYN` não encontrado | Confira a versão do OpenCV instalada |
| Erro ao carregar o modelo OpenVINO | Confira a instalação do OpenVINO e os arquivos `.xml` e `.bin` |
| Front-end mostra **Desconectada** | Verifique se a API está rodando |
| Vídeo permanece na fila | Verifique se o worker está em execução |
| Processamento lento | O tempo depende da duração, resolução, FPS e capacidade do processador |

### Dependências do processamento

O arquivo `backend/requirements-processamento.txt` contém:

```txt
python-dotenv>=1.0
SQLAlchemy>=2.0
PyMySQL>=1.1
cryptography>=42
imageio-ffmpeg>=0.5
ultralytics>=8.4.0
numpy
opencv-python==4.13.0.92
openvino
```

Evite instalar simultaneamente `opencv-python` e `opencv-python-headless`, pois ambos utilizam o módulo `cv2` e podem causar conflitos.

---

## 🛠️ Tecnologias

- **Visão computacional:** [Ultralytics YOLO26](https://docs.ultralytics.com/), OpenCV e FFmpeg (imageio-ffmpeg).
- **Detecção de rostos:** YuNet.
- **Detecção de placas veiculares:** YOLO26n.
- **Anonimização:** pixelização com OpenCV.
- **Otimização:** Intel OpenVINO.
- **Modelos:** PyTorch, ONNX e OpenVINO.
- **API:** Python e Flask.
- **Banco de dados:** MySQL 8, SQLAlchemy e PyMySQL.
- **Front-end:** HTML5, CSS3 e JavaScript (sem frameworks).
- **Treinamento:** Google Colab (GPU Tesla T4).
- **Dataset veicular:** Roboflow Universe.

---

## 👥 Equipe

| Integrante | GitHub |
|------------|--------|
| João Pedro Magri | [@Jpmagri-07](https://github.com/Jpmagri-07) |
| Libina | [@libinayantonini-sketch](https://github.com/libinayantonini-sketch) |
| Larissa | — |
| Vitória | — |
| Clara | — |
| Ana Clara | — |

Front-end desenvolvido originalmente em [luizfelipeyg-crypto/frontend_monitoramento_vias](https://github.com/luizfelipeyg-crypto/frontend_monitoramento_vias).

Banco de dados desenvolvido pela equipe de banco de dados (`database/`).

---

## 🤝 Como contribuir

1. Crie uma branch a partir da `main`:

```bash
git checkout -b feature/nome-da-funcionalidade
```

2. Adicione e registre suas alterações:

```bash
git add arquivo-alterado
git commit -m "Descrição clara da alteração"
```

3. Envie para o repositório:

```bash
git push origin feature/nome-da-funcionalidade
```

4. Abra um **Pull Request** descrevendo o que foi feito.

### Boas práticas do grupo

- Não suba o arquivo `backend/.env`, pois contém informações sensíveis.
- Não envie vídeos ou imagens privadas presentes em `backend/storage/`.
- Preserve o modelo original de sinalização.
- Mantenha os arquivos internos dos modelos OpenVINO juntos.
- Documente alterações nos modelos e dependências.
- Mudanças no banco devem utilizar novos scripts numerados em `database/migracoes/`.
- Mudanças em rotas, tabelas ou telas devem ser documentadas em `docs/`.
- Revise a anonimização antes de disponibilizar vídeos publicamente.
- Respeite as licenças dos modelos e datasets utilizados.

---

<p align="center">Desenvolvido por estudantes para a cidade de Londrina – PR</p>
