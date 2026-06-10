# PLANO DE MELHORIAS — COMANDO 2026

Este arquivo organiza todas as melhorias sugeridas no `app.md` em **etapas sequenciais**.
Cada etapa e independente e pode ser implementada separadamente.
A ordem foi pensada para entregar valor rapido e reduzir risco.

---

## ETAPA 1 — LOGIN COM GOOGLE (OAuth)

**Prioridade: ALTA**
**Arquivos afetados:** `pages/00_Login.py`, `pages/01_Principal.py`, `.streamlit/secrets.toml`, `requirements.txt`

### O que mudar

Substituir o login atual (digitando e-mail e comparando com planilha) por autenticacao
Google OAuth. O usuario clica em "Entrar com Google" e o app verifica se o e-mail
esta cadastrado na planilha de Usuarios.

### Passo a passo

1. **Instalar dependencia**
   ```
   pip install google-auth-oauthlib
   ```
   Adicionar ao `requirements.txt`:
   ```
   google-auth-oauthlib>=1.0.0
   ```

2. **Configurar credenciais OAuth no Google Cloud Console**
   - Acessar https://console.cloud.google.com/apis/credentials
   - Criar credenciais "OAuth 2.0 Client ID" (tipo "Web application")
   - Adicionar URIs de redirecionamento:
     - `http://localhost:8501` (desenvolvimento local)
     - `https://<seu-app>.streamlit.app/` (producao)
   - Copiar `client_id` e `client_secret`

3. **Atualizar `.streamlit/secrets.toml`**
   Adicionar secao `[google_oauth]`:
   ```toml
   [google_oauth]
   client_id = "SEU_CLIENT_ID.apps.googleusercontent.com"
   client_secret = "SEU_CLIENT_SECRET"
   redirect_uri = "http://localhost:8501"
   ```

4. **Criar arquivo `utils/auth.py`** (novo arquivo)
   ```python
   import streamlit as st
   import google_auth_oauthlib.flow
   import google.oauth2.credentials
   import json

   SCOPES = [
       "openid",
       "https://www.googleapis.com/auth/userinfo.email",
       "https://www.googleapis.com/auth/userinfo.profile",
   ]

   def get_google_flow():
       """Cria o fluxo de autenticacao Google OAuth."""
       client_config = {
           "web": {
               "client_id": st.secrets["google_oauth"]["client_id"],
               "client_secret": st.secrets["google_oauth"]["client_secret"],
               "auth_uri": "https://accounts.google.com/o/oauth2/auth",
               "token_uri": "https://oauth2.googleapis.com/token",
               "redirect_uris": [st.secrets["google_oauth"]["redirect_uri"]],
           }
       }
       flow = google_auth_oauthlib.flow.Flow.from_client_config(
           client_config, scopes=SCOPES
       )
       flow.redirect_uri = st.secrets["google_oauth"]["redirect_uri"]
       return flow

   def login_google():
       """Renderiza botao de login e retorna credenciais ou None."""
       flow = get_google_flow()
       auth_url, _ = flow.authorization_url(prompt="consent")

       if st.button("ENTRAR COM GOOGLE", width="stretch", type="primary"):
           st.markdown(f'<meta http-equiv="refresh" content="0;url={auth_url}">',
                       unsafe_allow_html=True)

       # Verificar se voltou do Google com codigo de autorizacao
       query_params = st.query_params
       if "code" in query_params:
           code = query_params["code"]
           flow.fetch_token(code=code)
           credentials = flow.credentials
           return credentials
       return None

   def get_user_info(credentials):
       """Retorna email e nome do usuario autenticado."""
       from google.oauth2.credentials import Credentials
       from googleapiclient.discovery import build

       service = build("oauth2", "v2", credentials=credentials)
       user_info = service.userinfo().get().execute()
       return {
           "email": user_info.get("email", "").lower().strip(),
           "nome": user_info.get("name", ""),
           "foto": user_info.get("picture", ""),
       }
   ```

