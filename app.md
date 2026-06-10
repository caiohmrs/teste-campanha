# ANÁLISE COMPLETA DO APLICATIVO "COMANDO 2026"

## 1. VISÃO GERAL

O "COMANDO 2026" é um aplicativo web desenvolvido em Streamlit para gestão de
campanha política (Max Maciel 2026). Ele funciona como um painel de comando
centralizado onde colaboradores, supervisores, administradores e equipe de
suporte interagem com um fluxo de trabalho baseado em:

- Registro de presenca (check-in/check-out) com foto e GPS
- Missoes diarias direcionadas por grupo
- Gestao de contratos (envio e upload de assinados)
- Gestao de grupos e macro-regioes (territorios)
- Gamificacao com ranking e pontuacao
- Controle de materiais por equipe
- Dashboard administrativo com logs, mapa e metricas

A arquitetura usa **Google Sheets como banco de dados principal** e **Google Drive
como armazenamento de arquivos** (fotos de check-in/check-out, contratos PDF).
Nao ha banco de dados relacional ou API backend — tudo roda diretamente no
Streamlit via chamadas as APIs do Google.

---

## 2. ESTRUTURA DO PROJETO

```
campanha.py                          # Entry point (redireciona para login)
funcoes.py                           # ~1306 linhas: toda a lógica de negócio
requirements.txt                     # Dependências
.streamlit/config.toml               # Configuração do Streamlit
.env                                 # Credenciais (secrets)

pages/
├── 00_Login.py                      # Tela de autenticação
├── 01_Principal.py                  # Roteador central por cargo
├── 02_Colaborador.py                # Painel do colaborador (~590 linhas)
├── 03_Supervisor.py                 # Painel do supervisor (~656 linhas)
├── 04_Admin.py                      # Painel administrativo (~663 linhas)
└── 05_Suporte.py                    # Painel de suporte técnico (~172 linhas)

utils/
├── __init__.py                      # Exporta estilos
├── styles.py                        # ~969 linhas CSS centralizado (neo-brutalista)
├── components.py                    # ~512 linhas de componentes HTML reutilizáveis
└── gamification.py                  # ~32 linhas: pontuação, limites, labels
```

---

## 3. FUNCIONALIDADES E COMO FUNCIONAM

### 3.1 LOGIN (pages/00_Login.py)

**Como funciona:**
- O usuario digita seu e-mail/ID no campo unico
- O sistema carrega a aba "Usuarios" do Google Sheets via URL publica CSV
- Compara o e-mail digitado (case-insensitive) com a coluna ID_Usuario
- Se encontra, salva o dicionario do usuario em `st.session_state["usuario_logado"]`
- Define um cookie `comando2026_user_id` via extra_streamlit_components (CookieManager)
- Redireciona para 01_Principal.py (roteador)

**Componentes Streamlit usados:**
- `st.text_input` — campo de e-mail
- `st.button` — botao "ENTRAR"
- `st.spinner` — feedback visual durante validacao
- `st.columns` — layout centralizado [1,2,1]
- `stx.CookieManager` — gerencia cookie de sessao
- `st.markdown` + `unsafe_allow_html=True` — cabecalho estilizado
- Componentes custom: `render_login_header()`, `render_login_box()`

---

### 3.2 ROTEADOR CENTRAL (pages/01_Principal.py)

**Como funciona:**
- Verifica se `usuario_logado` existe; se nao, volta para Login
- Captura o cargo do usuario e redireciona via `st.switch_page()`:
  - "colaborador" → pages/02_Colaborador.py
  - "supervisor" → pages/03_Supervisor.py
  - "admin" → pages/04_Admin.py
  - "suporte" → pages/05_Suporte.py
- Inicializa captura de erros globais via `sys.excepthook`

**Componentes Streamlit usados:**
- `st.switch_page` — redirecionamento
- `st.error` + `st.stop` — fallback para cargo desconhecido
- Variaveis de sessão para controle de estado

