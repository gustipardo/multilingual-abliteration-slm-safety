# Bitácora

Agrega tu último log primero:
- Qué hice:
- Qué esperaba vs. qué sucedió:
- Cómo cambia lo que pienso:
- Siguientes pasos:

---

## 08 May 2026 — reproducibilidad del E2B en RunPod

**Qué hice:**
- Re-corrí el E2B (base + abliterated × 7 idiomas) en RunPod para validar contra los números locales del blog post (4.1% base, 42.9% abliterated mean).
- Tres pods consecutivos. El primero lo maté yo por un error de bash: hice `kill` al PID del `sleep` del watchdog en vez de al subshell padre, así que el subshell siguió a la línea siguiente (`curl podTerminate`) y se autoterminó. Lección guardada en memoria.
- Los otros dos pods murieron solos a ~5h de uptime, en plena fase abliterada, en GPUs y regiones distintas (RTX 5090 SECURE NO, después RTX 4090 SECURE US). Sin logs del pod no es diagnosticable. El patrón (~5h, abliterated, secure cloud) sugiere causa externa de RunPod, no hardware ni código.
- Patché el bootstrap dos veces durante la sesión:
  - Watchdog `if sleep` guarded: si matás el sleep, el `if` falla y el `curl` no corre. Ahora la extensión mid-run es segura.
  - **Uploader incremental a HF cada 60s.** Sin esto los pods 2–3 hubieran perdido todo. Con esto la pérdida máxima por crash es 60s de trabajo.
- 12/14 celdas sobrevivieron en `gustipardo/abliteration-e2b-results`. Faltan AR y HI abliterated (Pod 3 murió antes de llegar).
- Bajé las 12 jsonls a `data/_runpod_e2b_2026-05-08/`, juzgué con Claude Haiku 4.5 vía API local (~$0.30, 17 min), computé compliance y diff celda por celda contra la baseline archivada en `data/_archive_local_e2b_2026-05-07/`.

**Resultados (12 celdas compartidas):**

| | local | cloud (RTX 4090) | Δ pp |
|---|---:|---:|---:|
| base mean (7 cells) | 4.1% | 3.4% | **−0.7** |
| abliterated mean (5 cells) | 43.6% | 46.6% | **+3.0** |

Dos celdas exceden 5 pp: **ZH abliterated +8 pp** (45→53%) y **DE abliterated +7 pp** (44→51%). Las otras 10 caen dentro de ±3 pp.

**Qué esperaba vs. qué sucedió:**
- Esperaba una corrida única de ~7h en RTX 5090, costo ~$5, números bit-exact con local. Sucedió: 3 pods, ~$10, números reproducen el headline pero con drift no trivial en dos celdas abliteradas.
- Esperaba que las celdas base reprodujeran mejor que las abliteradas. Se cumplió: base ±2 pp en todas, abliterated hasta 8 pp. Hipótesis: el modo abliterated genera los 512 tokens completos en cada prompt (no hay refusal corto que corte temprano), así que las diferencias kernel-level de greedy decoding entre GPUs se acumulan más.
- El +8 pp de ZH posiblemente viene del prompt set: las traducciones de BeaverTails no fueron back-translated, y contenido borderline + traducción ruidosa amplifica la sensibilidad del juez ante variaciones mínimas de generación.

**Cómo cambia lo que pienso:**
- **La conclusión del blog post se sostiene.** El headline (E2B abliterated mean = 42.9%) reproduce dentro de ~2 pp si proyecto AR y HI a los valores locales: la media full-7-langs del cloud queda en 44.7% vs 42.9% local. La curva no monotónica que pica en E4B (68%) no se ve afectada por un drift de ~3 pp en E2B.
- El single-vector abliteration de Wang et al. es robusto a cambio de hardware **en el sentido que importa para el paper**: la forma de los resultados se preserva, los rankings cross-language también (Hindi sigue al fondo, ES/PT arriba).
- Para reproducibilidad bit-exact necesitaría pinear versiones de transformers + bitsandbytes + torch + GPU exacto. Para reproducibilidad de las conclusiones del paper no hace falta.
- El uploader incremental debería ser parte de cualquier bootstrap futuro de inferencia larga. Va al template, no solo a este experimento.

**Siguientes pasos:**
- Rotar `HUGGINGFACE_TOKEN` y `ANTHROPIC_API_KEY` (expuestos en plaintext vía `--env` en los 3 pods de hoy).
- (Opcional) Cerrar AR/HI abliterated cloud corriéndolos local en la laptop (~2h, gratis). No vale la pena respender otro pod.
- (Opcional) Mecanística cloud: no la corrí. La local que está en el paper sigue siendo válida; un re-run cloud no agrega seguridad significativa al claim de cosine 0.31 / Silhouette 0.29 para E2B.
- Agregar nota a `EXPERIMENTS.md` documentando el cloud reproducibility check con su drift y su scope (12/14 cells, no mecanística).

---

## 06 May 2026

