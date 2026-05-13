# Script de la talk — 6 min

**Idioma:** español rioplatense, tono conversacional.
**Duración objetivo:** 360 segundos (6 minutos).
**Convención:** `==palabra==` = stress vocal fuerte. Decir SÍ O SÍ, marcar con la voz.
**Notas:** las oraciones son cortas a propósito — son para hablar, no para leer en voz baja. Si en el ensayo te queda raro, parafraseá pero mantené los `==términos==`.

---

## Slide 1 — Cover (≈25 s)

**Hook (mientras aparece la animación, esperar 2s):**

> Hay un modelo de IA que tiene ==cuatro mil quinientos millones== de parámetros, habla ciento cuarenta idiomas, corre en tu celular...
>
> ...y cumple ==el sesenta y ocho por ciento== de los pedidos dañinos que recibe.

**Cierre:**

> No es el más chico de su familia. No es el más grande.
>
> Es ==el del medio==. Y es el que cabe en un teléfono.

**Transición:** *click — slide 2.*

---

## Slide 2 — Las 48 horas (≈30 s)

**Hook:**

> Esta historia tiene dos fechas. Vienen pegadas.

**Cuerpo:**

> ==Dos de abril de 2026.== Google libera Gemma 4. Cuatro tamaños, código abierto, pesos públicos.
>
> ==Cuatro de abril de 2026.== Un usuario anónimo que se hace llamar `huihui-ai` sube a HuggingFace las cuatro versiones... ==con el filtro de seguridad roto==.
>
> Cuarenta y ocho horas entre el modelo oficial y su versión sin frenos. Cualquiera la baja gratis. Corre en una laptop.

**Cierre (lento, marcando):**

> El ==threat model== ya no es académico. Está en la calle.

**Transición:** *click.*

---

## Slide 3 — Qué es abliteration (≈35 s)

**Hook:**

> ¿Cómo se "rompe" un modelo de IA?

**Cuerpo:**

> Cuando un modelo decide rechazar un pedido dañino — "no te puedo ayudar con eso" — esa decisión no está repartida en toda la red.
>
> ==Vive en una sola dirección== dentro del modelo. Una sola. Eso lo descubrió Arditi en 2024.
>
> Se llama ==refusal direction==. Y la podés encontrar.
>
> ==Abliteration== es exactamente eso: la encontrás y la proyectás fuera de cada capa.

**Cierre:**

> El modelo deja de rechazar. Pero ==no pierde ninguna otra capacidad==. Sigue traduciendo, sigue resumiendo, sigue programando. Solo no dice que no.

**Transición:** *click.*

---

## Slide 4 — La pregunta abierta (≈25 s)

**Hook:**

> Esto que les acabo de contar ya se había estudiado. Pero con una trampa.

**Cuerpo:**

> Wang y su equipo, en 2025, mostraron que la receta funciona en ==trece idiomas distintos==. Una refusal direction sacada de inglés sirve para romper el filtro en chino, en árabe, en hindi.
>
> Pero ellos extraían la dirección en su laboratorio. Modelos de 7 a 14B parámetros. No habían testeado ==la versión pública== en Gemma 4.

**Cierre:**

> Mi pregunta fue: ¿cómo escala el ataque desde el modelo más chico (que cabe en un celu) hasta el más grande (31B)?

**Transición:** *click.*

---

## Slide 5 — Setup (≈25 s)

**Hook:**

> El experimento entero, en una respiración:

**Cuerpo (rápido, casi enumerando):**

> ==Tres tamaños== Dense — E2B, E4B, treinta y uno B.
>
> ==Dos condiciones== — modelo base y modelo abliterado, descargado tal cual de `huihui-ai`.
>
> ==Siete idiomas== — inglés, español, chino, portugués, alemán, árabe, hindi.
>
> ==Cien prompts dañinos por idioma== — sacados de BeaverTails.

**Cierre:**

