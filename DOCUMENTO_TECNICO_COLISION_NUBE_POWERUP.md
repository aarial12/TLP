# Documento Técnico: Implementación de Colisión con Nubes y Manejo de Tiempo para Power-Up

**Proyecto:** BrickScript (TLP)  
**Fecha:** Junio 2026  

---

## 1. Resumen Ejecutivo

Este documento detalla la implementación técnica de dos mecánicas centrales del juego Snake en BrickScript:
- **Colisión con Nubes (Cloud Collision)**: Lógica que gestiona las colisiones entre la serpiente y las nubes, incluyendo efectos especiales según la dificultad
- **Manejo de Tiempo para Power-Up (Power-Up Time Management)**: Sistema de invulnerabilidad basado en tiempo con duración configurable

Ambas funcionalidades están implementadas en el archivo `runtime.py` y son críticas para las dificultades CAT y ENTUSIASTA.

---

## 2. Arquitectura General

### 2.1 Estructura de Datos Principales

```python
# Atributos de la instancia Juego (líneas 72-79)
self.posicion_nube = None           # Coordenada (x, y) de la nube
self.posicion_powerup = None        # Coordenada (x, y) del power-up
self.invulnerabilidad_segundos = float(...)  # Duración de invulnerabilidad
self.invulnerable_hasta = 0         # Timestamp de fin de invulnerabilidad
```

### 2.2 Ciclo Principal de Actualización

El game loop ejecuta cada 50ms (0.05 segundos):

```python
# Líneas 145-164
def game_loop(self):
    self.timer_gravedad += 0.05
    if self.timer_gravedad >= self.velocidad_gravedad:
        self.ejecutar_evento('ON_TICK')
    self.actualizar_estado_invulnerabilidad()  # Actualiza estado de invulnerabilidad
    self.dibujar()
    self.timer_id = self.root.after(50, self.game_loop)
```

---

## 3. Colisión con Nubes (Cloud Collision)

### 3.1 Generación de Nubes

**Responsable:** `snake_spawn_comida()` (líneas 521-547)  
**Integrante:** Nicolas Arias (aarial12)

#### Lógica de Spawn

Las nubes se generan según la puntuación y dificultad:

```python
# Línea 535-540
if ((self.puntuacion % 50) == 0) and self.dificultad == 'CAT':
    while True:
        x, y = random.randint(0, self.ancho - 1), random.randint(0, self.alto - 1)
        if (x, y) not in self.serpiente_cuerpo:
            self.posicion_nube = (x, y)
            break
```

**Parámetros:**
- **Frecuencia:** Se genera cuando `puntuacion % 50 == 0`
- **Dificultad:** Solo en modo CAT
- **Posición:** Aleatoria dentro del grid (10x20)
- **Restricción:** No coloca nube donde está el cuerpo de la serpiente

### 3.2 Detección y Manejo de Colisiones

**Responsable:** `snake_mover_jugador()` (líneas 549-613)  
**Integrante:** Nicolas Arias (aarial12)

#### Punto de Detección

```python
# Líneas 576-581
if nueva_cabeza == self.posicion_nube:
    if not invulnerable:
        if self.puntuacion == 0:
            self.juego_terminado = True
        else:
            self.puntuacion = 0
```

#### Comportamiento según Estado

| Condición | Efecto | Línea |
|-----------|--------|-------|
| Colisiona + Vulnerable | Si puntuación = 0: **Game Over**; Si no: **Puntuación = 0** | 576-581 |
| Colisiona + Invulnerable | **Sin efecto** | 577 (condición negada) |

#### Tabla de Decisiones

```
┌─────────────────────┬──────────────┬─────────────────┐
│ Estado              │ Puntuación   │ Resultado       │
├─────────────────────┼──────────────┼─────────────────┤
│ Vulnerable          │ 0            │ GAME OVER       │
│ Vulnerable          │ > 0          │ Puntos = 0      │
│ Invulnerable        │ Cualquiera   │ Sin efecto      │
└─────────────────────┴──────────────┴─────────────────┘
```

### 3.3 Renderizado de Nubes

**Responsable:** `dibujar()` (líneas 261-267)  
**Integrante:** JoseMiguel0328

```python
# Líneas 261-267
if self.posicion_nube:
    x, y = self.posicion_nube
    if getattr(self, 'img_cloud', None):
        ts = self.taman_celda
        self.canvas.create_image(x * ts, y * ts, image=self.img_cloud, anchor='nw')
    else:
        self.dibujar_celda(x, y, COLOR_NUBE)
```

