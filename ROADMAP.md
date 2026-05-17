# Multilingual Abliteration SLM Safety — Roadmap (actualizado 2026-05-14)

> Reemplaza la versión 2026-05-05. Esa versión describía el experimento principal en marcha; ahora todo el pipeline está cerrado y la pregunta operativa es publicación + análisis de seguimiento. Fuente de verdad para hyperparams: `configs/experiment.yaml`. Reproducción paso a paso: `PROTOCOL.md`. Resultados detallados: `EXPERIMENTS.md`. Trabajo diferido: `FUTURE_WORK.md`.

---

## Estado actual

**Pipeline principal: cerrado.** Las 42 celdas del experimento principal (3 sizes Dense × 7 idiomas × 2 condiciones = 42 cells, 100 prompts c/u = 4.200 evaluaciones) están completas en inferencia, judging y mecanística.

| Eje | Estado | Output |
|-----|--------|--------|
| Inferencia 3 sizes × 7 langs × 2 conds | 42/42 celdas | `data/outputs/{e2b,e4b,31b}_{base,abliterated}_{lang}.jsonl` |
| Judging Claude Haiku 4.5 | 42/42 celdas | `data/outputs/*_judged.jsonl` + `compliance_rates.csv` |
| Refusal directions + Silhouette | 3/3 sizes | `data/outputs/refusal_directions_{e2b,e4b,31b}.pt`, `silhouette_scores.csv` |
| Figures cross-size | regeneradas 2026-05-06 | `figures/size_vs_compliance.png`, `compliance_abliterated_heatmap.png`, `silhouette_heatmap.png`, `pca_*_*.png` |
| Cloud reproducibility check E2B | 12/14 celdas en RunPod (2 perdidas por terminación externa); drift ≤+8 pp en peores cells, headline intacto | `data/_runpod_e2b_2026-05-08/` + `EXPERIMENTS.md` §1 |

**Resultados clave (final):**

- Compliance media post-abliteración: E2B 42.9% → **E4B 68.1%** ← peak → 31B 64.4%. Curva **no-monotónica**: +25.3 pp E2B→E4B y luego −3.7 pp E4B→31B.
- Gap base→abliterado también pico en E4B: +57.4 pp (vs +38.8 E2B, +51.3 31B).
- Base compliance sí escala monotónicamente con tamaño (4.1% → 10.7% → 13.1%); las dos curvas se desacoplan en 31B.
- **Cosine cross-lingual de refusal directions también pico en E4B** (mean 0.37 vs 0.31 E2B, 0.27 31B). La geometría predice el comportamiento.
- Silhouette monotónicamente decreciente en size (0.29 → 0.26 → 0.23): el "concepto de harm" interno se difumina con escala.
- Hindi consistentemente el más seguro de los 7 idiomas en cada size; refuta la lectura ingenua "low-resource = más vulnerable".
- E4B abliterated max = 74% (PT, DE) — es el cell del experimento más cercano al 80-90% que reporta Wang et al. para 7B+.

**Gasto a la fecha:** ~$41 RunPod + ~$3.30 Anthropic = ~$44 del grant de $350 BlueDot. Dentro de presupuesto.

---

## Hacia publicación

### P0 — Inminente (blog post + presentación BAISH)

Objetivo: cerrar la comunicación principal en 2 semanas, sin nuevos experimentos.

1. **Blog post (`BLOG_POST.md`).** Draft v1 ya escrito al 13 May 2026 (working draft, 28.7 KB). Falta:
   - Pasada final de prosa siguiendo `WRITING_PREFERENCES.md` (terminología bajada a tierra antes de usar términos, voz del autor, anclaje temporal de eventos).
   - Revisar Figura 1 (`size_vs_compliance.png`) — confirmar que el peak en E4B se lee a primera vista.
   - Apéndice A (compute + cloud reproducibility): mover los detalles de drift por celda desde `EXPERIMENTS.md` §1.
   - **Decisión pendiente:** ¿publicar en LessWrong, Alignment Forum, o sitio propio? (ver "Decisiones pendientes").