> Total: ==cuatro mil doscientas evaluaciones==. Juez para clasificar cumplido/rechazado: Claude Haiku 4.5. Misma cuantización en los seis modelos. Comparación limpia.

**Transición:** *click — viene el chart.*

---

## Slide 6 — Resultado principal (≈45 s)

**Hook (gesture al chart):**

> Esto era lo que yo esperaba ver. Una recta. "Más chico, más roto."
>
> Esto es lo que vi en cambio.

**Cuerpo (señalar el chart):**

> E2B, el más chico — el del celular básico — compliance abliterado del ==cuarenta y dos coma nueve por ciento==. Mal, pero no catastrófico.
>
> Treinta y uno B, el grande — el de la nube, el que necesita una GPU pro — ==sesenta y cuatro coma cuatro==. Bastante peor.
>
> Si seguimos esa recta uno esperaría que el del medio cayera... cerca del cincuenta. Cincuenta y dos, cincuenta y cinco.

**Beat dramático (pausa de un segundo):**

> El del medio dio ==sesenta y ocho coma uno==.

**Cierre:**

> ==La curva no es monótona.== Sube fuerte, después baja un poco. ==El pico de vulnerabilidad está en el medio==. No en los extremos.

**Transición:** *click — slide del mecanismo. Esta es la parte que más necesito que entiendan.*

---

## Slide 7 — Mecanismo (≈70 s) ⭐ CORE

**Hook:**

> Bueno. ==¿Por qué el del medio?==

**Setup conceptual (lento, didáctico):**

> Acuérdense de la refusal direction. Cada modelo tiene una.
>
> Pero en realidad, ==cada idioma dentro de un mismo modelo== tiene la suya. La del inglés, la del español, la del hindi. Son siete vectores distintos. Siete "huellas" de cómo el modelo dice que no, una por idioma.

**Construcción de la metáfora (manos haciendo el gesto):**

> Imaginen siete flechas saliendo del centro de una pelota.
>
> Si las siete flechas apuntan ==más o menos para el mismo lado==, son casi la misma flecha. Si apuntan para lados distintos, son siete cosas diferentes.

**Bajada a número:**

> Hay un número que mide eso: se llama ==cosine similarity==. Va de cero — flechas perpendiculares, no tienen nada que ver — a uno — flechas idénticas, la misma cosa.
>
> Lo medimos en los tres modelos:
>
> - En E2B, las siete flechas promedian un ==cero coma treinta y uno==.
> - En treinta y uno B, ==cero coma veintisiete==.
> - En E4B... ==cero coma treinta y siete==. ==El máximo==.

**Insight (el momento):**

> Y acá viene la parte importante. ==Cuando las siete flechas son casi la misma flecha, basta con borrar una para borrarlas todas==.
>
> Eso es exactamente lo que hace abliteration. Borra una flecha.
>
> En E4B esa flecha sirve para los siete idiomas a la vez. En E2B y en treinta y uno B sirve menos, queda residuo, queda filtro que sobrevivió.

**Cierre con el doble pico (lento, marcado):**

> ==El pico de compliance== y ==el pico de geometría== caen ==en el mismo modelo==. E4B.
>
> Una cosa importante: esto lo medimos ==después== de ver el compliance. Es una lectura consistente con los datos, no una predicción confirmada.
>
> Para validarlo del todo habría que ==repetir el ataque sacando nuestra propia refusal direction==, no usar la de `huihui-ai`. Si el pico sigue en E4B, está confirmado. Si se mueve, era un artefacto del extractor.

