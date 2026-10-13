# AGENTS.md — Manual técnico do TEApoia

Este documento descreve o estado real do projeto em 29/09/2026. Ele deve ser lido antes de qualquer alteração por outro agente Codex.

## 1. Identidade do projeto

Nome oficial: **TEApoia**. A grafia deve permanecer exatamente `TEApoia`.

O objetivo atual é uma plataforma educacional voltada principalmente para **professores**, ajudando-os a criar, adaptar e personalizar exercícios e materiais para estudantes autistas. Não é uma plataforma voltada diretamente para alunos: não há área do aluno, respostas, provas, pontuação, ranking ou gamificação.

## 2. Visão do produto e evolução

- **V1:** protótipo inicial de adaptação de um exercício pré-programado por regras.
- **V2:** OCR local de fotografias/imagens com Tesseract, texto editável pelo professor e adaptação baseada em regras.
- **V3 atual:** interface para professores com início, criação, adaptação, revisão do OCR, personalização, instrução personalizada, resultado, modelos, histórico local e configurações.
- **Futuro:** integração com IA local ou API.

IA, Ollama, APIs externas e modelos não estão implementados. Um agente não deve adicioná-los por iniciativa própria durante ajustes da V3.

## 3. Tecnologias atuais

Confirmadas no código e ambiente:

- Python do `.venv`: **3.14.6** (`.venv/bin/python`). O código usa a sintaxe `Path | None`, portanto Python 3.10 ou superior é necessário na prática.
- Tkinter e módulos padrão (`tkinter`, `json`, `pathlib`, `dataclasses`, `uuid`, `datetime`, `shutil`): interface e armazenamento local.
- Pillow: abertura, thumbnail e preview de imagens.
- pytesseract 0.3.13: ponte Python para o executável Tesseract.
- Tesseract OCR 5.5.3, instalado externamente no macOS. O `ocr.py` também procura `/opt/homebrew/bin/tesseract` e `/usr/local/bin/tesseract`.
- Dados de idioma `por` e `eng` estão disponíveis no ambiente testado.

Dependências essenciais da aplicação: Python com Tkinter, Pillow, pytesseract e Tesseract com idiomas `por` e `eng`. `json`, `uuid`, `dataclasses`, `pathlib`, `datetime` e `shutil` são biblioteca padrão. Não há dependência opcional declarada.

`requirements.txt` contém apenas:

```text
Pillow>=10.0.0
pytesseract>=0.3.10
```

## 4. Estrutura real

```text
TEApoia/
├── AGENTS.md
├── main.py
├── interface.py
├── estado.py
├── armazenamento.py
├── ocr.py
├── adaptador.py
├── requirements.txt
├── README.md
├── exemplos/
│   └── README.md
├── dados/
│   ├── exercicios.json
│   └── imagens/
│       └── 9b02afec-9ca5-4704-b74d-8001bff5c1b5.png
└── .idea/
    └── misc.xml
```

Arquivos Python:

- `main.py` (11 linhas): ponto de entrada. Cria `tk.Tk`, instancia `interface.TeaPoiaApp` e inicia `mainloop`. Não colocar lógica de tela aqui.
- `interface.py` (291 linhas): camada atual de navegação, widgets, telas, estado visual, seleção/preview de imagem e chamadas ao OCR/adaptador. `TeaPoiaApp` é a classe principal. Depende de Pillow, `ocr.py`, `adaptador.py`, `estado.py` e `armazenamento.py`. É o arquivo mais sensível da interface; alterações devem ser pequenas e não quebrar o fluxo.
- `estado.py`: dataclass `Atividade`, com nome, classe, matéria, imagem, texto OCR, texto revisado, instrução e campos legados `disciplina`, `serie` e `tema`. `limpar()` reinicia a atividade atual.
- `armazenamento.py`: dataclass `ExercicioSalvo` e classe `BibliotecaLocal`. Lê/grava `dados/exercicios.json`, gera UUID, registra data e copia a imagem para `dados/imagens/` quando o exercício é salvo. Não é banco de dados.
- `ocr.py`: `ErroOCR`, `_configurar_tesseract()` e `ler_texto_imagem(caminho_imagem)`. Não deve ser alterado sem necessidade.
- `adaptador.py`: função `adaptar_exercicio(texto, preferencias)`. É o mecanismo local baseado em regras; não contém IA.

