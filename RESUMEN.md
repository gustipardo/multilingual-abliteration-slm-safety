# Resumen del proyecto — para vos cuando volvés

> Última actualización: 2026-05-06. Si algo no calza con la realidad, el origen de verdad es siempre `STATUS.md` (matriz) y `bitacora.md` (lo que hice cada día).

## TL;DR de hoy

- **Pipeline completo para los tres tamaños Dense (E2B + E4B + 31B): inferencia + judging + mecanística terminados.** Las 42 celdas (3 × 7 × 2) están judged y los tres tamaños tienen refusal directions + Silhouette scores extraídos. Las figuras finales cross-size están en `figures/`.
- **E4B corrió en RunPod RTX 5090 el 5 de mayo** porque la laptop OOMeó al cargar pesos (8 GB de VRAM no alcanzan en el peak de loading de E4B). 7h 1m, **~$7.33** (sin mecanística). El bootstrap subió los resultados a un dataset privado de HuggingFace y se intentó autoeliminar el pod, pero la versión vieja de `runpodctl` no soporta `pod delete`. Lección en `runpod_lessons.md`.
- **Mecanística E4B + 31B corrieron el 6 de mayo en dos pods RunPod RTX 5090 fresh, en paralelo.** Cada una <30 min wall, ~$0.30-$0.40 por pod. El bootstrap nuevo (`bootstrap_mechanistic.sh`) usa GraphQL `podTerminate` para self-terminate — esta vez funcionó y los pods cerraron solos. Combined: ~$0.70.
- **Hallazgo de compliance, no monotónico, con pico en E4B**:
  - E2B abliterated: **42.9%** (max 47% en ES)
  - E4B abliterated: **68.1%** (max 74% en PT y DE) ← pico
  - 31B abliterated: **64.4%** (max 71% en DE)
  - El salto E2B→E4B es de +25.3 pp; el salto E4B→31B baja 3.7 pp.
- **El gap base→abliterated también es máximo en E4B** (+57.4 pp vs +38.8 en E2B y +51.3 en 31B). E4B es el punto más sensible al ataque de single-vector abliteration.
- **Hallazgo mecanístico, mismo pico en E4B:** la cosine similarity cross-lingual de las refusal directions también alcanza su máximo en E4B (mean 0.37 vs 0.31 en E2B y 0.27 en 31B; max 0.71). El Silhouette score baja monótonamente con el tamaño (0.29 → 0.26 → 0.23). El pico de compliance y el pico de geometría coinciden en E4B. Eso confirma el Mechanism #1 del Discussion ("refusal geometry más concentrada en mid-size Dense"). El Mechanism #2 (capability outpaces refusal then catches up) queda refutado por la cosine no-monotónica.
- **Framing del paper cerrado:** la vulnerabilidad post-abliteración tiene un *pico* en mid-size Dense (~4B) en compliance Y en geometría de rechazo. Es la zona más accesible al usuario y la más rota por el ataque público.
- **Próximo paso:** rotar tokens (HF/RunPod plaintext en `--env`); empezar a redactar la sección de Resultados del paper; opcional, comparar receta `huihui-ai` vs lab variant Wang sobre los mismos checkpoints (~$2) para distinguir Mechanism #1 vs #3.

---

## 1. ¿De qué trata esto?

Es tu proyecto mentoreado en **BAISH** (AI Safety). Investigás si los modelos chicos de lenguaje (los que corren en celular) son los más peligrosos cuando alguien les saca las restricciones de seguridad. La técnica para sacarlas se llama **"abliteración"** — un método público que en 48 hs después del release de Gemma 4 ya estaba aplicado en HuggingFace.

## 2. ¿Qué querés responder?

**Pregunta:** Cuando se ablitera un modelo en inglés, ¿se rompe la seguridad en otros idiomas también? ¿Y se rompe **MÁS** en los modelos chicos que en los grandes?

**Hipótesis:** Sí. Los chicos pierden seguridad multilingüe más rápido que los grandes. Esto es grave porque son los más accesibles (corren en un teléfono cualquiera).

**Nombre que le pusimos:** *democratization safety paradox* — los modelos más democratizados son también los más peligrosos cuando se abliteran.

## 3. ¿Por qué importa?

