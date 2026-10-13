"""Navegação e telas da V3. OCR e adaptação permanecem em módulos próprios."""

import tkinter as tk
from tkinter import font as tkfont
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext

from PIL import Image, ImageChops, ImageTk, UnidentifiedImageError

from adaptador import adaptar_exercicio
from armazenamento import BibliotecaLocal, ExercicioSalvo
from estado import Atividade
from ocr import ErroOCR, ler_texto_imagem


PREFERENCIAS = {
    "linguagem_direta": "Linguagem mais direta", "linguagem_simples": "Linguagem mais simples",
    "instrucoes_curtas": "Frases mais curtas", "dividir_etapas": "Dividir em etapas",
    "organizar": "Organizar informações", "reduzir": "Reduzir informações desnecessárias",
    "numeros": "Destacar números importantes", "palavras": "Destacar palavras-chave",
    "destacar_informacoes": "Destacar informações importantes", "pergunta": "Destacar a pergunta principal",
    "apresentar_exemplo": "Adicionar exemplo", "dica": "Adicionar dica", "visual": "Criar apoio visual",
}
GRUPOS = {"Linguagem": ["linguagem_direta", "linguagem_simples", "instrucoes_curtas"],
          "Estrutura": ["dividir_etapas", "organizar", "reduzir"],
          "Destaques": ["numeros", "palavras", "destacar_informacoes", "pergunta"],
          "Apoio pedagógico": ["apresentar_exemplo", "dica", "visual"]}
CORES = {"claro": ("#F7F9FC", "#FFFFFF", "#16213A", "#667085", "#2563EB", "#EAF2FF", "#14B8A6", "#885CF6"),
          "escuro": ("#111827", "#192536", "#F4F7FB", "#AEB9C9", "#3B82F6", "#1D3557", "#2DD4BF", "#A78BFA")}
ACOES = {
    "azul": ("#2563EB", "#1D4ED8", "#FFFFFF", None),
    "verde": ("#14B8A6", "#10A99E", "#FFFFFF", "#08766E"),
    "lilas": ("#7C3AED", "#6D28D9", "#FFFFFF", None),
}


def _retangulo_arredondado(canvas, x1, y1, x2, y2, raio, cor):
    """Desenha uma superfície arredondada sem depender do estilo nativo do sistema."""
    canvas.create_rectangle(x1 + raio, y1, x2 - raio, y2, fill=cor, outline="")
    canvas.create_rectangle(x1, y1 + raio, x2, y2 - raio, fill=cor, outline="")
    canvas.create_oval(x1, y1, x1 + 2 * raio, y1 + 2 * raio, fill=cor, outline="")
    canvas.create_oval(x2 - 2 * raio, y1, x2, y1 + 2 * raio, fill=cor, outline="")
    canvas.create_oval(x1, y2 - 2 * raio, x1 + 2 * raio, y2, fill=cor, outline="")
    canvas.create_oval(x2 - 2 * raio, y2 - 2 * raio, x2, y2, fill=cor, outline="")


class BotaoArredondado(tk.Canvas):
    """Botão de ação com cantos arredondados e os mesmos comandos da interface."""

    def __init__(self, pai, texto, comando, fundo, ativo, fonte, sombra=None, alinhamento="center", **opcoes):
        self.texto, self.comando = texto, comando
        self.fundo, self.ativo, self.fonte_cor = fundo, ativo, fonte
        self.sombra, self.alinhamento = sombra, alinhamento
        self.fonte = tkfont.Font(family="Arial", size=10, weight="bold")
        largura = self.fonte.measure(texto) + 30
        super().__init__(pai, width=largura, height=38, bg=pai.cget("bg"), bd=0,
                         highlightthickness=0, cursor="hand2", takefocus=1, **opcoes)
        self.bind("<Configure>", lambda evento: self._desenhar(self.fundo))
        self.bind("<Enter>", lambda evento: self._desenhar(self.ativo))
        self.bind("<Leave>", lambda evento: self._desenhar(self.fundo))
        self.bind("<ButtonPress-1>", lambda evento: self._desenhar(self.ativo))
        self.bind("<ButtonRelease-1>", self._acionar)
        self.bind("<Return>", lambda evento: self.invoke())
        self._desenhar(self.fundo)

    def _desenhar(self, cor):
        self.delete("all")
        largura, altura = max(self.winfo_width(), self.winfo_reqwidth()), max(self.winfo_height(), 38)
        _retangulo_arredondado(self, 0, 0, largura, altura, 12, cor)
        x, ancora = (15, "w") if self.alinhamento == "w" else (largura / 2, "center")
        if self.sombra:
            for deslocamento_x, deslocamento_y in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                self.create_text(x + deslocamento_x, altura / 2 + deslocamento_y, text=self.texto,
                                 fill=self.sombra, font=self.fonte, anchor=ancora)
        self.create_text(x, altura / 2, text=self.texto, fill=self.fonte_cor, font=self.fonte, anchor=ancora)

    def _acionar(self, evento):
        self._desenhar(self.ativo)
        self.comando()

    def invoke(self):
        self.comando()