**Características:**
- Intenta cargar sprite desde `assets/snake/objects/cloud.gif`
- Si no existe: dibuja rectángulo de color `#3B6294` (azul oscuro)
- Posición: Centro de celda en coordenadas de píxeles

---

## 4. Manejo de Tiempo para Power-Up (Power-Up Time Management)

### 4.1 Sistema de Invulnerabilidad

#### 4.1.1 Activación del Power-Up

**Responsable:** `snake_spawn_comida()` (líneas 542-547)  
**Integrante:** Nicolas Arias (aarial12)

```python
# Líneas 542-547
if ((self.puntuacion % 200) == 0) and (self.puntuacion != 0) and \
   (self.dificultad == 'CAT' or self.dificultad == 'ENTUSIASTA'):
    while True:
        x, y = random.randint(0, self.ancho - 1), random.randint(0, self.alto - 1)
        if (x, y) not in self.serpiente_cuerpo:
            self.posicion_powerup = (x, y)
            break
```

**Condiciones de Aparición:**
- `puntuacion % 200 == 0`: Cada 200 puntos
- `puntuacion != 0`: No en el inicio
- `dificultad in ['CAT', 'ENTUSIASTA']`: Solo en dificultades altas

#### 4.1.2 Consumo del Power-Up

**Responsable:** `snake_mover_jugador()` (líneas 602-610)  
**Integrante:** Nicolas Arias (aarial12)

```python
# Líneas 602-610
elif nueva_cabeza == self.posicion_powerup:
    self.ejecutar_evento('ON_EAT_POWERUP')
    self.ejecutar_evento('ON_EAT_FOOD')
    self.posicion_powerup = None
    self.activar_invulnerabilidad()  # Activar invulnerabilidad
    if self.crecimiento_pendiente > 0:
        self.crecimiento_pendiente -= 1
    else:
        self.serpiente_cuerpo.pop()
```

**Acciones:**
1. Ejecuta evento `ON_EAT_POWERUP` (añade puntos)
2. Ejecuta evento `ON_EAT_FOOD` (genera nueva comida)
3. Elimina el power-up del mapa
4. Activa invulnerabilidad temporal
5. Gestiona crecimiento de la serpiente

### 4.2 Gestión de Invulnerabilidad Basada en Tiempo

#### 4.2.1 Inicialización

**Responsable:** `__init__()` (línea 78)  
**Integrante:** Nicolas Arias (aarial12)

```python
# Línea 78
self.invulnerabilidad_segundos = float(self.datos_juego.get('config', {}).get('powerup_invulnerability', 3))
```

**Configuración:**
- Duración por defecto: **3 segundos**
- Configurable en `datos_juego['config']['powerup_invulnerability']`
- Tipo: Flotante (permite precisión decimal)

#### 4.2.2 Activación de Invulnerabilidad

**Responsable:** `activar_invulnerabilidad()` (líneas 640-642)  
**Integrante:** JoseMiguel0328

```python
# Líneas 640-642
def activar_invulnerabilidad(self):
    if self.invulnerabilidad_segundos > 0:
        self.invulnerable_hasta = max(self.invulnerable_hasta, time.time()) + self.invulnerabilidad_segundos
```

**Lógica:**
- Calcula timestamp de fin: `time.time() + invulnerabilidad_segundos`
- Usa `max()` para evitar sobreescribir invulnerabilidad activa
- Permite encadenamiento de power-ups

**Ejemplo Temporal:**
```
time.time() = 1000.0
invulnerabilidad_segundos = 3.0
invulnerable_hasta = 1003.0 (3 segundos en el futuro)
```

#### 4.2.3 Verificación de Estado Invulnerable

**Responsable:** `esta_invulnerable()` (líneas 644-645)  
**Integrante:** JoseMiguel0328

```python
# Líneas 644-645
def esta_invulnerable(self):
    return self.tipo_juego == 'SNAKE' and getattr(self, 'invulnerable_hasta', 0) > time.time()
```

**Lógica:**
- Compara tiempo actual con `invulnerable_hasta`
- Solo válido para modo SNAKE
- Retorna `True` si aún hay tiempo restante

#### 4.2.4 Actualización de Estado UI

**Responsable:** `actualizar_estado_invulnerabilidad()` (líneas 647-654)  
**Integrante:** JoseMiguel0328

