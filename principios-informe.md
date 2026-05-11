# Principios y reglas del informe — Flashcards Conversacionales

> Destilado de los comentarios del tutor en el Google Docs (marcados con `==`) + guía del autor.
> **Usar como checklist antes de cerrar cualquier versión del informe.**
> Estos principios son **transversales**: aplican a todo el documento, no solo a las secciones donde el tutor dejó el comentario.

---

## 0. Reglas críticas — SIEMPRE aplican antes de cualquier otra

> El tutor las marcó como **load-bearing** en la reunión del 9 mayo 2026 (revisión del Blog Post de multilingual-abliteration). Antes de aceptar cualquier otro principio del documento, verificar que el texto cumple estas dos.

### 0.1 Calibración de claims — matchear la fuerza del claim a la fuerza de la evidencia

**No hacer afirmaciones fuertes cuando la evidencia es débil.** En AI safety y en escritura técnica, *hedge language es una feature*, no una debilidad. Mismatchear el tipo de claim con la evidencia es la forma más rápida de perder confianza del lector.

Antes de cada oración con un claim, preguntar:

- ¿Cuántos data points lo respaldan? Si 1-2, es *existence-proof*, no *systematic*.
- ¿La diferencia está fuera del ruido? Si es 1-3 pp con SE pooled de ~1.8 pp, **hedge it explícitamente** ("a small but consistent" / "within noise" / "in this exact setup").
- ¿Testeé la negación? Si no, decirlo de entrada: "we did not test X".
- ¿La evidencia es post-hoc (los resultados ya estaban a la hora de escribir)? Marcar como *consistent with* o *one possible reading*, NUNCA como *prediction*.

Tipos de claim, ordenados de débil a fuerte (de la *Blog Post Writing Guide* de BlueDot):

| Tipo | Cuándo | Hedge correcto |
|------|--------|----------------|
| Existence-proof | "≥ 1 caso donde X pasa" | "we found at least one cell where..." |
| Systematic | "X pasa en muchos contextos" | requiere n alto, varios models/settings |
| Hedged | "compelling / suggestive / tentative evidence" | "consistent with" / "the data lean toward" |
| Narrow | "X es mejor en estas condiciones específicas" | "in this exact setup, ..." |
| Guarantee | "X siempre" | casi nunca apropiado en deep learning |

**Heurística:** leer cada oración con un claim y preguntar "¿qué evidencia exacta lo soporta, y esa evidencia justifica esa fuerza?". Detalle completo en §11.3 más abajo.

### 0.2 Vocabulario democratizado — bajar a tierra antes de usar el término

**Todo término técnico o jerga se presenta primero conectándolo con una experiencia familiar; recién después se puede usar libremente.** Si no podés bajar el término a tierra en una oración corta, **no lo uses todavía**: explicalo primero, o reemplazalo por una frase plana.

Fórmula: `[experiencia concreta familiar] + "esa/eso es [término técnico]"`

Términos del proyecto multilingual-abliteration que necesitan grounding antes de su primer uso:

- **abliteration** → "técnica pública de jailbreak que..."
- **refusal direction** → "una sola dirección dentro del 'espacio mental' del modelo que dispara el rechazo"
- **cosine similarity** → "una medida de qué tan paralelas son dos flechas: 1 = misma dirección, 0 = sin relación, negativo = opuestas"
- **Silhouette score** → "qué tan limpiamente se separan dos grupos en el espacio interno del modelo"
- **non-monotonic** → "la curva no sube siempre con el tamaño; sube y baja"
- **residual stream** → "el 'stream de pensamiento' interno que el modelo va construyendo capa por capa"

**Audit rule:** después de escribir un párrafo, listar cada palabra no-cotidiana y preguntar "¿está bajada a tierra antes de su primer uso?". Si no, fix. Detalle completo en §2.1 más abajo.

---

## 1. Lectura por perfiles (principio rector)

El informe debe poder ser leído cómodamente por **cualquier perfil**: técnico (programador, analista), no técnico (marketer, stakeholder, contable), usuario final, inversor, docente, futuro lector desconocido.

### Reglas

- **Separar párrafos y subtítulos por tipo de contenido**, de modo que cada perfil pueda **saltear** lo que no le interesa sin perder el hilo.
- **No mezclar** dentro del mismo párrafo descripción funcional ("qué hace la app") con descripción técnica ("cómo lo hace"). Dividir.
  - Ej.: la "solución concreta" (qué experimenta el usuario) va en una subsección; la "solución técnica" (WebRTC, Firebase, Foreground Service, etc.) va en otra subsección con subtítulo explícito.
