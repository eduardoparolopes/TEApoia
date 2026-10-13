# TEApoio

**TEApoio** é um protótipo para feira de ciências sobre adaptação pedagógica para uma educação mais inclusiva. Ele demonstra como a apresentação de um exercício pode ser ajustada para ficar mais clara e organizada para estudantes autistas.

## Versão atual: V3 — plataforma para professores

A V1 criou a adaptação baseada em regras e a V2 adicionou OCR local. A V3 organiza essas funções em uma experiência para professores: criação, adaptação de imagem, revisão do OCR, personalização pedagógica, instrução livre, resultado, modelos, biblioteca e configurações.

Não há inteligência artificial nesta versão. OCR e regras acontecem localmente. A biblioteca é mantida somente durante a sessão; não há banco de dados.

## Como instalar

1. Abra o projeto no PyCharm.
2. Configure um interpretador Python 3.
3. No terminal do PyCharm, instale a dependência:

```bash
python -m pip install -r requirements.txt
```

O Tkinter já acompanha a instalação padrão do Python e não precisa ser instalado pelo `pip`.

O Tesseract OCR também precisa estar instalado no macOS, com os idiomas português (`por`) e inglês (`eng`). Ele é um programa local e não faz parte do `requirements.txt`.

## Como executar

Execute o arquivo `main.py` pelo PyCharm ou use:

```bash
python main.py
```

## Como utilizar

1. Clique em **Selecionar imagem** e escolha uma imagem de exercício válida.
2. Aguarde o OCR local e revise/corrija o texto reconhecido.
3. Marque uma ou mais preferências de adaptação.
4. Clique em **ADAPTAR EXERCÍCIO**.
5. Veja o texto original, a versão adaptada e a lista de adaptações aplicadas.

## Funcionalidades que ainda não existem

- Inteligência artificial;
- Banco de dados, servidor ou integração com APIs.

## Próximas versões

- **V3 — adaptação de exercícios reais**
- **V4 — integração com inteligência artificial local**

## Estrutura

```text
TEApoio/
├── main.py          # Interface Tkinter
├── adaptador.py     # Regras locais de adaptação
├── ocr.py           # Leitura local da imagem com Tesseract
├── requirements.txt # Pillow e pytesseract
└── README.md
```