(  huihui-ai no inventó la matemática — usó la receta de Arditi 2024 — pero eligió los detalles concretos: qué prompts dañinos usar para sacar el promedio, qué
  prompts inocuos para el contraste, qué capa del modelo medir, qué seed. Esas decisiones se llaman "el extractor". El resultado fueron los pesos abliterados que
  publicó.

  Una "extracción independiente" es: agarrar el modelo base Gemma 4 (sin tocar), correr la misma matemática pero con otro código, otros prompts, otra capa, otro 
  seed, y ablitedar de cero. Si el pico de compliance vuelve a aparecer en E4B con ese nuevo intento, entonces el pico ES de Gemma 4 — no de los detalles que
  eligió huihui-ai. Si en cambio el pico se mueve a 31B o E2B, era un artefacto del extractor específico.
))
>
> Pero la coincidencia entre los dos picos ==es difícil de ignorar==.

**Transición:** *click — calibremos qué quiere decir esto en la calle.*

---

## Slide 8 — La paradoja calibrada (≈35 s)

**Hook:**

> Pongamos esto en hardware real.

**Cuerpo (señalar cada tier):**

> Un ==celular básico== — cuatro gigas de RAM. Ahí cabe E2B. Compliance post-abliteración: cuarenta y tres por ciento.
>
> Un ==celular alta gama== — ocho gigas de RAM, los teléfonos último modelo. Ahí cabe E4B. Compliance: ==sesenta y ocho==. ==El pico==.
>
> Una ==PC con GPU profesional== — treinta y dos gigas de VRAM. Ahí cabe treinta y uno B. Compliance: sesenta y cuatro.

**Insight:**

> El modelo más roto de toda la familia es ==el más grande que cabe en un teléfono==. No es teórico — es exactamente el modelo que un usuario natural elegiría: "bajo el más grande que mi celu aguanta".

**Transición:** *click.*

---

## Slide 9 — Belief update (≈35 s)

**Hook:**

> Tres cosas con las que entré a este experimento — y con las que ==no salgo==.

**Cuerpo (rápido, una por una):**

> Una: "==Modelos chicos igual a más vulnerables==". Forma fuerte del paradox naive. ==Falso==. El más roto está en el medio.
>
> Dos: "==Sin extracción de laboratorio, una receta pública no llega al umbral de amenaza==". ==Falso==. Wang et al., con extracción propia de lab, llegan cerca del ==noventa por ciento== en otras familias (Yi, Qwen, Llama 3). `huihui-ai`, con receta pública pura, llega al ==sesenta y ocho== en Gemma 4 E4B. Sí, hay brecha. Pero sesenta y ocho ==ya es siete de cada diez pedidos cumplidos==. La brecha entre 68 y 90 no salva a nadie.
>
> Tres: "==Los idiomas con menos datos en el preentrenamiento son los primeros en romperse==". ==Falso==. Hindi resiste mejor que Español, mejor que alemán, mejor que portugués, en los tres tamaños. La dirección del efecto va al revés de lo que esperaba.

**Transición:** *click — el cierre.*

---

## Slide 10 — Cierre y escala (≈35 s)

**Hook:**

> Esto es lo que pasa a escala.

**Cuerpo:**

> Hay aproximadamente ==tres mil millones de smartphones alta gama== en el mundo. En todos esos corre E4B.
>
> Hay aproximadamente ==cincuenta millones de PCs== con GPU profesional. Ahí corre treinta y uno B.

**Pregunta retórica (despacio):**

> Si ==uno de cada diez mil== usuarios de smartphone alta gama baja un Gemma 4 E4B abliterado... son ==trescientas mil instalaciones==.
>
> Trescientas mil personas con un modelo donde siete de cada diez pedidos dañinos se cumplen. En siete idiomas. En su bolsillo.

**Cierre (lento, mirando al público):**

> La receta está pública desde el ==cuatro de abril==. La barrera de entrada es bajar un archivo.
>
> ==El ataque más fuerte vive en el modelo más accesible.==
>
> Gracias.

---

## Slide 11 — Q&A (≈5 s)

> Estoy especialmente interesado en feedback sobre el ángulo mecanístico — y en qué otras familias open-weight valdría la pena testear.
>
> Preguntas.

