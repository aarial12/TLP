# -*- coding: utf-8 -*-
# runtime.py (VERSION INTEGRADA Y RETROCOMPATIBLE - Python 2.7)
from Queue import Queue
import sys
import json
import time
import random
import bisect


# Tkinter compatible con Python 2.7
import Tkinter as tk
from Tkinter import *
import tkMessageBox 
import os

import tanks

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

        # --- Carga de Configuración de Entidades desde datos_juego ---
        self.config_entidades = self.datos_juego.get('entidades', self.datos_juego.get('entities', {}))

        # --- Configuración Base de la GUI ---
        self.root = tk.Tk()
        self.root.title("BrickScript - " + self.tipo_juego)
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_ventana)
        
        # Ajuste dinámico del tamaño de celda según el juego
        if self.tipo_juego == 'TANKS':
            self.taman_celda = 5
        else:
            self.taman_celda = 25
            
        self.ancho_canvas = self.ancho * self.taman_celda
        self.alto_canvas = self.alto * self.taman_celda
        
        self.canvas = tk.Canvas(self.root, width=self.ancho_canvas, height=self.alto_canvas, bg='#111111')
        self.canvas.pack(side=tk.LEFT, padx=10, pady=10)

        self.marco_score = tk.Frame(self.root, width=150, height=self.alto_canvas, bg='#222222')
        self.marco_score.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        
        self.label_score = tk.Label(self.marco_score, text="PUNTUACION\n0", bg='#222222', fg='white', font=('Consolas', 16, 'bold'))
        self.label_score.pack(pady=40, padx=10)
        
        self.label_estado = tk.Label(self.marco_score, text="", bg='#222222', fg='#ffd700', font=('Consolas', 11, 'bold'))
        self.label_estado.pack(pady=10, padx=10)

        self.label_controles = tk.Label(self.marco_score, text="CONTROLES\nFlechas: Mover/Rotar", bg='#222222', fg='gray', font=('Consolas', 10))
        self.label_controles.pack(pady=20, padx=10)

        self.root.bind('<Key>', self.manejar_input_gui)

        # --- Inicialización de Estados Específicos por Juego ---
        
        # JUEGO: TANKS
        if self.tipo_juego == 'TANKS':
            self.entidades = []
            
            # Obtener datos de PLAYER desde datos_juego si existen
            cfg_player = self.config_entidades.get('PLAYER', {})
            hp_player = cfg_player.get('hp', 3)
            
            self.player = tanks.Tank(self.ancho/2, self.alto/2, 0, hp=hp_player, tipo='PLAYER')
            self.player.velocidad = cfg_player.get('velocidad', 1)
            self.player.color = cfg_player.get('color', "#05234B")
            self.entidades.append(self.player)
            
            self.tank_body = self.datos_juego['shapes']['TANK'][1]
            self.map = self.datos_juego['shapes']['MAP'][1]
            self.level = 1
            
            self.velocidad_gravedad = 0.01  
            self.color_tank = self.player.color
            self.color_pieza = '#3B6294'
            self.color_enemigo = '#F77777'
            self.color_jefe = '#008800'
            self.bullets = Queue()
            self.bullets_q = 0
            self.tick = 0
            self.boss_spawned = False
            self.siguiente_hito_boss = 300
            self.explosiones_activas = []
            self.puntos_spawn = []
            self.balas_maximas = 5
            self.balas_actuales = self.balas_maximas
            self.recargando = False
            self.tiempo_recarga = 1.5 
            self.boss_derrotado = False
            self.inicializar_grid_mapa()
            self.hammer_pos = None  # Stores (x, y) coordinates of active hammer

        # JUEGO: TETRIS
        if self.tipo_juego == 'TETRIS':
            self.pieza_actual = None
            self.pieza_x, self.pieza_y, self.pieza_rotacion = 0, 0, 0
            self.velocidad_gravedad = 0.4
            self.color_pieza = None
            self.power_up_piece = None
            self.power_up_x, self.power_up_y = 0, 0

        # JUEGO: SNAKE
        if self.tipo_juego == 'SNAKE':
            self.serpiente_cuerpo = []
            self.serpiente_direccion = (1, 0)
            self.posicion_comida = None
            self.posicion_veneno = None
            self.posicion_nube = None
            self.posicion_powerup = None
            self.velocidad_gravedad = 0.15
            self.color_pieza = None
            self.dificultad = 'CLASSIC' if 'dificulty' not in self.datos_juego.get('config', {}) else self.datos_juego['config']['dificulty']
            self.crecimiento_pendiente = 0
            self.invulnerabilidad_segundos = float(self.datos_juego.get('config', {}).get('powerup_invulnerability', 3))
            self.invulnerable_hasta = 0

            shapes = self.datos_juego.get('shapes', {})
            self.usar_nyancat = 'CAT' in shapes
            self.img_nyancat = {}
            self.img_nyancat_body = {}
            self.img_nyancat_trail = {}
            
            base_dir = os.path.dirname(os.path.abspath(__file__))
            for ext in ['.gif', '.png']:
                food_path = os.path.join(base_dir, 'assets', 'snake', 'fruits', 'food' + ext)
                poison_path = os.path.join(base_dir, 'assets', 'snake', 'fruits', 'poison' + ext if ext == '.gif' else 'poison1' + ext)
                cloud_path = os.path.join(base_dir, 'assets', 'snake', 'objects', 'cloud' + ext)
                powerup_path = os.path.join(base_dir, 'assets', 'snake', 'fruits', 'power-up' + ext)
                
                if os.path.exists(food_path) and not getattr(self, 'img_food', None): self.img_food = tk.PhotoImage(file=food_path)
                if os.path.exists(poison_path) and not getattr(self, 'img_poison', None): self.img_poison = tk.PhotoImage(file=poison_path)
                if os.path.exists(cloud_path) and not getattr(self, 'img_cloud', None): self.img_cloud = tk.PhotoImage(file=cloud_path)
                if os.path.exists(powerup_path) and not getattr(self, 'img_powerup', None): self.img_powerup = tk.PhotoImage(file=powerup_path)

            if self.usar_nyancat:
                base = 'snake/nyancat/'
                for ext in ['.gif', '.png']:
                    direcciones = {'RIGHT': base + 'head/nyancat_der' + ext, 'LEFT': base + 'head/nyancat_izq' + ext, 'UP': base + 'head/nyancat_arr' + ext, 'DOWN': base + 'head/nyancat_abj' + ext}
                    body_files = {'RIGHT': base + 'body/nyancat_body_der' + ext, 'LEFT': base + 'body/nyancat_body_izq' + ext, 'UP': base + 'body/nyancat_body_arr' + ext, 'DOWN': base + 'body/nyancat_body_abj' + ext}
                    trail_files = {'RIGHT': base + 'trail/nyancat_trail_der' + ext, 'LEFT': base + 'trail/nyancat_trail_izq' + ext, 'UP': base + 'trail/nyancat_trail_arr' + ext, 'DOWN': base + 'trail/nyancat_trail_abj' + ext}
                    
                    for dir_name, archivo in direcciones.items():
                        p = os.path.join(base_dir, 'assets', archivo)
                        if os.path.exists(p) and dir_name not in self.img_nyancat: self.img_nyancat[dir_name] = tk.PhotoImage(file=p)
                    for dir_name, archivo in body_files.items():
                        p = os.path.join(base_dir, 'assets', archivo)
                        if os.path.exists(p) and dir_name not in self.img_nyancat_body: self.img_nyancat_body[dir_name] = tk.PhotoImage(file=p)
                    for dir_name, archivo in trail_files.items():
                        p = os.path.join(base_dir, 'assets', archivo)
                        if os.path.exists(p) and dir_name not in self.img_nyancat_trail: self.img_nyancat_trail[dir_name] = tk.PhotoImage(file=p)

        self.timer_gravedad = 0
        self.ejecutar_evento('ON_START')
        self.timer_id = None 

    def run(self):
        self.root.after(50, self.game_loop) 
        self.root.mainloop() 

    def game_loop(self):
        if self.juego_terminado:
            self.mostrar_game_over()
            return
        
        if self.tipo_juego == 'SNAKE' and getattr(self, 'dificultad', '') == 'CAT':
            self.velocidad_gravedad = 0.075

        self.timer_gravedad += 0.05 
        if self.timer_gravedad >= self.velocidad_gravedad:
            self.timer_gravedad = 0
            self.ejecutar_evento('ON_TICK')

        if self.tipo_juego == 'SNAKE':
            self.actualizar_estado_invulnerabilidad()

        self.dibujar()
        self.timer_id = self.root.after(50, self.game_loop)

    def cerrar_ventana(self):
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
        
        if self.tipo_juego == 'TETRIS':
            if key == 'UP': self.ejecutar_evento('ON_KEY_UP')
            elif key == 'DOWN': self.ejecutar_evento('ON_KEY_DOWN')
            elif key == 'LEFT': self.ejecutar_evento('ON_KEY_LEFT')
            elif key == 'RIGHT': self.ejecutar_evento('ON_KEY_RIGHT')

        if self.tipo_juego == 'TETRIS' and getattr(self, 'power_up_piece', None):
            if key == 'UP': self.power_up_y = max(0, self.power_up_y - 1)
            elif key == 'DOWN': self.power_up_y = min(self.alto - 1, self.power_up_y + 1)
            elif key == 'LEFT': self.power_up_x = max(0, self.power_up_x - 1)
            elif key == 'RIGHT': self.power_up_x = min(self.ancho - 1, self.power_up_x + 1)
            elif key == 'SPACE': self.power_up_place()

        elif self.tipo_juego == 'SNAKE':
            if key == 'UP': self.snake_cambiar_direccion('UP')
            elif key == 'DOWN': self.snake_cambiar_direccion('DOWN')
            elif key == 'LEFT': self.snake_cambiar_direccion('LEFT')
            elif key == 'RIGHT': self.snake_cambiar_direccion('RIGHT')

    def random_color(self):
        colores = self.datos_juego.get('colors', [])
        if len(colores) > 0:
            index = random.randint(0, len(colores) - 1)
            return '#' + str(colores[index])
        return '#000FFF'

    # --- NÚCLEO DE RENDERIZADO UNIFICADO ---
    def dibujar(self):
        self.canvas.delete("all") 
        
        if self.tipo_juego == 'TANKS':
            hp_actual = self.player.hp if self.player in self.entidades else 0
            estado_municion = "RECARGANDO..." if self.recargando else str(self.balas_actuales) + " / " + str(self.balas_maximas)
            self.label_score.config(text="PUNTUACION\n" + str(self.puntuacion) + "\n\nHP PLAYER\n" + str(hp_actual) + "\n\nMUNICION\n" + estado_municion)
        else:
            self.label_score.config(text="PUNTUACION\n" + str(self.puntuacion))
            if self.tipo_juego == 'SNAKE':
                self.label_estado.config(text=self.texto_estado_snake())

        COLOR_GRID_FIJA = '#343434'
        for y in range(self.alto):
            for x in range(self.ancho):
                if self.grid[y][x] == 1 and self.tipo_juego != 'TANKS':
                    self.dibujar_celda(x, y, COLOR_GRID_FIJA)

        if self.tipo_juego == 'TANKS':
            self.draw_tanks()
            self.draw_map()
            self.draw_bullets()
            self.draw_explosions()
            self.draw_hammer()

        if self.tipo_juego == 'TETRIS' and self.pieza_actual:
            if self.power_up_piece:
                self.dibujar_celda(self.power_up_x, self.power_up_y, '#FFFF00')
            matriz_pieza = self.pieza_actual[self.pieza_rotacion]
            for y_offset, fila in enumerate(matriz_pieza):
                for x_offset, celda in enumerate(fila):
                    if celda == 1:
                        self.dibujar_celda(self.pieza_x + x_offset, self.pieza_y + y_offset, self.color_pieza)
        
        if self.tipo_juego == 'SNAKE':
            snake_invulnerable = self.esta_invulnerable()
            parpadeo = int(time.time() * 10) % 2 == 0
            COLOR_SNAKE_CABEZA = '#FFFFFF' if snake_invulnerable and parpadeo else ('#00FFFF' if hasattr(self, 'posicion_powerup') else '#00FF00')
            COLOR_SNAKE_CUERPO = '#7FFFD4' if snake_invulnerable and parpadeo else '#33CC33'
            COLOR_SNAKE_BORDE = '#FFFFFF' if snake_invulnerable else '#000000'
            ancho_borde = 2 if snake_invulnerable else 1

            if self.posicion_comida:
                x, y = self.posicion_comida
                if getattr(self, 'img_food', None): self.canvas.create_image(x * self.taman_celda, y * self.taman_celda, image=self.img_food, anchor='nw')
                else: self.dibujar_celda(x, y, '#FF0000')

            if self.posicion_veneno:
                x, y = self.posicion_veneno
                if getattr(self, 'img_poison', None): self.canvas.create_image(x * self.taman_celda, y * self.taman_celda, image=self.img_poison, anchor='nw')
                else: self.dibujar_celda(x, y, '#FF0199')

            if self.posicion_nube:
                x, y = self.posicion_nube
                if getattr(self, 'img_cloud', None): self.canvas.create_image(x * self.taman_celda, y * self.taman_celda, image=self.img_cloud, anchor='nw')
                else: self.dibujar_celda(x, y, '#3B6294')

            if getattr(self, 'posicion_powerup', None):
                x, y = self.posicion_powerup
                if getattr(self, 'img_powerup', None): self.canvas.create_image(x * self.taman_celda, y * self.taman_celda, image=self.img_powerup, anchor='nw')
                else: self.dibujar_celda(x, y, '#ffd700')

            for i, segmento in enumerate(self.serpiente_cuerpo):
                x, y = segmento
                direccion_segmento = self.obtener_direccion_segmento(i)

                if self.usar_nyancat:
                    if i == 0: self.dibujar_nyancat(x, y, direccion_segmento)
                    elif i == 1: self.dibujar_nyancat_body(x, y, direccion_segmento)
                    else: self.dibujar_nyancat_trail(x, y, direccion_segmento)
                else:
                    shape_names = list(self.datos_juego.get('shapes', {}).keys())
                    shape_type = shape_names[0] if shape_names else 'PIXEL'

                    if i == 0 and shape_type == 'PIXEL': self.dibujar_celda(x, y, COLOR_SNAKE_CABEZA, COLOR_SNAKE_BORDE, ancho_borde)
                    elif i == 0 and shape_type in ['TRIANGLE', 'CIRCLE']: self.dibujar_triangulo(x, y, COLOR_SNAKE_CABEZA, direccion_segmento, COLOR_SNAKE_BORDE, ancho_borde)
                    elif shape_type == 'CIRCLE': self.dibujar_circulo(x, y, COLOR_SNAKE_CUERPO, COLOR_SNAKE_BORDE, ancho_borde)
                    elif shape_type == 'TRIANGLE': self.dibujar_triangulo(x, y, COLOR_SNAKE_CUERPO, direccion_segmento, COLOR_SNAKE_BORDE, ancho_borde)
                    else: self.dibujar_celda(x, y, COLOR_SNAKE_CUERPO, COLOR_SNAKE_BORDE, ancho_borde)

    # --- PRIMITIVAS GRÁFICAS ADAPTADAS ---
    def dibujar_celda(self, x, y, color, outline='#000000', width=1):
        ts = self.taman_celda
        self.canvas.create_rectangle(x * ts, y * ts, (x + 1) * ts, (y + 1) * ts, fill=color, outline=outline, width=width)

    def dibujar_circulo(self, x, y, color, outline='#000000', width=1):
        ts = self.taman_celda
        self.canvas.create_oval(x * ts, y * ts, (x + 1) * ts, (y + 1) * ts, fill=color, outline=outline, width=width)

    def dibujar_triangulo(self, x, y, color, direccion=(1, 0), outline='#000000', width=1):
        ts = self.taman_celda
        x0, y0 = x * ts, y * ts
        if direccion == (1, 0): x1, y1, x2, y2, x3, y3 = x0, y0, x0, y0 + ts, x0 + ts, y0 + ts / 2
        elif direccion == (-1, 0): x1, y1, x2, y2, x3, y3 = x0 + ts, y0, x0 + ts, y0 + ts, x0, y0 + ts / 2
        elif direccion == (0, -1): x1, y1, x2, y2, x3, y3 = x0, y0 + ts, x0 + ts, y0 + ts, x0 + ts / 2, y0
        else: x1, y1, x2, y2, x3, y3 = x0, y0, x0 + ts, y0, x0 + ts / 2, y0 + ts
        self.canvas.create_polygon(x1, y1, x2, y2, x3, y3, fill=color, outline=outline, width=width)

    def dibujar_nyancat(self, x, y, direccion=(1, 0)):
        dir_map = {(1, 0): 'RIGHT', (-1, 0): 'LEFT', (0, -1): 'UP', (0, 1): 'DOWN'}
        dir_key = dir_map.get(direccion, 'RIGHT')
        if dir_key in self.img_nyancat and self.img_nyancat[dir_key]:
            self.canvas.create_image(x * self.taman_celda, y * self.taman_celda, image=self.img_nyancat[dir_key], anchor='nw')
        else: self.dibujar_triangulo(x, y, '#00FF00')

    def dibujar_nyancat_body(self, x, y, arg=None):
        direccion = arg if isinstance(arg, tuple) else (1, 0)
        color = arg if isinstance(arg, str) else '#33CC33'
        dir_map = {(1, 0): 'RIGHT', (-1, 0): 'LEFT', (0, -1): 'UP', (0, 1): 'DOWN'}
        dir_key = dir_map.get(direccion, 'RIGHT')
        img = self.img_nyancat_body.get(dir_key) or self.img_nyancat.get(dir_key)
        if img: self.canvas.create_image(x * self.taman_celda, y * self.taman_celda, image=img, anchor='nw')
        else: self.dibujar_circulo(x, y, color)

    def dibujar_nyancat_trail(self, x, y, direccion=(1, 0)):
        dir_map = {(1, 0): 'RIGHT', (-1, 0): 'LEFT', (0, -1): 'UP', (0, 1): 'DOWN'}
        dir_key = dir_map.get(direccion, 'RIGHT')
        img = self.img_nyancat_trail.get(dir_key) or self.img_nyancat.get(dir_key)
        if img: self.canvas.create_image(x * self.taman_celda, y * self.taman_celda, image=img, anchor='nw')
        else: self.dibujar_triangulo(x, y, '#228822', direccion)

    # --- CONTROLADOR CENTRAL DE EVENTOS ---
    def ejecutar_evento(self, nombre_evento):
        if nombre_evento in self.datos_juego.get('events', {}):
            for accion in self.datos_juego['events'][nombre_evento]:
                verbo, objeto = accion.get('accion'), accion.get('objeto')
                
                if verbo == 'INCREASE_SCORE':
                    self.puntuacion += int(objeto)
                    self.ejecutar_evento('SECRET')
                
                if verbo == 'GAME_OVER': 
                    self.juego_terminado = True

                if self.tipo_juego == 'SNAKE' and verbo == 'DURATION':
                    self.invulnerabilidad_segundos = max(0.0, float(objeto))

                # Eventos de Tetris
                if self.tipo_juego == 'TETRIS':
                    if verbo == 'SPAWN' and objeto == 'RANDOM_SHAPE': self.tetris_spawn_pieza()
                    if verbo == 'SPAWN' and objeto == 'POWER_UP': self.power_up()
                    if verbo == 'MOVE': self.tetris_mover_pieza(accion['params'][0])
                    if verbo == 'ROTATE': self.tetris_rotar_pieza()

                # Eventos de Snake
                if self.tipo_juego == 'SNAKE':
                    if verbo == 'SPAWN' and objeto == 'PLAYER': self.snake_spawn_jugador(accion)
                    if verbo == 'SPAWN' and objeto == 'FOOD': self.snake_spawn_comida()
                    if verbo == 'MOVE' and objeto == 'PLAYER': self.snake_mover_jugador()
                    if verbo == 'GROW': self.snake_crecer()

                # Eventos de Tanks
                if self.tipo_juego == 'TANKS':
                    if verbo == 'SPAWN' and (not self.entidades or len(self.entidades) <= 1): self.spawn()
                    if verbo == 'MOVE': self.move_tank(accion['params'][0], self.player)
                    if verbo == 'SHOT' and not self.recargando:
                        if self.balas_actuales > 0:
                            self.shoot(self.player)
                            self.balas_actuales -= 1
                        if self.balas_actuales == 0:
                            self.recargando = True
                            self.root.after(int(self.tiempo_recarga * 1000), self.finalizar_recarga)
                    if verbo == 'UPDATE':
                        self.verificar_colision_hammer()
                        self.update_bullets()
                        self.tick += 1
                        enemigos_vivos = [e for e in self.entidades if e.tipo in ['ENEMY', 'BOSS']]
                        traducir_dir = {0: 'UP', 1: 'LEFT', 2: 'DOWN', 3: 'RIGHT'}
                        
                        for enemy in enemigos_vivos:
                            if enemy in self.entidades:
                                # Usar velocidad propia de cada entidad
                                intervalo_mov = getattr(enemy, 'velocidad', 4)
                                if enemy.tipo == 'BOSS':
                                    if not (self.tick % intervalo_mov): self.patrullar_boss(enemy)
                                    if not (self.tick % 16): self.shoot(enemy)
                                else:
                                    if not (self.tick % intervalo_mov):
                                        if enemy.pasos_rafaga <= 0 or self.collition(traducir_dir[enemy.direc], enemy):
                                            enemy.rotate_tank(random.choice(['UP', 'LEFT', 'DOWN', 'RIGHT']), enemy) if hasattr(enemy, 'rotate_tank') else self.rotate_tank(random.choice(['UP', 'LEFT', 'DOWN', 'RIGHT']), enemy)
                                            enemy.pasos_rafaga = random.randint(8, 20)
                                        self.move_tank(traducir_dir[enemy.direc], enemy)
                                        enemy.pasos_rafaga -= 1
                                    if not (self.tick % 32): self.shoot(enemy)
                        self.revisar_estado_oleada()

    # =====================================================================
    # SEGMENTACIÓN: LOGICA DE TETRIS
    # =====================================================================
    def power_up(self):
        self.power_up_piece = [[[1]]] 
        self.power_up_color = '#FFFF00'  
        self.power_up_x = self.ancho / 2
        self.power_up_y = self.alto / 2

    def power_up_place(self):
        if self.power_up_piece:
            self.grid[self.power_up_y][self.power_up_x] = 1
            self.power_up_piece = None

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
        self.pieza_actual = shapes[nombres[indice]][1]
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
        elif dy > 0: self.tetris_fijar_pieza()

    def tetris_rotar_pieza(self):
        if not self.pieza_actual: return
        nueva_rotacion = (self.pieza_rotacion + 1) % len(self.pieza_actual)
        if not self.tetris_verificar_colision(self.pieza_x, self.pieza_y, nueva_rotacion):
            self.pieza_rotacion = nueva_rotacion

    def tetris_fijar_pieza(self):
        for y_offset, fila in enumerate(self.pieza_actual[self.pieza_rotacion]):
            for x_offset, celda in enumerate(fila):
                if celda == 1:
                    if 0 <= self.pieza_y + y_offset < self.alto and 0 <= self.pieza_x + x_offset < self.ancho:
                        self.grid[self.pieza_y + y_offset][self.pieza_x + x_offset] = 1
        self.pieza_actual = None
        self.tetris_limpiar_lineas()
        self.ejecutar_evento('ON_START')

    def tetris_verificar_colision(self, x, y, rotacion):
        if not self.pieza_actual: return False
        for y_offset, fila in enumerate(self.pieza_actual[rotacion]):
            for x_offset, celda in enumerate(fila):
                if celda == 1:
                    nx, ny = x + x_offset, y + y_offset
                    if not (0 <= nx < self.ancho and 0 <= ny < self.alto and self.grid[ny][nx] == 0): return True
        return False

    def tetris_limpiar_lineas(self):
        nuevo_grid = [fila for fila in self.grid if not all(fila)]
        lineas_limpias = self.alto - len(nuevo_grid)
        if lineas_limpias > 0:
            self.grid = [[0] * self.ancho for _ in range(lineas_limpias)] + nuevo_grid
            if lineas_limpias == 4: self.ejecutar_evento('ON_SECRET')
            for _ in range(lineas_limpias): self.ejecutar_evento('ON_LINE_CLEAR')
        self.crecimiento_pendiente = getattr(self, 'crecimiento_pendiente', 0) + 1

    # =====================================================================
    # SEGMENTACIÓN: LOGICA DE SNAKE
    # =====================================================================
    def snake_spawn_jugador(self, accion):
        coords = accion['params'][0] if accion.get('params') else [self.ancho / 2, self.alto / 2]
        self.serpiente_cuerpo = [(coords[0], coords[1])]
        self.serpiente_direccion = (1, 0)

    def snake_spawn_comida(self):
        while True:
            x, y = random.randint(0, self.ancho - 1), random.randint(0, self.alto - 1)
            if (x, y) not in self.serpiente_cuerpo:
                self.posicion_comida = (x, y)
                break
        if (self.puntuacion % 100 == 0) and self.dificultad not in ['BABY', 'CLASSIC']:
            while True:
                x, y = random.randint(0, self.ancho - 1), random.randint(0, self.alto - 1)
                if (x, y) not in self.serpiente_cuerpo:
                    self.posicion_veneno = (x, y)
                    break
        if (self.puntuacion % 50 == 0) and self.dificultad == 'CAT':
            while True:
                x, y = random.randint(0, self.ancho - 1), random.randint(0, self.alto - 1)
                if (x, y) not in self.serpiente_cuerpo:
                    self.posicion_nube = (x, y)
                    break
        if (self.puntuacion % 200 == 0) and (self.puntuacion != 0) and self.dificultad in ['CAT', 'ENTUSIASTA']:
            while True:
                x, y = random.randint(0, self.ancho - 1), random.randint(0, self.alto - 1)
                if (x, y) not in self.serpiente_cuerpo:
                    self.posicion_powerup = (x, y)
                    break

    def snake_mover_jugador(self):
        if not self.serpiente_cuerpo: return
        cabeza_x, cabeza_y = self.serpiente_cuerpo[0]
        dir_x, dir_y = self.serpiente_direccion
        nueva_cabeza = (cabeza_x + dir_x, cabeza_y + dir_y)
        invulnerable = self.esta_invulnerable()

        if not (0 <= nueva_cabeza[0] < self.ancho and 0 <= nueva_cabeza[1] < self.alto):
            if invulnerable:
                self.serpiente_direccion = (-dir_x, -dir_y)
                dir_x, dir_y = self.serpiente_direccion
                nueva_cabeza = (cabeza_x + dir_x, cabeza_y + dir_y)
            else:
                self.ejecutar_evento('ON_COLLISION_WALL')
                return

        if not invulnerable and nueva_cabeza in self.serpiente_cuerpo[:-1] and self.dificultad != 'CAT':
            self.ejecutar_evento('ON_COLLISION_SELF')
            return
        elif not invulnerable and nueva_cabeza in self.serpiente_cuerpo[:-1] and self.dificultad == 'CAT':
            if self.puntuacion == 0: self.ejecutar_evento('ON_COLLISION_WALL')
            else: self.puntuacion = 0

        self.serpiente_cuerpo.insert(0, nueva_cabeza)

        if nueva_cabeza == self.posicion_nube:
            if not invulnerable:
                if self.puntuacion == 0: self.juego_terminado = True
                else: self.puntuacion = 0

        if nueva_cabeza == self.posicion_veneno:
            if not invulnerable:
                if self.dificultad == 'ENTUSIASTA': self.puntuacion = 0  
                else: self.juego_terminado = True
                self.posicion_veneno = None
        
        if nueva_cabeza == self.posicion_comida:
            self.ejecutar_evento('ON_EAT_FOOD')
            if self.crecimiento_pendiente > 0: self.crecimiento_pendiente -= 1
            else: self.serpiente_cuerpo.pop()
        elif self.crecimiento_pendiente > 0:
            self.crecimiento_pendiente -= 1
        elif getattr(self, 'posicion_powerup', None) and nueva_cabeza == self.posicion_powerup:
            self.ejecutar_evento('ON_EAT_POWERUP')
            self.ejecutar_evento('ON_EAT_FOOD')
            self.posicion_powerup = None
            self.activar_invulnerabilidad()
            if self.crecimiento_pendiente > 0: self.crecimiento_pendiente -= 1
            else: self.serpiente_cuerpo.pop()
        else:
            self.serpiente_cuerpo.pop()

    def snake_cambiar_direccion(self, direccion):
        if direccion == 'UP' and self.serpiente_direccion[1] != 1: self.serpiente_direccion = (0, -1)
        elif direccion == 'DOWN' and self.serpiente_direccion[1] != -1: self.serpiente_direccion = (0, 1)
        elif direccion == 'LEFT' and self.serpiente_direccion[0] != 1: self.serpiente_direccion = (-1, 0)
        elif direccion == 'RIGHT' and self.serpiente_direccion[0] != -1: self.serpiente_direccion = (1, 0)
    
    def obtener_direccion_segmento(self, indice):
        if indice == 0: return self.serpiente_direccion
        if indice >= len(self.serpiente_cuerpo): return (1, 0)
        ax, ay = self.serpiente_cuerpo[indice]
        ant_x, ant_y = self.serpiente_cuerpo[indice - 1]
        return (ant_x - ax, ant_y - ay)

    def snake_crecer(self):
        self.crecimiento_pendiente += 1

    def activar_invulnerabilidad(self):
        if getattr(self, 'invulnerabilidad_segundos', 0) > 0:
            self.invulnerable_hasta = max(getattr(self, 'invulnerable_hasta', 0), time.time()) + self.invulnerabilidad_segundos

    def esta_invulnerable(self):
        return self.tipo_juego == 'SNAKE' and getattr(self, 'invulnerable_hasta', 0) > time.time()

    def actualizar_estado_invulnerabilidad(self):
        if self.esta_invulnerable():
            restantes = max(0.0, self.invulnerable_hasta - time.time())
            self.label_estado.config(text="INVULNERABLE\n{0:.1f}s".format(restantes))
        else:
            self.label_estado.config(text="")

    def texto_estado_snake(self):
        if self.esta_invulnerable():
            restantes = max(0.0, self.invulnerable_hasta - time.time())
            return "INVULNERABLE\n{0:.1f}s".format(restantes)
        return ""

    # =====================================================================
    # SEGMENTACIÓN: LOGICA DE TANKS
    # =====================================================================
    def inicializar_grid_mapa(self):
        wall_h = self.alto / 10
        wall_w = self.ancho / 10
        self.puntos_spawn = []
        for y_offset, fila in enumerate(self.map[self.level]):
            for x_offset, celda in enumerate(fila):
                pos_x = x_offset * wall_w
                pos_y = y_offset * wall_h
                if celda == 1:
                    for gy in range(pos_y, pos_y + wall_h):
                        for gx in range(pos_x, pos_x + wall_w):
                            if gy < self.alto and gx < self.ancho: self.grid[gy][gx] = 1
                elif celda == 2:
                    self.puntos_spawn.append((pos_x, pos_y))

    def spawn(self):
        if not self.puntos_spawn: return
        if self.puntuacion < 200: porcentaje = 0.20
        elif self.puntuacion < 400: porcentaje = 0.40
        elif self.puntuacion < 1600: porcentaje = 0.60
        elif self.puntuacion < 2200: porcentaje = 0.80
        else: porcentaje = 1.00

        cantidad = max(1, int(len(self.puntos_spawn) * porcentaje))
        posiciones = random.sample(self.puntos_spawn, min(cantidad, len(self.puntos_spawn)))
        
        # Filtrar los tipos de enemigos configurados en el JSON (excluyendo a PLAYER y BOSS)
        tipos_enemigos = [nombre for nombre, cfg in self.config_entidades.items() 
        if cfg.get('tipo', 'ENEMY') == 'ENEMY' and nombre != 'PLAYER']
        
        for (pos_x, pos_y) in posiciones:
            if abs(self.player.x - pos_x) < 7 and abs(self.player.y - pos_y) < 7: continue
            
            # Si hay tipos configurados, elegir uno al azar; de lo contrario usará valores por defecto
            if tipos_enemigos:
                nombre_tipo = random.choice(tipos_enemigos)
                cfg = self.config_entidades[nombre_tipo]
                hp_enemigo = cfg.get('hp', 1)
                vel_enemigo = cfg.get('velocidad', 4)
                color_enemigo = cfg.get('color', self.color_enemigo)
            else:
                hp_enemigo = 1
                vel_enemigo = 4
                color_enemigo = self.color_enemigo

            nuevo_enemigo = tanks.Tank(pos_x, pos_y, 2, hp=hp_enemigo, tipo='ENEMY')
            nuevo_enemigo.velocidad = vel_enemigo
            nuevo_enemigo.color = color_enemigo
            self.entidades.append(nuevo_enemigo)
            self.spawn_hammer()

    def spawn_boss(self):
        self.boss_spawned = True
        cfg_boss = self.config_entidades.get('BOSS', {})
        hp_boss = cfg_boss.get('hp', 20)
        vel_boss = cfg_boss.get('velocidad', 4)
        color_boss = cfg_boss.get('color', self.color_jefe)

        boss = tanks.Tank(self.ancho / 2 - 7, 2, 2, hp=hp_boss, tipo='BOSS')
        boss.shape_name = 'BOSS' 
        boss.direccion_patrulla = 1
        boss.velocidad = vel_boss
        boss.color = color_boss
        self.entidades.append(boss)

    def patrullar_boss(self, boss):
        tam_boss = 14
        siguiente_x = boss.x + boss.direccion_patrulla
        if siguiente_x < 1 or siguiente_x > (self.ancho - tam_boss - 1):
            boss.direccion_patrulla *= -1
            return
        colision = False
        for i in range(tam_boss):
            check_x = siguiente_x if boss.direccion_patrulla == -1 else siguiente_x + tam_boss
            if self.grid[boss.y + i][check_x] == 1:
                colision = True
                break
        if colision: boss.direccion_patrulla *= -1
        else: boss.x = siguiente_x

    def revisar_estado_oleada(self):
        if len([e for e in self.entidades if e.tipo in ['ENEMY', 'BOSS']]) == 0:
            if self.puntuacion >= self.siguiente_hito_boss and not self.boss_spawned: self.spawn_boss()
            else: 
                self.spawn()
                

    def ejecutar_explosion(self, centro_x, centro_y):
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                tx, ty = centro_x + dx, centro_y + dy
                if 0 <= tx < self.ancho and 0 <= ty < self.alto:
                    if self.grid[ty][tx] == 1: 
                        self.grid[ty][tx] = 0
                    
                    for entidad in self.entidades[:]:
                        tam = 14 if entidad.tipo == 'BOSS' else 7
                        if entidad.x <= tx < (entidad.x + tam) and entidad.y <= ty < (entidad.y + tam):
                            if entidad.tipo == 'BOSS': 
                                continue
                            entidad.recibir_danio(1)
                            if entidad.hp <= 0:
                                if entidad.tipo == 'PLAYER': 
                                    self.juego_terminado = True
                                elif entidad.tipo == 'BOSS':
                                    self.puntuacion += 200
                                    self.entidades.remove(entidad)
                                    self.boss_spawned = False
                                    self.siguiente_hito_boss = self.puntuacion + 150
                                else:
                                    self.puntuacion += 25
                                    self.entidades.remove(entidad)
        self.explosiones_activas.append({'x': centro_x, 'y': centro_y, 'ticks': 8})

    def verificar_impacto(self, x, y, tipo_bala):
        ancho_bala = 2 if tipo_bala == 'BOSS' else 1
        for bx in range(ancho_bala):
            for by in range(ancho_bala):
                tx, ty = x + bx, y + by
                if not (0 <= tx < self.ancho and 0 <= ty < self.alto): return True
                
                # --- Check Entity Collisions FIRST ---
                for entidad in self.entidades[:]:
                    if tipo_bala == 'ENEMY' and entidad.tipo in ['ENEMY', 'BOSS']: continue
                    if tipo_bala == 'PLAYER' and entidad.tipo == 'PLAYER': continue
                    tam = 14 if entidad.tipo == 'BOSS' else 7
                    if entidad.x <= tx < (entidad.x + tam) and entidad.y <= ty < (entidad.y + tam):
                        entidad.recibir_danio(1)
                        if entidad.hp <= 0:
                            if entidad.tipo == 'PLAYER': self.juego_terminado = True
                            else:
                                if entidad.tipo == 'BOSS':
                                    self.puntuacion += 100
                                    self.boss_derrotado = True
                                    self.boss_spawned = False
                                    self.siguiente_hito_boss = self.puntuacion + 150
                                else: self.puntuacion += 25
                                self.entidades.remove(entidad)
                                if len([e for e in self.entidades if e.tipo in ['ENEMY', 'BOSS']]) == 0:
                                    if self.boss_derrotado:
                                        self.player.hp += 1
                                        self.boss_derrotado = False
                                        self.mostrar_game_win()
                                    elif self.puntuacion >= self.siguiente_hito_boss and not self.boss_spawned: self.spawn_boss()
                                    else: self.spawn()
                        return True

                # --- Check Wall Collisions SECOND ---
                if self.grid[ty][tx] == 1:
                    if tipo_bala == 'BOSS': self.ejecutar_explosion(x, y)
                    else: self.grid[ty][tx] = 0
                    return True
        return False
    
    def update_bullets(self):
        if self.bullets_q == 0: return
        for i in range(self.bullets_q):
            bullet = self.bullets.get()
            if bullet[2] == 0: bullet[1] -= 1
            elif bullet[2] == 1: bullet[0] -= 1
            elif bullet[2] == 2: bullet[1] += 1
            else: bullet[0] += 1

            if not (0 <= bullet[0] < self.ancho and 0 <= bullet[1] < self.alto):
                self.bullets_q -= 1
                continue
            bullet[4] += 1 
            if bullet[3] == 'BOSS' and bullet[4] >= 35 and random.random() < 0.20:
                self.ejecutar_explosion(bullet[0], bullet[1])
                self.bullets_q -= 1
                continue
            if self.verificar_impacto(bullet[0], bullet[1], bullet[3]):
                self.bullets_q -= 1
                continue
            
            self.bullets.put(bullet)

    def finalizar_recarga(self):
        self.balas_actuales = self.balas_maximas
        self.recargando = False

    def draw_tanks(self):
        for entidad in self.entidades:
            # Seleccionar color dinámico de la entidad
            if hasattr(entidad, 'color') and entidad.color:
                color = entidad.color
            else:
                color = self.color_tank if entidad.tipo == 'PLAYER' else (self.color_enemigo if entidad.tipo == 'ENEMY' else self.color_jefe)
                
            matriz = self.tank_body[entidad.direc]
            factor = 2 if entidad.tipo == 'BOSS' else 1
            for y_offset, fila in enumerate(matriz):
                for x_offset, celda in enumerate(fila):
                    if celda == 1:
                        if factor > 1:
                            for ey in range(factor):
                                for ex in range(factor): self.dibujar_celda(entidad.x + (x_offset * factor) + ex, entidad.y + (y_offset * factor) + ey, color)
                        else: self.dibujar_celda(entidad.x + x_offset, entidad.y + y_offset, color)

    def draw_map(self):
        for y in range(self.alto):
            for x in range(self.ancho):
                if self.grid[y][x] == 1:
                    self.canvas.create_rectangle(x * self.taman_celda, y * self.taman_celda, (x + 1) * self.taman_celda, (y + 1) * self.taman_celda, fill="#CCD0D4", outline="")
    
    def shoot(self, tank):
        tam = 14 if tank.tipo == 'BOSS' else 7
        bx, by = tank.x, tank.y
        if tank.tipo == 'BOSS':
            bx += (tam / 2) - 1
            by += tam
        else:
            if tank.direc == 0: bx += tam / 2; by -= 1
            elif tank.direc == 1: bx -= 1; by += tam / 2
            elif tank.direc == 2: bx += tam / 2; by += tam
            elif tank.direc == 3: bx += tam; by += tam / 2
        self.bullets.put([bx, by, tank.direc, tank.tipo, 0])
        self.bullets_q += 1

    def draw_bullets(self):
        for bullet in list(self.bullets.queue):
            if bullet[3] == 'BOSS':
                for ox in [0, 1]:
                    for oy in [0, 1]: 
                        self.dibujar_circulo(bullet[0] + ox, bullet[1] + oy, '#FF5500')
            else: 
                self.dibujar_circulo(bullet[0], bullet[1], '#FF0000')

    def draw_explosions(self):
        ts = self.taman_celda
        explosiones_vivas = []

        for exp in self.explosiones_activas:
            cx, cy = exp['x'], exp['y']
            radio = 4 if exp['ticks'] > 4 else 2
            
            for dy in range(-radio, radio + 1):
                for dx in range(-radio, radio + 1):
                    tx, ty = cx + dx, cy + dy
                    if 0 <= tx < self.ancho and 0 <= ty < self.alto:
                        color = '#FF9900' if (dx + dy + exp['ticks']) % 2 == 0 else '#FF3300'
                        self.canvas.create_rectangle(tx * ts, ty * ts, (tx + 1) * ts, (ty + 1) * ts, fill=color, outline="")

            exp['ticks'] -= 1
            if exp['ticks'] > 0:
                explosiones_vivas.append(exp)

        self.explosiones_activas = explosiones_vivas

    def move_tank(self, direction, tank ):
        self.rotate_tank(direction, tank)
        if self.collition(direction, tank): return
        if direction == 'LEFT': tank.x -= 1
        elif direction == 'UP': tank.y -= 1
        elif direction == 'DOWN': tank.y += 1
        elif direction == 'RIGHT': tank.x += 1

    def rotate_tank(self, direction, tank):
        if direction == 'LEFT': tank.direc = 1
        elif direction == 'UP': tank.direc = 0
        elif direction == 'DOWN': tank.direc = 2
        elif direction == 'RIGHT': tank.direc = 3

    def collition(self, direction, tank):
        tam = 7 
        if tank.tipo == 'PLAYER' and getattr(self, 'boss_spawned', False):
            if direction == 'UP' and tank.y - 1 < int(self.alto * 0.25): return 1
        if direction == 'LEFT' and tank.x < 1: return 1
        if direction == 'UP' and tank.y < 1: return 1
        if direction == 'DOWN' and tank.y > (self.alto - tam): return 1
        if direction == 'RIGHT' and tank.x > (self.ancho - tam): return 1
        
        for i in range(tam):
            tx, ty = tank.x, tank.y
            if direction == 'LEFT': ty += i; tx -= 1
            elif direction == 'RIGHT': ty += i; tx += tam
            elif direction == 'UP': ty -= 1; tx += i
            elif direction == 'DOWN': ty += tam; tx += i
            if 0 <= ty < self.alto and 0 <= tx < self.ancho and self.grid[ty][tx] == 1: return 1
        return 0

    def spawn_hammer(self):
        max_intentos = 100
        for _ in range(max_intentos):
            # Pick random top-left corner for a 3x3 hammer box
            x = random.randint(1, self.ancho - 4)
            y = random.randint(1, self.alto - 4)
            
            # Check if the 3x3 area is completely clear of wall blocks (grid == 0)
            area_libre = True
            for dy in range(3):
                for dx in range(3):
                    if self.grid[y + dy][x + dx] != 0:
                        area_libre = False
                        break
                if not area_libre:
                    break
            
            if area_libre:
                self.hammer_pos = (x, y)
                break

    def verificar_colision_hammer(self):
        """Checks if player overlaps with the hammer to give +1 HP."""
        if not self.hammer_pos or self.player not in self.entidades:
            return

        hx, hy = self.hammer_pos
        tam_player = 7   # Tanks player bounding box is 7x7
        tam_hammer = 3   # Hammer bounding box is 3x3
        
        # AABB Collision Check between Player (7x7) and Hammer (3x3)
        if (self.player.x < hx + tam_hammer and self.player.x + tam_player > hx and
            self.player.y < hy + tam_hammer and self.player.y + tam_player > hy):
            
            self.player.hp += 1       # Give 1 HP to player
            self.hammer_pos = None    # Remove hammer from screen

    def draw_hammer(self):
        """Renders the hammer onto the Canvas."""
        if not self.hammer_pos:
            return

        hx, hy = self.hammer_pos
        ts = self.taman_celda

        # Draw Metallic Head (3x1 rectangle on top)
        self.canvas.create_rectangle(hx * ts, hy * ts, (hx + 3) * ts, (hy + 1) * ts, fill="#A9A9A9", outline="#000000")
        # Draw Wooden Handle (1x2 rectangle centered underneath)
        self.canvas.create_rectangle((hx + 1) * ts, (hy + 1) * ts, (hx + 2) * ts, (hy + 3) * ts, fill="#8B4513", outline="#000000")

    # =====================================================================
    # SISTEMA DE TERMINACIÓN
    # =====================================================================
    def mostrar_game_over(self):
        tkMessageBox.showinfo("Juego Terminado", "Puntuacion Final: " + str(self.puntuacion))
        self.root.destroy()
        sys.exit(0)

    def mostrar_game_win(self):
        tkMessageBox.showinfo("VICTORIA!!!", "Puntuacion Final: " + str(self.puntuacion))
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "Uso: python runtime.py <archivo_juego.json>"
        sys.exit(1)
    archivo_juego = sys.argv[1]
    try:
        with open(archivo_juego, 'r') as f: datos_juego = json.load(f)
    except IOError:
        print "Error: No se pudo encontrar el archivo " + archivo_juego
        sys.exit(1)
    juego = Juego(datos_juego)
    juego.run()
    if len(sys.argv) != 2:
        print "Uso: python runtime.py <archivo_juego.json>"
        sys.exit(1)
    archivo_juego = sys.argv[1]
    try:
        with open(archivo_juego, 'r') as f: datos_juego = json.load(f)
    except IOError:
        print "Error: No se pudo encontrar el archivo " + archivo_juego
        sys.exit(1)
    juego = Juego(datos_juego)
    juego.run()