- Gemma 4 salió en abril 2026 y a las **48 horas** ya había versiones abliteradas públicas en HuggingFace.
- Estos modelos corren en celulares, sin filtros, en 140+ idiomas.
- **Wang et al. 2025** mostró que la abliteración rompe la seguridad multilingüe en modelos de **7B o más**.
- Nadie todavía estudió qué pasa con **sub-7B**, que son los más usados en países con poca compute.
- Si confirmamos la hipótesis, hay que cambiar cómo se entrena la seguridad en modelos chicos.

## 4. ¿Cómo lo respondemos?

Construimos una matriz de **42 celdas**:

- **3 tamaños Dense** de Gemma 4 → E2B (~2B), E4B (~4B), 31B (~31B)
- **2 condiciones** → base (versión original) vs abliterated (versión sin restricciones)
- **7 idiomas** → EN, ES, ZH, PT, DE, AR, HI (DE agregado el 1 May 2026)
- **100 prompts dañinos** por celda → **4.200 respuestas en total** (1% de resolución por prompt, antes 50 = 2%)

> El cuarto modelo del lineup, **Gemma 4 26B-A4B (MoE)**, queda fuera del experimento principal porque mezclaría el efecto de tamaño con el de arquitectura (Dense vs MoE). Lo dejamos como sub-pregunta para reactivar después → ver `FUTURE_WORK.md`.

Para cada respuesta, **Claude Haiku** decide si "complió" o "rechazó" (no usamos detección por keywords porque Gemma 4 hace *delayed refusal*: empieza ayudando y a mitad de camino rechaza).

Después miramos la **geometría interna** del modelo (refusal direction + Silhouette Score) para entender **por qué** los chicos se rompen más. Replicamos la metodología de Wang et al.

## 5. ¿Qué hardware se usa?

| Modelo | Hardware | Cuánto tardó (medido) |
|--------|----------|----------------------|
| E2B | tu laptop (RTX 4070, 4-bit) | 5h 47m total (100 × 7 × 2 + mecanística) |
| E4B | RunPod RTX 5090 (4-bit) † | 7h 1m inferencia + judging + 12 min mecanística (pod separado) |
| 31B | RunPod RTX 5090 (4-bit) | 23h 44m inferencia + judging + 30 min mecanística (pod separado) |

† E4B se planeó para la laptop pero la VRAM de 8 GB no alcanza en el peak de loading. Se mudó a la nube; con `expandable_segments:True` quizá funcione local en una nueva intentona.

Costo total real en la nube: **~$31.53** (31B inferencia $23.50 + E4B inferencia $7.33 + E4B mecanística $0.30 + 31B mecanística $0.40). Dentro de la línea de $50 del grant.

## 6. ¿Qué tenés hecho?

| Fase | Qué | Estado |
|------|-----|--------|
| 0 | Teoría: idea validada (18/20), novelty check, lit review (27 fuentes) | ✅ |
| 1 | Repo, scripts, configs, Docker, venv | ✅ |
| 2 | Dataset: 50 prompts × 6 idiomas en `data/prompts/` | ✅ |
| 3a | Sanity check E2B en inglés (5 prompts): **safety collapse confirmado** (80% compliance en abliterated vs ~0-40% en base) | ✅ |
| Web | Sitio Astro de presentación en `web/` | ✅ |
| Pipeline | Runner unificado, status tracker, harmless multilingüe, bugs metodológicos arreglados | ✅ |
| 3b-E2B | E2B Dense × 7 idiomas × 2 cond = 14 corridas, judging y mecanística completas | ✅ 2026-05-03 |
| 4 | RunPod: 31B Dense (14 corridas inferencia + judging) | ✅ 2026-05-04 (~$23.50) |
| 3b-E4B | E4B Dense × 7 idiomas × 2 cond = 14 corridas (RunPod, sin mecanística) | ✅ 2026-05-05 (~$7.33) |
| 5b | 31B mecanística (refusal directions + silhouette) | ✅ 2026-05-06 (pod fresca, ~$0.40, 30 min) |
| 5c | E4B mecanística | ✅ 2026-05-06 (pod fresca, ~$0.30, 12 min) |
| 5 | Análisis mecanístico cruzado E2B + E4B + 31B | ✅ 2026-05-06 (cosine sim peak en E4B; Silhouette monotónico decreciente) |
| 6 | Análisis estadístico + figuras finales (`scripts/06_visualize.py`) | ✅ 2026-05-06 (5 figuras regeneradas con la matriz completa) |
| 7 | Paper | 🟦 next |

