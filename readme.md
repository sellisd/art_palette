[![Run on Repl.it](https://repl.it/badge/github/sellisd/art_palette)](https://repl.it/github/sellisd/art_palette)
[![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io/https://github.com/sellisd/art_palette)
## Art palette game

A single player game of color matching. The goal is to match the foreground and background colors to reveal a palette inspired by a famous piece of art.

Use the mouse to scroll up or down to change the color of the central square. Once the color matches the background click to advance to the next color in the palette. If the foreground color is not very close to the background (closer than a small threshold) you lose a life. After successfully matching all colors in a palette you end the level and reveal the artwork. At any time during the game you can click on the link in the top left corner in front of the level title to open in a browser more information about the work of art.

## Installation

```
git clone https://github.com/sellisd/art_palette.git
pip3 install -r art_palette/requirements.txt
cd art_palette
python3 art.py
```