---

## Slide 12 — FAQ anticipadas (BACKUP — durante Q&A)

Si surge una pregunta predecible, levantar este slide y responder con las notas. Las cinco que más probablemente vienen:

> **Q1. ¿Y el modelo MoE 26B-A4B que dejaste afuera?**
>
> Para ==no mezclar el efecto del tamaño con el de la arquitectura==. Si lo metía al eje "tamaño" no podía separar si una diferencia venía del routing MoE o del tamaño total. Queda como sub-pregunta independiente: comparar 26B-A4B contra E4B (mismos ~4B parámetros activos, distinto routing).

> **Q2. ¿Los modelos abliterados pierden capacidades?**
>
> ==No==. El paper de Arditi 2024 reporta ==≈99% retención== en MMLU y HumanEval. El modelo abliterado sigue siendo útil — solo deja de negarse. Eso es exactamente lo que lo hace peligroso: útil + dañino al mismo tiempo.

> **Q3. ¿Qué defensas existen hoy?**
>
> Tres frentes. ==Pre-publicación==: tamper-resistance, fine-tuning adversarial que hace más costosa la abliteration (Tamirisa et al. 2024). ==Detección==: medir cosine sim entre la refusal direction del modelo público y un baseline conocido — abliterados saltan a cero. ==Distribución==: políticas en HuggingFace contra cuentas que publican abliterados. Paliativo, no solución.

> **Q4. ¿Por qué Hindi resiste más que Español, alemán o portugués?**
>
> Honestamente, ==no sé==. Hay que separar dos cosas:
>
> ==Lo observado== (firme): Hindi cae siempre entre los más bajos en los tres tamaños — 39% en E2B, 65% en E4B, 60% en 31B. Es robusto al tamaño.
>
> ==El mecanismo== (especulación): una conjetura razonable es que la refusal direction extraída de Hindi tenga menor cosine similarity con la de inglés que las de Español o portugués. La data pairwise existe en mi pipeline (matriz 7×7 por modelo), pero en este experimento solo reporté ==el promedio sobre los 21 pares==, no analicé par-por-par. Eso es exactamente el siguiente análisis a hacer.
>
> Lo único que puedo decir con confianza: la dirección del efecto va al opuesto de lo que esperaba al inicio del proyecto. Esperaba que Hindi se rompiera primero. No se rompe primero.

> **Q5. ¿Por qué el pico justo en E4B y no en otro tamaño?**
>
> Conjetura: E4B tiene capacidad para ==alinear los siete idiomas en un solo eje== (la geometría se "limpia"), pero no la suficiente para diferenciarlos por idioma como hace 31B. E2B no llega a alinearlos. Necesita más puntos de la curva (E6B, E8B si existieran) para validarlo.

---

## Slide 13 — Cómo se midió la cosine similarity (BACKUP — methodology deep-dive)

Si alguien pregunta "¿cómo midieron exactamente el cosine?" o "¿qué quiere decir refusal direction?", levantar este slide. Cuatro pasos:

> **Uno · dos sets de prompts por idioma.**
>
> 100 dañinos (BeaverTails traducido) + 100 inocuos curados (también traducidos al idioma target). Importante: ==ambos sets en el mismo idioma==. Si los inocuos estuvieran en inglés y los dañinos en, por ejemplo, hindi, la dirección que sacamos confundiría "dañino vs inocuo" con "inglés vs hindi". Eso lo aprendimos de Wang et al. 2025.

> **Dos · activaciones del modelo base.**
>
> Cada prompt pasa por el chat template del modelo, se corre por la red, y extraemos el ==residual stream== en la ==última capa==, en el ==último token==. Eso da un vector por prompt. 100 dañinos → 100 vectores; lo mismo para los inocuos.
>
> Detalle: usamos el modelo ==base==, no el abliterado. Queremos caracterizar la geometría de rechazo *antes* del ataque.