---

### 3.3 PAINEL COLABORADOR (pages/02_Colaborador.py)

**Funcionalidades:**

1. **Mensagem do Dia (Banner de Diretrizes)**
   - Carrega aba "Mensagens" e filtra pelo ID_Grupo do usuario
   - Exibe banner informativo com a mensagem + tarefa direcionada
   - Usuario precisa confirmar que leu antes de prosseguiguir (`st.stop()`)
   - Variavel `mensagem_exibida` na sessao controla exibicao unica

2. **Captura de GPS**
   - Usa `get_geolocation()` do streamlit_js_eval
   - Armazena coordenadas em `st.session_state['last_coords']`
   - Mostra status visual: verde (ativo), vermelho (erro), amarelo (buscando)

3. **Check-in (Modal Dialog)**
   - `@st.dialog` do Streamlit cria modal "Registro de Entrada"
   - `st.camera_input` — foto obrigatoria tirada na hora
   - Upload da foto para Google Drive via `salvar_foto_drive()`
   - Registra acao na aba "Logs" via `registrar_acao()`
   - Atualiza pontuacao via `atualizar_pontuacao_usuario()`
   - Salva cookie `comando2026_checkin_time`

4. **Check-out (Modal Dialog)**
   - Modal "Registro de Saida"
   - Tambem exige foto obrigatoria
   - `st.select_slider` — clima do dia (Dificil/Normal/Excelente)
   - `st.text_area` — observacoes
   - Upload + registro + pontuacao (mesmo fluxo do check-in)
   - Remove cookie de check-in time

5. **Missoes Diarias**
   - Exibe tarefa direcionada vinda da planilha de Mensagens
   - Botao "CONCLUIR MISSAO DE HOJE" registra acao + pontos
   - Acoes de rede: Instagram (abre perfil) e WhatsApp (mensagem pronta)

6. **Aba Meus Contratos**
   - Carrega aba "Contratos" e filtra pelo ID_Usuario
   - Para cada contrato pendente: botao para baixar original
   - `st.file_uploader` (type=pdf) — upload do contrato assinado
   - Upload para Drive + atualiza status na planilha

7. **Aba Ranking (Gamificacao)**
   - Carrega aba "Leaderboard" e calcula:
     - Pontos acumultados do usuario ditadelat
     - Posicao no ranking (filtrado por cargo)
     - Progresso de acoes do dia (feitas/limite)
   - Componentes: `render_leaderboard`, `render_action_progress`, `render_info_ranking`

8. **Suporte**
   - Botao WhatsApp para falar com supervisor (busca via ID_Supervisor)
   - Botao WhatsApp para suporte tecnico (numero fixo 5561998788292)

**Componentes Streamlit usados:**
- `st.tabs` — 3 abas (Missoes, Contratos, Ranking)
- `st.dialog` — modais de check-in/check-out
- `st.camera_input` — captura de foto
- `st.status` — processo de registro expandido
- `st.select_slider` — clima do dia
- `st.link_button` — links externos (Instagram, WhatsApp)
- `st.file_uploader` — upload de PDF
- `st.expander` — secoes colapsaveis (info ranking, progresso)
- `st.container(border=True)` — cards visuais
- `st.link_button` e `st.button` extensivamente

---

### 3.4 PAINEL SUPERVISOR (pages/03_Supervisor.py)

**Funcionalidades:**

Tudo que o colaborador tem, **mais**:

1. **Aba Acompanhamento (Equipe)**
   - Carrega colaboradores vinculados via ID_Supervisor
   - Para cada membro: expander com status (COMPLETO/EM CAMPO/REDES/OFF)
     - COMPLETO = check-in + missao concluida
     - EM CAMPO = so check-in
     - REDES = so acoes de rede
     - OFF = nenhuma acao
   - Mostra ultimas 5 acoes de cada membro com horario, acao e clima
   - Botao de acao rapida via WhatsApp (motivar/cobrar/reforcar)