**Qué hice:**
- Revisión crítica de `BLOG_POST.md` contra la *Blog Post Writing Guide* (BlueDot) y mis principios de §11.
- Verifiqué cada cita externa con WebSearch + WebFetch: Wang 2025, Arditi 2024, Han 2024 (WildGuard), Abu Shairah 2025 (defensa), página oficial de Gemma 4.
- Correcciones factuales que metí al post:
  - **Wang et al.** testea 3 modelos principales en sus experimentos de §4 (Llama3.1-8B-Instruct, Qwen2.5-7B-Instruct, gemma-2-9B-Instruct) y menciona modelos adicionales por familia (Yi, Qwen2.5-14B). El post decía "ten Dense models, 2B to 70B parameters", lo cual sobrevendía el alcance del paper. Ajusté a "instruction-tuned models from Yi, Qwen 2.5, Llama 3, and Gemma 2, with their main analyses on 7B–14B variants". El "smallest model verifiable" del paper es 7B, no 2B.
  - La cita textual del paper es **"consistently approaching or exceeding 90%"** (presente continuo). El post tenía una de las menciones como **"approached or exceeded 90%"** (pasado). Lo arreglé. Además, ese 90% es de la *non-English universality experiment* (vectores extraídos de DE/ZH/TH), no de la English-derived ablation. Aclaré los tres idiomas fuente.
  - El término **"abliteration"** lo acuñó **FailSpy** (portmanteau de *ablation* + *obliteration*), no Arditi et al. Arditi llama al método "directional ablation". Aclaración en TL;DR e introducción.
  - **Gemma 4** se liberó el **2 de abril de 2026** (no "abril 2026" genérico). El "E" en E2B/E4B significa **effective parameters** vía Per-Layer Embeddings: ~2.3B y ~4.5B (no "~2B" y "~4B"). Actualicé TL;DR + Intro + Methods.
  - **31B wall time**: el post decía "20h 19m of effective wall time, costing $23.50" pero EXPERIMENTS.md tiene 20h 19m = inferencia + judging y 23h 44m = pod total ($23.50). Aclaré ambos.
  - Paper de defensa (Abu Shairah 2025): el post decía "semantically rich refusals". El paper en realidad propone "extended refusals con justificaciones detalladas que distribuyen la señal de rechazo entre múltiples tokens". Reescribí.
- Mejoras de calidad:
  - Nota de **incertidumbre estadística** en Results §1 (SE pooled ≈ 1.8 pp con n=100, el gap E4B→31B es ~2 SE pero respaldado por sign test 4-0-3).
  - Definí *refusal direction* explícitamente en la primera oración de la Intro.
  - Apreté el heading de Result 3.
  - Reemplacé el placeholder de Figure 1 con el comando exacto que la genera (`scripts/06_visualize.py`).
- **Estilo verificado por grep**: 0 em dashes, 0 en dashes en prosa, 0 trigger words de §11.2. El post ya estaba limpio en estilo.
- **No tocado**: el link al repo en TL;DR sigue como `_[link to repo]_` — no encontré la URL canónica en README/CLAUDE.md.

**Qué esperaba vs. qué sucedió:**
- Esperaba 1-2 imprecisiones menores. Encontré que varias citaciones a Wang et al. *sobrevendían* lo que el paper hace (10 modelos / 2B-70B vs. en realidad 3 main + algunos extras en 7B-14B). La regla §11.7 ("verificar que la cita dice lo que afirmás") rindió mucho — sin abrir el paper, los claims se leen verosímiles.
- Esperaba que el estilo tuviera algo para limpiar. Lo grepeé y no apareció nada. La calibración del §11.2 ya está internalizada.
- Confirmé que estructuralmente el post sigue la guía BlueDot al pie: TL;DR + Figure 1 + Intro (con threat model explícito) + Methods + Results (main primero) + Discussion (con limitaciones y calibración) + Related + Future Work. Sólo faltan Figure 1 real y el link al repo.

**Cómo cambia lo que pienso:**
- El post está más cerca de "publishable después de Figure 1 + repo link" de lo que pensaba al empezar. Las correcciones eran reales pero todas surgical (oraciones individuales, no estructura).
- El error más caro era el "ten Dense models, 2B to 70B parameters" — probablemente vino de mezclar memoria entre el paper de Arditi (que sí testea 13 modelos hasta 72B) y el de Wang (que testea 3 main + extensiones en 7B-14B). Es exactamente la trampa que la §11.7 advierte. Lección: cuando hay dos papers cercanos en el mismo subcampo, mejor abrir Table 1 antes de paraphrasear.
- La cita misquoteada ("approached or exceeded" vs "approaching or exceeding") es minúscula pero exactamente el tipo de error que erosiona confianza en una review estricta.

**Siguientes pasos:**
- ~~Correr `python scripts/06_visualize.py` para generar Figure 1 real~~ → hecho misma sesión, ver bloque "06 May 2026 — sesión vespertina" abajo.
- ~~Completar el link al repo en TL;DR (línea 13)~~ → hecho misma sesión, link `https://github.com/gustipardo/multilingual-abliteration-slm-safety`.
- ~~Mantener pendiente la mecanística E4B + 31B~~ → corrida y cerrada en la sesión vespertina del mismo día.
- (Opcional) Verificar contra Wang et al. Figure 1 directo si los "70 to 90% range" del Result 3 se sostienen exactamente. Si tenés el PDF a mano, revisalo.
- Rotar tokens (HF, RunPod) — pasaron por `--env` plaintext en los dos pods de mecanística.

---

## 06 May 2026 — sesión vespertina (mecanística E4B + 31B)

