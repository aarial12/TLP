=============================================================
          PROYECTO: BrickScript - Un Lenguaje para Juegos Retro
=============================================================

BrickScript es un lenguaje de programacion simple (un "DSL" o Lenguaje de Dominio Especifico) disenado para crear juegos clasicos de estilo "Brick Game", como Tetris y Snake.

Este proyecto incluye el compilador que traduce el codigo BrickScript a un formato que la computadora entiende, y el motor de juego que lo ejecuta.

El runtime fue implementado para Windows con Python 2.7

-------------------------------------------------------------
                      COMO JUGAR
-------------------------------------------------------------

Para compilar y ejecutar un juego, hemos creado un script que hace todo el trabajo por ti.

1. Abre una terminal de comandos (cmd.exe) en la carpeta principal del proyecto (C:\tpl).

2. Usa el comando "./jugar" seguido del nombre del juego que quieres ejecutar (sin la extension .brick).

   PARA JUGAR SNAKE ORIGINAL:
   ./jugar snake

   PARA JUGAR TETRIS ORIGINAL:
   ./jugar tetris

   PARA JUGAR SNAKE REMAKE:
   ./jugar snake_remake

   PARA JUGAR TETRIS REMAKE:
   ./jugar tetris_REMAKE

   PARA JUGAR TANKS:
   ./jugar tanks

El script primero compilara el archivo .brick correspondiente. Si la compilacion es exitosa, el juego se iniciara automaticamente.

Para salir del juego, presiona la tecla 'q'.