2. **Controle de Materiais**
   - Expander "Controle de Materiais e Nivel de Estoque"
   - Formulario para registrar entrega de material (render_material_form)
   - Resumo de materiais por grupo (render_material_summary)
   - Niveis: Pouco (100), Medio (500), Muito (1000), Acabou (0)
   - Data de analise selecionavel para filtrar logs do dia

3. **Relatorio de Equipe**
   - Botao para enviar relatorio consolidado via WhatsApp para coordenacao

**Componentes Streamlit usados:**
- `st.date_input` — selecao de data de analise
- `st.columns` com gap="large" — layouts
- Componentes custom: render_material_form, render_material_summary
- Todo o resto igual ao colaborador

---

### 3.5 PAINEL ADMIN (pages/04_Admin.py)

**Funcionalidades:**

**6 abas administrativas:**

1. **EQUIPES**
   - Filtro por Macro_Grupo (selectbox dinamico)
   - Para cada supervisor: card com nome, macro, ID grupo, tamanho da equipe, ativos hoje
   - Botao WhatsApp + Botao Grupo para cada supervisor
   - Expander com lista de voluntarios de cada equipe

2. **DASHBOARD**
   - Ticker animado de ultimas 10 acoes (CSS animation)
   - 3 metricas principais: Acoes Totais, Colaboradores Ativos, Contratos Registrados
   - Tabela com ultimos 20 logs (st.dataframe)
   - Botao de exportacao para Excel (xlsxwriter via BytesIO)

3. **MAPA**
   - `folium.Map` centrado na media das coordenadas
   - `st_folium` renderiza mapa interativo no Streamlit
   - Filtro por data (st.selectbox)
   - Markers com popup (nome + acao)
   - Coordenadas extraidas da coluna "Localizacao" dos logs

4. **MENSAGENS (Diretrizes)**
   - Formulario para criar/atualizar diretrizes por grupo
   - Campos: ID do Grupo, Mensagem de Popup, Missao de Rua
   - Seleciona grupo existente ou cria novo
   - Atualiza diretamente na aba "Mensagens" via gspread

5. **CADASTRO**
   - Formulario de novo integrante: ID, Nome, WhatsApp, Cargo, Grupo, Supervisor
   - Listas dinamicas de supervisores e grupos (da planilha)
   - Secao de Gestao de Grupos: criar novo grupo + novo Macro_Grupo
   - Lista de grupos cadastrados agrupados por Macro_Grupo (expanders)

6. **CONTRATOS**
   - Envio de contrato para integrante (upload PDF + grava na planilha)
   - Monitoramento: tabela com status de todos os contratos
   - Links para original e assinado

**Componentes Streamlit usados:**
- `st.tabs` — 6 abas
- `st.selectbox` — filtros dinâmicos
- `st.form` + `st.form_submit_button` — formularios
- `st.metric` — cards de metricas
- `st.dataframe` — tabelas de dados
- `folium.Map` + `st_folium` — mapa interativo
- `st.download_button` — exportacao Excel
- `st.selectbox`, `st.text_input`, `st.text_area` — formularios
- `st.file_uploader` — upload PDF

---

### 3.6 PAINEL SUPORTE (pages/05_Suporte.py)

**Funcionalidades:**

1. **DIAGNOSTICO**
   - Testa todas as conexoes: Sheets, Drive, Planilha, Cache
   - Exibe cards visuais (verde/vermelho) para cada conexao
   - Botao para executar teste sob demanda

2. **LOGS DE ERRO**
   - Exibe erros da sessao atual (st.session_state["error_log"])
   - Metricas: Total, Criticos, Funcoes Afetadas, Ultimo Erro
   - Filtro por tipo de erro
   - Cada erro em expander com detalhes

3. **TODAS AS ACOES** (implementacao parcial/incompleta)
4. **SIMULADOR** (referenciado, implementacao nao visivel no codigo lido)
5. **SISTEMA** (referenciado, implementacao nao visivel)