5. **Reescrever `pages/00_Login.py`**
   ```python
   import streamlit as st
   from utils.styles import inject_styles
   from utils.components import render_login_header, render_login_box
   from utils.auth import login_google, get_user_info
   from funcoes import carregar_dados

   st.set_page_config(page_title="COMANDO 2026 - Login", page_icon="", layout="centered")
   inject_styles()

   # Se ja logado, vai pro roteador
   if st.session_state.get("usuario_logado"):
       st.switch_page("pages/01_Principal.py")

   st.markdown("<br><br>", unsafe_allow_html=True)
   col_l1, col_l2, col_l3 = st.columns([1, 2, 1])

   with col_l2:
       render_login_header()
       with st.container():
           render_login_box()

           # Tentar login Google
           credentials = login_google()

           if credentials:
               with st.spinner("VALIDANDO..."):
                   user_info = get_user_info(credentials)
                   email = user_info["email"]

                   # Verificar se usuario existe na planilha
                   df_usuarios = carregar_dados(
                       "Usuarios",
                       st.secrets["planilha"]["id"],
                       st.session_state.get("error_log")
                   )

                   if df_usuarios is not None:
                       user_match = df_usuarios[
                           df_usuarios["ID_Usuario"].str.lower() == email
                       ]
                       if not user_match.empty:
                           st.session_state["usuario_logado"] = user_match.iloc[0].to_dict()
                           st.session_state["google_credentials"] = {
                               "token": credentials.token,
                               "refresh_token": credentials.refresh_token,
                               "token_uri": credentials.token_uri,
                               "client_id": credentials.client_id,
                               "client_secret": credentials.client_secret,
                           }
                           st.rerun()
                       else:
                           st.error("E-MAIL NAO CADASTRADO. Solicite acesso ao supervisor.")
                   else:
                       st.error("ERRO AO CARREGAR DADOS. Tente novamente.")
   ```

6. **Atualizar `pages/01_Principal.py`** — adicionar logout que limpa credenciais Google
   ```python
   # No logout, limpar tambem as credenciais Google
   if "google_credentials" in st.session_state:
       del st.session_state["google_credentials"]
   ```

7. **Atualizar logout em todas as paginas** — adicionar limpeza de `google_credentials`

### Resultado esperado
- Usuario clica "Entrar com Google" → redireciona para Google → volta autenticado
- E-mail validado automaticamente contra a planilha
- Nao precisa mais digitar e-mail manualmente
- Sessao mais segura (token OAuth em vez de cookie simples)

---

## ETAPA 2 — ELIMINAR DUPLICACAO DE CODIGO (Sidebar + Session State)

**Prioridade: ALTA**
**Arquivos afetados:** `pages/02_Colaborador.py`, `pages/03_Supervisor.py`, `pages/04_Admin.py`, `pages/05_Suporte.py`, `utils/components.py`

### O que mudar

Extrair o sidebar (com logout) e a inicializacao de session_state para funcoes
reutilizaveis. Hoje cada pagina repete ~40 linhas identicas.

### Passo a passo

1. **Criar funcao `init_session_state()` em `utils/components.py`**
   ```python
   def init_session_state():
       """Inicializa todas as variaveis de sessao necessarias."""
       defaults = {
           "usuario_logado": None,
           "error_log": [],
           "mensagem_exibida": False,
           "logout_em_andamento": False,
           "last_coords": "Aguardando...",
       }
       for key, value in defaults.items():
           if key not in st.session_state:
               st.session_state[key] = value
   ```

2. **Criar funcao `render_sidebar()` em `utils/components.py`**
   ```python
   def render_sidebar():
       """Renderiza sidebar com perfil e logout. Retorna True se logout acionado."""
       import extra_streamlit_components as stx
       from funcoes import get_agora_br
       import traceback

       cookie_manager = stx.CookieManager()
       u = st.session_state.get("usuario_logado", {})

       with st.sidebar:
           st.header("Perfil")
           if u:
               st.write(f"Ola, **{u.get('Nome', 'Usuario').split()[0]}**")
               st.caption(f"Cargo: {u.get('Cargo', '')}")

           if st.button("ATUALIZAR PAINEL", width="stretch"):
               with st.spinner("Buscando dados..."):
                   st.cache_data.clear()
                   st.rerun()

           if st.button("Sair / Trocar Conta", width="stretch"):
               # Limpar cookies
               try:
                   cookie_manager.delete("comando2026_user_id", key="del_user")
                   cookie_manager.delete("comando2026_checkin_time", key="del_check")
               except:
                   pass

               # Limpar sessao
               st.session_state.clear()
               st.cache_data.clear()
               st.switch_page("pages/00_Login.py")
   ```

3. **Simplificar cada pagina** — substituir ~40 linhas por:
   ```python
   from utils.components import init_session_state, render_sidebar

   init_session_state()
   render_sidebar()
   ```