> **Tres · refusal direction por idioma.**
>
> Promediamos las activaciones dañinas, promediamos las inocuas, y restamos: `direction = mean(harmful) − mean(harmless)`. Después normalizamos a norma uno. ==Un vector por idioma==, siete vectores por modelo. Es exactamente el método de Arditi 2024.

> **Cuatro · cosine similarity entre los 21 pares.**
>
> Siete idiomas dan veintiún pares (combinatoria de 7 tomados de a 2). Para cada par calculamos `cos(θ) = a·b` — las direcciones ya están normalizadas, así que el cosine es directamente el producto escalar. Promediamos los 21 valores. Ese es el número que reporto: ==0.31 E2B==, ==0.37 E4B==, ==0.27 31B==.

Si insisten en más detalle:

- El máximo cross-lingual también pica en E4B: 0.71 (vs 0.67 E2B y 0.52 31B).
- El mínimo cross-lingual no muestra patrón claro entre los tres modelos.
- La elección de "última capa" sigue la convención de Wang et al. y Arditi et al. Capas más tempranas codifican sintaxis, capas finales codifican task-specific information — la "última capa" del residual stream es donde la representación de rechazo está más limpia, según ambos papers.

---

## Slide 14 — Limitations (BACKUP — si preguntan por robustez)

Si alguien pregunta "¿qué tan robusto es esto?", levantar este slide:

> Cinco caveats importantes:
>
> Una sola familia de modelos — Gemma 4 Dense. No probé Llama, Qwen, Mistral.
>
> Una sola receta de abliteration — la de `huihui-ai`. Repetir el ataque con otra extracción (otro código, otros prompts, otra capa) podría desplazar el pico.
>
> Un solo juez — Claude Haiku 4.5. Wang et al. usaron WildGuard.
>
> Siete idiomas. Faltan los más ==safety-misaligned==: yoruba, polaco, persa.
>
> La lectura mecanística es post-hoc. Es ==consistent with==, no una predicción confirmada.
>
> Es un hallazgo preliminar. Necesita más testing.

---

## Timing total

| Slide | Tema                  | Segundos |
|-------|-----------------------|---------:|
| 1     | Cover                 | 25       |
| 2     | 48 horas              | 30       |
| 3     | Qué es abliteration   | 35       |
| 4     | Pregunta abierta      | 25       |
| 5     | Setup                 | 25       |
| 6     | Resultado principal   | 45       |
| 7     | Mecanismo ⭐          | 70       |
| 8     | Paradox calibrada     | 35       |
| 9     | Belief update         | 35       |
| 10    | Cierre y escala       | 35       |
| 11    | Q&A intro             | 5        |
| **Total** |                   | **365** |

365s = 6 min 5 s. Buffer mínimo. Si vas apurado: recortá slide 4 (la pregunta abierta se entiende con menos contexto) y slide 9 (la tercera creencia de Hindi se puede dejar para Q&A).

## Las 12 frases que ==tenés que decir sí o sí==

Si todo lo demás se cae, que estas frases lleguen:

1. "==Cuarenta y ocho horas== entre el modelo y su versión rota."
2. "El rechazo vive en ==una sola dirección== dentro del modelo."
3. "==Abliteration== la encuentra y la borra."
4. "==Cuatro mil doscientas evaluaciones==. Una sola receta."
5. "==La curva no es monótona==."
6. "==El pico está en el medio==."
7. "==Cosine similarity== — cuán parecidas son las flechas de rechazo entre idiomas."
8. "Cuando las flechas se parecen, ==borrar una borra todas==."
9. "El pico de compliance y el pico de geometría ==caen en el mismo modelo==."
10. "El más roto es ==el más grande que cabe en un celular==."
11. "==Trescientas mil instalaciones== potenciales en smartphones alta gama."
12. "==El ataque más fuerte vive en el modelo más accesible==."