**Componentes Streamlit usados:**
- `st.columns(4)` — grid de metricas
- `st.selectbox` — filtro de tipo de erro
- `st.expander` — detalhes de cada erro
- `st.metric` — contadores
- `st.json` — detalhes tecnicos

---

## 4. CONEXÕES EXTERNAS

### 4.1 Google Sheets (gspread + URL CSV)

**Modo 1 — Leitura via URL pública (gviz):**
```python
url = f"https://docs.google.com/spreadsheets/d/{planilha_id}/gviz/tq?tqx=out:csv&sheet={nome_aba}"
df = pd.read_csv(url)
```
- Usado em `carregar_dados()` para todas as leituras de dados
- Consome a aba "Usuarios", "Mensagens", "Logs", "Contratos", "Leaderboard"
- Vantagem: sem limite de chamadas de API, resposta rapida (=cache)
- Desvantagem: requer planilha publica na web

**Modo 2 — Escrita via gspread (Service Account):**
```python
client = gspread.authorize(ServiceAccountCredentials.from_service_account_info(...))
planilha = client.open_by_key(secrets["planilha"]["id"])
aba = planilha.worksheet("Logs")
aba.append_row([...])
```
- Credenciais via `st.secrets["connections"]["gsheets"]` (Service Account JSON)
- Usado para: append_row em Logs, Contratos, Mensagens, Grupos, Usuarios, Materiais, Leaderboard
- Leitura via `get_all_records()` quando precisa de dados atualizados para escrita

### 4.2 Google Drive (google-api-python-client)

**Credenciais OAuth (Refresh Token):**
```python
creds = OAuthCredentials(token=None, refresh_token=..., client_id=..., client_secret=...)
drive_service = build('drive', 'v3', credentials=creds)
```

**Operacoes:**
- Upload de fotos JPEG → pasta `id_pasta_fotos`
- Upload de documentos PDF → pasta `id_pasta_contratos`
- Definicao de permissao publica de leitura (`type: anyone, role: reader`)
- Retorna `webViewLink` para visualizacao

### 4.3 Nominatim / OpenStreetMap (geopy)

**Geocodificacao reversa:**
- Converte coordenadas GPS em endereco legivel
- Usado em `obter_endereco_simples()` para registrar local nas acoes/Logs
- User-agent: "comando2026_geocoder"
- Timeout: 10 segundos
- Resultado: rua + bairro OU bairro + cidade

### 4.4 Navegador do Usuario (streamlit_js_eval)

**Geolocalizacao:**
- `get_geolocation()` captura lat/lon via API de geolocalizacao do navegador
- Disponivel em todas as paginas de usuario (colaborador/supervisor)
- Permissao depende do navegador do usuario

---

## 5. SISTEMA DE GAMIFICAÇÃO

**Arquivo:** `utils/gamification.py`

| Acao            | Pontos | Limite Diario |
|-----------------|--------|---------------|
| checkin         | 5      | 1             |
| checkout        | 5      | 1             |
| missao          | 10     | 1             |
| insta_engage    | 2      | 3             |
| whatsapp        | 10     | 1             |

**Como funciona:**
- Acao registrada → normalizada para codigo interno (ex: "Check-in" → "checkin")
- Verifica limite diario (contando acoes do mesmo tipo no mesmo dia)
- Se limite nao atingido: credita pontos no leaderboard
- Grava nova linha na aba "Leaderboard" a cada acao (nao atualiza linha existente — modelo append-only)
- Calculo de ranking: ordenacao por pontos_total descendente
- Ranking separado por cargo (colaboradores so veem colaboradores, supervisores so veem supervisores)

**Problema conhecido:** O calculo do ranking por cargo depende de merge com a planilha
"Usuarios" para obter o cargo. O filtro usa `str.contains()` que pode dar match
parcial em cargos com nomes similares.

---