4. **Remover duplicacao dos modais check-in/check-out**
   - Criar funcao `render_checkin_modal()` e `render_checkout_modal()` em `utils/components.py`
   - Importar em ambas as paginas (Colaborador e Supervisor) em vez de duplicar

### Resultado esperado
- ~160 linhas de codigo duplicado eliminadas
- Manutencao centralizada (mudar o sidebar = 1 arquivo)
- Menos bugs (correcao em um lugar aplica em todos)

---

## ETAPA 3 — SEGURANCA BASICA

**Prioridade: ALTA**
**Arquivos afetados:** `funcoes.py`, `pages/04_Admin.py`, `pages/02_Colaborador.py`, `pages/03_Supervisor.py`

### O que mudar

Adicionar sanitizacao de inputs, validacao de uploads e protecao contra XSS.

### Passo a passo

1. **Criar funcao de sanitizacao em `funcoes.py`**
   ```python
   import html
   import re

   def sanitize_text(text):
       """Remove HTML tags e scripts de texto livre."""
       if not text or not isinstance(text, str):
           return ""
       # Escapa entidades HTML
       text = html.escape(text)
       # Remove tags HTML restantes
       text = re.sub(r"<[^>]+>", "", text)
       return text.strip()

   def validate_pdf_upload(uploaded_file):
       """Valida se o arquivo e realmente um PDF."""
       if uploaded_file is None:
           return False
       # Verificar MIME type
       if uploaded_file.type != "application/pdf":
           return False
       # Verificar extensao
       if not uploaded_file.name.lower().endswith(".pdf"):
           return False
       # Verificar tamanho maximo (10MB)
       if uploaded_file.size > 10 * 1024 * 1024:
           return False
       # Verificar magic bytes (%PDF)
       header = uploaded_file.read(4)
       uploaded_file.seek(0)
       if header != b"%PDF":
           return False
       return True
   ```

2. **Aplicar sanitizacao em todos os `st.text_input` e `st.text_area`**
   - Mensagens do Admin (ID do grupo, mensagem, missao)
   - Observacoes do check-out
   - Nomes no cadastro
   - Feedback nas acoes

3. **Aplicar validacao de PDF nos uploads**
   - Contrato assinado (Colaborador e Supervisor)
   - Envio de contrato (Admin)
   ```python
   if arq:
       if not validate_pdf_upload(arq):
           st.error("Arquivo invalido. Envie apenas PDFs de ate 10MB.")
           return
   ```

4. **Atualizar `.gitignore`** — garantir que `.env` e `.streamlit/secrets.toml` estao listados

5. **Adicionar meta tag de seguranca no CSS** (em `styles.py`)
   ```css
   # Adicionar no inject_styles():
   st.markdown('<meta http-equiv="X-Content-Type-Options" content="nosniff">',
               unsafe_allow_html=True)
   ```

### Resultado esperado
- Inputs sanitizados contra XSS
- Uploads validados (magic bytes, MIME, tamanho)
- Credenciais protegidas no git

---

## ETAPA 4 — CACHE DE CONEXOES GOOGLE

**Prioridade: MEDIA**
**Arquivos afetados:** `funcoes.py`

### O que mudar

As funcoes `_get_gspread_client()` e `_get_drive_credentials()` sao chamadas
repetidamente e recriam a conexao a cada vez. Usar `st.cache_resource` para
manter conexoes vivas durante a sessao.

### Passo a passo

1. **Substituir `_get_gspread_client` por versao cacheada**
   ```python
   @st.cache_resource(ttl=3600)
   def _get_gspread_client_cached(secrets_json):
       """Retorna cliente gspread cacheado por 1 hora."""
       import json
       creds_dict = json.loads(secrets_json) if isinstance(secrets_json, str) else secrets_json
       scope = [
           "https://www.googleapis.com/auth/spreadsheets",
           "https://www.googleapis.com/auth/drive"
       ]
       creds = ServiceAccountCredentials.from_service_account_info(creds_dict, scopes=scope)
       return gspread.authorize(creds)

   def _get_gspread_client(secrets, error_log=None):
       """Wrapper que usa cache."""
       try:
           creds_dict = secrets.get("connections", {}).get("gsheets")
           import json
           return _get_gspread_client_cached(json.dumps(creds_dict))
       except Exception as e:
           if error_log is not None:
               error_log.append({...})
           return None
   ```