class AlternadorTema(tk.Canvas):
    """Controle compacto de tema com indicadores desenhados no próprio Canvas."""

    def __init__(self, pai, modo, comando):
        self.modo, self.comando = modo, comando
        super().__init__(pai, width=54, height=30, bg=pai.cget("bg"), bd=0,
                         highlightthickness=0, cursor="hand2", takefocus=1)
        self.bind("<ButtonRelease-1>", lambda evento: self.comando())
        self.bind("<Return>", lambda evento: self.comando())
        self._desenhar()

    def _desenhar(self):
        trilho = "#DCEBFF" if self.modo == "claro" else "#273A52"
        indicador = "#2563EB" if self.modo == "claro" else "#2DD4BF"
        self.delete("all")
        _retangulo_arredondado(self, 1, 1, 53, 29, 14, trilho)
        centro_x = 15 if self.modo == "claro" else 39
        self.create_oval(centro_x - 10, 5, centro_x + 10, 25, fill=indicador, outline="")
        if self.modo == "claro":
            self.create_oval(centro_x - 6, 9, centro_x + 6, 21, fill="#FFFFFF", outline="")
            self.create_oval(centro_x - 2, 7, centro_x + 9, 18, fill=indicador, outline="")
        else:
            self.create_oval(centro_x - 3, 12, centro_x + 3, 18, fill="#102033", outline="")
            for dx, dy in ((0, -7), (5, -5), (7, 0), (5, 5), (0, 7), (-5, 5), (-7, 0), (-5, -5)):
                self.create_line(centro_x + round(dx * .55), 15 + round(dy * .55), centro_x + dx, 15 + dy,
                                 fill="#102033", width=2)


class TeaPoiaApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root, self.modo, self.tela = root, "claro", "Início"
        root.title("TEApoia")
        root.geometry("1180x760")
        root.minsize(950, 630)
        self.atividade, self.biblioteca = Atividade(), BibliotecaLocal()
        self.vars = {chave: tk.BooleanVar() for chave in PREFERENCIAS}
        self.preview: ImageTk.PhotoImage | None = None
        self._imagens_marca: list[ImageTk.PhotoImage] = []
        self.modo_entrada, self.texto_manual = "imagem", ""
        self._casca(); self.inicio()

    @property
    def c(self): return CORES[self.modo]

    def _casca(self):
        bg, painel, texto, _, _, _, _, _ = self.c
        self.root.configure(bg=bg)
        self.shell = tk.Frame(self.root, bg=bg); self.shell.pack(fill="both", expand=True)
        self.menu = tk.Frame(self.shell, bg=painel, width=190); self.menu.pack(side="left", fill="y"); self.menu.pack_propagate(False)
        self.area = tk.Frame(self.shell, bg=bg); self.area.pack(side="left", fill="both", expand=True)
        self._imagens_marca = []
        marca = tk.Frame(self.menu, bg=painel); marca.pack(fill="x", padx=16, pady=(20, 18))
        logo = self._imagem_marca("logo_teapoia.png", (38, 38))
        nome = self._imagem_marca("nome_teapoia.png", (96, 28))
        if logo and nome:
            tk.Label(marca, image=logo, bg=painel).pack(side="left")
            tk.Label(marca, image=nome, bg=painel).pack(side="left", padx=(9, 0))
        else:
            tk.Label(marca, text="TEApoia", bg=painel, fg=texto, font=("Arial", 16, "bold")).pack(anchor="w")
        for nome, func in [("⌂  Início", self.inicio), ("＋  Criar exercício", self.criar), ("↗  Adaptar exercício", self.adaptar), ("▣  Meus exercícios", self.biblioteca_tela), ("▤  Modelos", self.modelos)]:
            BotaoArredondado(self.menu, nome, func, "#FFFFFF", "#EAF2FF", "#111827", alinhamento="w").pack(fill="x", padx=8, pady=3)
        tk.Frame(self.menu, bg=painel).pack(fill="both", expand=True)
        BotaoArredondado(self.menu, "⚙  Configurações", self.configuracoes, "#FFFFFF", "#EAF2FF", "#111827", alinhamento="w").pack(fill="x", padx=8, pady=8)

    def _imagem_marca(self, arquivo, tamanho):
        """Carrega um recurso da marca pelo caminho do projeto e mantém a referência Tk."""
        caminho = Path(__file__).resolve().parent / "assets" / arquivo
        try:
            with Image.open(caminho) as origem:
                imagem = origem.convert("RGBA")
            conteudo = imagem.getchannel("R").point(lambda valor: 255 if valor < 245 else 0)
            area = conteudo.getbbox()
            if area:
                imagem = imagem.crop(area)
            canais = imagem.split()
            branco = ImageChops.darker(ImageChops.darker(canais[0], canais[1]), canais[2])
            imagem.putalpha(branco.point(lambda valor: 0 if valor > 245 else 255))
            imagem.thumbnail(tamanho, Image.Resampling.LANCZOS)
            foto = ImageTk.PhotoImage(imagem)
        except (FileNotFoundError, UnidentifiedImageError, OSError):
            return None
        self._imagens_marca.append(foto)
        return foto

    def pagina(self, nome, titulo, subtitulo):
        self.tela = nome
        for w in self.area.winfo_children(): w.destroy()
        bg, _, texto, muted, _, _, _, _ = self.c
        p = tk.Frame(self.area, bg=bg, padx=30, pady=23); p.pack(fill="both", expand=True)
        linha = tk.Frame(p, bg=bg); linha.pack(fill="x")
        if nome == "Início":
            marca = self._imagem_marca("nome_teapoia.png", (230, 58))
            if marca:
                tk.Label(linha, image=marca, bg=bg).pack(side="left", pady=(2, 0))
            else:
                tk.Label(linha, text=titulo, bg=bg, fg=texto, font=("Arial", 21, "bold")).pack(side="left")
        else:
            tk.Label(linha, text=titulo, bg=bg, fg=texto, font=("Arial", 21, "bold")).pack(side="left")
        AlternadorTema(linha, self.modo, self.alternar).pack(side="right")
        tk.Label(p, text=subtitulo, bg=bg, fg=muted, font=("Arial", 10), pady=7).pack(anchor="w")
        return p

    def card(self, pai):
        return tk.Frame(pai, bg=self.c[1], highlightbackground="#DDE4EF" if self.modo == "claro" else "#334155", highlightthickness=1, padx=16, pady=14)

    def botao(self, pai, texto, comando, principal=True, estilo=None):
        estilo = estilo or ("azul" if principal else "verde")
        fundo, ativo, fonte, sombra = ACOES[estilo]
        return BotaoArredondado(pai, texto, comando, fundo, ativo, fonte, sombra)

    def caixa(self, pai, altura=8):
        return scrolledtext.ScrolledText(pai, height=altura, wrap="word", padx=9, pady=8, relief="flat", bg=self.c[1], fg=self.c[2], insertbackground=self.c[2], font=("Arial", 10))

    def informacoes_exercicio(self, pai):
        """Campos mínimos compartilhados pela criação e adaptação."""
        bloco = self.card(pai); bloco.pack(fill="x", pady=(0, 14))
        tk.Label(bloco, text="Informações do exercício", bg=self.c[1], fg=self.c[2], font=("Arial", 11, "bold")).pack(anchor="w")
        linha = tk.Frame(bloco, bg=self.c[1]); linha.pack(fill="x", pady=(8, 0))
        self.campos_info = {}
        for nome, valor in [("Nome do exercício", self.atividade.nome), ("Classe/Ano", self.atividade.classe), ("Matéria", self.atividade.materia)]:
            campo = tk.Frame(linha, bg=self.c[1]); campo.pack(side="left", fill="x", expand=True, padx=(0, 9))
            tk.Label(campo, text=nome, bg=self.c[1], fg=self.c[3], font=("Arial", 9, "bold")).pack(anchor="w")
            entrada = tk.Entry(campo, relief="flat", highlightthickness=1, highlightbackground="#DDE4EF", bg=self.c[0], fg=self.c[2], insertbackground=self.c[2])
            entrada.insert(0, valor); entrada.pack(fill="x", pady=(4, 0)); self.campos_info[nome] = entrada

    def guardar_informacoes(self):
        if not hasattr(self, "campos_info"):
            return
        self.atividade.nome = self.campos_info["Nome do exercício"].get().strip()
        self.atividade.classe = self.campos_info["Classe/Ano"].get().strip()
        self.atividade.materia = self.campos_info["Matéria"].get().strip()

    def alternar(self):
        if self.tela == "Adaptar" and self.modo_entrada == "texto" and hasattr(self, "texto_manual_widget"):
            self.texto_manual = self.texto_manual_widget.get("1.0", tk.END).strip()
        self.modo = "escuro" if self.modo == "claro" else "claro"
        self.shell.destroy(); self._casca()
        {"Início": self.inicio, "Criar": self.criar, "Adaptar": self.adaptar, "Revisão": self.revisao, "Personalização": self.personalizacao, "Resultado": self.resultado, "Biblioteca": self.biblioteca_tela, "Modelos": self.modelos, "Configurações": self.configuracoes}[self.tela]()

    def inicio(self):
        p = self.pagina("Início", "TEApoia", "Mais inclusão na prática pedagógica.")
        tk.Label(p, text="Olá, professor!", bg=self.c[0], fg=self.c[2], font=("Arial", 17, "bold"), pady=4).pack(anchor="w")
        tk.Label(p, text="Como podemos ajudar você hoje?", bg=self.c[0], fg=self.c[3]).pack(anchor="w", pady=(0, 14))
        linha = tk.Frame(p, bg=self.c[0]); linha.pack(fill="x")
        for simbolo, titulo, desc, fn, estilo in [("＋", "Criar novo exercício", "Defina o conteúdo da atividade.", self.criar, "azul"), ("↗", "Adaptar exercício", "Envie uma atividade e torne-a mais acessível.", self.adaptar, "verde"), ("◈", "Explorar modelos", "Use referências como ponto de partida.", self.modelos, "lilas")]:
            ca = self.card(linha); ca.pack(side="left", fill="both", expand=True, padx=(0, 12))
            tk.Label(ca, text=simbolo, bg=ACOES[estilo][0], fg=ACOES[estilo][2], font=("Arial", 16, "bold"), padx=10, pady=6).pack(anchor="w")
            tk.Label(ca, text=titulo, bg=self.c[1], fg=self.c[2], font=("Arial", 12, "bold"), pady=10).pack(anchor="w")
            tk.Label(ca, text=desc, bg=self.c[1], fg=self.c[3], wraplength=205, justify="left").pack(anchor="w")
            self.botao(ca, "Começar →", fn, False, estilo).pack(fill="x", pady=(15, 0))
        for titulo, conteudo in [("Exercícios recentes", "Nenhum exercício salvo nesta sessão."), ("Modelos utilizados recentemente", "Matemática · Problemas com quantidades\nPortuguês · Leitura e interpretação\nCiências · Observação e investigação")]:
            ca = self.card(p); ca.pack(fill="x", pady=(18, 0)); tk.Label(ca, text=titulo, bg=self.c[1], fg=self.c[2], font=("Arial", 11, "bold")).pack(anchor="w"); tk.Label(ca, text=conteudo, bg=self.c[1], fg=self.c[3], justify="left", pady=7).pack(anchor="w")

    def criar(self):
        p = self.pagina("Criar", "Criar novo exercício", "Prepare um conteúdo para personalizar. Não há geração por IA nesta versão.")
        self.informacoes_exercicio(p)
        ca = self.card(p); ca.pack(fill="both", expand=True)
        tk.Label(ca, text="Enunciado ou conteúdo da atividade", bg=self.c[1], fg=self.c[2], font=("Arial", 11, "bold")).pack(anchor="w")
        self.criar_texto = self.caixa(ca, 14); self.criar_texto.pack(fill="both", expand=True, pady=8)
        self.botao(ca, "Continuar para personalização →", self.continuar_criar).pack(anchor="e")

    def continuar_criar(self):
        texto = self.criar_texto.get("1.0", tk.END).strip()
        if not texto: messagebox.showwarning("Conteúdo necessário", "Escreva o conteúdo da atividade para continuar."); return
        self.guardar_informacoes(); self.atividade.texto = texto; self.atividade.tema = "Atividade criada"; self.personalizacao()

    def adaptar(self):
        p = self.pagina("Adaptar", "Adaptar exercício", "1. Envie a atividade  ·  2. Revise o texto  ·  3. Personalize  ·  4. Revise o resultado")
        self.informacoes_exercicio(p)
        linha = tk.Frame(p, bg=self.c[0]); linha.pack(fill="both", expand=True)
        ca = self.card(linha); ca.pack(side="left", fill="both", expand=True, padx=(0, 12))
        tk.Label(ca, text="Enviar atividade", bg=self.c[1], fg=self.c[2], font=("Arial", 14, "bold")).pack(anchor="w")
        opcoes = tk.Frame(ca, bg=self.c[1]); opcoes.pack(anchor="w", pady=(12, 8))
        self.botao(opcoes, "Selecionar imagem", self.escolher_imagem, False, "azul").pack(side="left")
        self.botao(opcoes, "Digitar exercício", lambda: self.selecionar_modo_entrada("texto"), False, "verde").pack(side="left", padx=(8, 0))
        if self.modo_entrada == "imagem":
            self.nome = tk.Label(ca, text=self.atividade.imagem.name if self.atividade.imagem else "Nenhuma imagem selecionada.", bg=self.c[1], fg=self.c[3]); self.nome.pack(anchor="w")
            self.status = tk.Label(ca, text="O OCR usa Tesseract localmente.", bg=self.c[1], fg=self.c[3], wraplength=330, justify="left"); self.status.pack(anchor="w", pady=12)
        else:
            tk.Label(ca, text="Digite ou cole aqui o exercício que deseja adaptar.", bg=self.c[1], fg=self.c[3]).pack(anchor="w", pady=(7, 4))
            self.texto_manual_widget = self.caixa(ca, 12); self.texto_manual_widget.pack(fill="both", expand=True, pady=(0, 8))
            self.texto_manual_widget.insert("1.0", self.texto_manual)
        pr = self.card(linha); pr.pack(side="left", fill="both", expand=True)
        if self.modo_entrada == "imagem":
            tk.Label(pr, text="Pré-visualização", bg=self.c[1], fg=self.c[2], font=("Arial", 14, "bold")).pack(anchor="w")
            self.preview_label = tk.Label(pr, text="A imagem aparecerá aqui.", bg=self.c[1], fg=self.c[3], pady=105); self.preview_label.pack(fill="both", expand=True)
            self.remover_preview = self.botao(pr, "×", self.remover_imagem, False)
            if self.atividade.imagem:
                self.remover_preview.place(relx=1.0, rely=0.0, anchor="ne", x=-8, y=8)
                self.mostrar_preview(self.atividade.imagem)
        else:
            tk.Label(pr, text="Entrada de texto", bg=self.c[1], fg=self.c[2], font=("Arial", 14, "bold")).pack(anchor="w")
            tk.Label(pr, text="O conteúdo será aberto para revisão antes da personalização.", bg=self.c[1], fg=self.c[3], wraplength=330, justify="left", pady=105).pack(fill="both", expand=True)
        self.botao(p, "Próximo: revisar texto →", self.abrir_revisao).pack(anchor="e", pady=15)

    def selecionar_modo_entrada(self, modo):
        if modo == self.modo_entrada:
            return
        if self.modo_entrada == "texto" and hasattr(self, "texto_manual_widget"):
            self.texto_manual = self.texto_manual_widget.get("1.0", tk.END).strip()
        self.guardar_informacoes()
        self.modo_entrada = modo
        self.adaptar()

    def escolher_imagem(self):
        if self.modo_entrada != "imagem":
            if hasattr(self, "texto_manual_widget"):
                self.texto_manual = self.texto_manual_widget.get("1.0", tk.END).strip()
            self.guardar_informacoes()
            self.modo_entrada = "imagem"
            self.adaptar()
        self.selecionar_imagem()

    def selecionar_imagem(self):
        caminho = filedialog.askopenfilename(title="Selecione uma imagem", filetypes=[("Imagens", "*.png *.jpg *.jpeg *.gif *.bmp"), ("Todos", "*.*")])
        if not caminho: return
        self.guardar_informacoes()
        try:
            self.atividade.imagem = Path(caminho); self.mostrar_preview(self.atividade.imagem)
        except (UnidentifiedImageError, OSError): messagebox.showerror("Imagem inválida", "Não foi possível abrir esta imagem."); return
        self.nome.configure(text=f"Imagem selecionada: {self.atividade.imagem.name}"); self.status.configure(text="Lendo texto da imagem..."); self.root.update_idletasks()
        try: self.atividade.texto_ocr = ler_texto_imagem(self.atividade.imagem); self.atividade.texto = self.atividade.texto_ocr
        except ErroOCR as erro: self.atividade.texto_ocr = self.atividade.texto = ""; self.status.configure(text="Não foi possível concluir o OCR."); messagebox.showwarning("OCR", str(erro)); return
        self.status.configure(text="Texto reconhecido. Revise-o antes de continuar." if self.atividade.texto else "Não foi possível identificar texto nesta imagem.")

    def mostrar_preview(self, caminho):
        try:
            with Image.open(caminho) as im: im.thumbnail((540, 430)); self.preview = ImageTk.PhotoImage(im.copy())
            self.preview_label.configure(image=self.preview, text="")
            if hasattr(self, "remover_preview"):
                self.remover_preview.place(relx=1.0, rely=0.0, anchor="ne", x=-8, y=8)
        except (UnidentifiedImageError, OSError): self.preview_label.configure(image="", text="Não foi possível mostrar a imagem.")

    def remover_imagem(self):
        """Remove somente a referência local da atividade, nunca o arquivo do usuário."""
        self.atividade.imagem = None
        self.atividade.texto_ocr = ""
        self.atividade.texto = ""
        self.preview = None
        self.preview_label.configure(image="", text="A imagem aparecerá aqui.")
        self.nome.configure(text="Nenhuma imagem selecionada.")
        self.status.configure(text="O OCR usa Tesseract localmente.")
        self.remover_preview.place_forget()

    def abrir_revisao(self):
        if self.modo_entrada == "texto":
            self.texto_manual = self.texto_manual_widget.get("1.0", tk.END).strip()
            if not self.texto_manual:
                messagebox.showwarning("Conteúdo necessário", "Digite ou cole um exercício para continuar."); return
            self.atividade.imagem = None
            self.atividade.texto_ocr = ""
            self.atividade.texto = self.texto_manual
        elif not self.atividade.imagem:
            messagebox.showwarning("Imagem não selecionada", "Selecione uma imagem para continuar."); return
        elif not self.atividade.texto:
            messagebox.showwarning("Texto necessário", "Não foi possível identificar texto na imagem. Selecione outra imagem ou digite o exercício."); return
        self.guardar_informacoes()
        self.revisao()

    def revisao(self):
        entrada_manual = self.modo_entrada == "texto"
        p = self.pagina("Revisão", "Revisar exercício" if entrada_manual else "Texto reconhecido", "Revise o texto antes de continuar. A sua edição será usada na adaptação.")
        linha = tk.Frame(p, bg=self.c[0]); linha.pack(fill="both", expand=True)
        esq = self.card(linha); esq.pack(side="left", fill="both", expand=True, padx=(0, 12)); tk.Label(esq, text="Entrada manual" if entrada_manual else "Imagem original", bg=self.c[1], fg=self.c[2], font=("Arial", 12, "bold")).pack(anchor="w")
        self.imagem_rev = tk.Label(esq, text="O exercício foi inserido diretamente." if entrada_manual else "Sem imagem", bg=self.c[1], fg=self.c[3], pady=65); self.imagem_rev.pack(fill="both", expand=True)
        if self.atividade.imagem:
            try:
                with Image.open(self.atividade.imagem) as im: im.thumbnail((380, 320)); self.preview = ImageTk.PhotoImage(im.copy())
                self.imagem_rev.configure(image=self.preview, text="")
            except (UnidentifiedImageError, OSError): pass
        dir = self.card(linha); dir.pack(side="left", fill="both", expand=True); tk.Label(dir, text="Texto do exercício" if entrada_manual else "Texto reconhecido", bg=self.c[1], fg=self.c[2], font=("Arial", 12, "bold")).pack(anchor="w")
        self.texto_rev = self.caixa(dir, 18); self.texto_rev.pack(fill="both", expand=True, pady=8); self.texto_rev.insert("1.0", self.atividade.texto)
        self.botao(p, "Próximo: personalizar →", self.continuar_revisao).pack(anchor="e", pady=15)

    def continuar_revisao(self):
        texto = self.texto_rev.get("1.0", tk.END).strip()
        if not texto: messagebox.showwarning("Texto vazio", "Digite ou corrija o texto antes de continuar."); return
        self.atividade.texto = texto; self.personalizacao()

    def personalizacao(self):
        p = self.pagina("Personalização", "Personalização pedagógica", "Selecione estratégias e registre a sua orientação para a atividade.")
        grade = tk.Frame(p, bg=self.c[0]); grade.pack(fill="x")
        for i, (grupo, chaves) in enumerate(GRUPOS.items()):
            ca = self.card(grade); ca.grid(row=i//2, column=i%2, sticky="nsew", padx=(0,12), pady=(0,12)); grade.columnconfigure(i%2, weight=1)
            tk.Label(ca, text=grupo, bg=self.c[1], fg=self.c[2], font=("Arial", 11, "bold")).pack(anchor="w")
            for chave in chaves: tk.Checkbutton(ca, text=PREFERENCIAS[chave], variable=self.vars[chave], bg=self.c[1], fg=self.c[2], activebackground=self.c[1], selectcolor=self.c[1], anchor="w").pack(fill="x")
        ca = tk.Frame(p, bg=self.c[5], padx=16, pady=14); ca.pack(fill="both", expand=True)
        tk.Label(ca, text="✦  Instrução personalizada", bg=self.c[5], fg=self.c[7], font=("Arial", 13, "bold")).pack(anchor="w")
        tk.Label(ca, text="Como você gostaria que o exercício fosse adaptado?", bg=self.c[5], fg=self.c[2]).pack(anchor="w", pady=4)
        self.instrucao = self.caixa(ca, 5); self.instrucao.pack(fill="both", expand=True); self.instrucao.insert("1.0", self.atividade.instrucao)
        tk.Label(ca, text="Ex.: destaque os números importantes em azul.  •  Explique cada etapa com uma frase curta.  •  Coloque um exemplo antes da questão.", bg=self.c[5], fg=self.c[3], wraplength=800, justify="left", pady=8).pack(anchor="w")
        self.botao(p, "Gerar exercício adaptado →", self.gerar, estilo="lilas").pack(anchor="e", pady=15)

    def gerar(self):
        self.atividade.instrucao = self.instrucao.get("1.0", tk.END).strip()
        selecionadas = [k for k,v in self.vars.items() if v.get()]
        suportadas = [k for k in selecionadas if k in {"instrucoes_curtas","dividir_etapas","destacar_informacoes","linguagem_direta","apresentar_exemplo"}]
        if not suportadas: messagebox.showwarning("Preferência necessária", "Selecione ao menos uma preferência disponível nas regras atuais."); return
        self.adaptado, self.realizadas = adaptar_exercicio(self.atividade.texto, suportadas); self.resultado()

    def resultado(self):
        p = self.pagina("Resultado", "Exercício adaptado", "Revise o resultado antes de salvar ou iniciar uma nova atividade.")
        linha = tk.Frame(p, bg=self.c[0]); linha.pack(fill="both", expand=True)
        linha.columnconfigure(0, weight=1); linha.columnconfigure(1, weight=2); linha.rowconfigure(0, weight=1)
        original = self.card(linha); original.grid(row=0, column=0, sticky="new", padx=(0, 12))
        tk.Label(original, text="VERSÃO ORIGINAL", bg=self.c[1], fg=self.c[3], font=("Arial", 10, "bold")).pack(anchor="w")
        texto_original = self.caixa(original, 11); texto_original.pack(fill="both", pady=8)
        texto_original.insert("1.0", self.atividade.texto); texto_original.configure(state="disabled")
        adaptado = self.card(linha); adaptado.grid(row=0, column=1, sticky="nsew")
        tk.Label(adaptado, text="EXERCÍCIO ADAPTADO", bg=self.c[1], fg=self.c[6], font=("Arial", 12, "bold")).pack(anchor="w")
        texto_adaptado = self.caixa(adaptado, 16); texto_adaptado.pack(fill="both", expand=True, pady=8)
        texto_adaptado.insert("1.0", getattr(self, "adaptado", "")); texto_adaptado.configure(state="disabled")
        tk.Label(adaptado, text="Recursos utilizados na adaptação", bg=self.c[1], fg=self.c[2], font=("Arial", 11, "bold")).pack(anchor="w", pady=(4, 0))
        tk.Label(adaptado, text="\n".join("✓ " + x for x in getattr(self, "realizadas", [])), bg=self.c[1], fg=self.c[6], justify="left").pack(anchor="w", pady=6)
        if self.atividade.instrucao:
            tk.Label(adaptado, text="Orientação registrada pelo professor: " + self.atividade.instrucao, bg=self.c[1], fg=self.c[3], wraplength=600, justify="left").pack(anchor="w")
        b=tk.Frame(p,bg=self.c[0]); b.pack(fill="x"); self.botao(b,"← Nova atividade",self.nova,False).pack(side="left"); self.botao(b,"Editar texto",self.revisao,False).pack(side="left",padx=8); self.botao(b,"Adaptar novamente",self.personalizacao,False).pack(side="left"); self.botao(b,"Salvar exercício",self.salvar).pack(side="right")

    def nova(self):
        self.atividade.limpar(); self.preview=None
        self.modo_entrada, self.texto_manual = "imagem", ""
        for v in self.vars.values(): v.set(False)
        self.adaptar()

    def salvar(self):
        item = ExercicioSalvo(
            nome=self.atividade.nome or self.atividade.tema or "Atividade adaptada",
            classe=self.atividade.classe or "Não informado",
            materia=self.atividade.materia or "Não informado",
            texto=self.atividade.texto,
            texto_ocr=self.atividade.texto_ocr,
            adaptado=self.adaptado,
            preferencias=[PREFERENCIAS[k] for k, v in self.vars.items() if v.get()],
            instrucao=self.atividade.instrucao,
        )
        self.biblioteca.salvar(item, self.atividade.imagem)
        messagebox.showinfo("Exercício salvo", "O exercício foi salvo no histórico local.")

    def biblioteca_tela(self):
        p=self.pagina("Biblioteca","Meus exercícios","Histórico local dos exercícios salvos no TEApoia."); ca=self.card(p); ca.pack(fill="both",expand=True)
        itens = self.biblioteca.listar()
        if not itens: tk.Label(ca,text="Nenhum exercício salvo ainda.",bg=self.c[1],fg=self.c[3],pady=20).pack(anchor="w")
        for x in itens:
            linha = tk.Frame(ca, bg=self.c[1]); linha.pack(fill="x", pady=5)
            tk.Label(linha, text=f"{x.nome}  ·  {x.materia}  ·  {x.classe}\n{x.atualizado_em}", bg=self.c[1], fg=self.c[2], justify="left").pack(side="left")
            self.botao(linha, "Abrir", lambda item=x: self.abrir_salvo(item), False).pack(side="right")

    def abrir_salvo(self, item):
        """Mostra exatamente o exercício escolhido no histórico."""
        p = self.pagina("Biblioteca", item.nome, f"{item.materia} · {item.classe} · salvo em {item.atualizado_em}")
        ca = self.card(p); ca.pack(fill="both", expand=True)
        tk.Label(ca, text="Texto original / revisado", bg=self.c[1], fg=self.c[2], font=("Arial", 11, "bold")).pack(anchor="w")
        original = self.caixa(ca, 7); original.pack(fill="x", pady=6); original.insert("1.0", item.texto); original.configure(state="disabled")
        tk.Label(ca, text="Personalização utilizada", bg=self.c[1], fg=self.c[2], font=("Arial", 11, "bold")).pack(anchor="w", pady=(8, 0))
        tk.Label(ca, text="\n".join(f"✓ {valor}" for valor in item.preferencias) or "Nenhuma preferência registrada.", bg=self.c[1], fg=self.c[6], justify="left").pack(anchor="w")
        tk.Label(ca, text=f"Instrução personalizada: {item.instrucao or 'Não informada.'}", bg=self.c[1], fg=self.c[3], wraplength=800, justify="left", pady=8).pack(anchor="w")
        tk.Label(ca, text="Exercício adaptado", bg=self.c[1], fg=self.c[2], font=("Arial", 11, "bold")).pack(anchor="w")
        adaptado = self.caixa(ca, 8); adaptado.pack(fill="both", expand=True, pady=6); adaptado.insert("1.0", item.adaptado); adaptado.configure(state="disabled")
        self.botao(p, "Continuar editando", lambda: self.continuar_salvo(item)).pack(anchor="e", pady=14)

    def continuar_salvo(self, item):
        self.atividade.nome, self.atividade.classe, self.atividade.materia = item.nome, item.classe, item.materia
        self.atividade.texto, self.atividade.texto_ocr, self.atividade.instrucao = item.texto, item.texto_ocr, item.instrucao
        self.atividade.imagem = Path(item.imagem) if item.imagem and Path(item.imagem).exists() else None
        for chave, variavel in self.vars.items(): variavel.set(PREFERENCIAS[chave] in item.preferencias)
        self.personalizacao()

    def modelos(self):
        p=self.pagina("Modelos","Modelos","Referências simples para o professor usar como ponto de partida.")
        for categoria,nome,texto in [("Matemática","Problemas com quantidades","Maria tem 4 caixas com 6 livros cada. Quantos livros ela tem?"),("Português","Leitura e interpretação","Leia o texto e responda à pergunta principal."),("Ciências","Observação e investigação","Observe o experimento e descreva o que aconteceu.")]:
            ca=self.card(p);ca.pack(fill="x",pady=6);tk.Label(ca,text=categoria,bg=self.c[1],fg=self.c[7],font=("Arial",9,"bold")).pack(anchor="w");tk.Label(ca,text=nome,bg=self.c[1],fg=self.c[2],font=("Arial",12,"bold")).pack(anchor="w");self.botao(ca,"Usar modelo",lambda t=texto:self.usar_modelo(t),False,"lilas").pack(anchor="e")

    def usar_modelo(self,texto): self.atividade.texto=texto;self.atividade.tema="Modelo de exercício";self.personalizacao()

    def configuracoes(self):
        p=self.pagina("Configurações","Configurações","Preferências gerais da interface TEApoia.");ca=self.card(p);ca.pack(fill="x");tk.Label(ca,text="Aparência",bg=self.c[1],fg=self.c[2],font=("Arial",12,"bold")).pack(anchor="w");tk.Label(ca,text="Modo atual: "+self.modo,bg=self.c[1],fg=self.c[3],pady=8).pack(anchor="w");self.botao(ca,"Alternar modo claro / escuro",self.alternar,False).pack(anchor="w")