## 6. COMPONENTES DO STREAMLIT UTILIZADOS

### 6.1 Componentes Nativos Streamlit Usados

| Componente | Onde e como e usado |
|---|---|
| `st.set_page_config()` | Em todas as paginas (titulo, icone, layout) |
| `st.markdown(unsafe_allow_html=True)` | HTML custom em todos os componentes |
| `st.columns()` | Layouts em grade (2, 3, 4 colunas com gaps) |
| `st.container(border=True)` | Cards visuais |
| `st.tabs()` | Navegacao por abas (3 a 6 abas por pagina) |
| `st.expander()` | Secoes colapsaveis (info, listas, detalhes) |
| `st.dialog()` | Modais de check-in/check-out (Streamlit 1.28+) |
| `st.text_input()` | Inputs de texto (login, IDs, nomes) |
| `st.text_area()` | Areas de texto (mensagens, observacoes) |
| `st.button()` | Botoes de acao em todo o app |
| `st.selectbox()` | Selecoes (macro-grupos, destinatarios, tipos, datas) |
| `st.select_slider()` | Slider de clima (check-out) |
| `st.form()` / `st.form_submit_button()` | Formularios (cadastro, mensagens, materiais) |
| `st.file_uploader()` | Upload de PDFs e fotos |
| `st.camera_input()` | Captura de camera (check-in/check-out) |
| `st.link_button()` | Links externos (Instagram, WhatsApp, Maps) |
| `st.dataframe()` | Tabelas de dados (logs, contratos) |
| `st.metric()` | Cards de metricas (dashboard, suporte) |
| `st.status()` | Processamento assincrono (check-in) |
| `st.spinner()` | Loading (validacao, envio) |
| `st.tabs()` | Navegacao principal |
| `st.date_input()` | Selecao de data (supervisor) |
| `st.tabs()` | 3-6 abas por painel |
| `st.divider()` | Separadores visuais |
| `st.json()` | Debug de diagnostico |
| `st.download_button()` | Exportacao Excel |
| `st.error()` / `st.success()` / `st.warning()` / `st.info()` | Feedback visual |
| `st.switch_page()` | Redirecionamento entre paginas |
| `st.cache_data()` | Cache de dados da planilha (TTL=120s) |
| `st.rerun()` | Recarregamento da pagina |
| `st.stop()` | Parar execucao (mensagem do dia) |
| `st.session_state` | Estado global da sessao |

### 6.2 Bibliotecas Externas de UI

| Biblioteca | Uso |
|---|---|
| `extra_streamlit_components (stx)` | CookieManager para sessoes persistentes |
| `streamlit_js_eval` | get_geolocation() — GPS do navegador |
| `folium` + `streamlit_folium` | Mapa interativo com marcadores |
| `xlsxwriter` | Geracao de Excel para exportacao |

### 6.3 Bibliotecas de Backend/Dados

| Biblioteca | Uso |
|---|---|
| `pandas` | DataFrames para manipulacao de dados |
| `gspread` | Leitura/escrita no Google Sheets |
| `google-api-python-client` | Upload no Google Drive |
| `google-auth` | Autenticacao OAuth e Service Account |
| `geopy` (Nominatim) | Geocodificacao reversa de coordenadas |

---

## 7. PROBLEMAS IDENTIFICADOS

### 7.1 CRITICOS (Seguranca e Funcionalidade)

1. **Credenciais de Service Account no secrets**: O JSON do Service Account Google e tratado
   como dicionario em `st.secrets["connections"]["gsheets"]`. Se o Streamlit Cloud ou similar
   os expor em logs, ha risco de vazamento. O arquivo `.gitignore` nao exclui `.env`.

2. **Upload de arquivo PDF sem validacao real**: O upload em `st.file_uploader(type=['pdf'])` 
   so verifica extensao. Usuarios podem enviar arquivos maliciosos. Nao ha validacao de MIME type
   no backend.