2. **Substituir `_get_drive_credentials` por versao cacheada**
   ```python
   @st.cache_resource(ttl=3600)
   def _get_drive_credentials_cached(creds_json):
       """Retorna credenciais Drive cacheadas por 1 hora."""
       import json
       creds_info = json.loads(creds_json) if isinstance(creds_json, str) else creds_info
       creds = OAuthCredentials(
           token=None,
           refresh_token=creds_info["refresh_token"],
           token_uri=creds_info["token_uri"],
           client_id=creds_info["client_id"],
           client_secret=creds_info["client_secret"]
       )
       if creds.expired and creds.refresh_token:
           creds.refresh(Request())
       return creds

   def _get_drive_credentials(secrets, error_log=None):
       """Wrapper que usa cache."""
       try:
           import json
           creds_info = secrets["google_drive"]
           return _get_drive_credentials_cached(json.dumps(creds_info))
       except Exception as e:
           if error_log is not None:
               error_log.append({...})
           return None
   ```

3. **Atualizar `diagnosticar_conexoes()`** — reutilizar conexoes cacheadas em vez de criar novas

### Resultado esperado
- Conexoes Google reutilizadas durante a sessao
- Menos chamadas de API (reduz rate limiting)
- Resposta mais rapida nas operacoes de leitura/escrita

---

## ETAPA 5 — CORRIGIR BUGS CRITICOS

**Prioridade: ALTA**
**Arquivos afetados:** `pages/04_Admin.py`, `utils/components.py`, `pages/02_Colaborador.py`

### O que mudar

Corrigir bugs que podem causar erros em producao.

### Passo a passo

1. **Admin.py — codigo-morta no logout (linhas 126-146)**
   - Remover bloco duplicado de `cookie_manager.delete` e `st.session_state.clear()`
   - Manter apenas o primeiro bloco (linhas 111-126)

2. **Admin.py — extracao de coordenadas no mapa (linha 348)**
   ```python
   # ANTES (quebra com "Sem GPS"):
   df_m_filtrado['lat'], df_m_filtrado['lon'] = zip(*df_m_filtrado['Localização'].apply(
       lambda pos: (float(pos.split(",")[0]), float(pos.split(",")[1]))
       if isinstance(pos, str) and "," in pos else (None, None)
   ))

   # DEPOIS (valida antes de extrair):
   def extrair_coords(pos):
       if not isinstance(pos, str) or "," not in pos:
           return None, None
       try:
           lat, lon = pos.split(",")
           lat, lon = float(lat.strip()), float(lon.strip())
           if -35 < lat < 5 and -75 < lon < -35:  # faixa do Brasil
               return lat, lon
       except (ValueError, IndexError):
           pass
       return None, None

   df_m_filtrado['lat'], df_m_filtrado['lon'] = zip(
       *df_m_filtrado['Localização'].apply(extrair_coords)
   )
   ```

3. **components.py — `st.space()` pode nao existir**
   ```python
   # ANTES:
   st.space("small")

   # DEPOIS (compativel com todas as versoes):
   st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
   ```

4. **components.py — `render_action_link_button` inconsistente**
   - Substituir por `st.link_button` nativo do Streamlit
   - Ou manter HTML mas com CSS class consistente com o tema

5. **Colaborador/Supervisor — `render_material_form` key fixo**
   - Adicionar parametro `key_suffix` para gerar keys unicas
   ```python
   def render_material_form(secrets, key_suffix=""):
       with st.form(key=f"form_material_grupo{key_suffix}", clear_on_submit=True):
           ...
   ```

6. **funcoes.py — `carregar_dados` cria cliente gspread inutilmente**
   - Remover chamada de `_get_gspread_client()` dentro de `carregar_dados()`
   - A funcao so le via CSV publico, nao precisa de gspread

### Resultado esperado
- Mapa nao quebra com coordenadas invalidas
- Logout do Admin funciona corretamente
- Sem AttributeError em versoes antigas do Streamlit
- Formularios com keys unicas

---

## ETAPA 6 — MELHORAR PERFORMANCE DO LEADERBOARD

**Prioridade: MEDIA**
**Arquivos afetados:** `funcoes.py`, `pages/02_Colaborador.py`, `pages/03_Supervisor.py`

### O que mudar

O Leaderboard e append-only (cada acao = nova linha). Isso infla a planilha.
Mudar para modelo que atualiza o total do usuario em vez de criar linha nova.

