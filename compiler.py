# -*- coding: utf-8 -*-
# compiler.py
# Compilador universal para BrickScript (Python 2.7 Compatible)
# Uso: python compiler.py <archivo_entrada.brick>

import sys
import re
import json

def lexer(codigo_fuente):
    # Eliminar comentarios (#...) excepto en codigos HEX (#456657)
    # Primero removemos comentarios que empiezan con # seguidos de espacio o al inicio de linea sola
    lineas = codigo_fuente.splitlines()
    lineas_limpias = []
    for linea in lineas:
        # Si hay un comentario con espacio ej: # esto es un comentario
        if '#' in linea and not re.search(r'#[0-9a-fA-F]{6}', linea):
            linea = linea.split('#')[0]
        lineas_limpias.append(linea)
    codigo_fuente = '\n'.join(lineas_limpias)

    # Regex que incluye Hex Colors (ej: #456657), palabras, numeros (con + / -) y simbolos
    token_regex = r'#[0-9a-fA-F]{6}|\b[a-zA-Z_]+\b|[+-]?\d+|[\[\](),:]'
    tokens = re.findall(token_regex, codigo_fuente)
    return tokens

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.posicion = 0
        self.ast = {
            "tipo_juego": None, 
            "config": {}, 
            "shapes": {}, 
            "events": {}, 
            "colors": [],
            "entidades": {}
        }

    def parse(self):
        while self.posicion < len(self.tokens):
            token_actual = self.tokens[self.posicion].upper()
            if token_actual == 'GAME_TYPE':
                self.parsear_tipo_juego()
            elif token_actual == 'GAME_GRID':
                self.parsear_grid()
            elif token_actual == 'DIFICULTY':
                self.parsear_dificultad()
            elif token_actual == 'DEFINE':
                self.parsear_shape()
            elif token_actual == 'ON':
                self.parsear_evento()
            elif token_actual == 'COLORS':
                self.parsear_color()
            elif token_actual == 'TYPE':
                self.parsear_type()
            else:
                self.posicion += 1
        return self.ast

    def consumir(self, token_esperado=None):
        if self.posicion < len(self.tokens):
            token = self.tokens[self.posicion]
            if token_esperado and token.upper() != token_esperado.upper():
                raise Exception("Error de sintaxis: Se esperaba '" + str(token_esperado) + "' pero se encontro '" + str(token) + "'")
            self.posicion += 1
            return token
        if token_esperado:
            raise Exception("Error de sintaxis: Se esperaba '" + str(token_esperado) + "' pero se llego al final del archivo.")
        return None

    def parsear_tipo_juego(self):
        self.consumir('GAME_TYPE')
        self.ast['tipo_juego'] = self.consumir()

    def parsear_grid(self):
        self.consumir('GAME_GRID')
        self.consumir('(')
        ancho = int(self.consumir())
        self.consumir(',')
        alto = int(self.consumir())
        self.consumir(')')
        self.ast['config']['grid_size'] = [ancho, alto]

    def parsear_dificultad(self):
        self.consumir('DIFICULTY')
        dificulty = self.consumir()
        self.ast['config']['dificulty'] = dificulty

    def parsear_shape(self):
        self.consumir('DEFINE')
        self.consumir('SHAPE')
        nombre_shape = self.consumir()
        self.consumir(':')
        
        valor_chance = 1
        if self.posicion < len(self.tokens) and self.tokens[self.posicion].upper() == 'CHANCE':
            self.consumir('CHANCE')
            valor_chance = int(self.consumir())

        estados = []
        while self.posicion < len(self.tokens) and self.tokens[self.posicion].upper() == 'STATE':
            self.consumir('STATE')
            self.consumir()  # ID/Nombre de estado (ej: UP, 1)
            self.consumir(':')
            matriz = []
            while self.posicion < len(self.tokens) and self.tokens[self.posicion] == '[':
                fila = []
                self.consumir('[')
                while self.tokens[self.posicion] != ']':
                    fila.append(int(self.consumir()))
                    if self.tokens[self.posicion] == ',': 
                        self.consumir(',')
                self.consumir(']')
                matriz.append(fila)
            estados.append(matriz)
        self.consumir('END')
        self.ast['shapes'][nombre_shape] = [valor_chance, estados]

    def parsear_type(self):
        self.consumir('TYPE')
        entitie = self.consumir()

        if entitie not in self.ast['entidades']:
            self.ast['entidades'][entitie] = {'hp': 1, 'velocidad': 1, 'color': 'white'}

        block_keywords = ['TYPE', 'DEFINE', 'ON', 'GAME_TYPE', 'GAME_GRID', 'DIFICULTY', 'COLORS']

        while self.posicion < len(self.tokens):
            token = self.tokens[self.posicion].upper()

            if token == 'END':
                self.consumir('END')
                break
            elif token in block_keywords:
                break
            elif token == 'HP':
                self.consumir()
                self.ast['entidades'][entitie]['hp'] = int(self.consumir())
            elif token == 'SPEED':
                self.consumir()
                self.ast['entidades'][entitie]['velocidad'] = int(self.consumir())
            elif token == 'COLOR':
                self.consumir()
                self.ast['entidades'][entitie]['color'] = self.consumir()
            else:
                self.posicion += 1

    def parsear_evento(self):
        self.consumir('ON')
        nombre_evento = 'ON_' + self.consumir()
        self.consumir(':')
        acciones = []
        
        # Verbos que no requieren un objeto destino
        standalone_verbs = ['GAME_OVER', 'SPAWN']

        while self.posicion < len(self.tokens) and self.tokens[self.posicion].upper() != 'END':
            verbo = self.consumir()
            
            if verbo.upper() in standalone_verbs:
                acciones.append({'accion': verbo, 'objeto': None, 'params': []})
                continue
            
            objeto = self.consumir()
            if objeto.isdigit() or (objeto.startswith('-') and objeto[1:].isdigit()) or (objeto.startswith('+') and objeto[1:].isdigit()):
                acciones.append({'accion': verbo, 'objeto': None, 'params': [int(objeto)]})
                continue

            params = []
            if self.posicion < len(self.tokens) and self.tokens[self.posicion].upper() == 'AT':
                self.consumir('AT')
                if self.tokens[self.posicion].upper() == 'RANDOM':
                    params.append(self.consumir())
                else:
                    self.consumir('(')
                    x = int(self.consumir())
                    self.consumir(',')
                    y = int(self.consumir())
                    self.consumir(')')
                    params.append([x, y])
            elif self.posicion < len(self.tokens) and self.tokens[self.posicion].upper() not in [
                'END', 'ON', 'DEFINE', 'SPAWN', 'MOVE', 'ROTATE', 'INCREASE_SCORE', 'SET_DIRECTION', 'GROW', 'GAME_OVER', 'MAP'
            ]:
                token_param = self.consumir()
                params.append(int(token_param) if (token_param.isdigit() or token_param.startswith('+') or token_param.startswith('-')) else token_param)
            
            acciones.append({'accion': verbo, 'objeto': objeto, 'params': params})
        
        self.consumir('END')
        self.ast['events'][nombre_evento] = acciones

    def parsear_color(self):
        self.consumir('COLORS')
        self.consumir(':')
        colores = []
        while self.posicion < len(self.tokens) and self.tokens[self.posicion].upper() == 'COLOR':
            self.consumir('COLOR')
            self.consumir()
            self.consumir(':')
            self.consumir('[')
            color = self.consumir()
            while self.posicion < len(self.tokens) and self.tokens[self.posicion] != ']':
                color += self.consumir()
            self.consumir(']')
            colores.append(color)
        self.consumir('END')
        self.ast['colors'] = colores

def generar_codigo(ast, archivo_salida):
    with open(archivo_salida, 'w') as f:
        json.dump(ast, f, indent=2)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "Uso: python compiler.py <archivo_entrada.brick>"
        sys.exit(1)
    archivo_entrada = sys.argv[1]
    archivo_salida = archivo_entrada.replace('.brick', '.json')
    print "Compilando " + archivo_entrada + "..."
    try:
        with open(archivo_entrada, 'r') as f:
            codigo = f.read()
            tokens = lexer(codigo)
            parser = Parser(tokens)
            ast = parser.parse()
            generar_codigo(ast, archivo_salida)
            print "Compilacion exitosa! Archivo de juego creado en " + archivo_salida
    except Exception, e:
        print "\n!!! ERROR DE COMPILACION !!!"
        print str(e)
        sys.exit(1)