3. **Pasta do Drive com permissao publica**: Toda foto e contrato recebe 
   `{'type': 'anyone', 'role': 'reader'}`. Qualquer pessoa com o link pode acessar.
   Fotos de check-in podem conter informacoes sensiveis.

4. **Sem sanitizacao de inputs de texto**: Textos digitados pelo usuario sao inseridos 
   diretamente no Google Sheets e renderizados via `unsafe_allow_html=True`.
   Risco de XSS se alguem injetar script HTML em campos de texto.

5. **Loop de redirecionamento potencial**: Se `st.switch_page` falhar em alguma 
   condicao, a pagina pode ficar em loop de redirecionamento.

### 7.2 ESTRUTURAIS (Manutenibilidade)

6. **Duplicacao massiva de codigo**: 
   - Sidebar com logout esta duplicado em 4 paginas (Colaborador, Supervisor, Admin, Suporte)
   - Logica de modal check-in/check-out duplicada em Colaborador e Supervisor (copia identica)
   - Inicializacao de session_state duplicada em todas as paginas
   - Mesmo padrao de carregamento de dados (df_msgs, df_usuarios, df_logs) repetido

7. **Tamanho excessivo dos arquivos**:
   - `funcoes.py`: 1306 linhas — junta todas as funcoes de backend misturadas
   - `styles.py`: 969 linhas CSS inline
   - `components.py`: 512 linhas de HTML gerado via string
   - Cada pagina de painel e enorme (Admin tem 663 linhas so em uma pagina)

8. **carregar_dados nao usa gspread**: A funcao de leitura usa URL publica CSV 
   (`gviz/tq`), enquanto as funcoes de escrita usam `gspread`. Isso significa que 
   leituras nao refletem mudancas imediatas (delay de propagacao do CSV publico).
   Alem disso, `_get_gspread_client()` e criado dentro de `carregar_dados()` 
   (linha 246) mas nunca e usado — e so para shear no codigo.

9. **Registro acoplado a gamificacao**: A funcao `registrar_acao()` tambem 
   atualiza a pontuacao dentro dela mesma. Isso acopla duas responsabilidades.
   Se a gamificacao falhar, o registro da acao tambem falha.

10. **Leaderboard append-only infla a planilha**: Cada acao grava uma NOVA linha no 
    Leaderboard, nao atualiza uma existente. A planilha cresce linearmente com cada acao.
    Para 50 colaboradores fazendo 5 acoes/dia = 250 linhas/dia = ~91.000 linhas/ano.

### 7.3 PERFORMANCE

11. **Todas as paginas carregam dados da planilha ao abrir**:
    Nao ha cache efetivo entre paginas (cada pagina recarrega do zero).
    `carregar_dados()` usa `@st.cache_data(ttl=120)` mas as funcoes de gspread
    nao sao cacheadas. A requisicao HTTP ao CSV do Google e feita em cada load.

12. **get_geolocation() e chamado em cada rerun**: Toda vez que a pagina recarrega,
    a requisicao de geolocacao e refeita. Isso pode causar lentidao no mobile.

13. **Carregamento de abas completas**: `get_all_records()` carrega TODOS os dados 
    das abas Leaderboard e Usuarios/re. Para planilhas grandes, isso e lento e custoso.

14. **Diagnostico cria cliente gspread 4 vezes**: A funcao `diagnosticar_conexoes()` 
    chama `_get_gspread_client()` e `_get_drive_credentials()` separadamente, recriando 
    conexoes a cada teste.

### 7.4 UX / COMPONENTES

15. **`render_action_link_button` cria botao via HTML anchor, nao st.link_button**:
    O componente `render_action_link_button()` (components.py linha 194-200) gera um `<a>` 
    com HTML inline para botoes de acao de rede. Isso e inconsistente com o resto do app 
    que usa `st.link_button`. Alem disso, tem potencial de incompatibilidade CSS.