`dados/exercicios.json` e `dados/imagens/` são dados gerados pela aplicação e já contêm um exercício salvo. `.idea/misc.xml` é configuração do PyCharm, não lógica da aplicação.

## 5. Funcionalidades confirmadas como implementadas

### OCR

1. O professor seleciona um arquivo por `filedialog.askopenfilename` em `interface.py`.
2. Pillow abre a imagem e cria um preview.
3. `ler_texto_imagem()` configura o executável Tesseract, verifica `por` e `eng` e chama `pytesseract.image_to_string(..., lang="por+eng")`.
4. O texto retornado é colocado em `Atividade.texto_ocr` e `Atividade.texto`.
5. Na tela `Revisão`, `texto_rev` é editável. Ao avançar, o conteúdo editado substitui `Atividade.texto` e é usado na adaptação.
6. Erros de imagem, Tesseract, idiomas e OCR são convertidos em mensagens por `ErroOCR`.

### Adaptação

Está em `adaptador.py`. A função recebe o texto e uma lista de chaves de preferências. As regras que realmente alteram o resultado são:

- `instrucoes_curtas`: separa frases e as apresenta como instruções curtas;
- `linguagem_direta`: inclui apresentação objetiva da atividade;
- `destacar_informacoes`: extrai números e exibe informações importantes;
- `dividir_etapas`: cria três etapas genéricas;
- `apresentar_exemplo`: adiciona um exemplo de multiplicação.

As opções novas `linguagem_simples`, `organizar`, `reduzir`, `numeros`, `palavras`, `pergunta`, `dica` e `visual` aparecem na interface e podem ser marcadas, mas não têm regra correspondente em `adaptador.py`. Atualmente `interface.py` filtra e envia ao adaptador somente as cinco chaves suportadas. Isso é **parcial**, não deve ser descrito como adaptação completa.

O resultado mostra texto original, texto adaptado e recursos realizados. A instrução personalizada é preservada e exibida como orientação, mas ainda não transforma o texto por regras.

### Interface e navegação

Implementadas em `interface.py`:

- Início com logo textual `TEApoia`, saudação ao professor e ações Criar, Adaptar e Modelos;
- Criar exercício, com conteúdo livre e campos Nome, Classe/Ano e Matéria;
- Adaptar exercício, seleção de imagem, preview e OCR;
- Revisão do texto OCR em área editável;
- Personalização pedagógica com quatro grupos: Linguagem, Estrutura, Destaques e Apoio pedagógico;
- caixa de instrução personalizada;
- resultado com original, adaptado, recursos, Nova atividade, Editar texto, Adaptar novamente e Salvar exercício;
- Meus exercícios, com leitura do histórico JSON e botão Abrir;
- visualização individual do item salvo e ação Continuar editando;
- Modelos simples de Matemática, Português e Ciências;
- Configurações com alternância de modo claro/escuro;
- preview ampliado e botão `×` para remover a imagem apenas da atividade atual;
- botão de resultado nomeado `Editar texto`.

O modo escuro é implementado recriando a casca visual com `CORES`. Não houve teste visual automatizado porque o ambiente Codex não possui sessão gráfica Tkinter.

## 6. Estado atual da V3

Fluxo desejado:

```text
Início
  ↓
Criar exercício OU Adaptar exercício
  ↓
OCR (somente adaptação por imagem)
  ↓
Revisão editável
  ↓
Personalização pedagógica
  ↓
Instrução personalizada
  ↓
Exercício adaptado
  ↓
Revisão
  ↓
Salvar
```

Já implementado: início, criação de conteúdo manual, adaptação por imagem, OCR, revisão editável, seleção de preferências, instrução personalizada, resultado, nova atividade, adaptar novamente, salvar JSON, abrir histórico e continuar editando. O fluxo de criação manual não gera questões automaticamente; ele exige que o professor escreva o conteúdo.

Parcial: as opções pedagógicas que não existem no adaptador são apenas coletadas/registradas; a instrução personalizada é exibida, mas não é aplicada ao texto. A biblioteca abre texto e resultado, mas a tela de detalhes não mostra a imagem original visualmente, embora o caminho da imagem seja salvo.

Ainda não implementado: IA, Ollama, API externa, persistência de preferências de interface, edição do item salvo diretamente no registro existente e geração automática de exercícios.