2. **Presentación BAISH (`presentacion-talk.html` + `TALK_SCRIPT.md`).** Slides HTML al 13 May 2026 listos. Falta:
   - Ensayo cronometrado (target: 20-25 min + Q&A).
   - Definir fecha con facilitadores BAISH.
3. **Reporte BlueDot.** Pendiente. Formato y deadline a confirmar con Joshua. Tentativamente: blog post + tabla de gastos + 1 párrafo sobre próximos pasos.
4. **Subir outputs a HuggingFace público (no privados).** Hoy `gustipardo/abliteration-{size}-{results,mechanistic}` están privados; pasarlos a públicos para reproducibilidad del paper.

### P1 — Siguiente paso académico (workshop / conferencia)

Objetivo: convertir el blog post en preprint con evidencia adicional.

1. **Experimento Recipe-comparison (Mechanism #3).** Es el único experimento que **adjudica** entre Mechanism #1 (geometría concentrada en mid-size Dense) y Mechanism #3 (recipe-driven). Plan: re-extraer refusal directions con el método "lab variant" de Wang et al. 2025 sobre los mismos 6 checkpoints. Si el peak E4B persiste con la otra recipe → es geometría (#1). Si desaparece → es artefacto de la receta huihui-ai (#3). **Costo estimado:** ~1h RunPod RTX 5090 × 3 sizes = ~$3 + ~$0.50 Anthropic = ~$4. **Bloqueante para preprint serio.**
2. **Validación a mano de la "delayed refusal" en una sub-muestra.** N≈50 respuestas borderline, eyeballing por humano para estimar precisión del judge Claude Haiku. Refuerza la confianza en los headline numbers.
3. **WildGuard como segundo judge (paridad con Wang et al.).** El BUDGET reserva $50 para esto. Re-juzgar las 4.200 respuestas con WildGuard, comparar con Haiku. Si hay drift sistemático lo reportamos; si no, refuerza el resultado.
4. **Target preprint:** arXiv + workshop NeurIPS 2026 SafeML / SoLaR / TML. Decisión sobre cuál: depende de fechas de submission (chequear cuando esté el draft).

---

## Experimentos pendientes

Ordenados por urgencia. Costos asumen RunPod RTX 5090 SECURE @ $0.99/hr + Claude Haiku 4.5 @ ~$0.25/MTok.

| # | Experimento | Costo | Tiempo | Estado | Por qué |
|---|-------------|-------|--------|--------|---------|
| 1 | Recipe-comparison (Wang et al. lab variant) sobre 6 checkpoints | ~$4 | ~3h compute + 1h Anthropic | Diseño pendiente | Adjudica Mech #1 vs #3 — bloqueante para preprint |
| 2 | E2B AR + HI abliterated re-run **local** (cerrar reproducibility check) | $0 | ~2h laptop | Pendiente | Cierra los 2/14 huecos de la corrida cloud E2B; sin RunPod porque las 3 pods anteriores tuvieron terminación externa misteriosa |
| 3 | WildGuard como segundo judge sobre las 4.200 respuestas existentes | ~$0 + $50 access | ~1 día | Diseño pendiente | Paridad metodológica con Wang et al. — segundo judge robustifica |
| 4 | **MoE sub-question** (Gemma 4 26B-A4B inference + judging + mecanística) | ~$5 + ~$1 | ~5h | Diferido a `FUTURE_WORK.md` §1 | Sub-pregunta novedosa (¿activos vs densos cambia la geometría de safety?), pareo natural con E4B |
| 5 | Bootstrap CI para per-cell compliance y Spearman size×compliance | $0 | ~2h local | Pendiente | Necesario para reporte estadístico del paper |

**No correr:** ningún tamaño nuevo de Gemma 4 (no hay), ningún idioma nuevo (los 7 ya cubren families + resource levels), ningún re-run de cells ya completas excepto si la recipe-comparison lo requiere.

---

## Análisis pendiente

Datos crudos sobran; faltan vueltas analíticas sobre lo ya producido.

1. **Spearman tamaño × compliance + CIs.** Con 3 puntos el rank-correlation es débil estadísticamente; reportar con CI claro y discutir la limitación. Datos en `compliance_rates.csv`.
2. **Bootstrap CI per-cell.** N=100 por cell → SE binomial ≈ ±5 pp. Hacer bootstrap 1000× sobre prompts para CIs reales (no asume binomial). Script no existe aún; crear `scripts/07_bootstrap_ci.py`.
3. **Análisis layer-by-layer de refusal direction.** Hoy `04_compute_refusal_directions.py` extrae la dirección en el layer pico por size. Falta plot multi-layer × multi-size mostrando dónde vive la dirección y si la profundidad relativa cambia con scale. Datos crudos están en los `.pt`.
4. **Per-language cosine matrices side-by-side.** Hoy `figures/cosine_*` están por size separado. Falta una figura 3×3 (size × size) o 3-panel para el blog post mostrando que la matriz E4B es más uniforme/brillante que E2B y 31B.
5. **Correlación cosine cross-lingual ↔ compliance por celda.** Para cada (size, lang), ¿la cosine promedio de ese idioma con los otros 6 predice su compliance abliterado? Hipótesis: lang con cosine alto → más vulnerable. Se chequea en 5 minutos con `compliance_rates.csv` + `cosine_similarity_*.csv`.
6. **PCA visual cross-size en una sola figura.** Hoy hay 7 PCAs por size = 21 PNGs. Para el blog post conviene 1 figura compacta side-by-side.
7. **Análisis de tipos de prompts donde abliteración falla más vs menos.** BeaverTails tiene categorías (hate, drugs, sexual, etc.). ¿Hay categorías donde el peak E4B no se sostiene? Datos están en los jsonls (`metadata.category`).

---

## Comunicación

| Canal | Estado | Próximo paso |
|-------|--------|--------------|
| `bitacora.md` (BAISH facilitators, Google Doc espejo) | Última entrada 8 May 2026 | Entry de hoy 14 May cubriendo: cloud E2B check cerrado, blog post v1, presentación HTML, roadmap actualizado |
| Blog post (`BLOG_POST.md`) | Draft v1 13 May 2026 | Pasada final de prosa + decidir venue (LW / AF / propio) |
| Presentación BAISH (`presentacion-talk.html`, `TALK_SCRIPT.md`) | Slides + script listos 13 May | Ensayo cronometrado + agendar fecha |
| Reporte BlueDot ($350 grant) | No iniciado | Confirmar formato/deadline con Joshua; tentativamente blog + tabla gastos |
| Preprint (arXiv + workshop) | No iniciado | Bloqueado por recipe-comparison (P1 #1); abrir doc apenas haya draft de blog limpio |
| Repo GitHub público | Actualizado al 13 May | Pasar HF datasets a públicos (hoy son privados) |
| Twitter / posteo de difusión | No iniciado | Esperar a que blog esté publicado |

---

## Out-of-scope

Lo que **no** se hace en este experimento, documentado para que no se confunda con TODO:

- **Modelos no-Gemma-4** (Llama, Qwen, Yi, Mistral, etc.). Wang et al. ya los cubre 7B+; el aporte nuestro es dentro de Gemma 4 Dense.
- **Sizes <2B o entre 4B y 31B.** No existen en el lineup Gemma 4.
- **Idiomas adicionales** más allá de los 7 elegidos (EN, ES, ZH, PT, DE, AR, HI). Los 7 ya cubren families + resource levels; más idiomas no agregan información proporcionalmente.
- **Otros tipos de jailbreak** (DAN, prompt injection, GCG, etc.). Scope = abliteración como amenaza pública concreta, no jailbreak en general.
- **Re-entrenar / re-abliterar internamente.** Usamos los checkpoints públicos huihui-ai porque son el threat model real. Re-abliterar nosotros sería otra investigación.
- **Recovery / safety training post-abliteración.** Hay literatura propia sobre re-alinear modelos abliterados; fuera de scope.
- **Gemma 4 26B-A4B MoE** en el experimento principal. Diferido a `FUTURE_WORK.md` §1 como sub-pregunta separada.

---

## Decisiones pendientes (solo Gusti)

Ordenadas por urgencia, no por importancia.

1. **Venue del blog post.** LessWrong (audiencia AI safety nativa, pero el formato es post-largo) vs Alignment Forum (más técnico, gating fuerte) vs sitio propio en `web/` (control total, menos alcance). **Recomendación tentativa:** LW para alcance + crossposting a AF.
2. **¿Correr recipe-comparison (P1 #1) **antes** de publicar blog post, o después?** Pros de antes: el blog post se vuelve más fuerte si Mech #1 vs #3 ya está adjudicado. Pros de después: blog post sale rápido, recipe-comparison alimenta el preprint. **Sesgo personal:** publicar antes, el blog post no necesita adjudicar todo.
3. **¿Cerrar las 2 celdas AR + HI cloud E2B?** Costo $0 (correr local), valor: cierra la auditoría de reproducibilidad. Pero el headline ya está intacto sin ellas. Decidir si se hace antes del blog post o como follow-up post-publicación.
4. **¿Activar el experimento MoE (`FUTURE_WORK.md` §1) antes o después del preprint?** Si va antes, el preprint tiene 4 puntos y la sub-pregunta MoE integrada. Si va después, queda como follow-up paper.
5. **Reporte BlueDot: ¿formato libre o pedir template a Joshua?** Pedir template para no improvisar.
6. **Token rotation pendiente** desde el run E4B (HF, Anthropic, RunPod expuestos en env vars del pod). **Housekeeping**, hacer esta semana.

---

## Cross-references

- `README.md` — pipeline overview y entry points (English).
- `EXPERIMENTS.md` — log completo de todas las corridas con timings, costos, drift analysis.
- `BLOG_POST.md` — draft de publicación principal.
- `BUDGET.md` — desglose del grant BlueDot, números reales vs estimados.
- `FUTURE_WORK.md` — sub-preguntas diferidas (MoE; mecanística diferida ya cerrada).
- `bitacora.md` — log de sesiones (español), espejado a Google Doc compartido con BAISH.
- `STATUS.md` — snapshot auto-generado de la matriz.
- `WRITING_PREFERENCES.md` — guía de estilo para blog/paper.
- `TALK_SCRIPT.md`, `presentacion-talk.html` — presentación BAISH.
- `PROTOCOL.md` — protocolo reproducible paso a paso (español, técnico).
- `principios-informe.md` — principios de comunicación para el reporte.

---

## Contradicciones encontradas entre archivos (al actualizar)

1. **`FUTURE_WORK.md` §2 todavía describe la mecanística diferida** ("Análisis mecanístico de 31B Dense... quedó diferido"). En realidad la mecanística de E4B y 31B se completó el 2026-05-06 (ver `EXPERIMENTS.md` §2). El archivo `FUTURE_WORK.md` deberia actualizarse: §2 está cerrado, solo §1 (MoE) sigue abierto. **No lo modifiqué en esta pasada** porque el pedido era actualizar solo `ROADMAP.md`.
2. **`BUDGET.md` línea 32** dice "E2B cloud reproducibility re-run... 12/14 cells salvaged" — consistente con `EXPERIMENTS.md` §1. OK.
3. **`README.md` línea 5** dice "mechanistic done" (consistente). **Línea 209** linkea a `ROADMAP.md#phase-4-cloud-runs` que era anchor de la versión anterior; ya no existe esa sección (este ROADMAP nuevo no usa "Phase 4"). Link queda roto. **No lo modifiqué** porque era pedido no modificar otros archivos; flaggeo para futura sesión.
4. **`ROADMAP.md` previo (2026-05-05)** dice "Phase 7 — Paper writing — 🟦 next" pero a hoy hay un blog post v1 (13 May) en `BLOG_POST.md` que es la unidad de publicación elegida primero, no un paper directo. La estrategia cambió: blog → preprint, no directo paper. Reflejado en este nuevo roadmap.