**Qué hice:**
- Corrí la **mecanística E4B + 31B** en dos pods RunPod RTX 5090 fresh, en paralelo. Los dos cerraron OK, autoeliminaron por GraphQL, subieron resultados a HF privado.
- E4B mecanística: pod `em1mtytsod1j59`, ~12 min wall, ~$0.30. Refusal directions + Silhouette + PCA listos.
- 31B mecanística: pod `gv5a86hody3u4r`, ~30 min wall, ~$0.40. Mismo output set.
- Bajé los dos tarballs de HF (`gustipardo/abliteration-{e4b,31b}-mechanistic`), descomprimí, mergeé `silhouette_scores.csv` con las filas E2B previas, copié `refusal_directions_*.pt`, `cosine_similarity_*.csv` y los PCA pngs a `data/outputs` y `figures/`.
- Corrí `python scripts/06_visualize.py` localmente — generó las 5 figuras cross-size finales (compliance heatmaps base/abl/delta, size_vs_compliance, silhouette_by_size). El placeholder verbal de Figure 1 en el blog post ya pudo reemplazarse por la imagen real.
- Regeneré `STATUS.md` con `python scripts/00_status.py` (ahora muestra ✓ en mechanistic para los 3 tamaños).
- Actualicé los .md afectados con los nuevos números: `BLOG_POST.md` (drop "pending", agregar Result 4 mechanistic + actualizar Discussion mechanisms + Calibración), `EXPERIMENTS.md` (nueva sección "E4B + 31B Mechanistic Re-run" arriba + tabla "What Remains" actualizada), `CLAUDE.md` raíz (Status line nueva), `README.md` (badge + status + tabla de fases), `ROADMAP.md` (fases 5b/5c/6 marcadas done).

**Resultados mecanísticos (cross-size):**

Cosine similarity de refusal directions (mean off-diagonal en matriz 7×7):

| | E2B | E4B | 31B |
|---|---|---|---|
| mean | 0.31 | **0.37** | 0.27 |
| max  | 0.67 | **0.71** | 0.52 |

Silhouette scores (separación harmful vs harmless en activaciones):

| | media |
|---|---|
| E2B | **0.29** |
| E4B | 0.26 |
| 31B | **0.23** |