- Si un párrafo/subtítulo es **técnico**, ir a fondo — así el técnico se queda y el resto saltea sin culpa. No hacer párrafos "medio técnicos" que aburren al no-técnico y frustran al técnico.
- Los subtítulos deben **anunciar el perfil al que hablan**. Un lector debe poder hacer índice mental con solo leer los títulos.

---

## 2. Lenguaje y terminología

### 2.1 Bajar a tierra antes de usar un término complejo

Todo término técnico, académico o jerga (fricción, repetición espaciada, dificultad cognitiva deseable, curva del olvido, ContentProvider, ephemeral token, foreground service, GEO, gamificación, etc.) debe **presentarse primero** conectándolo con una experiencia cotidiana, y **después** se puede usar libremente.

**Fórmula:** `[experiencia concreta y familiar] + "esa/eso es [término técnico]"`

- ❌ Mal: "Este proyecto nació de esa fricción."
- ✅ Bien: "El esfuerzo extra que te cuesta sacar el teléfono, desbloquearlo y mirar la carta mientras caminás — esa **fricción** — es lo que este proyecto ataca."

Una vez establecido el puente, el término queda disponible para el resto del documento sin re-explicarlo.

### 2.2 Lenguaje natural antes que culto

Preferir sinónimos comunes y regionalismos cuando mejoran comprensión: "trastes" o "platos sucios" en vez de solo "quehaceres domésticos"; "molestia" como sinónimo accesible de "fricción" cuando cabe. El informe no es un paper — es un documento persuasivo que además resiste el escrutinio técnico.

### 2.3 Imágenes para conceptos físicos

Si el concepto tiene representación visual, **agregar imagen**: flashcard física, curva del olvido, captura de AnkiDroid, diagrama de arquitectura. Una imagen suele bajar a tierra mejor que un párrafo.

---

## 3. Alcance del informe vs alcance del MVP

### Regla central

**El informe no está delimitado al MVP.** El MVP es **una sección** del informe, no el filtro que recorta todo lo demás.

- Al definir la solución, hablar de la **visión del producto** (agnóstico a la app, multiplataforma, multi-asistente de voz: auto, Alexa, CarPlay, Android Auto, Tesla, iOS, web, etc.).
- Al definir el MVP, **delimitar explícitamente** el recorte: "Para validar la hipótesis, el MVP se limita a Android + AnkiDroid + suscripción mensual. La elección de React Native + Expo mantiene al código agnóstico, habilitando expansión posterior a iOS sin reescritura".
- **Justificar toda restricción.** Cada "solo X" del informe debe responder a "¿por qué no Y?":
  - ¿Por qué solo Android? → Por dónde está el 99% de usuarios AnkiDroid + validación antes de iOS.
  - ¿Por qué solo móvil? → Por ser donde ocurre la fricción que atacamos; expansión natural es Android Auto, Alexa, etc.
  - ¿Por qué nativo? → ContentProvider de AnkiDroid exige Kotlin; el resto del stack es cross-platform.

### Corolario

Nunca escribir "la app hace X" cuando se refiere a "el MVP hace X". Usar los dos términos con precisión.

---

## 4. Anclar siempre en el tiempo

### Regla

**Si alguien lee este informe en 15 años, ¿entiende el contexto temporal?**

- Referencias a tecnología emergente siempre con año: "las APIs de conversación por voz en tiempo real alcanzaron viabilidad comercial entre **2024 y 2025**".
- Referencias a eventos, discusiones, decisiones de otros actores con fecha: "en **octubre de 2024**, David Allison confirmó en Reddit…".
- Al mencionar "actualmente", "hoy", "reciente" → agregar la fecha absoluta del informe (2026) para que el lector futuro reinterprete correctamente.
- Menciones de métricas de mercado (downloads, MAU, precios) con la fecha en que se tomaron.

---

## 5. Evidencia y fuentes

### Regla

Toda afirmación fuerte sobre el mercado, los usuarios o la competencia necesita **fuente verificable**. Reddit, foros, issues de GitHub, reportes públicos funcionan — y son más creíbles para un tutor/jurado que afirmaciones sin respaldo.

