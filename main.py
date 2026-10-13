"""Ponto de entrada da interface TEApoia."""

import tkinter as tk

from interface import TeaPoiaApp


if __name__ == "__main__":
    raiz = tk.Tk()
    TeaPoiaApp(raiz)
    raiz.mainloop()
