# -*- coding: utf-8 -*-
# runtime.py (VERSION CON INTERFAZ GRAFICA USANDO Tkinter y caracteres ASCII unicamente)
from Queue import Queue
import sys
import json
import time
import random
import bisect
# Tkinter es la libreria GUI estandar de Python, compatible con 2.7
import Tkinter as tk
from Tkinter import *
import tkMessageBox # Necesario para el GAME OVER
# Quitamos os y msvcrt ya que la GUI maneja el dibujo y el input
import os
# import msvcrt 

class Juego:
    def __init__(self, datos_juego):
        self.datos_juego = datos_juego
        self.tipo_juego = self.datos_juego.get('tipo_juego', 'TETRIS')
        config = self.datos_juego.get('config', {})
        self.ancho = config.get('grid_size', [10, 20])[0]
        self.alto = config.get('grid_size', [10, 20])[1]
        self.grid = [[0 for _ in range(self.ancho)] for _ in range(self.alto)]
        self.puntuacion = 0
        self.juego_terminado = False
        
        # --- Configuracion de la GUI ---
        self.root = tk.Tk()
        self.root.title("BrickScript - " + self.tipo_juego)
        # Configurar la accion al cerrar la ventana ('X' de la barra de titulo)
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_ventana)
        
        if(self.tipo_juego == 'TANKS'):
            self.taman_celda = 5 # Pixeles por celda
        else:
            self.taman_celda = 25;
        self.ancho_canvas = self.ancho * self.taman_celda
        self.alto_canvas = self.alto * self.taman_celda
        
        # Canvas para dibujar el juego
        self.canvas = tk.Canvas(self.root, width=self.ancho_canvas, height=self.alto_canvas, bg='#111111')
        self.canvas.pack(side=tk.LEFT, padx=10, pady=10)

        # Marco lateral para la puntuacion y controles
        self.marco_score = tk.Frame(self.root, width=150, height=self.alto_canvas, bg='#222222')
        self.marco_score.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        
        self.label_score = tk.Label(self.marco_score, text="PUNTUACION\n0", bg='#222222', fg='white', font=('Consolas', 16, 'bold'))
        self.label_score.pack(pady=40, padx=10)
        
        # Nota: Se ha eliminado 'Q: Salir' de los controles en pantalla
        self.label_controles = tk.Label(self.marco_score, text="CONTROLES\nFlechas: Mover/Rotar", bg='#222222', fg='gray', font=('Consolas', 10))
        self.label_controles.pack(pady=20, padx=10)

        # Configurar eventos de teclado. Usamos <Key> para capturar cualquier tecla
        self.root.bind('<Key>', self.manejar_input_gui)

        if self.tipo_juego == 'TANKS':
            self.player_position = [self.alto/2, self.alto/2, 'UP']
            self.tank_body = self.datos_juego['shapes']['TANK'][1][0]
            self.velocidad_gravedad = 0.4
            self.color_pieza = '#3B6294'
            self.bullets = Queue()
            self.bullets_q = 0
            self.velocidad_gravedad = 0.01


        if self.tipo_juego == 'TETRIS':
            self.pieza_actual = None
            self.pieza_x, self.pieza_y, self.pieza_rotacion = 0, 0, 0
            self.velocidad_gravedad = 0.4
            self.color_pieza = None
            self.power_up_piece = None
            self.power_up_x, self.power_up_y = 0, 0

        if self.tipo_juego == 'SNAKE':
            self.serpiente_cuerpo = []
            self.serpiente_direccion = (1, 0)
            self.posicion_comida = None
            self.posicion_veneno = None
            self.posicion_nube = None
            self.velocidad_gravedad = 0.15
            self.color_pieza = None
            self.dificultad = 'CLASSIC' if 'dificulty' not in self.datos_juego.get('config') else self.datos_juego['config']['dificulty']
            self.crecimiento_pendiente = 0

            shapes = self.datos_juego.get('shapes', {})
            self.usar_nyancat = 'CAT' in shapes
            self.img_nyancat = {}
            self.img_nyancat_body = {}
            self.img_nyancat_trail = {}
            
            #Sprites
            if self.dificultad != 'CLASSIC':
                base_dir = os.path.dirname(os.path.abspath(__file__))
                food_path = os.path.join(base_dir, 'assets', 'snake', 'fruits', 'food.png')
                poison_path = os.path.join(base_dir, 'assets', 'snake', 'fruits', 'poison1.png')
                cloud_path = os.path.join(base_dir, 'assets', 'snake', 'objects', 'cloud.png')
                self.img_food = tk.PhotoImage(file=food_path) if os.path.exists(food_path) else None
                self.img_poison = tk.PhotoImage(file=poison_path) if os.path.exists(poison_path) else None
                self.img_cloud = tk.PhotoImage(file=cloud_path) if os.path.exists(cloud_path) else None

            if self.usar_nyancat:

                base = 'snake/nyancat/'
                direcciones = {
                    'RIGHT': base + 'head/nyancat_der.png',
                    'LEFT':  base + 'head/nyancat_izq.png',
                    'UP':    base + 'head/nyancat_arr.png',
                    'DOWN':  base + 'head/nyancat_abj.png'
                }

                body_files = {
                    'RIGHT': base + 'body/nyancat_body_der.png',
                    'LEFT':  base + 'body/nyancat_body_izq.png',
                    'UP':    base + 'body/nyancat_body_arr.png',
                    'DOWN':  base + 'body/nyancat_body_abj.png'
                }
                trail_files = {
                    'RIGHT': base + 'trail/nyancat_trail_der.png',
                    'LEFT':  base + 'trail/nyancat_trail_izq.png',
                    'UP':    base + 'trail/nyancat_trail_arr.png',
                    'DOWN':  base + 'trail/nyancat_trail_abj.png'
                }
            

                for dir_name, archivo in direcciones.items():
                    img_path = os.path.join(base_dir, 'assets', archivo)
                    self.img_nyancat[dir_name] = tk.PhotoImage(file=img_path)

                for dir_name, archivo in body_files.items():
                    img_path = os.path.join(base_dir, 'assets', archivo)
                    self.img_nyancat_body[dir_name] = tk.PhotoImage(file=img_path)
                for dir_name, archivo in trail_files.items():
                    img_path = os.path.join(base_dir, 'assets', archivo)
                    self.img_nyancat_trail[dir_name] = tk.PhotoImage(file=img_path)
                    
        self.timer_gravedad = 0
        self.ejecutar_evento('ON_START')
        self.timer_id = None # Para controlar el loop de Tkinter

    def run(self):
        # Inicia el ciclo principal de juego de Tkinter
        self.root.after(50, self.game_loop) 
        self.root.mainloop() 

    def game_loop(self):
        if self.juego_terminado:
            self.mostrar_game_over()
            return
        
        if self.tipo_juego == 'SNAKE'and self.dificultad == 'CAT':
            self.velocidad_gravedad = 0.075
        self.dibujar()
        # Logica de TICK/Gravedad
        # El loop se ejecuta cada 50ms (0.05 segundos)
        self.timer_gravedad += 0.05 
        if self.timer_gravedad >= self.velocidad_gravedad:
            self.timer_gravedad = 0
            self.ejecutar_evento('ON_TICK')
        
        

        # Programa el siguiente ciclo de juego
        self.timer_id = self.root.after(50, self.game_loop)

    def cerrar_ventana(self):
        # Detiene el loop de juego de forma segura
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
        self.root.destroy()
        sys.exit(0)

    def manejar_input_gui(self, event):
        key = event.keysym.upper()
        
        if self.tipo_juego == 'TANKS':
            if key == 'UP': self.ejecutar_evento('ON_KEY_UP')
            elif key == 'DOWN': self.ejecutar_evento('ON_KEY_DOWN')
            elif key == 'LEFT': self.ejecutar_evento('ON_KEY_LEFT')
            elif key == 'RIGHT': self.ejecutar_evento('ON_KEY_RIGHT')
            elif key == 'SPACE': self.ejecutar_evento('ON_KEY_SPACE')
        
        # Mapeo de teclas de flecha
        if self.tipo_juego == 'TETRIS':
            if key == 'UP': self.ejecutar_evento('ON_KEY_UP')
            elif key == 'DOWN': self.ejecutar_evento('ON_KEY_DOWN')
            elif key == 'LEFT': self.ejecutar_evento('ON_KEY_LEFT')
            elif key == 'RIGHT': self.ejecutar_evento('ON_KEY_RIGHT')

        if self.tipo_juego == 'TETRIS' and self.power_up_piece:
        # Power-up piece movement (no collision checking)
            if key == 'UP': self.power_up_y = max(0, self.power_up_y - 1)
            elif key == 'DOWN': self.power_up_y = min(self.alto - 1, self.power_up_y + 1)
            elif key == 'LEFT': self.power_up_x = max(0, self.power_up_x - 1)
            elif key == 'RIGHT': self.power_up_x = min(self.ancho - 1, self.power_up_x + 1)
            elif key == 'SPACE': self.power_up_place()

        elif self.tipo_juego == 'SNAKE':
            # Llamamos a las funciones internas para Snake
            if key == 'UP': self.snake_cambiar_direccion('UP')
            elif key == 'DOWN': self.snake_cambiar_direccion('DOWN')
            elif key == 'LEFT': self.snake_cambiar_direccion('LEFT')
            elif key == 'RIGHT': self.snake_cambiar_direccion('RIGHT')

    def random_color(self):
        colores = self.datos_juego['colors']
        registros = len(colores)
        if registros > 0:
            index = random.randint(0, registros - 1)
            return '#' + str(self.datos_juego['colors'][index])
        else:
            return '#000FFF'

    def dibujar(self):
        self.canvas.delete("all") # Borrar todo en cada frame
        self.label_score.config(text="PUNTUACION\n" + str(self.puntuacion))
        
        # Colores
        COLOR_GRID_FIJA = '#343434' # Gris oscuro para las celdas fijadas (Tetris)
        COLOR_PIEZA = self.color_pieza
        COLOR_SNAKE_CABEZA = '#00FF00' # Verde brillante
        COLOR_SNAKE_CUERPO = '#33CC33' # Verde normal
        COLOR_FOOD = '#FF0000'      # Rojo
        COLOR_VENENO = '#FF0199'
        COLOR_NUBE = '#3B6294'

        # 1. Dibujar la cuadricula estatica (grid base)
        for y in range(self.alto):
            for x in range(self.ancho):
                if self.grid[y][x] == 1:
                    self.dibujar_celda(x, y, COLOR_GRID_FIJA)

        if self.tipo_juego == 'TANKS':

            for y_offset, fila in enumerate(self.tank_body):
                for x_offset, celda in enumerate(fila):
                    if celda == 1:
                        self.dibujar_celda(self.player_position[0] + x_offset, self.player_position[1] + y_offset, COLOR_PIEZA)
                        


        # 2. Dibujar la pieza actual de Tetris
        if self.tipo_juego == 'TETRIS' and self.pieza_actual:
            if self.power_up_piece:
                self.dibujar_celda(self.power_up_x, self.power_up_y, '#FFFF00')
            matriz_pieza = self.pieza_actual[self.pieza_rotacion]
            for y_offset, fila in enumerate(matriz_pieza):
                for x_offset, celda in enumerate(fila):
                    if celda == 1:
                        self.dibujar_celda(self.pieza_x + x_offset, self.pieza_y + y_offset, COLOR_PIEZA)
        
        # 3. Dibujar Snake y Comida
        if self.tipo_juego == 'SNAKE':
            if self.posicion_comida:
                x, y = self.posicion_comida
                if getattr(self, 'img_food', None):
                    ts = self.taman_celda
                    self.canvas.create_image(x * ts, y * ts, image=self.img_food, anchor='nw')
                else:
                    self.dibujar_celda(x, y, COLOR_FOOD)

            if self.posicion_veneno:
                x, y = self.posicion_veneno
                if getattr(self, 'img_poison', None):
                    ts = self.taman_celda
                    self.canvas.create_image(x * ts, y * ts, image=self.img_poison, anchor='nw')
                else:
                    self.dibujar_celda(x, y, COLOR_VENENO)

            if self.posicion_veneno:
                x, y = self.posicion_nube
                if getattr(self, 'img_poison', None):
                    ts = self.taman_celda
                    self.canvas.create_image(x * ts, y * ts, image=self.img_cloud, anchor='nw')
                else:
                    self.dibujar_celda(x, y, COLOR_NUBE)



            for i, segmento in enumerate(self.serpiente_cuerpo):
                x, y = segmento
                direccion_segmento = self.obtener_direccion_segmento(i)

                if self.usar_nyancat:
                    if i == 0:
                        self.dibujar_nyancat(x, y, direccion_segmento)
                    elif i == 1:
                        self.dibujar_nyancat_body(x, y, direccion_segmento)
                    else:
                        self.dibujar_nyancat_trail(x, y, direccion_segmento)
                else:
                    shape_names = list(self.datos_juego.get('shapes', {}).keys())
                    shape_type = shape_names[0] if shape_names else 'PIXEL'

                    if i == 0 and shape_type == 'PIXEL':
                        self.dibujar_celda(x, y, COLOR_SNAKE_CABEZA)
                    elif i == 0 and shape_type == 'TRIANGLE':
                        self.dibujar_triangulo(x, y, COLOR_SNAKE_CABEZA, direccion_segmento)
                    elif i == 0 and shape_type == 'CIRCLE':
                        self.dibujar_triangulo(x, y, COLOR_SNAKE_CABEZA)
                    elif shape_type == 'CIRCLE':
                        self.dibujar_circulo(x, y, COLOR_SNAKE_CUERPO)
                    elif shape_type == 'TRIANGLE':
                        self.dibujar_triangulo(x, y, COLOR_SNAKE_CUERPO, direccion_segmento)
                    else:
                        self.dibujar_celda(x, y, COLOR_SNAKE_CUERPO)

    def dibujar_celda(self, x, y, color):
        ts = self.taman_celda # Alias para taman de celda
        x1, y1 = x * ts, y * ts
        x2, y2 = x1 + ts, y1 + ts
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline='#000000')

    def dibujar_circulo(self, x, y, color):
        ts = self.taman_celda # Alias para taman de celda
        x1, y1 = x * ts, y * ts
        x2, y2 = x1 + ts, y1 + ts
        self.canvas.create_oval(x1, y1, x2, y2, fill=color, outline='#000000')

    def dibujar_triangulo(self, x, y, color, direccion=(1, 0)):
        ts = self.taman_celda
        x0 = x * ts
        y0 = y * ts

        if direccion == (1, 0):      
            x1, y1 = x0, y0
            x2, y2 = x0, y0 + ts
            x3, y3 = x0 + ts, y0 + ts / 2
        elif direccion == (-1, 0):   
            x1, y1 = x0 + ts, y0
            x2, y2 = x0 + ts, y0 + ts
            x3, y3 = x0, y0 + ts / 2
        elif direccion == (0, -1):   
            x1, y1 = x0, y0 + ts
            x2, y2 = x0 + ts, y0 + ts
            x3, y3 = x0 + ts / 2, y0
        else:                        
            x1, y1 = x0, y0
            x2, y2 = x0 + ts, y0
            x3, y3 = x0 + ts / 2, y0 + ts

        self.canvas.create_polygon(x1, y1, x2, y2, x3, y3, fill=color, outline='#000000')

    def dibujar_nyancat(self, x, y, direccion=(1, 0)):
        ts = self.taman_celda
        x1, y1 = x * ts, y * ts
        
        # Mapeo de dirección a imagen
        dir_map = {
            (1, 0): 'RIGHT',
            (-1, 0): 'LEFT',
            (0, -1): 'UP',
            (0, 1): 'DOWN'
        }
        
        dir_key = dir_map.get(direccion, 'RIGHT')
        
        if dir_key in self.img_nyancat and self.img_nyancat[dir_key]:
            self.canvas.create_image(x1, y1, image=self.img_nyancat[dir_key], anchor='nw')
            return
                
        # Fallback: dibujar triángulo si NyanCat no está disponible
        self.dibujar_triangulo(x, y, '#00FF00')

    def dibujar_nyancat_body(self, x, y, arg=None):
        if isinstance(arg, tuple):
            direccion = arg
            color = '#33CC33'
        else:
            color = arg or '#33CC33'
            direccion = (1, 0)

        dir_map = {(1, 0): 'RIGHT', (-1, 0): 'LEFT', (0, -1): 'UP', (0, 1): 'DOWN'}
        dir_key = dir_map.get(direccion, 'RIGHT')

        img = None
        if hasattr(self, 'img_nyancat_body'):
            img = self.img_nyancat_body.get(dir_key)
        if not img:
            img = getattr(self, 'img_nyancat', {}).get(dir_key)

        if img:
            ts = self.taman_celda
            self.canvas.create_image(x * ts, y * ts, image=img, anchor='nw')
            return
        # Fallback 
        self.dibujar_circulo(x, y, color)

    def dibujar_nyancat_trail(self, x, y, direccion=(1, 0)):
        dir_map = {(1, 0): 'RIGHT', (-1, 0): 'LEFT', (0, -1): 'UP', (0, 1): 'DOWN'}
        dir_key = dir_map.get(direccion, 'RIGHT')

        img = None
        if hasattr(self, 'img_nyancat_trail'):
            img = self.img_nyancat_trail.get(dir_key)
        if not img:
            img = getattr(self, 'img_nyancat', {}).get(dir_key)

        if img:
            ts = self.taman_celda
            self.canvas.create_image(x * ts, y * ts, image=img, anchor='nw')
            return
        # Fallback: triángulo orientado
        self.dibujar_triangulo(x, y, '#228822', direccion)

    def ejecutar_evento(self, nombre_evento):
        if nombre_evento in self.datos_juego['events']:
            for accion in self.datos_juego['events'][nombre_evento]:
                verbo, objeto = accion.get('accion'), accion.get('objeto')
                
                if verbo == 'INCREASE_SCORE':
                    self.puntuacion += int(objeto)
                    self.ejecutar_evento('SECRET')
                
                if verbo == 'GAME_OVER': self.juego_terminado = True

                if self.tipo_juego == 'TETRIS':
                    if verbo == 'SPAWN' and objeto == 'RANDOM_SHAPE': self.tetris_spawn_pieza()
                    if verbo == 'SPAWN' and objeto == 'POWER_UP': self.power_up()
                    if verbo == 'MOVE': self.tetris_mover_pieza(accion['params'][0])
                    if verbo == 'ROTATE': self.tetris_rotar_pieza()

                if self.tipo_juego == 'SNAKE':
                    
                    if verbo == 'SPAWN' and objeto == 'PLAYER': self.snake_spawn_jugador(accion)
                    if verbo == 'SPAWN' and objeto == 'FOOD': self.snake_spawn_comida()
                    if verbo == 'MOVE' and objeto == 'PLAYER': self.snake_mover_jugador()
                    if verbo == 'GROW': self.snake_crecer()

                if self.tipo_juego == 'TANKS':
                    self.spawn_player()
                    if verbo == 'MOVE': self.move_tank(accion['params'][0])
                    if verbo == 'SHOT': self.shoot()
                    if verbo == 'UPDATE': self.update_bullets()
                    
    # METODOS DE LOGICA DE JUEGO (MANTENIDOS DEL ARCHIVO ORIGINAL)
    # ---------------------------------------------------------------------

    def power_up(self):
        self.power_up_piece = [[[1]]] 
        self.power_up_color = '#FFFF00'  
        self.power_up_x = self.ancho / 2
        self.power_up_y = self.alto / 2

    def power_up_place(self):
        if self.power_up_piece:
            self.grid[self.power_up_y][self.power_up_x] = 1  # Place at that position
            self.power_up_piece = None  # Consume the power-up

    def spawn_player(self):
        shapes = self.datos_juego['shapes']

    def update_bullets(self):
        if (self.bullets_q == 0):
            return

        for i in range(self.bullets_q):
            bullet = self.bullets.get()
            if (bullet[0] > self.ancho or bullet[0] < 0 or bullet[1] > self.alto or bullet[1] < 0):
                self.bullets_q -= 1 
                continue
            
            print("bala en ",bullet[0],", ",bullet[1])
            bullet[1] -= 1
            
            self.dibujar_circulo(bullet[0], bullet[1], '#FF0000')
            self.bullets.put(bullet)
    
    def shoot(self):
        self.bullets.put([self.player_position[0] , self.player_position[1]])
        self.bullets_q += 1

    def move_tank(self, direction):
        if self.collition(direction):
            return
        if direction == 'LEFT':
            self.player_position[0] -= 1
            self.rotate_tank(direction)
        elif direction == 'UP':
            self.player_position[1] -= 1
            self.rotate_tank(direction)
        elif direction == 'DOWN':
            self.player_position[1] += 1
            self.rotate_tank(direction)
        elif direction == 'RIGHT':
            self.player_position[0] += 1
            self.rotate_tank(direction)

    def rotate_tank(self, direction):
        if direction == 'LEFT':
            self.tank_body = self.datos_juego['shapes']['TANK'][1][1]
        elif direction == 'UP':
            self.tank_body = self.datos_juego['shapes']['TANK'][1][0]
        elif direction == 'DOWN':
            self.tank_body = self.datos_juego['shapes']['TANK'][1][2]
        elif direction == 'RIGHT':
            self.tank_body = self.datos_juego['shapes']['TANK'][1][3]

    def collition(self, direction):
        if direction == 'LEFT':
            if self.player_position[0] < 1:
                return 1
        elif direction == 'UP':
            if self.player_position[1] < 1:
                return 1
        elif direction == 'DOWN':
            if self.player_position[1] > self.alto - 7:
                return 1
        elif direction == 'RIGHT':
            if self.player_position[0] > self.ancho-7:
                return 1
        return 0
    
    def tetris_spawn_pieza(self):
        shapes = self.datos_juego['shapes']
        nombres = list(shapes.keys())

        pesos_acumulados = []
        total = 0
        for nombre in nombres:
            total += shapes[nombre][0]
            pesos_acumulados.append(total)

        punto = random.uniform(0, total)
        indice = bisect.bisect(pesos_acumulados, punto)
        nombre_pieza = nombres[indice]

        self.pieza_actual = shapes[nombre_pieza][1]
        self.color_pieza = self.random_color()
        self.pieza_x, self.pieza_y, self.pieza_rotacion = self.ancho / 2 - 2, 0, 0
        if self.tetris_verificar_colision(self.pieza_x, self.pieza_y, self.pieza_rotacion):
            self.juego_terminado = True

    def tetris_mover_pieza(self, direccion):
        if not self.pieza_actual: return
        dx, dy = 0, 0
        if direccion == 'LEFT': dx = -1
        elif direccion == 'RIGHT': dx = 1
        elif direccion == 'DOWN': dy = 1
        if not self.tetris_verificar_colision(self.pieza_x + dx, self.pieza_y + dy, self.pieza_rotacion):
            self.pieza_x += dx
            self.pieza_y += dy
        elif dy > 0:
            self.tetris_fijar_pieza()

    def tetris_rotar_pieza(self):
        if not self.pieza_actual: return
        nueva_rotacion = (self.pieza_rotacion + 1) % len(self.pieza_actual)
        if not self.tetris_verificar_colision(self.pieza_x, self.pieza_y, nueva_rotacion):
            self.pieza_rotacion = nueva_rotacion

    def tetris_fijar_pieza(self):
        matriz_pieza = self.pieza_actual[self.pieza_rotacion]
        for y_offset, fila in enumerate(matriz_pieza):
            for x_offset, celda in enumerate(fila):
                if celda == 1:
                    if 0 <= self.pieza_y + y_offset < self.alto and 0 <= self.pieza_x + x_offset < self.ancho:
                        self.grid[self.pieza_y + y_offset][self.pieza_x + x_offset] = 1
        self.pieza_actual = None
        self.tetris_limpiar_lineas()
        self.ejecutar_evento('ON_START')

    def tetris_verificar_colision(self, x, y, rotacion):
        if not self.pieza_actual: return False
        matriz_pieza = self.pieza_actual[rotacion]
        for y_offset, fila in enumerate(matriz_pieza):
            for x_offset, celda in enumerate(fila):
                if celda == 1:
                    nuevo_x, nuevo_y = x + x_offset, y + y_offset
                    if not (0 <= nuevo_x < self.ancho and 0 <= nuevo_y < self.alto and self.grid[nuevo_y][nuevo_x] == 0):
                        return True
        return False

    def tetris_limpiar_lineas(self):
        nuevo_grid = [fila for fila in self.grid if not all(fila)]
        lineas_limpias = self.alto - len(nuevo_grid)
        if lineas_limpias > 0:
            self.grid = [[0] * self.ancho for _ in range(lineas_limpias)] + nuevo_grid

            if lineas_limpias == 4:
                self.ejecutar_evento('ON_SECRET')

            for _ in range(lineas_limpias): self.ejecutar_evento('ON_LINE_CLEAR')


        self.crecimiento_pendiente += 1


    # METODOS DE SALIDA (ADAPTADOS A GUI)
    # -----------------------------------

    def mostrar_game_over(self):
        # Muestra una ventana de mensaje de Tkinter
        tkMessageBox.showinfo("Juego Terminado", "Puntuacion Final: " + str(self.puntuacion))
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "Uso: python runtime.py <archivo_juego.json>"
        sys.exit(1)
    archivo_juego = sys.argv[1]
    try:
        with open(archivo_juego, 'r') as f:
            datos_juego = json.load(f)
    except IOError:
        print "Error: No se pudo encontrar el archivo " + archivo_juego
        sys.exit(1)
    juego = Juego(datos_juego)
    juego.run()
    