16. **`st.space()` pode causar erro**: Usado em `render_leaderboard` 
    (components.py linha 350) — esse componente e do Streamlit experimental e pode 
    nao existir em todas as versoes. Causara `AttributeError` se a versao nao suportar.

17. **Sidebar codigo-morta no logout Admin**: As linhas 126-146 do Admin.py contem 
    codigo de de log duplicado apos `st.switch_page()`, que torna-se inalcancavel apos 
    redirecionamento.

18. **Expander contendo formulario de materiais nao tem key unico**: 
    O formulario em `render_material_form` usa key fixo `form_material_grupo`, o que 
    pode causar conflito se chamado multiplas vezes.

19. **Filtro no mapa pode quebrar**: A extracao de coordenadas no mapa (Admin.py linha 348) 
    usa `lambda pos: float(pos.split(",")[0])` sem verificar se conteudo GPS e valido 
    antes. Coordenadas como "Sem GPS" ou "Aguardando..." causariam excecao.

### 7.5 REQUISITOS / DEPENDENCIAS

20. **requirements.txt tem entrada duplicada**: `gspread` aparece nas linhas 3 e 10.
    `oauth2client` listado mas nao importado em nenhum arquivo visivel.

21. **gspread + google-api-python-client competem**: As duas bibliotecas usam 
    versoes diferentes do google-auth. Podem haver conflitos de dependencias.

22. **extra-streamlit-components sem pinning de versao**: O CookieManager mudou de API 
    entre versoes. Sem pinning, updates podem quebrar a sessao.

---

## 8. COMPONENTES QUE PODERIAM SER USADOS PARA MELHORAR

### 8.1 Componentes Streamlit Nao Utilizados (que resolveriam problemas)

| Componente | Problema que resolveria |
|---|---|
| `st.page_link()` | Navegacao mais limpa entre paginas (st.switch_page e mais recente, mas st.page_link e explicito) |
| `st.toast()` | Notificacoes nao-intrusivas para acoes registradas (em vez de st.success + time.sleep) |
| `st.barchart()` / `st.line_chart()` | Graficos de evolucao de acoes no Dashboard Admin (atualmente so tem metricas simples) |
| `st.cache_resource()` | Cache de conexoes gspread e drive (atualmente recria a cada chamada) — mudancst.cache_data so funciona para funcoes puras |
| `st.cache_data()` com `show_spinner=True` | Feedback visual durante recarga de dados (atualmente spinner e manual) |
| `st.form(key="...")` com validacao | Validacao de campos obrigatorios (atualmente feita manual com if/else) |
| `st.popover()` | Links de acao rapida dentro de botoes (Instagram, WhatsApp) |
| `st.toggle()` | Switch on/off para filtros (mais intuitivo que selectbox para booleanos) |
| `st.pydeck_chart()` | Mapa mais performatico que folium (especialmente com muitos marcadores) |
| `st.progress()` | Barra de progresso nativa (em vez de HTML custom) |
| `st.skeleton()` | Loading skeleton durante carregamento de dados |
| `st.fragment()` | Atualizacoes parciais sem rerun completo (Streamlit 1.37+) |
| `st.navigation()` | Menu de navegacao declarativo (substituiria o roteador manual) |

### 8.2 Bibliotecas Externas Sugeridas

| Biblioteca | Beneficio |
|---|---|
| `streamlit-authenticator` | Autenticacao robusta com hash de senha, cookies seguros, recuperacao de senha |
| `st-gsheets-connection` | Conexao nativa do Streamlit com Sheets (ja em requirements mas nao usada) |
| `pydantic` | Validacao de dados de entrada (formularios, uploads) |
| `loguru` | Logging estruturado (substituiria o sistema manual de error_log) |
| `streamlit-option-menu` | Menu lateral estilizado para navegacao |
| `plotly` | Graficos interativos para dashboard (evolucao temporal, comparativos) |
| `streamlit-aggrid` | Tabela avancada com filtros, ordenacao, edicao inline |
| `python-dotenv` | Gerenciamento de ambiente local (ja ha .env mas nao e carregado) |
| `tenacity` | Retry com backoff para chamadas de API (Drive, Sheets) |
| `streamlit-camera-input-live` | Camera input com preview melhorado |