### Passo a passo

1. **Criar funcao `atualizar_pontuacao_v2()` em `funcoes.py`**
   ```python
   def atualizar_pontuacao_v2(id_usuario, nome, cargo, acao, planilha_id, secrets, error_log=None):
       """
       Versao otimizada: atualiza a linha existente do usuario em vez de
       criar linha nova. So cria linha se for a primeira acao do usuario.
       """
       from utils.gamification import PONTUACAO, LIMITE_DIARIO

       try:
           ws = _ws_leaderboard(planilha_id, secrets, error_log)
           registros = ws.get_all_records()

           # Encontrar a linha mais recente do usuario
           linhas_usuario = [
               (i, r) for i, r in enumerate(registros, start=2)
               if str(r.get('id_usuario')) == str(id_usuario)
           ]

           hoje_str = get_agora_br().strftime("%d/%m/%Y")

           if not linhas_usuario:
               # Primeira acao do usuario — criar linha
               ganho = PONTUACAO.get(acao, 0)
               ws.append_row([
                   str(id_usuario), str(nome), str(cargo),
                   ganho,  # pontos_total
                   get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                   1,  # pontos_dia
                   hoje_str,
                   acao,
                   ganho
               ])
               return True

           # Usuario ja existe — atualizar ultima linha
           ultima_linha_idx, ultima_linha = linhas_usuario[-1]

           total_atual = int(ultima_linha.get('pontos_total', 0) or 0)

           # Verificar limite diario
           acoes_hoje_acao = [
               r for _, r in linhas_usuario
               if r.get('data_dia') == hoje_str and r.get('tipo_acao') == acao
           ]
           limite = LIMITE_DIARIO.get(acao)
           limite_atingido = (limite is not None and len(acoes_hoje_acao) >= limite)
           ganho = 0 if limite_atingido else PONTUACAO.get(acao, 0)

           novo_total = total_atual + ganho

           # Atualizar celulas da ultima linha
           cabecalho = ws.row_values(1)
           col_total = cabecalho.index('pontos_total') + 1
           col_ultima = cabecalho.index('ultima_atualizacao') + 1

           ws.update_cell(ultima_linha_idx, col_total, novo_total)
           ws.update_cell(ultima_linha_idx, col_ultima,
                          get_agora_br().strftime("%d/%m/%Y %H:%M:%S"))

           # Registrar acao detalhada (opcional — pode ser desativado para economizar)
           ws.append_row([
               str(id_usuario), str(nome), str(cargo),
               novo_total,
               get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
               len(acoes_hoje_acao) + (1 if ganho > 0 else 0),
               hoje_str, acao, ganho
           ])

           return True
       except Exception as e:
           if error_log is not None:
               error_log.append({...})
           return False
   ```

2. **Adicionar cache ao carregar Leaderboard**
   ```python
   @st.cache_data(ttl=60)  # cache de 1 minuto para ranking
   def carregar_leaderboard_cached(planilha_id):
       return carregar_dados("Leaderboard", planilha_id)
   ```

3. **Atualizar paginas para usar `carregar_leaderboard_cached`**

### Resultado esperado
- Planilha Leaderboard cresce mais devagar
- Ranking calculado mais rapido (menos linhas para processar)
- Cache reduz chamadas ao Google Sheets

---

## ETAPA 7 — MELHORAR UX COM COMPONENTES NATIVOS

**Prioridade: MEDIA**
**Arquivos afetados:** `utils/components.py`, `pages/04_Admin.py`, `pages/02_Colaborador.py`

### O que mudar

Substituir HTML custom por componentes nativos do Streamlit para melhorar
acessibilidade, consistencia e manutencao.

### Passo a passo

1. **Substituir `render_action_link_button` por `st.link_button`**
   ```python
   # ANTES (HTML custom):
   def render_action_link_button(texto, url):
       st.markdown(f'<a href="{url}" target="_blank"><div class="action-link-btn">{texto}</div></a>',
                   unsafe_allow_html=True)

   # DEPOIS (nativo):
   def render_action_link_button(texto, url):
       st.link_button(texto, url, width="stretch")
   ```

2. **Adicionar `st.toast()` para feedback nao-intrusivo**
   ```python
   # Em vez de st.success() + time.sleep(2) + st.rerun():
   st.toast("Acao registrada com sucesso!", icon="")
   time.sleep(1)
   st.rerun()
   ```