**Status vivo de la matriz:** corré `python scripts/00_status.py` y mirá `STATUS.md`.

## 7. ¿Qué falta para cerrar el experimento?

**Pendientes técnicos:**

- **Token rotation (housekeeping urgente)** — los HUGGINGFACE_TOKEN y RUNPOD_API_KEY se loguearon en plaintext al pasarlos como `--env` a RunPod (E4B inferencia, 31B inferencia, E4B mecanística, 31B mecanística). Conviene rotarlos en huggingface.co/settings/tokens y runpod.io. ANTHROPIC_API_KEY también, ya que pasó por los pods de inferencia.
- **Receta-comparison experiment (opcional, ~$2)** — para distinguir Mechanism #1 (geometría de Gemma 4 Dense) de Mechanism #3 (huihui-ai recipe específicamente), correr la lab variant de Wang et al. sobre los mismos 6 checkpoints. Es la única follow-up que cierra completamente el círculo mecanístico.

`HUGGINGFACE_TOKEN`, `ANTHROPIC_API_KEY` y `RUNPOD_API_KEY` están cargados en `.env`. Los outputs mecanísticos quedaron como backup en datasets HF privados: `gustipardo/abliteration-{e4b,31b}-mechanistic`. Los datos finales también están en `data/outputs/` localmente.

## 8. ¿Cómo seguir cuando volvés?

```bash
# 1. Ver dónde estás
python scripts/00_status.py

# 2. Avanzar UN modelo (mismo comando local y en RunPod)
python scripts/run_pipeline.py --size e2b
python scripts/run_pipeline.py --size e4b
python scripts/run_pipeline.py --size 31b   # en RunPod
# python scripts/run_pipeline.py --size 26b  # OUT OF SCOPE — sub-pregunta MoE, ver FUTURE_WORK.md

# 3. Cuando estén las 4, generar las figuras del paper
python scripts/06_visualize.py
```

El runner es **idempotente**: si una celda ya está hecha, la salta. Si se corta el judging a mitad de camino, retoma. No vas a perder progreso.

## 9. Plata

| Concepto | Estado |
|----------|--------|
| BlueDot Rapid Grant aprobado | 2026-04-21 (Joshua, team@bluedot.org) |
| Recibido en Dolar App | 2026-04-29, **347 USD** efectivos |
| Distribución (en `BUDGET.md`) | Claude Code Max 200, RunPod 50, API 20, otros 30, WildGuard 50 |
| **RunPod gastado** | **~$31.53** (31B inf $23.50 + E4B inf $7.33 + E4B mech $0.30 + 31B mech $0.40) — dentro de la línea de $50 |
| RunPod opcional (receta-comparison Mechanism #3) | ~$2 |

## 10. Archivos clave (qué leer cuando)

| Cuándo | Qué leer |
|--------|----------|
| **Volvés y no te acordás nada** | `RESUMEN.md` (este archivo) |
| **Querés ver el estado de las corridas** | `STATUS.md` |
| **Querés saber qué hiciste cada día** | `bitacora.md` (sí, es tu Google Doc) |
| **Querés reproducir el experimento desde cero** | `PROTOCOL.md` |
| **Querés el plan completo por fases** | `ROADMAP.md` |
| **Querés los resultados parciales** | `EXPERIMENTS.md` |
| **Querés ver el budget** | `BUDGET.md` |
| **Querés la pregunta y el diseño** | `idea.md` |
| **Querés cambiar un hiperparámetro** | `configs/experiment.yaml` |
| **Querés saber qué quedó fuera del scope y por qué** | `FUTURE_WORK.md` |

**Repo público:** https://github.com/gustipardo/multilingual-abliteration-slm-safety

## 11. Bitácora — flujo importante

Tenés un Google Doc con los facilitadores de BAISH que se actualiza desde `bitacora.md`. **Cada vez que trabajás en el proyecto**, agregá una entrada nueva al principio (debajo del template) con:

- Qué hice
- Qué esperaba vs. qué sucedió
- Cómo cambia lo que pienso
- Siguientes pasos

Español simple, frases cortas, fechas absolutas. Después copiás al Google Doc.

---

**Si algo de esto está desactualizado:** corré `python scripts/00_status.py` y revisá `bitacora.md`. La matriz y la bitácora son la verdad — este resumen es solo el mapa.