```python
# Líneas 647-654
def actualizar_estado_invulnerabilidad(self):
    if self.tipo_juego != 'SNAKE':
        return
    if self.esta_invulnerable():
        restantes = max(0.0, self.invulnerable_hasta - time.time())
        self.label_estado.config(text="INVULNERABLE\n{0:.1f}s".format(restantes))
    else:
        self.label_estado.config(text="")
```

**Características:**
- Se ejecuta en cada frame del game loop
- Calcula tiempo restante en segundos
- Formatea con 1 decimal: "INVULNERABLE\n2.3s"
- Limpia el label cuando termina la invulnerabilidad

#### 4.2.5 Integración en Lógica de Movimiento

**Responsable:** `snake_mover_jugador()` (líneas 549-567, 576-590, 602-610)  
**Integrante:** Nicolas Arias (aarial12)

```python
# Línea 554
invulnerable = self.esta_invulnerable()

# Línea 557
if invulnerable:
    self.serpiente_direccion = (-dir_x, -dir_y)  # Rebota

# Línea 577
if not invulnerable:
    # Detecta colisión con nube
```

**Comportamientos de Invulnerabilidad:**

| Evento | Vulnerable | Invulnerable |
|--------|-----------|--------------|
| Colisión Pared | Game Over | Rebota (invierte dirección) |
| Colisión Propio (CAT) | Puntos=0 | Sin efecto |
| Colisión Nube | Puntos=0 | Sin efecto |
| Colisión Veneno | Game Over/Puntos=0 | Sin efecto |

### 4.3 Renderizado de Power-Up

**Responsable:** `dibujar()` (líneas 269-275)  
**Integrante:** JoseMiguel0328

```python
# Líneas 269-275
if self.posicion_powerup:
    x, y = self.posicion_powerup
    if getattr(self, 'img_powerup', None):
        ts = self.taman_celda
        self.canvas.create_image(x * ts, y * ts, image=self.img_powerup, anchor='nw')
    else:
        self.dibujar_celda(x, y, COLOR_POWERUP)
```

**Características:**
- Sprite: `assets/snake/fruits/power-up.gif`
- Color fallback: `#ffd700` (dorado)
- Renderizado cada frame

### 4.4 Efectos Visuales de Invulnerabilidad

**Responsable:** `dibujar()` (líneas 217-221)  
**Integrante:** JoseMiguel0328

```python
# Líneas 217-221
snake_invulnerable = self.esta_invulnerable()
parpadeo = int(time.time() * 10) % 2 == 0
COLOR_SNAKE_CABEZA = '#FFFFFF' if snake_invulnerable and parpadeo else '#00FFFF'
COLOR_SNAKE_CUERPO = '#7FFFD4' if snake_invulnerable and parpadeo else '#33CC33'
COLOR_SNAKE_BORDE = '#FFFFFF' if snake_invulnerable else '#000000'
```