3. **Adicionar `st.progress()` nativo nos modais de check-in/check-out**
   ```python
   # Em vez de st.spinner():
   progress = st.progress(0, text="Processando...")
   progress.progress(30, text="Enviando foto...")
   # ... upload ...
   progress.progress(70, text="Registrando acao...")
   # ... registro ...
   progress.progress(100, text="Concluido!")
   ```

4. **Adicionar `st.metric()` no Dashboard Admin para mais contexto**
   ```python
   # Adicionar delta (comparacao com ontem):
   c1.metric("Acoes Totais", total_acoes, delta=acoes_hoje)
   c2.metric("Colaboradores Ativos", usuarios_ativos, delta=ativos_hoje - ativos_ontem)
   ```

5. **Usar `st.toggle()` para filtros booleanos no Admin**
   ```python
   # Em vez de selectbox com "Sim"/"Nao":
   mostrar_inativos = st.toggle("Mostrar usuarios inativos", value=False)
   ```

6. **Adicionar `st.skeleton()` ou `st.spinner()` durante carregamento de dados**
   ```python
   with st.spinner("Carregando dados da planilha..."):
       df = carregar_dados("Usuarios", planilha_id, error_log)
   ```

### Resultado esperado
- Interface mais consistente e acessivel
- Feedback visual mais rico (toasts, progress bars)
- Menos CSS custom para manter

---

## ETAPA 8 — DASHBOARD ADMIN MELHORADO

**Prioridade: MEDIA**
**Arquivos afetados:** `pages/04_Admin.py`

### O que mudar

Adicionar graficos e metricas mais ricas ao dashboard administrativo.

### Passo a passo

1. **Adicionar grafico de evolucao de acoes (st.line_chart)**
   ```python
   with st.expander("Evolucao de Acoes (ultimos 7 dias)"):
       df_logs['data'] = df_logs['Data_Hora'].str.split().str[0]
       acoes_por_dia = df_logs.groupby('data').size().reset_index(name='acoes')
       acoes_por_dia = acoes_por_dia.sort_values('data').tail(7)
       st.line_chart(acoes_por_dia.set_index('data'))
   ```

2. **Adicionar grafico de acoes por tipo (st.bar_chart)**
   ```python
   with st.expander("Acoes por Tipo"):
       df_logs['tipo_curto'] = df_logs['Tipo_Acao'].str.split('|').str[0].str.strip()
       acoes_tipo = df_logs['tipo_curto'].value_counts()
       st.bar_chart(acoes_tipo)
   ```

3. **Adicionar grafico de colaboradores por Macro_Grupo**
   ```python
   with st.expander("Distribuicao por Macro Regiao"):
       if 'Macro_Grupo' in df_gerencial.columns:
           dist_macro = df_gerencial.groupby('Macro_Grupo').size()
           st.bar_chart(dist_macro)
   ```

4. **Adicionar filtro de periodo no Dashboard**
   ```python
   col_f1, col_f2 = st.columns(2)
   with col_f1:
       data_inicio = st.date_input("Data inicio", value=agora_br - timedelta(days=7))
   with col_f2:
       data_fim = st.date_input("Data fim", value=agora_br)
   ```

5. **Adicionar tabela interativa com st.dataframe + configuracao de colunas**
   ```python
   st.dataframe(
       df_logs.tail(50),
       column_config={
           "Data_Hora": st.column_config.DatetimeColumn("Data/Hora"),
           "ID_Usuario": st.column_config.TextColumn("Usuario"),
           "Tipo_Acao": st.column_config.TextColumn("Acao"),
           "Localizacao": st.column_config.TextColumn("GPS"),
       },
       hide_index=True,
       width="stretch"
   )
   ```

### Resultado esperado
- Dashboard com visao temporal (evolucao, tendencias)
- Filtros por periodo
- Tabela mais legivel com tipos de coluna corretos

---

## ETAPA 9 — MAPA MELHORADO

**Prioridade: BAIXA**
**Arquivos afetados:** `pages/04_Admin.py`

### O que mudar

O mapa atual usa folium que e pesado. Melhorar performance e adicionar recursos.

### Passo a passo