- ✅ "Discusión en r/Anki con 200+ upvotes donde usuarios piden modo voz" (linkear).
- ✅ "Comentario de David Allison (dev oficial AnkiDroid) en hilo X" (linkear).
- ✅ Capturas/quotes de workarounds caseros documentados (plugins TTS + Bluetooth, scripts con Whisper, VoiceAttack).
- ❌ "Existe demanda del mercado" sin evidencia.

Cuando haya espacio, citar **qué dijeron los usuarios**, no solo que existen.

---

## 6. Anticipar objeciones del lector

### Regla

Si una frase puede disparar una objeción obvia en la cabeza del lector, **abordarla explícitamente** en el mismo pasaje — no dejar al lector con la duda.

Ejemplos detectados por el tutor:

- "Estudiar sin mirar la pantalla" → el lector piensa "¿manejando?". Abordarlo: advertencia explícita + analogía del "alcohol antes de manejar: se puede, no se debe", dejando la decisión al criterio del usuario. Posiblemente cubrirlo en términos y condiciones.
- "Anki no implementa modo voz" → el lector piensa "si es buena idea, ¿por qué el líder no la hizo?". Abordarlo: citar la respuesta oficial (preocupaciones de seguridad vial) y justificar por qué un tercero sí puede asumir ese riesgo con disclaimers.
- "Solo Android" → el lector piensa "¿y los demás dispositivos?". Abordarlo: explicar MVP vs visión, stack agnóstico, ruta de expansión.

**Heurística:** leer cada párrafo con el sombrero de un lector hostil. Cualquier "¿y qué pasa con…?" que aparezca debe tener respuesta en el texto.

---

## 7. Voz del autor

### Regla

**Agregar punto de vista propio** — no solo exponer hechos. El informe es un trabajo del autor, no un reporte neutro de Wikipedia.

- Opiniones justificadas ("a mi criterio…", "creo que…", "mi apuesta es…") cuando corresponde.
- Llamados al pensamiento del lector ("pensalo así…", "comparalo con…").
- Analogías propias (ej. alcohol/conducción como paralelo al modo voz).
- Dejar claro qué decisiones son apuestas y por qué.

---

## 8. Qué va en el informe principal vs qué va aparte

### Regla

El informe principal es **el documento general**. Todo contenido que sea:

- Muy específico de un perfil técnico estrecho,
- Muy largo en detalle operativo,
- Con vida propia (reutilizable en otros contextos),

→ debe ir en **archivo separado** y referenciarse desde el informe con un resumen + link.

Ejemplos:

- ✅ **Pitch**: ya vive en archivo separado (bien).
- 🤔 **Casos de uso completos**: ¿deberían estar extensos en el informe, o resumidos + anexo? Evaluar.
- 🤔 **Plan de validación MVP**: vive en `MVP_validation_plan.md` → resumir en informe, no duplicar.
- 🤔 **Arquitectura técnica detallada**: probablemente anexo técnico.

**Criterio práctico:** si al leer una sección, un perfil no-técnico piensa "esto me lo podría haber dado en 3 líneas" → la sección es candidata a extraerse.

---

## 9. Pitch físico (tip específico, vale como recordatorio)

Al momento de presentar/pitchear el proyecto: **llevar una flashcard física** y presentarla. Es el anclaje físico definitivo del concepto.

---

## 10. Checklist de revisión por versión

Antes de cerrar cualquier revisión del informe, recorrerlo haciéndose estas preguntas:

- [ ] ¿Un **marketer** puede leer solo la parte no-técnica y entender el proyecto?
- [ ] ¿Un **programador** puede leer solo la parte técnica y tener suficiente detalle?
- [ ] ¿Un **inversor** encuentra rápido: problema, solución, mercado, diferenciación, validación, monetización?
- [ ] ¿Un **usuario** entiende qué experimenta, sin necesidad de entender cómo está hecho?
- [ ] ¿Todos los **términos técnicos** se bajaron a tierra antes de usarse libremente?
- [ ] ¿El informe habla de **MVP solo en la sección de MVP**, y en el resto habla de la visión general?
- [ ] ¿Toda **restricción** ("solo Android", "solo móvil", "solo suscripción") tiene su por qué explícito?
- [ ] ¿Toda afirmación **de mercado o de usuario** tiene fuente (link a Reddit, foro, stats)?
- [ ] ¿Las referencias a **tecnología/eventos** tienen año absoluto?
- [ ] ¿Aparece la **voz del autor** (opinión, apuesta, criterio)? ¿No es un reporte neutro?
- [ ] ¿Anticipé las **objeciones obvias** (conducir, por qué el líder no lo hizo, alcance)?
- [ ] ¿Hay **imágenes** donde el concepto es físico/visual (flashcard, curva, arquitectura)?
- [ ] ¿Lo que está en el informe principal **merece estar ahí** vs en archivo separado?
- [ ] ¿Un lector en **2041** entendería el contexto temporal?

