# FUTURE_WORK.md — Preguntas que dejamos abiertas a propósito

Este archivo documenta extensiones del experimento que **no** corremos en el scope principal, pero que tienen el código y el plan listos para reactivarse cuando los resultados principales estén publicados.

---

## 1. ¿La arquitectura MoE afecta distinto al colapso de safety?

### Por qué quedó fuera del scope principal

El lineup de Gemma 4 mezcla arquitecturas: E2B, E4B y 31B son **Dense**, mientras que **26B-A4B es Mixture-of-Experts** (26B totales / 4B activos por token via routing).

Si comparamos los 4 tamaños como un único eje, el MoE introduce un **confounder de arquitectura**: el cambio en compliance entre, digamos, E4B (Dense, 4B) y 26B-A4B (MoE, 4B activos) podría venir tanto de la diferencia de tamaño total como del mecanismo de routing — y no podríamos separar los dos efectos.

Para el experimento principal **fijamos arquitectura = Dense** y nos quedamos con E2B, E4B, 31B. Así la única variable que cambia entre tamaños es el tamaño.

### Sub-pregunta para abrir después

> **¿Activar 4B parámetros vía routing (MoE) produce una geometría de safety distinta a tener 4B parámetros densos siempre activos?**

La comparación natural es:

| Modelo | Parámetros activos | Parámetros totales | Arquitectura |
|--------|--------------------|--------------------|--------------|
| Gemma 4 **E4B** | 4B | 4B | Dense |
| Gemma 4 **26B-A4B** | 4B | 26B | MoE |

Pareando por **parámetros activos**, la única diferencia es la arquitectura (y la capacidad total). Eso aísla el efecto MoE.

Esta sub-pregunta es genuinamente novedosa porque Wang et al. 2025 (el paper que replicamos) sólo estudia modelos Dense.

### Cómo reabrirla cuando los resultados principales estén listos

El código ya soporta `26b` como tamaño válido — está en `configs/experiment.yaml`, en los scripts (`02_run_inference.py`, `03_llm_judge.py`, `04_compute_refusal_directions.py`, `05_silhouette_scores.py`, `run_pipeline.py`) y en `06_visualize.py`. Para reactivarlo:

```bash
# 1. Levantar pod en RunPod
runpodctl create pod --gpu 'RTX 5090' --image pytorch/pytorch:2.3.0-cuda12.1-cudnn8-runtime --disk 100

# 2. Correr la matriz para 26B-A4B (idempotente, no toca lo ya hecho)
python scripts/run_pipeline.py --size 26b

# 3. Comparación pareada con E4B
#    En 06_visualize.py: agregar plot 26B-A4B vs E4B con eje x = "active params"
```

**Costo estimado:** ~5 horas de RunPod (RTX 5090 ~$0.74/hr) ≈ **$4–5 USD**. Plus ~$1 USD de API para el judging de 1.400 nuevas respuestas (100 prompts × 7 idiomas × 2 condiciones).

### Pre-requisitos antes de reabrirla

1. Resultados principales (E2B, E4B, 31B) con conclusiones publicables.
2. Decidir cómo se reporta: como sub-sección del mismo paper o como appendix / paper separado.
3. Revisar literatura nueva sobre MoE safety entre la fecha del paper principal y el momento de reabrir esto.

### Resultados que invalidarían la sub-pregunta

- Si la curva tamaño → compliance de los 3 Dense es perfectamente lineal y predice exactamente 26B-A4B en el lugar correspondiente a sus parámetros activos (4B), la pregunta MoE pierde fuerza.
- Si la abliteración huihui-ai no es comparable entre Dense y MoE (distinta cantidad de capas afectadas, etc.), hay que descartar o tratar como confound documentado.

---

## 2. Análisis mecanístico de 31B Dense (refusal directions + silhouette)

### Por qué quedó diferido

El run de 31B en RunPod (3-4 May 2026, ver `EXPERIMENTS.md`) completó las dos primeras patas (inference base + abliterated, judging completo) pero **no la mecanística**. A las ~22 horas de uso continuo de la RTX 5090, la NVML library del driver NVIDIA entró en estado degradado: `nvidia-smi` empezó a devolver `Failed to initialize NVML: Unknown Error` y los forward passes con `output_hidden_states=True` cayeron a 11 minutos por prompt (vs ~2 segundos esperados). A ese ritmo la fase mecanística iba a tardar 256 horas — inviable.

Maté el proceso, empaqueté `data/outputs/` (1.7 MB con todos los jsonl + judged + compliance_rates.csv), bajé a la laptop, paré y eliminé el pod. Lo único que falta del 31B es la mecanística.

### Cómo reabrirla

Pod fresca evita el estado degradado de NVML. La idea es correr SOLO la mecanística (refusal directions + silhouette) sobre el 31B, ojalá junto con la del E4B cuando esté lista, así las 3 tablas (E2B/E4B/31B) salen del mismo batch:

```bash
# 1. Pod fresca en RunPod
runpodctl ssh add-key --key-file ~/.ssh/id_ed25519.pub  # si no estaba registrada
ENV='{"HUGGINGFACE_TOKEN":"...","HF_TOKEN":"...","ANTHROPIC_API_KEY":"..."}'
runpodctl pod create --gpu-id "NVIDIA GeForce RTX 5090" \
  --template-id runpod-torch-v280 --container-disk-in-gb 200 \
  --cloud-type SECURE --env "$ENV"

# 2. Tarball mínimo + bootstrap (mismo que el run principal — incluye fix de HF_XET)
# Empujar al pod, untar.

# 3. Correr SOLO mecanística para 31B
python scripts/run_pipeline.py --size 31b --skip-judging --force
# El --force re-corre las fases que no encuentra. Como inference y judging YA están
# (los jsonl viajan en el tarball), saltea esas y va a refusal directions + silhouette.
# (Alternativa más limpia: agregar --mechanistic-only a run_pipeline.py.)
```

**Costo estimado:** ~30-60 min × $0.99/hr ≈ **$1 USD** (carga de modelo + 100 forward passes harmful + 10 harmless × 7 idiomas × 2 condiciones).

### Pre-requisitos

1. Tener al menos E2B + 31B mecanístico done. Si E4B también está listo, mejor — una sola corrida cubre los 3 sizes.
2. Tarball del proyecto a mano (`/tmp/runpod_payload/project.tar.gz` o regenerable).
3. SSH key ya registrada en RunPod (de lo contrario, pod nuevo no acepta SSH).

### Por qué no es urgente

El hallazgo principal del paper (gap E2B → 31B = +21.5pp en compliance media) ya está. La mecanística agrega: (a) similarity coseno entre refusal directions de distintos idiomas (¿es la misma dirección o diferente por idioma?), (b) silhouette score (¿qué tan separadas están las activations harmful vs harmless?), (c) PCA visual. Es contenido para la sección de Discusión / Análisis del paper, no para la headline.

---