1. **Adicionar agrupamento de marcadores (MarkerCluster)**
   ```python
   from folium.plugins import MarkerCluster

   mapa = folium.Map(location=[df_geo['lat'].mean(), df_geo['lon'].mean()], zoom_start=12)
   marker_cluster = MarkerCluster().add_to(mapa)

   for _, row in df_geo.iterrows():
       nome_exib = row['Nome'] if pd.notna(row['Nome']) else row['ID_Usuario']
       folium.Marker(
           [row['lat'], row['lon']],
           popup=f"{nome_exib} - {row['Tipo_Acao']}"
       ).add_to(marker_cluster)
   ```

2. **Adicionar heatmap de atividade**
   ```python
   from folium.plugins import HeatMap

   with st.expander("Mapa de Calor"):
       heat_data = df_geo[['lat', 'lon']].values.tolist()
       mapa_heat = folium.Map(location=[df_geo['lat'].mean(), df_geo['lon'].mean()], zoom_start=11)
       HeatMap(heat_data).add_to(mapa_heat)
       st_folium(mapa_heat, width=1200, height=600)
   ```

3. **Adicionar filtro por tipo de acao no mapa**
   ```python
   tipos_acao = df_m_filtrado['Tipo_Acao'].str.split('|').str[0].str.strip().unique()
   tipo_mapa = st.selectbox("Filtrar por tipo de acao:", ["Todos"] + list(tipos_acao))
   if tipo_mapa != "Todos":
       df_geo = df_geo[df_geo['Tipo_Acao'].str.contains(tipo_mapa)]
   ```

### Resultado esperado
- Mapa mais performatico com muitos marcadores
- Heatmap para visualizar concentracao de atividades
- Filtro por tipo de acao

---

## ETAPA 10 — REQUIREMENTS.TXT LIMPO

**Prioridade: BAIXA**
**Arquivos afetados:** `requirements.txt`

### O que mudar

Limpar dependencias duplicadas e nao utilizadas.

### Passo a passo

1. **Substituir `requirements.txt` por:**
   ```
   streamlit>=1.28.0
   pandas>=2.0.0
   gspread>=5.10.0
   google-auth>=2.22.0
   google-auth-oauthlib>=1.0.0
   google-auth-httplib2>=0.1.1
   google-api-python-client>=2.95.0
   extra-streamlit-components>=0.1.60
   streamlit-js-eval>=0.1.5
   xlsxwriter>=3.1.0
   geopy>=2.3.0
   folium>=0.14.0
   streamlit-folium>=0.15.0
   ```

2. **Remover duplicatas:** `gspread` aparecia 2x
3. **Remover nao-utilizados:** `oauth2client` (nao e importado em lugar nenhum)
4. **Adicionar versoes minimas** para evitar conflitos

### Resultado esperado
- Instalacao mais rapida e confiavel
- Sem conflitos de dependencias
- Todas as versoes pinadas

---

## ORDEM RECOMENDADA DE IMPLEMENTACAO

| Ordem | Etapa | Prioridade | Tempo estimado |
|-------|-------|------------|----------------|
| 1 | Etapa 1 — Login Google | ALTA | 2-3 horas |
| 2 | Etapa 5 — Corrigir bugs criticos | ALTA | 1-2 horas |
| 3 | Etapa 3 — Seguranca basica | ALTA | 1-2 horas |
| 4 | Etapa 2 — Eliminar duplicacao | ALTA | 2-3 horas |
| 5 | Etapa 4 — Cache de conexoes | MEDIA | 1 hora |
| 6 | Etapa 6 — Performance Leaderboard | MEDIA | 2 horas |
| 7 | Etapa 7 — UX com nativos | MEDIA | 2 horas |
| 8 | Etapa 8 — Dashboard melhorado | MEDIA | 2 horas |
| 9 | Etapa 9 — Mapa melhorado | BAIXA | 1-2 horas |
| 10 | Etapa 10 — Requirements limpo | BAIXA | 30 min |

**Total estimado: 15-20 horas de trabalho**

---

## NOTAS IMPORTANTES

- **Sempre testar em ambiente local antes de subir para producao**
- **Fazer backup da planilha Google Sheets antes de mudar a estrutura do Leaderboard**
- **A Etapa 1 (Login Google) requer configuracao no Google Cloud Console — fazer primeiro**
- **As Etapas 2, 3, 5 podem ser feitas em qualquer ordem (sao independentes)**
- **A Etapa 6 requer migracao de dados do Leaderboard — fazer com cuidado**
- **Commitar a cada etapa concluida para facilitar rollback se necessario**