---

## 11. Reglas para blog posts y reportes técnicos de investigación

> Adicional a las reglas 1 a 10 (que aplican siempre). Esta sección consolida lo aprendido al redactar el blog post de *multilingual-abliteration-slm-safety* (mayo 2026), mezclando: (a) la *Blog Post Writing Guide* de los facilitadores BAISH/BlueDot, (b) el análisis del paper de referencia Wang et al. 2025 *"Refusal Direction is Universal Across Safety-Aligned Languages"* (NeurIPS 2025), y (c) reglas estilísticas del autor para escribir en inglés sin sonar a IA.

### 11.1 Audiencia y foco

- **Definir audiencia primero.** Para AI safety: investigadores de safety + ML practitioners sin background safety. Calibrar jerga, definiciones, framing y motivación a ese grupo.
- **Un solo takeaway principal.** Decidir la frase única que querés que el lector se lleve, y hacer que el post entero apunte a ella desde el título hasta la conclusión. Un lector que sólo skimea debe llevarse esa frase.
- **Esfuerzo concentrado en Figure 1 y TL;DR.** La mayoría de los lectores sólo leen eso. Casi todo el esfuerzo de redacción y diseño va ahí.
- **Escribir para un lector con cero contexto.** Vos tenés meses de proyecto en la cabeza; el lector no tiene nada. Cada frase debe leerse sin haber leído las anteriores del proyecto.

### 11.2 Estilo "human, no AI"

Reglas estilísticas explícitas para que el texto no se lea como output de un LLM. Si una de estas se viola, vuelve a sonar genérico aunque el contenido sea correcto.

- **Cero em dashes (`—`)**. Es el tic más reconocible de IA en inglés. Reemplazar por punto, coma, paréntesis, dos puntos, o reestructurar la frase.
- **Cero en dashes (`–`) en prosa.** Sólo en rangos numéricos (e.g. `2024–2025`). En prosa usar "to" o "a".
- **Cero emojis.** En ninguna sección. Tampoco ✓/✗/⚠ como "tildes". Si necesitás marcar estado en una tabla, usar palabras: `done`, `pending`, `deferred`.
- **Evitar palabras gatillo.** Estas marcan output de IA en inglés: *furthermore, moreover, importantly, notably, it is worth noting, delve, leverage, robust, comprehensive, in conclusion, essentially, fundamentally, intricate, paradigm, navigate the landscape*. Si hace falta una transición, una frase corta declarativa funciona mejor.
- **Bullet lists con bullets de verdad.** Cada bullet es una oración completa que se lee sola. No usar bullets como "items breves de una lista" cuando el contenido pide prosa.
- **Negrita escasa.** Sólo donde el lector que skimea debe parar. Si todo está en negrita, nada lo está.
- **Listas de tres ítems sólo cuando hay tres ítems reales.** No inventar el tercero por ritmo retórico.

### 11.3 Tipos de claim y calibración

Un *claim* (Neel Nanda) es una statement específico, evidence-backed, de conocimiento nuevo que querés que el lector crea y recuerde. El post se construye alrededor de **1 a 3 claims** y todo lo demás los justifica.

Cinco tipos, ordenados de más débil a más fuerte. **El tipo del claim debe matchear la fuerza de la evidencia**; mismatchearlo erosiona confianza más rápido que cualquier otra cosa.

| Tipo | Cuándo usar | Ejemplo |
|------|-------------|---------|
| Existence-proof | "Encontramos al menos un caso donde X pasa" | Un solo modelo donde la abliteration cumple > 90% |
| Systematic | "X pasa generalmente en un rango amplio de contextos" | "En 9 de 10 modelos 7B+, X" |
| Hedged ("compelling / suggestive / tentative evidence") | La evidencia apunta una dirección pero no la fija | El hedge debe matchear la fuerza |
| Narrow | "X es la mejor opción **en estas condiciones específicas**" | Restringís scope a cambio de poder afirmar más fuerte |
| Guarantee | "X es siempre cierto" | Casi nunca apropiado en deep learning |

