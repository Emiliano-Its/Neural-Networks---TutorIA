# Especificación del simulador TutorIA UANL
Semilla 42. Se generan 3,600 alumnos de 1er semestre y solo los que tienen Matemáticas I >= 70 pasan al dataset de Mate II (~2,000). La red nunca ve las variables ocultas.

## Ocultas
q ~ N(0,1) es la base matemática y c ~ N(0,1) la constancia, con corr(q,c)=0.3. Hay 7 habilidades h: derivadas, álgebra básica, regla de la cadena, límites, identidades trigonométricas, polinomios y derivadas parciales, con θ_h = 0.8q + 0.6ε_h. A es la autoeficacia oculta y sale de q y c.

## 1er semestre (A1)
k_s = ρ_s q + sqrt(1-ρ_s²) η_s
cal_s = μ_s + σ_s·reescalar(0.75k_s + 0.45c + 0.5u_s), recortada a [0,100]. Reescalar deja la desviación en 1.
Cada materia: ρ, μ, σ y meta de reprobación (<70):
- Matemáticas I: 0.85, 72, 13, meta 40–55%
- Química General: 0.50, 72, 13, meta 40–55%
- Álgebra para Ingeniería: 0.75, 74, 12, meta 35–45%
- Física I: 0.65, 74, 12, meta 35–45%
- Dibujo para Ingeniería: 0.30, 80, 9, meta 10–20%
- Aplicación de las TI: 0.20, 84, 9, meta 5–15%
- Competencia comunicativa: 0.10, 84, 9, meta 5–15%
A2 = número de materias abajo de 70.

## Encuesta (puntos de partida; se ajustan al calibrar)
- B1 horas de estudio por semana: media ~8, sube con c, recorte 0–40.
- B2 asistencia: media 0.85, sube con c, recorte 0.30–1.
- B3 horas de sueño: media 6.6, sd 1.1, baja un poco con el trabajo.
- B4 regularidad del sueño 1–5: sube con c.
- B5 trabajo: 45% trabaja, de 8 a 30 h; los demás 0.
- B6 materias inscritas: casi siempre 6 o 7, rango 5–8.
- B7 asesorías 1–5: sube con c y con MENOS q.
- C1 autoeficacia 1–5: sale de A.
- C2 meta de calificación: media 82, sube con autoeficacia, recorte 70–100.
- C3 esfuerzo 1–5: sale de c.
- D1 consumo 1–5: 30% "no respondió"; el resto, un poco más alto con menos c.

## Test adaptativo (15 preguntas)
P(acierto) = 0.25 + 0.75/(1+exp(-1.7(θ_h - b))), con b en {-1,0,+1}. Cada habilidad empieza con b=0. Si acierta sigue b=+1, y si falla, b=-1 (14 preguntas). La pregunta 15 va a la habilidad con la estimación más incierta y es la dificultad que le falta. Sale un dominio de 0 a 1 por habilidad, estimado desde θ. El tiempo por pregunta ronda 45 s y sube con θ bajo; la entrada es el tiempo promedio.

## Nota de Mate II
D = Σ w_h θ_h, con w: derivadas 5/17, álgebra básica 4/17, cadena 2/17, límites 2/17, trigonométricas 2/17, polinomios 1/17, parciales 1/17.
G = Σ r_s k_s, con r: Mate I 0.762, Álgebra 0.095, Dibujo 0.095, Física I 0.048 y las demás 0.
z = reescalar(0.40D + 0.20G + 0.20c + 0.10A)
nota = 74.5 + 6.5z + E_hábitos + ε, con ε ~ N(0,5) y recortada a [0,100].
E_hábitos va centrado para que el alumno promedio quede en 0:
- estudio: 3·ln(1+horas/4)
- asistencia: 10·(asis−0.85)
- sueño: −0.5·(horas−7.5)² con mínimo −4, más 0.6·(regularidad−3)
- trabajo: −0.15 por hora arriba de 15
- carga: −1 por materia arriba de 7
- asesorías: 0.5·(B7−1)
Riesgo con cortes 80/70: bajo ≥80, medio de 70 a 79.9, alto <70.

## Metas de calibración
- Riesgo alto: 30–35%, con bajo y medio parecidos.
- La reprobación de cada materia queda dentro de su rango.
- corr(asistencia, nota): 0.35–0.45.
- corr(C1, nota): 0.28–0.38.
- R² de la nota con solo B3 y B4: ≤25%.
- Mate I es la previa con mayor correlación con la nota, y las dos previas con menor correlación son TI y Competencia comunicativa.
- Techo de exactitud del riesgo usando la nota sin ruido: 70–75%.

## 28 entradas (estandarizadas)
Las 7 calificaciones de A1 (posición frente al promedio de cada materia), A2, B1, B2, B3, B4 (0–1), B5, B6, B7 (0–1), C1, C2, C3, D1 más el indicador "no respondió" (si salta, se pone el valor promedio), los 7 dominios del test y el tiempo promedio. D1 nunca entra al SOM.

## Archivos
data/alumnos.csv guarda solo observables, la nota y el riesgo. data/ocultas.csv guarda q, c, θ, k, A y la nota sin ruido, y nunca entra a la red. División 70/15/15 estratificada por riesgo. La curva de horas recomendadas varía B1 de 0 a 20 en el modelo y se compara con la curva verdadera.

## Cambios respecto a la versión acordada (2026-11-04)
Aplicados en un commit aparte para poder revertirlos.
1. Base de la nota: 72.5 → 74.5. Con 72.5 y E_hábitos centrado, el riesgo alto salía en 39%. Con 74.5 queda en el rango de 30–35%.
2. μ de Competencia comunicativa: 85 → 84. Con 85 la reprobación esperada era 4.8%, abajo de la meta de 5–15%.
3. Meta de orden: antes pedía que Competencia comunicativa fuera la de menor correlación. Ahora pide que TI y Competencia comunicativa sean las dos de menor correlación, en cualquier orden, porque ambas tienen peso 0 en G y su orden depende del ruido.