## 7. Personalização pedagógica — requisito central

A página deve permanecer organizada e não deve ser redesenhada sem necessidade. Os grupos atuais são:

- **Linguagem:** linguagem mais direta, linguagem mais simples, frases mais curtas;
- **Estrutura:** dividir em etapas, organizar informações, reduzir informações desnecessárias;
- **Destaques:** destacar números importantes, palavras-chave, informações importantes e pergunta principal;
- **Apoio pedagógico:** adicionar exemplo, adicionar dica e criar apoio visual.

Também existe `Instrução personalizada`, onde o professor escreve livremente, por exemplo: “Destaque os números importantes em azul.”, “Coloque as palavras-chave em negrito.” ou “Acrescente uma dica sem entregar a resposta.”

Futuramente texto, preferências e instrução devem poder ser enviados juntos a um serviço de adaptação, sem acoplar a interface a Ollama ou fornecedor específico.

## 8. Informações do exercício

Nome, classe/ano e matéria já são solicitados nas telas Criar e Adaptar e ficam em `Atividade.nome`, `Atividade.classe` e `Atividade.materia`. O salvamento JSON também registra esses campos. Os campos legados `disciplina`, `serie` e `tema` ainda existem em `Atividade`, mas não são a fonte principal atual.

## 9. Meus exercícios e histórico

`BibliotecaLocal` usa JSON local em `dados/exercicios.json`. Ao salvar, gera identificador UUID, data/hora, copia a imagem original para `dados/imagens/` quando há uma imagem acessível e registra:

- identificador;
- nome;
- classe/ano;
- matéria;
- caminho da imagem;
- texto OCR bruto;
- texto corrigido (`texto`);
- preferências selecionadas;
- instrução personalizada;
- resultado adaptado;
- data de atualização.

`Meus exercícios` lista os registros persistidos. `Abrir` mostra o registro escolhido e `Continuar editando` carrega seus dados para a personalização. Não há banco de dados externo nem servidor.

## 10. Identidade visual e requisitos de interface

Nome: `TEApoia`. A interface deve ser profissional, moderna, limpa, tecnológica, acessível e acolhedora, sem aparência infantil. Base: preto, branco e cinzas neutros. Acentos: azul, verde, roxo e amarelo; não devem dominar a interface. Tipografia preferencial: Inter ou equivalente disponível.

Devem ser preservados como requisitos de refinamento:

- logo TEApoia em destaque na página inicial;
- botões com bordas finas/arredondadas ou discretas, sem bordas pretas pesadas;
- contraste adequado nos modos claro e escuro;
- nunca branco sobre branco nem texto escuro sobre fundo muito escuro;
- preview de imagem grande, proporcional e com botão X de remoção;
- ação `Editar texto`, não apenas `Editar`;
- Personalização Pedagógica é considerada boa e não deve ser redesenhada sem necessidade.

## 11. Arquitetura futura de IA

Requisito futuro, não implementação atual:

```text
Interface
   ↓
Serviço de adaptação
   ↓
Implementação escolhida
   ├── regras locais
   ├── IA local (por exemplo, Ollama)
   └── API externa
```

A interface não deve chamar diretamente Ollama ou um fornecedor de API. A implementação atual é somente a função local em `adaptador.py`.

## 12. Decisões que não devem ser desfeitas

- O produto é voltado a professores, não a alunos.
- Não adicionar área do aluno, gamificação, ranking, pontuação, diagnóstico ou funcionalidades clínicas.
- Não criar login/cadastro complexo sem solicitação.
- Não transformar elementos de referências visuais em funcionalidades obrigatórias sem pedido.
- Preservar OCR, revisão/edição do texto reconhecido e adaptação por regras.
- Não substituir funcionalidades existentes por versões fictícias.
- Não reescrever o projeto inteiro quando uma alteração local resolver a tarefa.

## 13. Bugs e problemas conhecidos (não corrigidos neste documento)