### 11.4 Estructura del post (en este orden de **lectura**)

1. **Title.** Describe el hallazgo, no el tema. *"Abliterated Gemma 4 Dense Complies with Harmful Prompts Most at 4B"*, no *"On Multilingual Safety in Gemma 4"*.
2. **TL;DR (obligatorio).** Bullet list scaneable. Cada bullet se entiende solo. Incluir: setup del campo (1-2 líneas), motivación, contributions (1-3 claims con evidencia core), impact (cómo actualizar creencias), link al código.
3. **Figure 1 (obligatorio).** "Hero figure" arriba que resume el método o resultado principal. Caption dice **qué muestra Y el takeaway**, no sólo el label.
4. **Introduction.** Beats: contexto + motivación → background técnico → gap → research question (planteada como pregunta) → contribution con calificadores → preview de la evidencia más fuerte → impact. Si tenés varios claims, repetir Contribution + preview por claim. Para AI safety, **nombrar el threat model y el failure mode específico**.
5. **Methods (recomendado).** Detalle suficiente para que un lector competente reproduzca. Modelos, datasets, métricas, decisiones de setup no obvias. Hyperparámetros principales en main text, el resto al appendix. Describir **qué hicimos**, no **cómo se implementa con pandas**.
6. **Results.** Liderar con el resultado principal que responde la RQ; los soporting van después. Tablas y figuras antes que prosa para findings cuantitativos. **Reportar resultados negativos y nulos**, no cherry-pickear. La prosa interpreta, no repite los números de la tabla.
7. **Discussion.** Responder la RQ explícitamente (full / parcial / no). Revisitar la motivación. Limitaciones (ver 11.5). Calibrar claims (ver 11.6).
8. **Related Work (opcional).** 2-3 líneas de trabajo más relevantes. Por cada uno: una línea de qué hicieron, una de cómo difiere/se construye sobre ellos.
9. **Future Work (recomendado).** Al menos 2-3 follow-ups concretos. Experimentos específicos, no wishlists vagas.
10. **Acknowledgements (opcional).** Con consentimiento explícito antes de nombrar a alguien.
11. **Appendix (opcional).** Lo que soporta un claim del main text pero es muy largo (tablas de hyperparams, ablation grids, prompts completos). Lo que tu main claim depende de **debe estar en el main text**, no en el appendix.

### 11.5 Limitaciones up front

Esta es la regla más violada y la más cara cuando se viola.

- **Incluir todas las limitaciones relevantes**, incluso las incómodas. Ejemplo: "evaluamos sólo una receta de abliteración pública y un solo juez; no sabemos si el efecto generaliza".
- **No omitir** una limitación porque debilita el resultado. En AI safety, honestidad epistémica > paper más fuerte.
- Formato: bullet list separado en la sección Discussion. Cada bullet 1 a 3 líneas.

### 11.6 Calibración de claims (showed / believe / speculate)

Distinguir explícitamente qué tan fuerte es cada afirmación.

- **What we showed.** Lo que la evidencia respalda directamente. Números medidos en este experimento.
- **What we believe but did not show.** Lo que es la lectura más razonable de los datos pero requiere experimentos adicionales para confirmar.
- **What we speculate.** Predicciones que extrapolan más allá de lo medido.

Estas tres categorías van como bullets explícitos al final de Discussion. No mezclar.

### 11.7 Citations

- Inline, hyperlinked, formato APA author-year. El link va sobre la cita. Ejemplo: `As in [Zou et al. 2023](https://arxiv.org/abs/2307.15043), we define...`
- **Verificar que la cita dice lo que afirmás.** No paraphrasear de memoria; abrir el paper. Errores comunes: atribuir a Wang el judge que usó otro grupo, decir "tested only 7B+" cuando el paper testeó 2B-70B.
- Si no estás 100% seguro de los autores, citar por título + año con link (`[An embarrassingly simple defense (2025)](url)`) en lugar de inventar autores.

### 11.8 Anti-overclaiming

- **Inform, don't persuade.** Hacer matchear el lenguaje a la evidencia. Hedged language es **una feature** cuando está justificado. Overclaiming es la forma más rápida de perder a los lectores que más querés.
- Hedge words que matchean evidencia: *consistent with*, *suggests*, *plausibly*, *small but consistent*, *one possible reading*.
- Asserciones nudas sólo cuando los datos las soportan directamente.