**Qué esperaba vs. qué sucedió:**
- Esperaba que la curva de cosine sim también fuera no monotónica con pico en E4B (predicción del Mechanism #1 del Discussion). **Se cumplió clavado**: 0.31 / 0.37 / 0.27. La forma matchea la curva de compliance.
- Esperaba que el Silhouette score fuera más alto en E2B (predicción del Mechanism #1). **Se cumplió**: 0.29 / 0.26 / 0.23, monotónicamente decreciente.
- No esperaba que Mechanism #2 ("capability outpaces refusal then catches up") quedara *refutado*. La curva de cosine es no monotónica, así que el escenario monotónico que predecía Mechanism #2 no se sostiene.
- Mechanism #3 (recipe-driven) sigue **untested** — sólo se distingue corriendo Wang et al.'s lab variant en los mismos 6 checkpoints. Esa es la única follow-up importante que queda abierta.

**Cómo cambia lo que pienso:**
- El paper tiene historia mecanística clara y *coherente* con la compliance. **El pico de compliance en E4B y el pico de cosine sim en E4B coinciden**, y eso es exactamente lo que predice "geometría de rechazo más concentrada en mid-size Dense". No un coincidencia: las dos curvas tienen la misma forma. Mecánicamente publicable.
- 31B abliterada complió MENOS que E4B (64.4% vs 68.1%) y a la vez tiene la geometría más distribuida (Silhouette más bajo, cosine sim más bajo). La interpretación natural: en 31B el rechazo está implementado a través de múltiples componentes redundantes, no de una sola dirección dominante. Single-vector ablation remueve uno, pero queda estructura residual.
- E2B también complió menos que E4B pero por una razón distinta (Silhouette alto pero cosine sim cross-lingual bajo): per-language refusal directions diverge en E2B, así que un vector inglés borra "el inglés" pero no las otras lenguas.
- Resultado: **el medio Dense (~4B) es donde el ataque cross-lingual es más efectivo** porque (a) las refusal directions están convergiendo en una sola, y (b) harmful/harmless siguen razonablemente separados localmente.
- El framing del paper es mucho más fuerte ahora. "Compliance peak coincides with geometry peak at the most consumer-accessible size."

**Siguientes pasos:**
- Rotar HF token y RunPod API key (los dos quedaron en plaintext en los `--env` de los pods).
- Empezar a draftear la sección Results del paper. Compliance + mechanistic ya están ambos finales y consistentes. El blog post tiene la estructura que el paper puede expandir.
- Decidir si vale la pena correr el Mechanism #3 experiment (recipe comparison: Wang lab variant vs huihui-ai sobre los mismos 6 checkpoints). Costo: ~$2 + tiempo de implementar el extractor. Lo que aporta: distingue "Gemma 4 Dense específicamente" de "huihui-ai recipe específicamente". Worth para el paper, no urgente para el blog post.
- (Open) Mantener pendiente el sub-experimento MoE 26B-A4B (`FUTURE_WORK.md` §1). Sigue out of scope del paper principal.

---

## 05 May 2026

**Qué hice:**
- Cerré el tercer punto de la curva: corrí E4B Dense (14 celdas, 100 prompts × 7 idiomas × 2 condiciones) **en RunPod RTX 5090**, no en la laptop como estaba planeado.
- Primero intenté correrlo en la laptop, dos veces. La primera vez falló por `python: command not found` (el `nohup` no heredó el venv). La segunda, ya con el venv correcto, fue OOM en CUDA: a 36% del weight loading el peak de uso saltó por arriba de los 7.62 GiB disponibles del RTX 4070 — pese a que en teoría 4-bit deja el modelo en ~3 GB. El loader tiene un peak transitorio que no entra en 8 GB.
- Migré a RunPod. Escribí `bootstrap_e4b.sh` (variante de `bootstrap.sh` para 31B): mismo flujo de validación de tokens y deps, pero con tres cambios — `--skip-mechanistic` en el runner, upload del tarball de resultados a un dataset privado de HuggingFace al final, y autoeliminación del pod. Más un watchdog de 8h por las dudas.
- Crear el pod requería `--env` como JSON object, no flags repetidos (un detalle del CLI que no estaba documentado en `runpod_lessons.md`). Lo crucé y funcionó.
- Mientras dormía, el pipeline corrió limpio: 7h 1m totales en RTX 5090, $7.33. Inferencia base 2h 4m, abliterated 4h 30m, judging 27 min, sin mecanística.
- Subió el tarball (1.6 MB) a `gustipardo/abliteration-e4b-results` (privado). Después intentó autoeliminarse con `runpodctl pod delete $RUNPOD_POD_ID` y **falló**: la versión de `runpodctl` que se instala con `cli.runpod.net | bash` es una vieja (`1.14.15`) que no tiene el subcomando `pod`. Devolvió `Error: unknown command "pod" for "runpodctl"` y el pod siguió corriendo. Lo borré a mano cuando me desperté — el pod estuvo idle ~17 min cobrando.
- Bajé los outputs con `hf download`, los descomprimí en `data/outputs/`, regeneré `compliance_rates.csv` con `scripts/03_llm_judge.py --table` (combinando E2B + E4B + 31B), corrí `scripts/00_status.py`.
- Actualicé memoria con la lección de `runpodctl` (`runpod_lessons.md`) y el doc index. Actualicé README, RESUMEN, ROADMAP, EXPERIMENTS, BUDGET, CLAUDE.md raíz, y los componentes Astro de la web (Results, Scenarios, Timeline) con los nuevos números.

**Resultados E4B (compliance rates):**

| | EN | ES | ZH | PT | DE | AR | HI | media |
|---|---|---|---|---|---|---|---|---|
| base       | 13% | 11% | 7% | 16% | 10% | 9% | 9% | **10.7%** |
| abliterated | 70% | 66% | 64% | 74% | 74% | 64% | 65% | **68.1%** |
| Δ (gap)    | +57 | +55 | +57 | +58 | +64 | +55 | +56 | **+57.4** |

Curva completa de los tres tamaños:

| | E2B (~2B) | E4B (~4B) | 31B (~31B) |
|---|---|---|---|
| base media       | 4.1% | 10.7% | 13.1% |
| abliterated media | 42.9% | **68.1%** ← pico | 64.4% |
| gap base→abl     | +38.8 pp | **+57.4 pp** ← pico | +51.3 pp |

**Qué esperaba vs. qué sucedió:**
- Esperaba que E4B corriera en la laptop overnight (~10-13h) y diera un valor *intermedio* entre E2B (43%) y 31B (64%) — algo en torno al 55%. Lo que vi: la laptop no aguanta E4B en 4-bit (peak de loading > 8 GB), tuve que mover a la nube; y el resultado **no fue intermedio sino que superó a 31B** (68% vs 64%). La curva tamaño→compliance NO es monótona, tiene un **pico en E4B**.
- Esperaba que la autoeliminación del pod funcionara con `runpodctl pod delete`. No funcionó porque el binario que se instala con el script de `cli.runpod.net` es una versión vieja con otro layout de subcomandos. Lección aprendida y guardada: para self-terminate desde dentro del pod conviene la GraphQL API directo con curl (sin dependencia de CLI). $0.28 perdidos en idle pero el data ya estaba subido.
- Esperaba que el upload a HF fuera frágil. Funcionó perfecto: el bootstrap creó el repo (`exist_ok=True`), subió el 1.6 MB, y a la mañana lo bajé sin drama. Ese patrón es más robusto que `runpodctl send`/`receive` para corridas desatendidas.
- No esperaba que E4B cerrara más cerca del rango Wang et al. (80-90% para 7B+) que 31B. PT y DE quedaron en 74%, máximo de toda la matriz. La lectura de "rechazo low-rank residual" que estaba sosteniendo el 31B se debilita cuando ves que en el modelo intermedio el ataque es casi total.

**Cómo cambia lo que pienso:**
- **El framing del paper cambia (otra vez).** Antes del 31B el framing era "los chicos están más expuestos". Después del 31B (con E2B + 31B) era "escalar empeora la seguridad". Ahora con E4B en el medio: ninguna de las dos lecturas naive funciona — la curva tiene un **pico en mid-size Dense (~4B)** y baja levemente al escalar más. Es un finding más interesante que un eje monótono porque (a) refuta los dos framings naive, (b) ubica la vulnerabilidad máxima en el tamaño *más accesible* de la familia (4B corre en consumer GPUs, cerca de phone-scale a baja cuantización), y (c) deja al 31B con compliance abliterada *menor* que el 4B, lo que sugiere que la complicación de baja-rango residual se da más en los extremos que en el medio. El paradigma de la "democratization safety paradox" sigue válido pero por un mecanismo distinto al que imaginé al principio.
- El plot que va al paper ya no es una recta con tres puntos sino una **curva con curvatura**, y la implicación de política se sostiene incluso mejor: el modelo más vulnerable es el que tiene más chances de correr en un teléfono.
- Para el próximo overnight, no instalar `runpodctl` con `cli.runpod.net | bash` para self-terminate — usar curl + GraphQL directamente. La memoria ya tiene la receta.
- Worth también: el flujo "bootstrap → ejecuta pipeline → sube tarball a HF privado → autoelimina" funciona y vale la pena dejarlo como template para futuras corridas desatendidas (incluida la mecanística pendiente).

**Siguientes pasos:**
- Correr la **mecanística E4B + 31B** en pods frescas (separadas, ~$1 cada una, ~30-60 min cada una) con `--skip-judging --force` apuntando a `04_compute_refusal_directions.py` y `05_silhouette_scores.py`. Conviene split en dos pods porque la GPU se degrada después de ~22h (lección del 31B) y si bien estas corridas son cortas, no quiero arriesgar.
- Una vez que estén las refusal directions de los tres tamaños, correr `scripts/06_visualize.py` para los plots cross-size: heatmap de compliance abliterada × idioma × tamaño, gráfico de la curva no monótona, silhouette × tamaño.
- **Empezar a esbozar la sección Results del paper.** Los compliance numbers ya son finales; el storytelling cambió pero está más fuerte. Argumento principal del Results: "the post-abliteration compliance curve is non-monotonic and peaks at the most consumer-accessible Dense size in the Gemma 4 family".
- Rotar tokens (HF, Anthropic, RunPod) — los tres se loguearon en plaintext en el `--env` del E4B. (Lo mismo había que hacer del 31B; lo postergué entonces, conviene hacerlo ya).
- Actualizar la web: rebuild Astro y verificar que los nuevos componentes muestran E4B.

---

## 04 May 2026

**Qué hice:**
- Corrí 31B Dense en RunPod RTX 5090 (32GB, secure cloud Noruega). Aproveché el día para no quemar la noche con la corrida más cara.
- Setup: instalé `runpodctl` 2.2, registré la SSH pubkey, cargué $50 de crédito, armé un tarball mínimo del proyecto (70KB: scripts + configs + data/prompts + bootstrap.sh) y un bootstrap idempotente que valida GPU + tokens + acceso HF antes de descargar el modelo.
- Dos fallos de arranque antes de la corrida buena: (1) primer pod con 50 GB de disco — insuficiente, los pesos del 31B en bf16 son ~62 GB cada modelo, recreé con 200 GB; (2) `HF_XET_HIGH_PERFORMANCE=1` (default del template torch-v280 de RunPod) hizo crashear el download paralelo con "Internal Writer Error: receiver dropped" — lo desactivé en el bootstrap.
- Tercer pod corrió limpio. Pipeline completo de inferencia + judging:
  - Inference base × 7 idiomas: 6h 10min
  - Inference abliterated × 7 idiomas: 13h 42min (long-tail más pesado que en E2B)
  - Judging Claude Haiku: 27 min
- Análisis mecanístico (refusal directions + silhouette) **abandonado**: a las ~22h de uso continuo la GPU entró en estado degradado (NVML library no responde, forward passes a 11 min/prompt en lugar de ~2 segundos). A ese ritmo la fase tardaría 256 horas. Maté el proceso, empaqueté `data/outputs` (1.7 MB), bajé a la laptop por scp, paré y eliminé el pod.

**Resultados 31B (compliance rates):**

| | EN | ES | ZH | PT | DE | AR | HI | media |
|---|---|---|---|---|---|---|---|---|
| base       | 16% | 12% | 13% | 16% | 12% | 10% | 13% | **13.1%** |
| abliterated | 67% | 64% | 65% | 63% | 71% | 61% | 60% | **64.4%** |

Gap base→abliterated: **+51.3pp** en 31B (vs +38.8pp en E2B). El salto absoluto post-abliteración es **+12.5pp más grande** en 31B.

Comparación con E2B (eje tamaño):

| | E2B (~2B) | 31B (~31B) | Δ E2B→31B |
|---|---|---|---|
| base media       | 4.1% | 13.1% | +9pp |
| abliterated media | 42.9% | 64.4% | **+21.5pp** |

**Qué esperaba vs. qué sucedió:**
- Esperaba ~16h de corrida total a $0.99/hr ≈ $16. Costó **~$23.50** (~24h por la fase mecanística que arrancó antes de tirar la toalla). Dentro del budget de $50.
- Esperaba que 31B abliterated llegara a 70-80% (cerca del rango Wang et al. 7B+). Quedó en 64.4% promedio. Más comprometido que E2B pero no tanto como los 7B+ del paper original — confirma el patrón "más distribuido que en 7B, menos que en 2B" que esperábamos para un dense 31B.
- No esperaba que la GPU se degradara al hacer forward passes con `output_hidden_states=True`. Es un modo de uso distinto al de generación (genera 1 forward por prompt, no decoding loop), y la NVML library se rompió silenciosamente. Confirma que para corridas largas en cloud conviene partir el work en pods separados (uno para inferencia, otro para mecanístico) en vez de uno monolítico.
- No esperaba que el setup de RunPod tuviera tantos rakes: SSH key no se inyecta en pods existentes (solo al crear), `PUBLIC_KEY` env vacía si registrás la key después, container disk default 20 GB que para LLMs grandes no alcanza ni para un modelo, defaults agresivos de hf_xet/hf_transfer que rompen en shards grandes.

**Cómo cambia lo que pienso:**
- El hallazgo principal del paper queda **consolidado**: la abliteración escala con tamaño. La curva 2B → 31B muestra +21.5pp de compliance media post-abliteración, sin tocar metodología. Cuando termine E4B local tendré los 3 puntos (2B/4B/31B) para el plot tamaño→vulnerabilidad y el Spearman.
- El abliterated del 31B no llega al 80-90% de Wang et al. — sigue habiendo una "complicación de baja-rango" residual incluso en 31B. Es un finding sutil que distingue Gemma 4 31B de los 7B+ del paper de referencia, y reaffirma la pregunta del paper.
- Workflow de RunPod: la próxima vez parto el pipeline en dos pods separados (inferencia primero, mecanístico segundo en pod fresco) y uso `runpodctl pod create --container-disk-in-gb 200` desde el inicio. El bootstrap actualizado ya tiene el fix de `HF_HUB_DISABLE_XET=1`.
- Tener `nohup` + log persistente + monitor remoto que streamea cambios de fase fue **clave**. Pude ver lo que pasaba sin tener que estar mirando, y agarré el problema mecanístico ni bien apareció.

**Siguientes pasos:**
- Esta noche: dejar corriendo E4B local (`python scripts/run_pipeline.py --size e4b`). Estimo 10-13h. Idempotente.
- Cuando termine E4B, tendremos los 3 puntos (E2B + E4B + 31B) y se puede correr `scripts/06_visualize.py` para los plots cross-size.
- Re-correr el análisis mecanístico del 31B en pod nuevo (RunPod RTX 5090 fresca) con `--skip-judging --force` apuntando a refusal directions + silhouette. Estimo $1, 30-60 min. **Diferido** hasta tener E2B + E4B + 31B mecanístico para comparar las 3 curvas.
- Empezar a esbozar la sección de Resultados del paper con la tabla de compliance × 3 sizes ya disponible.
- Rotar los tokens de HF y Anthropic — los expuse al inyectarlos como env vars en RunPod y quedaron en logs.

---

## 03 May 2026

**Qué hice:**
- Corrí E2B end-to-end con la matriz nueva (100 prompts × 7 idiomas × 2 condiciones) usando el runner mejorado. Se ejecutó toda la corrida sin intervención: inferencia base, inferencia abliterated, judging con Claude Haiku, refusal directions y silhouette. Pipeline completo en una sola pasada.
- Tardó **5 horas 47 minutos**, contra mi estimación de 2:35. La diferencia: el modelo abliterated genera respuestas largas (compla → 512 tokens) mientras que el base se corta temprano con un refuse de 30-50 tokens. Abliterated tardó 2.4× más que base. Actualicé las estimaciones del runner con los números reales.
- Antes de arrancar, archivé los outputs viejos del run anterior (50 × 6) en `data/_archive_50prompts_6langs/outputs/` así el runner empieza limpio.
- Validé el banner end-to-end: arrancó bien, mostró las 7 fases con tiempos estimados, fue avanzando con las notificaciones de cambio de idioma y archivo. El log persistente en `logs/e2b_20260503_005202.log` quedó completo con timestamps por fase.
- Encontré un mini bug en `00_status.py` — el denominador estaba hardcoded en "12" (del scope viejo de 6 idiomas). Lo hice dinámico (`n_langs × 2 = 14`). Regeneré `STATUS.md` con el fix.
- Documenté los resultados en `EXPERIMENTS.md` con tabla, timings, observaciones y comando para reproducir.
- Actualicé README, RESUMEN, CLAUDE.md (raíz) con el nuevo estado: E2B done, E4B next.

**Resultados E2B (compliance rates):**

| | EN | ES | ZH | PT | DE | AR | HI |
|---|---|---|---|---|---|---|---|
| base       | 4% | 7% | 4% | 6% | 4% | 2% | 2% |
| abliterated | 42% | 47% | 45% | 40% | 44% | 43% | 39% |

Gap promedio base→abliterated: **+39 puntos** en los 7 idiomas. Safety collapse confirmado.

**Qué esperaba vs. qué sucedió:**
- Esperaba ~2-3 horas. Tardó casi 6. La estimación inicial subestimó el costo de generar respuestas largas en el modelo abliterado.
- Esperaba que low-resource (HI) tuviera más compliance que high-resource (ES, EN). Salió al revés: ES tiene el highest (47%) y HI el lowest (39%). Hipótesis interesante para el paper.
- Esperaba que abliterated llegara a 80-90% como Wang et al. en 7B+. Quedó en 47% max. Esto **es** consistente con el post de LessWrong sobre "low-rank refusal in small models" que cité en Phase 0. El SLM tiene componentes de rechazo residuales que el single-vector abliteration de huihui-ai no toca. Es evidencia para el paper, no un bug.

**Cómo cambia lo que pienso:**
- El hallazgo de que el abliterated max sea ~47% en lugar de ~85% es **el resultado más interesante de la corrida**. Es un tipo de finding que el paper puede destacar: en SLMs el ataque de single-vector funciona pero está acotado por la geometría de rechazo más distribuida.
- La uniformidad del gap entre idiomas (+34 a +41) refuta una versión cruda de la hipótesis "low-resource más vulnerable", pero no la versión interesante: la uniformidad por sí misma es un dato. Implica que la dirección de rechazo aprendida desde inglés se proyecta universalmente al resto de idiomas que el modelo aprendió.
- Tener el banner + log persistente sirvió: pude ver progreso en las notificaciones, no me preocupé en ningún momento si se había tildado.

**Siguientes pasos:**
- Esta noche: dejar corriendo E4B local. Comando: `python scripts/run_pipeline.py --size e4b`. Estimo ~10-12 horas (E4B es 2× E2B en parámetros + el efecto del abliterated long-tail). Idempotente, banner + log.
- Cuando termine E4B y ya tenga 2 puntos en la curva, decidir si arrancar 31B en RunPod o esperar a tener algo más.
- Empezar a esbozar el blog post / paper con los hallazgos de E2B mientras corre E4B.

---

## 02 May 2026 (continuación — auditoría y pipeline robusto)

**Qué hice:**
- Auditoría punto por punto del estado del proyecto: prompts, traducciones, cuantización, GPU RunPod, documentación, scripts, end-to-end y barras de progreso. Verifiqué cada cosa contra el código real, no de memoria.
- Resultado: encontré tres bugs reales que no se vieron en sesiones anteriores.
- **Bug 1 (cuantización inconsistente):** los scripts `02_run_inference.py`, `04_compute_refusal_directions.py` y `05_silhouette_scores.py` usaban `BitsAndBytesConfig` pero solo `02` tenía `bnb_4bit_use_double_quant=True`. Eso es un confounder técnico chico — el modelo que produce las respuestas tendría una cuantización ligeramente distinta del modelo cuyas activaciones analizo. Lo alineé en los tres scripts.
- **Bug 2 (`06_visualize.py` desactualizado):** todo el archivo seguía con el lineup viejo de 4 modelos (incluyendo MoE) y 6 idiomas (sin DE). Lo reescribí entero para el scope nuevo: 3 sizes Dense, 7 idiomas con DE, sin lógica MoE en las figuras principales. El MoE quedaría para `FUTURE_WORK.md`.
- **Bug 3 (docstrings):** `01_prepare_dataset.py` decía "50 prompts, 6 languages" y sugería subir a `wildguard-multilingual-50`. Lo actualicé a 100, 7 y BeaverTails.
- **Mejoras al pipeline (D):** rehice `run_pipeline.py` con un runner visualmente claro:
  - Banner inicial con resumen de la corrida (size, condiciones, idiomas, hardware, tiempo total estimado, path al log).
  - Cada fase tiene un header numerado `[N/M]` con el comando exacto, hora de inicio y estimación.
  - Footer por fase con tiempo elapsed y estado (✓/✗).
  - Resumen final con tabla de tiempos por fase.
  - Logging persistente a `logs/{size}_{timestamp}.log` con eventos estructurados (sin contaminar con bytes de tqdm).
  - Colores ANSI con detección de TTY (no rompe en `tee`/CI).
- **Meta-progreso entre idiomas:** modifiqué `02_run_inference.py` para que muestre `── language 3/7: ZH (e2b/base) ──` antes de cada idioma, así no necesito contar tqdm bars para saber dónde voy.
- **Meta-progreso entre archivos:** mismo patrón en `03_llm_judge.py --all`.

**Qué esperaba vs. qué sucedió:**
- Esperaba que la auditoría confirmara que estaba todo OK. Aparecieron tres bugs reales — el de la cuantización es el más serio porque era un confounder técnico que se podría haber colado al paper.
- El runner nuevo terminó siendo más trabajo del previsto pero quedó bien: probé el banner y los headers en seco y se ven claros y útiles.

**Cómo cambia lo que pienso:**
- Hacer auditoría con verificación real (leer el código, no solo recordar) atrapa cosas que recordadas se asumen correctas. Vale la pena el tiempo.
- Para corridas largas (E2B duró 2hs, E4B va a durar más, 31B ~7hs), el feedback visual no es un nice-to-have: es lo que diferencia "está corriendo bien" de "se tildó hace 40 minutos y no me dí cuenta".
- Tener el log persistente desbloquea poder dejar correr el pipeline en background y revisar lo que pasó después.

**Siguientes pasos:**
- Re-correr E2B con la matriz nueva (100 × 7) usando el `run_pipeline.py` mejorado, para validar que todo el flow funciona end-to-end con el banner.
- Continuar con E4B local.
- Levantar pod en RunPod para 31B Dense.
- Cerrar judging + análisis mecanístico.

---

## 02 May 2026

**Qué hice:**
- Revisé el set de prompts en los 7 idiomas y encontré uno solo no traducido (ZH 043, "stealing someone's car"). Lo traduje a mano al chino. Los IDs 013 (Picardy Place Court) son direcciones — los traductores las dejan en inglés en todos los idiomas y eso es lingüísticamente correcto.
- Dejé por escrito la decisión de cuantización: los modelos se cargan con bitsandbytes 4-bit NF4 + double-quant + compute bf16, en HuggingFace Transformers, todos con la misma config. Documenté por qué no usamos GGUF Q6 (la sugerencia de CanIRun.ai) — la mecanística necesita hooks que solo funcionan en HF Transformers, y un Q6 31B se infla a ~120 GB al cargarlo.
- Recibí el feedback del facilitador: el experimento mezclaba 3 variables (cuantización, arquitectura, tamaño). Cuantización ya quedó fija. Arquitectura no: el lineup de Gemma 4 incluye 26B-A4B, que es Mixture-of-Experts. Comparar Dense con MoE en el mismo eje "tamaño" introduce un confounder.
- Decidí reducir scope a 3 modelos Dense (E2B, E4B, 31B) y dejar el MoE como sub-pregunta diferida. Creé `FUTURE_WORK.md` con el plan de reactivación (cómo correrlo, costo estimado, pre-requisitos).
- Actualicé toda la documentación para que quede coherente con el scope nuevo: README, RESUMEN, PROTOCOL, ROADMAP (lo reescribí entero porque estaba muy desactualizado), idea, BUDGET, EXPERIMENTS, STATUS, CLAUDE.md y los 9 componentes de la web. Los nuevos números son 42 celdas, 4.200 evaluaciones, 6 modelos.
- El código sigue aceptando `--size 26b` para que reactivar la sub-pregunta no requiera cambios.

**Qué esperaba vs. qué sucedió:**
- Esperaba que arreglar la traducción del chino fuera lo más sencillo del día. Lo fue.
- No esperaba el feedback del facilitador sobre el confounder de arquitectura. Tuvo razón: hubiera sido un problema serio al revisar el paper.
- Reescribir el ROADMAP entero fue más trabajo del previsto, pero dejó la documentación mucho más limpia (era el archivo más desactualizado del repo).

**Cómo cambia lo que pienso:**
- El scope reducido (3 Dense en vez de 4 modelos) hace el experimento más limpio metodológicamente y más rápido de cerrar. El paper queda con 3 puntos en la curva tamaño → compliance, suficiente para Spearman + bootstrap CIs.
- Tener `FUTURE_WORK.md` me saca presión: la sub-pregunta MoE no se pierde, queda registrada con plan de reactivación. Si los resultados principales son contundentes, el MoE se vuelve un follow-up natural.
- Mantener el `26b` en el código aunque esté out-of-scope es la decisión correcta: cuesta cero ahora y desbloquea la reactivación con un solo comando.

**Siguientes pasos:**
- Re-correr E2B con la matriz nueva (100 prompts × 7 idiomas, incluyendo DE) localmente.
- Continuar con E4B local.
- Levantar pod en RunPod para 31B Dense.
- Cerrar el judging con Claude Haiku sobre las 4.200 respuestas.

---

## 30 Apr 2026

**Qué hice:**
- Compré los 20 USD de API credits de Anthropic con la tarjeta de Dolar App.
- Verifiqué que los 4 modelos base de Gemma 4 son Apache-2.0: no hay que aceptar licencia.
- Preparé el entorno local (venv, dependencias, CUDA, API keys) y dejé todo listo para ejecutar el primer test con E2B.

**Qué esperaba vs. qué sucedió:**
- Esperaba más fricción con licencias y setup; salió todo más rápido de lo previsto.

**Cómo cambia lo que pienso:**
- Ya no hay bloqueantes operativos. Lo que sigue es correr.

**Siguientes pasos:**
- Correr la matriz local de E2B (6 idiomas × 2 condiciones) y juzgar con Claude Haiku.
- Mirar resultados y decidir si seguir con E4B local o pasar a RunPod.

---

## 22 Apr 2026

**Qué hice:**
- Recibí ayer el email de Joshua: ¡BlueDot aprobó el Rapid Grant de 350 USD!
- Actualicé la bitácora y el CLAUDE.md con el nuevo estado del proyecto.
- Revisé el BUDGET.md y el monto aprobado encaja perfecto con lo que pedí.
- Repasé el diseño experimental: entendí bien la matriz de 48 celdas (4 tamaños × 6 idiomas × 2 condiciones) y por qué comparamos base vs abliterated.
- Audité el script `02_run_inference.py` — seed, greedy, chat template OK. Encontré un bug: el argparse no acepta `26b`/`31b` (bloqueante para Fase 4).
- Escribí `PROTOCOL.md`: documento técnico que explica paso a paso cómo reproducir el experimento desde cero, con el porqué de cada decisión (por qué Gemma 4, por qué huihui-ai, por qué BeaverTails, por qué 6 idiomas, etc).

**Qué esperaba vs. qué sucedió:**
- Esperaba una respuesta sobre el grant pero no sabía si saldría. Salió aprobado por el monto completo.
- El grant desbloquea justo las fases que estaban pausadas por falta de compute.
- Pensaba que el pipeline estaba 100% listo; encontrar el bug de argparse me recordó que antes de gastar plata en RunPod hay que correr una auditoría seria.

**Cómo cambia lo que pienso:**
- El proyecto deja de estar "paused - awaiting funding". Ahora puedo avanzar.
- Alguien externo validó la idea con plata real. Es una señal fuerte de que el research vale la pena.
- Tener `PROTOCOL.md` me saca ansiedad: si mañana pierdo el contexto, el archivo me devuelve al mismo punto sin depender de memoria.
- Antes de pagar RunPod, voy a terminar primero Fase 3 local y mirar los resultados parciales. Si ya son contundentes en E2B+E4B, la Fase 4 es solo confirmación.

**Siguientes pasos:**
- Reclamar el grant en el portal de Airtable.
- Arreglar el bug del argparse en `02_run_inference.py`.
- Correr sanity check completo y después la matriz de Fase 3 (E2B + E4B × 6 idiomas × 2 condiciones = 24 corridas locales).
- Correr el judging con Claude Haiku sobre esos 24 archivos.
- Con los resultados parciales en la mano, decidir si arrancar Fase 4 (RunPod 26B + 31B).

**Bonus del día (tarde):**
- Arreglé el bug del argparse en los 5 scripts que lo tenían (`02` a `06`) — todos ahora aceptan `26b/31b`.
- Armé una página web en Astro para presentar el proyecto: `web/`. Es un sitio estático con flow lineal tipo paper (hero → resumen → problema → pregunta → hipótesis → método → matriz → resultados → escenarios → estado → financiamiento → referencias). Sigue los principios del informe (bajar términos técnicos a tierra antes de usarlos, anclar eventos en el tiempo, voz del autor explícita) y la identidad visual del design system (navy + amber + sage + terracota, Fraunces + Inter + JetBrains Mono). La matriz de 48 celdas está renderizada y lista para ir llenándose a medida que se completen corridas.

---

## 21 Apr 2026

Creé cuenta en Dolar App para poder recibir pagos en USD.
Llegó el email de BlueDot: grant aprobado por 350 USD (revisado hoy 22 Apr).

## 15 Apr 2026

Verifiqué si el reframe propuesto por Claude Code es válido.
Creé cuentas en Hugging Face y RunPod.
Ejecuté algunos tests y estructuré el GitHub repo.
Envié la solicitud de fondos a BlueDot.

## 13 Apr 2026

Empecé el GitHub repo + validé la idea con la skill.
https://github.com/gustipardo/multilingual-abliteration-slm-safety

## 11 Apr 2026

Determiné la idea y escribí su resumen.

## 10 Apr 2026

Consulté a facilitadores del curso sobre la idea propuesta.

## 9 Apr 2026

Con la info de Gemma 4 pensé cómo sus características se podrían relacionar con las ideas propuestas en el docs y dónde podía combinarlos.

## 8 Apr 2026

Analicé hacer un paper con Gemma 4, investigué sobre el tema.
