# TRIBE v2 · Engajamento Neural de Vídeo

App web que recebe um vídeo e prediz a resposta cortical (fMRI) do espectador médio
usando o modelo [TRIBE v2](https://github.com/facebookresearch/tribev2) do Meta FAIR.
A magnitude L2 da ativação predita ao longo do tempo é usada como **score de
engajamento neural** (0–100), com curva temporal e picos de atenção.

> **Licença do modelo:** CC-BY-NC-4.0. Uso pessoal / pesquisa / acadêmico apenas.

## Arquitetura

```
frontend/   HTML+JS estático (Chart.js via CDN), servido pelo backend
backend/    FastAPI + wrapper do TRIBE v2 (tribe_engine.py)
colab/      Notebook que sobe tudo no Colab com GPU e expõe via ngrok
```

## Como rodar (caminho recomendado: Colab + ngrok)

1. Abra `colab/run_in_colab.ipynb` no Google Colab.
2. Ative GPU (T4 mínimo, L4/A100 melhor).
3. Rode as células em ordem. Cole seu authtoken do
   [ngrok](https://dashboard.ngrok.com/get-started/your-authtoken).
4. Acesse a URL pública no navegador, faça upload de um `.mp4` e veja a análise.

## Como rodar localmente (precisa GPU NVIDIA + Python 3.11)

```bash
git clone https://github.com/facebookresearch/tribev2.git ../tribev2
pip install -e ../tribev2
pip install -r backend/requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Abra `http://localhost:8000` e use `http://localhost:8000` como URL do backend.

## API

`POST /predict`  (multipart, campo `video`) →

```json
{
  "score": 62.4,
  "curve": [12.1, 18.7, ...],
  "peak_seconds": [4, 17, 42, 58, 71],
  "duration_s": 90,
  "n_vertices": 20484
}
```

`GET /health` → status do servidor.

## Métrica

`score(t) = clip(||preds[t, :]||₂ / 8.0 × 100, 0, 100)` — magnitude da ativação
cortical predita, normalizada. Score global = média da curva. Picos = top 5
segundos com maior ativação.

A constante `REFERENCE_SCALE = 8.0` em `backend/tribe_engine.py` é um valor de
calibração inicial — ajuste depois de medir um conjunto de vídeos de referência.

## Limites conhecidos

- TRIBE v2 prediz **média populacional**, não preferência individual.
- "Engajamento" aqui = magnitude de ativação cortical. Vídeos chocantes podem
  pontuar alto mas não serem percebidos como "alta qualidade".
- Inferência leva alguns minutos por minuto de vídeo em GPU média.
- Pesos do modelo (~1 GB) são baixados na primeira execução e cacheados em `./cache`.