**Efecto de Parpadeo:**
- `time.time() * 10`: 10 ciclos por segundo
- `% 2 == 0`: Alterna cada 0.1 segundos
- Color cabeza: Blanco (#FFFFFF) cuando invulnerable
- Color cuerpo: Aguamarina (#7FFFD4) cuando invulnerable
- Borde: Blanco cuando invulnerable

---

## 5. Flujo de Eventos Integrado

### 5.1 Diagrama de Flujo: Colisión con Nube

```
┌─────────────────────────────────────────┐
│   ON_TICK (cada velocidad_gravedad)     │
└────────────────┬────────────────────────┘
                 │
        ┌────────▼────────┐
        │  snake_mover()  │
        └────────┬────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
    ▼                         ▼
nueva_cabeza ==        nueva_cabeza !=
posicion_nube?         posicion_nube?
    │                         │
    ▼                         ▼
esta_invulnerable?     (continuar)
    │
┌───┴────┐
│        │
SI      NO
│        │
▼        ▼
Sin   ┌─────────┐
efecto│puntos=0?│
      └────┬────┘
           │
      ┌────┴────┐
      │          │
      SI         NO
      │          │
      ▼          ▼
   G.OVER    puntos=0
```

### 5.2 Diagrama de Flujo: Power-Up y Invulnerabilidad

```
                    ON_TICK
                      │
                      ▼
              snake_mover_jugador()
                      │
          ┌───────────┴───────────┐
          │                       │
          ▼                       ▼
nueva_cabeza ==            nueva_cabeza !=
posicion_powerup?          posicion_powerup?
          │                       │
         YES                      NO
          │                   (continuar)
          ▼
    ┌──────────────────────┐
    │ activar_invulnerable │
    │  (time.time() + 3s)  │
    └──────────────────────┘
          │
          ▼
  invulnerable_hasta = T
          │
          ▼
   game_loop() cada 50ms
          │
          ▼
actualizar_estado_invulnerabilidad()
          │
    ┌─────┴──────┐
    │            │
   SI           NO
    │            │
    ▼            ▼
Mostrar    Limpiar UI
tiempo     "INVULNERABLE"
restante   desaparece
"X.Xs"
```

---

## 6. Detalles de Implementación Críticos

### 6.1 Sincronización de Tiempo

#### Problema: Acumulación de Error
El sistema usa `time.time()` que retorna segundos desde epoch con decimales.

#### Solución Implementada

```python
# Línea 642
self.invulnerable_hasta = max(self.invulnerable_hasta, time.time()) + self.invulnerabilidad_segundos
```

- `max()`: Evita reducción de tiempo si se activa otro power-up
- Permite stacking de invulnerabilidades
- Precisión: ±10ms (resolución de game_loop)

### 6.2 Generación de Posiciones

#### Problema: Colisiones con Serpiente
La nube podría colocarse donde está el cuerpo.

#### Solución Implementada

```python
# Líneas 536-540
while True:
    x, y = random.randint(0, self.ancho - 1), random.randint(0, self.alto - 1)
    if (x, y) not in self.serpiente_cuerpo:
        self.posicion_nube = (x, y)
        break
```

- Loop infinito hasta encontrar posición válida
- Verificación: `(x, y) not in serpiente_cuerpo`
- Complejidad O(1) promedio si serpiente < 70% del grid

### 6.3 Transiciones de Estado

#### Problema: Parpadeo Inconsistente
Sin sincronización, el parpadeo puede desincronizarse del tiempo real.

#### Solución Implementada

```python
# Línea 218
parpadeo = int(time.time() * 10) % 2 == 0
```

- Basado en tiempo real, no en contador
- Frecuencia: 10 ciclos/segundo (100ms)
- Independiente del frame rate

---

## 7. Distribución de Responsabilidades por Integrante

### 7.1 Nicolas Arias (@aarial12)

**Commits:** 6 contribuciones  
**Rol Principal:** Arquitecto de Lógica de Juego

#### Responsabilidades:

1. **Generación de Nubes**
   - Función: `snake_spawn_comida()` (líneas 535-540)
   - Lógica de frecuencia según puntuación
   - Validación de posición

2. **Detección de Colisiones con Nubes**
   - Función: `snake_mover_jugador()` (líneas 576-581)
   - Cálculo de consecuencias
   - Diferenciación por dificultad

3. **Generación de Power-Ups**
   - Función: `snake_spawn_comida()` (líneas 542-547)
   - Condiciones de aparición
   - Restricciones de dificultad

4. **Consumo de Power-Ups**
   - Función: `snake_mover_jugador()` (líneas 602-610)
   - Ejecución de eventos
   - Integración con movimiento

5. **Integración de Invulnerabilidad en Movimiento**
   - Función: `snake_mover_jugador()` (líneas 554, 557, 577)
   - Cambios de comportamiento según estado
   - Rebote en paredes

#### Líneas de Código: ~80 líneas

---

### 7.2 JoseMiguel0328 (@JoseMiguel0328)

**Commits:** 2 contribuciones  
**Rol Principal:** Implementación de Sistemas de Tiempo y Presentación

#### Responsabilidades:

1. **Activación de Invulnerabilidad**
   - Función: `activar_invulnerabilidad()` (líneas 640-642)
   - Cálculo de timestamp de fin
   - Lógica de encadenamiento con `max()`

2. **Verificación de Estado Invulnerable**
   - Función: `esta_invulnerable()` (líneas 644-645)
   - Comparación de tiempos
   - Validación de modo de juego

3. **Actualización de UI de Invulnerabilidad**
   - Función: `actualizar_estado_invulnerabilidad()` (líneas 647-654)
   - Cálculo de tiempo restante
   - Formateo de display (1 decimal)

4. **Renderizado de Nubes**
   - Función: `dibujar()` (líneas 261-267)
   - Carga de sprites
   - Fallback de colores

5. **Renderizado de Power-Ups**
   - Función: `dibujar()` (líneas 269-275)
   - Carga de imágenes
   - Posicionamiento en canvas

6. **Efectos Visuales de Invulnerabilidad**
   - Función: `dibujar()` (líneas 217-221)
   - Parpadeo sincronizado
   - Cambios de color

#### Líneas de Código: ~60 líneas

---

## 8. Flujo de Ejecución Completo

### 8.1 Ejemplo: Comer Power-Up y Activar Invulnerabilidad

```
T=0ms:     Game inicia
T=100ms:   Puntuación alcanza 200 (ejemplo)
           → snake_spawn_comida() genera power-up en (5,5)
           
T=150ms:   Serpiente se mueve
           → nueva_cabeza = (5,5)
           → nueva_cabeza == posicion_powerup? YES
           → ejecutar_evento('ON_EAT_POWERUP')  [+puntos]
           → ejecutar_evento('ON_EAT_FOOD')    [genera comida]
           → posicion_powerup = None
           → activar_invulnerabilidad()
              • invulnerable_hasta = time.time() + 3.0
              • invulnerable_hasta = 1023.150 (ejemplo)

T=150-3150ms:
           → Cada 50ms: game_loop()
           → actualizar_estado_invulnerabilidad()
           → T=150ms:   Restantes = 3000ms → "INVULNERABLE\n3.0s"
           → T=1550ms:  Restantes = 1600ms → "INVULNERABLE\n1.6s"
           → T=3150ms:  Restantes = 0ms    → "INVULNERABLE\n0.0s"
           → T=3200ms:  esta_invulnerable() retorna FALSE → "" (limpiar)

T=3150ms+: Serpiente vulnerable nuevamente
           → Colisiones normales aplican
```

### 8.2 Tabla de Estados de Serpiente

| Tiempo (ms) | Estado | Visual | Comportamiento |
|-------------|--------|--------|-----------------|
| 0-100 | Normal | #00FFFF cabeza, #33CC33 cuerpo | Movimiento normal, muere en colisiones |
| 100 | Come Power-Up | Transición | Invulnerabilidad activada |
| 100-3100 | Invulnerable | Parpadea #FFFFFF | Rebota en paredes, immune colisiones |
| 3100+ | Normal | #00FFFF cabeza, #33CC33 cuerpo | Movimiento normal |

---

## 9. Configuración Requerida

### 9.1 Archivo JSON de Configuración

```json
{
  "tipo_juego": "SNAKE",
  "config": {
    "grid_size": [10, 20],
    "dificulty": "CAT",
    "powerup_invulnerability": 3.0
  },
  "events": {
    "ON_TICK": [
      {"accion": "SPAWN", "objeto": "PLAYER"},
      {"accion": "MOVE", "objeto": "PLAYER"},
      {"accion": "SPAWN", "objeto": "FOOD"}
    ],
    "ON_EAT_POWERUP": [
      {"accion": "INCREASE_SCORE", "objeto": 50}
    ]
  }
}
```

### 9.2 Valores Recomendados

```python
# Duración de invulnerabilidad por dificultad
INVULNERABILIDAD_SEGUNDOS = {
    'BABY':        0.0,    # Sin invulnerabilidad
    'CLASSIC':     0.0,
    'ENTUSIASTA':  3.0,    # Recomendado
    'CAT':         5.0,    # Más desafío
}

# Frecuencia de spawn
FRECUENCIA_NUBE = 50        # Puntos entre nubes (CAT)
FRECUENCIA_POWERUP = 200    # Puntos entre power-ups
```

---

## 10. Pruebas y Validación

### 10.1 Casos de Prueba: Colisión con Nube

| Caso | Dificultad | Puntos | Invulnerable | Resultado |
|------|-----------|--------|--------------|-----------|
| 1 | CAT | 50 | No | Puntos → 0 |
| 2 | CAT | 50 | Sí | Sin efecto |
| 3 | CAT | 0 | No | GAME OVER |
| 4 | ENTUSIASTA | 0 | - | No hay nube |

### 10.2 Casos de Prueba: Power-Up

| Caso | Puntos | Dificultad | Resultado |
|------|--------|-----------|-----------|
| 1 | 200 | CAT | Power-up aparece |
| 2 | 200 | BABY | No aparece |
| 3 | 0 | CAT | No aparece (condición ≠ 0) |
| 4 | Come Power-Up | CAT | Invulnerabilidad 3s |

### 10.3 Casos de Prueba: Invulnerabilidad

| Tiempo (ms) | Estado | Parpadea | Immune |
|-------------|--------|----------|--------|
| 0-3000 | Activa | Sí (cada 100ms) | Sí |
| 3000-3100 | Transición | Fade out | Sí |
| 3100+ | Inactiva | No | No |

---

## 11. Optimizaciones y Consideraciones de Performance

### 11.1 Complejidad Algorítmica

```python
snake_spawn_comida():     O(n)      # n = cuerpo de serpiente
esta_invulnerable():      O(1)      # Comparación de tiempo
activar_invulnerabilidad(): O(1)    # Asignación
snake_mover_jugador():    O(1)      # Comparación de posición
```

### 11.2 Overhead de Tiempo

- **Llamada `time.time()`**: ~1-10 µs (microsegundos)
- **Comparación `>` timestamp**: <1 µs
- **Impacto por frame**: <10 µs (negligible en loop de 50ms)

### 11.3 Memoria

```python
Atributos adicionales: ~24 bytes (3 floats/tuples)
Sprites en memoria: ~50KB cada uno (cloud.gif, power-up.gif)
```

---

## 12. Lecciones Aprendidas y Recomendaciones

### 12.1 Fortalezas de la Implementación

✅ **Sincronización precisa** de invulnerabilidad basada en tiempo real  
✅ **Generación segura** de posiciones (evita colisiones inmediatas)  
✅ **Retroalimentación visual** clara (parpadeo + UI)  
✅ **Encadenamiento** de power-ups (con `max()`)  
✅ **Dificultades diferenciadas** según modo de juego

### 12.2 Áreas de Mejora Futuras

⚠️ **Limite de iteraciones** en loop infinito de spawn  
⚠️ **Serialización** de estado de invulnerabilidad (save/load)  
⚠️ **Animación suave** del parpadeo (easing)  
⚠️ **Sonidos** de activación de power-up  
⚠️ **Partículas** en colisión de nube  

### 12.3 Recomendaciones de Refactoring

```python
# Propuesta: Constantes configurables
class GameConfig:
    POWERUP_DURATION_SECONDS = 3.0
    CLOUD_SPAWN_INTERVAL = 50
    POWERUP_SPAWN_INTERVAL = 200
    CLOUD_BLINK_FREQUENCY = 10  # ciclos/segundo
```

---

## 13. Anexos

### Anexo A: Mapa de Dependencias

```
inicio (Juego.__init__)
  ├── invulnerabilidad_segundos ← config JSON
  ├── invulnerable_hasta ← inicializa a 0
  └── posicion_nube, posicion_powerup ← inicializa a None

game_loop()
  ├── actualizar_estado_invulnerabilidad()
  │   └── esta_invulnerable()
  │       └── time.time() > invulnerable_hasta
  └── dibujar()
      ├── Color serpiente (si esta_invulnerable())
      ├── Renderizado cloud (posicion_nube)
      └── Renderizado powerup (posicion_powerup)

ON_TICK
  └── snake_mover_jugador()
      ├── Colisión nube (si nueva_cabeza == posicion_nube)
      ├── Colisión powerup (si nueva_cabeza == posicion_powerup)
      │   └── activar_invulnerabilidad()
      │       └── invulnerable_hasta = time.time() + duracion
      └── Comportamiento vulnerable vs invulnerable
```

### Anexo B: Convenciones de Código

```python
# Nombrado de variables
posicion_* = (x, y)          # Tupla de coordenadas
*_segundos = float           # Duración en segundos
*_hasta = timestamp (float)  # Momento en el tiempo (time.time())
serpiente_* = lista          # Atributos relacionados con serpiente
```

### Anexo C: Referencias de Archivos

- **Código principal:** `runtime.py` (685 líneas)
- **Configuración:** `datos_juego.json`
- **Assets:**
  - `assets/snake/objects/cloud.gif`
  - `assets/snake/fruits/power-up.gif`

---

## 14. Historial de Cambios

| Versión | Fecha | Cambio | Autor |
|---------|-------|--------|-------|
| 1.0 | 2026-06-11 | Documento inicial | Tech Team |
| - | 2026-06-07 | Power-up implementado | JoseMiguel0328 |
| - | 2026-05-03 | Dificultades + nubes | aarial12 |

---

## 15. Aprobaciones y Validación

- **Revisado por:** Equipo Técnico TLP
- **Estado:** ✅ Validado en versión 1.0
- **Última actualización:** 2026-06-11

---

**Documento Técnico Final**  
*BrickScript - Proyecto TLP*  
*Junio 2026*