### 11.9 Toda oración debe ser verdadera

Fact-checkear cada afirmación factual del post: prior work, números, definiciones, resultados propios. **Sin exageraciones.** Si no estás seguro: verificalo, calificalo, o eliminalo. Una sola afirmación falsa es suficiente para que el lector pierda la confianza en el resto.

Aplicar esta regla a **cada oración en cada sección**, no sólo a las "clave".

### 11.10 Anticipar al lector escéptico

Imaginá al lector buscando agujeros. Cada claim debe ser uno que pueda seguir y verificar. Anticipar las objeciones obvias y responderlas en el texto, no esperar a que las plantee.

Patrón útil para findings contraintuitivos: presentar la objeción como "Si pensabas X, los datos no soportan X porque Y". Hacerlo dos veces, una para cada framing previo posible (e.g. "si pensabas que small = más vulnerable... si pensabas que big = más vulnerable...").

### 11.11 Workflow de redacción

Las dos sub-reglas que más rinden por minuto invertido:

- **Una capa por pasada.** Las pasadas son: armar el argumento, estructurar el post, escribir prosa, pulir wording, fixear gramática. Trying todo a la vez = working memory full = todo peor. Una capa, una pasada.
- **Review en dos passes.** Primera pasada *macro*: argumento, estructura, flujo entre secciones. Segunda pasada *micro*: word choice, gramática, citations. Mezclarlas desperdicia tiempo y energía mental.

**Orden de redacción** (distinto del orden de lectura del lector):
1. Definir core claims (1-3, con una línea de evidencia y una de por qué importa)
2. Outline en bullets (no prosa todavía)
3. Figures, especialmente Figure 1
4. Results (main result primero, después soporting)
5. Methods
6. Discussion (RQ + limitaciones + calibración)
7. Related Work
8. Introduction (penúltima de las largas; necesitás saber dónde terminaste para hacer bien el roadmap)
9. TL;DR (última)

El title se puede draftear en cualquier momento del proceso.

### 11.12 Pre-publish checklist (de la guía BlueDot)

Antes de cerrar cualquier versión:

- [ ] Cada oración, en cada sección, fue verificada por accuracy factual, sin exageraciones.
- [ ] Cada oración, en cada sección, es legible para alguien sin exposición previa al proyecto.
- [ ] El trabajo está comprimido a 1-3 claims, cada uno emparejado con evidencia.
- [ ] Las objeciones obvias del lector escéptico están anticipadas y respondidas en el texto.
- [ ] El title describe los findings, no sólo el tema.
- [ ] El TL;DR es una bullet list scaneable, se lee solo, y nombra la pregunta + el método + la respuesta.
- [ ] El threat model y la relevancia para AI safety son explícitos en el Introduction.
- [ ] Todas las limitaciones relevantes están en Discussion, sin omitir las incómodas.
- [ ] Los claims están calibrados: what showed / what believe / what speculate, distinguidos.
- [ ] Cada figura tiene un caption que se lee solo (qué muestra + takeaway).
- [ ] El código está linkeado desde el post.
- [ ] **Cero em dashes, cero emojis, cero palabras gatillo de la 11.2.**

### 11.13 Compatibilidad con las reglas 1-10

Las reglas de blog técnico **no contradicen** las reglas 1-10 del informe Flashcards: las extienden a un contexto distinto (research blog post) que requiere capas adicionales (calibración de claims, fact-checking de prior work, anti-overclaiming).

Las reglas que **siempre aplican** independientemente del documento:
- 1. Lectura por perfiles (técnico / no-técnico / inversor)
- 2. Bajar a tierra antes de usar términos complejos
- 4. Anclar en el tiempo (referencias con año)
- 5. Evidencia y fuentes
- 6. Anticipar objeciones del lector
- 7. Voz del autor (opiniones justificadas)

---

## Origen

- Comentarios del tutor en el Google Docs, marcados con `==` en `Conversational Flashcards - Alvarez Gustavo - Seminario Integrador.md` (líneas 19-20, 23, 29, 31, 33-34, 40, 46, 52-53).
- Guía adicional del autor (21 abril 2026).
- Sección 11 (mayo 2026): destilado de la *Blog Post Writing Guide* (BlueDot/BAISH facilitators) + análisis estructural del paper Wang et al. 2025 *"Refusal Direction is Universal Across Safety-Aligned Languages"* + reglas estilísticas del autor para escribir en inglés sin sonar a IA.