### 8.3 Arquitetura

| Melhoria | Beneficio |
|---|---|
| **Separar backend em API (FastAPI/Flask)** | Desacoplar logica de negocio do Streamlit; permitir cache server-side; rate limiting |
| **Usar PostgreSQL/SQLite** | Substituir Google Sheets como banco principal; queries mais rapidas; transacoes atomicas |
| **Redis para cache** | Cache de sessao e dados com TTL; reduzir chamadas ao Google Sheets |
| **Celery para tarefas async** | Upload de fotos e processamento de GPS em background |
| **Docker** | Ambiente reprodutivel; facil deploy |
| **GitHub Actions CI/CD** | Testes automaticos; deploy continuo |

---

## 9. RESUMO DAS ABAS/POR CARGO

### Colaborador (3 abas)
1. Missoes e Presenca — Check-in/out, missoes diarias, acoes de rede
2. Meus Contratos — Download e upload de contratos assinados
3. Ranking — Progresso pessoal e leaderboard

### Supervisor (4 abas)
1. Missoes e Presenca — Mesmo do colaborador
2. Meus Contratos — Mesmo do colaborador
3. Acompanhamento — Equipe, materiais, relatorios
4. Ranking — Progresso pessoal e leaderboard

### Admin (6 abas)
1. Equipes — Hierarquia de supervisores e voluntarios
2. Dashboard — Metricas, ticker, logs, exportacao Excel
3. Mapa — Mapa interativo com marcadores GPS
4. Mensagens — Criacao de diretrizes por grupo
5. Cadastro — Novo integrante, grupos e macro-grupos
6. Contratos — Envio e monitoramento de contratos

### Suporte (5 abas)
1. Diagnostico — Teste de conexoes
2. Logs de Erro — Erros da sessao
3. Todas as Acoes — (parcialmente implementado)
4. Simulador — (referenciado)
5. Sistema — (referenciado)

---

## 10. FLUXO DE DADOS

```
[Usuario] → [Streamlit App] → [Google Sheets API]
                ↓                    ↑
           [st.session_state]   [Leitura via CSV publico]
                ↓                    ↑
           [Google Drive API]   [Escrita via gspread]
                ↓
           [Nominatim/OSM]
                ↓
           [Geocodificacao reversa]
```

1. Usuario faz login → valida contra aba "Usuarios" (CSV publico)
2. Acao registrada → append_row na aba "Logs" (gspread)
3. Foto tirada → upload para Google Drive (API v3)
4. GPS capturado → geocodificacao via Nominatim → endereco salvo no log
5. Pontuacao calculada → append_row na aba "Leaderboard" (gspread)
6. Dashboard Admin → le dados de Logs + Usuarios → exibe metricas
7. Mapa → le coordenadas de Logs → renderiza marcadores via folium

---

## 11. CONCLUSAO

O COMANDO 2026 e um aplicativo funcional que resolve um problema real de gestao
de campanha politica com recursos limitados. A escolha de Google Sheets como
backend e pragmatica para o contexto (baixo custo, facil manutencao, sem
infraestrutura dedicada). O design neo-brutalista com cores ouro/vermelho e
identidade visual forte.

Os principais pontos de melhoria sao:
1. **Seguranca**: sanitizacao de inputs, validacao de uploads, revisao de permissoes
2. **Performance**: cache de conexoes, otimizacao de queries, fragmentacao de reruns
3. **Manutenibilidade**: extracao de duplicacoes, modularizacao, separacao backend/UI
4. **Escalabilidade**: migrar de Sheets para banco relacional quando o volume crescer
5. **UX**: usar mais componentes nativos do Streamlit, adicionar graficos e notificacoes