1. **`interface.py`, linhas 110–117 — lista inicial estática.** A seção “Exercícios recentes” sempre mostra “Nenhum exercício salvo nesta sessão”, mesmo quando existem registros em `dados/exercicios.json`. Impacto: o resumo da página inicial não reflete o histórico. Não impede a execução; causa de provável implementação estática.
2. **`interface.py`, linhas 221–224 — preferências parciais.** Oito opções são exibidas, mas somente cinco chegam ao adaptador e alteram o resultado. Impacto: marcar certas opções não muda a adaptação, embora elas sejam registradas ao salvar. Não impede a execução; é limitação deliberada da adaptação atual.
3. **`interface.py`, linhas 212–216 e 232 — instrução personalizada não é aplicada.** Ela é guardada e exibida, mas não altera o texto adaptado. Impacto: o professor vê a orientação registrada, mas a regra local não a executa.
4. **`interface.py`, linhas 263–274 — detalhes do histórico não exibem a imagem.** O caminho é armazenado e a imagem é copiada no salvamento, mas a tela aberta exibe os textos e metadados, não um preview da imagem.
5. **`armazenamento.py`, linhas 28–34 — JSON incompatível é tratado como lista vazia.** Se o arquivo estiver corrompido ou tiver schema antigo, `listar()` retorna vazio silenciosamente. Impacto: o histórico pode parecer apagado; não há aviso ao usuário.
6. **Portabilidade do caminho da imagem.** O JSON armazena caminho absoluto para a imagem copiada. Mover o projeto para outro computador pode tornar o caminho inválido, embora os dados textuais continuem disponíveis.
7. **`.idea/misc.xml` — interpretador apontado para caminho antigo.** A configuração registra `~/PycharmProjects/PythonProject1/.venv`, enquanto o projeto atual está em `TEApoia/.venv`. Isso pode fazer o PyCharm usar um interpretador inexistente/errado. Não foi alterado.
8. **`.venv/bin/pip` — shebang aponta para `PythonProject1`.** O executável `pip` do ambiente tem caminho antigo; use o interpretador configurado no PyCharm e verifique o ambiente antes de instalar. Não foi alterado.
9. **Ambiente sem sessão gráfica.** A sintaxe, importações, OCR e histórico foram testados, mas a janela Tkinter não foi visualmente aberta neste ambiente. Isso limita a confirmação visual de modo claro/escuro e layout.

## 14. Como executar

O executável Python confirmado do projeto é `.venv/bin/python` (Python 3.14.6). Em um shell macOS, a forma de ativar o ambiente é:

```bash
source .venv/bin/activate
```

Depois, executar:

```bash
python main.py
```

Ou, sem ativar:

```bash
.venv/bin/python main.py
```

Dependências Python declaradas em `requirements.txt` são Pillow e pytesseract. O Tkinter acompanha Python e o Tesseract é externo; não deve ser colocado no `requirements.txt`. A instalação normal, quando necessária e autorizada, é:

```bash
python -m pip install -r requirements.txt
```

No ambiente auditado, o executável `pip` tem shebang antigo; não corrigir isso automaticamente. O Tesseract local precisa estar instalado e oferecer `por` e `eng`.

Teste de OCR confirmado com a imagem existente no projeto:

```bash
.venv/bin/python -c 'from ocr import ler_texto_imagem; print(ler_texto_imagem("dados/imagens/9b02afec-9ca5-4704-b74d-8001bff5c1b5.png"))'
```

Verificação de sintaxe confirmada:

```bash
.venv/bin/python -m py_compile main.py interface.py estado.py armazenamento.py adaptador.py ocr.py
```

## 15. COMO TRABALHAR NESTE PROJETO

Antes de modificar qualquer código:

1. Ler este `AGENTS.md`.
2. Analisar os arquivos relacionados à tarefa.
3. Identificar o que já funciona.
4. Não assumir que o código precisa ser refeito.
5. Fazer a menor alteração necessária.
6. Não alterar funcionalidades não relacionadas.
7. Executar/testar a aplicação depois da alteração.
8. Informar quais arquivos foram alterados.
9. Informar o que foi testado.
10. Se houver dúvida sobre uma decisão de produto, perguntar antes de implementar algo grande.

Para interface: preservar funcionalidade, alterar apenas o necessário e verificar modo claro/escuro quando houver ambiente gráfico.

Para OCR: não substituir Tesseract sem solicitação e preservar a edição do texto reconhecido.

Para IA futura: não acoplar a interface diretamente a fornecedor; manter possibilidade de IA local ou API através de uma camada de serviço.

## 16. Regra de ouro

**Antes de melhorar o TEApoia, entenda primeiro como ele funciona.**

O próximo Codex deve tratar o projeto como software existente em evolução, não como um projeto vazio.
