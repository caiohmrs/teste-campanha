# =============================================================================
# UTILS.PY - FUNÇÕES UTILITÁRIAS E CONEXÕES (SEM UI STREAMLIT)
# =============================================================================

from datetime import datetime, timezone, timedelta
import gspread
import io
import pandas as pd
import requests
from geopy.geocoders import Nominatim
import streamlit as st
import traceback

# Gamificação – dicionários de pontos e limites diários
from utils.gamification import PONTUACAO, LIMITE_DIARIO

# Google Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google.oauth2.credentials import Credentials as OAuthCredentials
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.discovery import build

# =============================================================================
# CONFIGURAÇÕES GLOBAIS
# =============================================================================

TIMEZONE_OFFSET = -3  # Horário de Brasília


# =============================================================================
# FUNÇÕES DE TEMPO
# =============================================================================

def get_agora_br():
    """Retorna o horário atual em Brasília (UTC-3), convertido de forma consistente a partir do horário UTC.
    
    Returns:
        datetime: Objeto datetime representando o horário atual em Brasília.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=TIMEZONE_OFFSET)


# =============================================================================
# FUNÇÕES DE VALIDAÇÃO
# =============================================================================

def validar_gps_basico(coords_str):
    """Verifica se uma string de coordenadas (lat,lon) parece válida, verificando se está dentro das faixas geográficas do Brasil.
    
    Args:
        coords_str (str): Coordenadas no formato 'lat,lon' ou string similar.
    
    Returns:
        bool: True se as coordenadas estiverem dentro da faixa do Brasil, False caso contrário ou se a entrada for inválida.
    """
    if not coords_str or coords_str in ["Sem GPS", "Não informada", "Erro GPS", "Aguardando...",
                                        "GPS Inválido/Desativado"]:
        return False
    try:
        if "," in str(coords_str):
            lat, lon = map(float, str(coords_str).split(','))
            return -35 < lat < 5 and -75 < lon < -35
    except:
        pass
    return False


def sanitize_whatsapp(v):
    """Limpa e formata um número de telefone para o padrão brasileiro (55 + DDD + 9 dígitos).
    
    Args:
        v (str, int, None): O número de telefone original, que pode conter formatações, espaços ou caracteres não numéricos.
    
    Returns:
        str: O número formatado no padrão 55XXXXXXXXXXX, ou uma string vazia se o número for inválido.
    """
    if v is None or str(v).lower() in ["nan", "none", ""]:
        return ""

    s = str(v).strip().split('.')[0]
    nums = "".join(filter(str.isdigit, s))

    if nums.startswith("55") and len(nums) >= 12:
        core = nums[2:]
    else:
        core = nums

    if core.startswith("0"):
        core = core[1:]

    if len(core) == 10:
        core = core[:2] + "9" + core[2:]

    if len(core) == 11:
        return "55" + core

    return nums if len(nums) >= 10 else ""


# =============================================================================
# FUNÇÕES DE GOOGLE - CREDENCIAIS
# =============================================================================

def _get_drive_credentials(secrets, error_log=None):
    """Obtém e valida as credenciais do Google Drive usando OAuth (Refresh Token).
    
    Args:
        secrets (dict): Dicionário contendo as credenciais do Google, incluindo 'refresh_token', 'token_uri', 'client_id' e 'client_secret'.
        error_log (list, optional): Lista para registro de erros. Se fornecida, erros serão adicionados a ela.
    
    Returns:
        google.oauth2.credentials.Credentials: Objeto de credenciais válido, ou None se houver falha.
    """
    try:
        creds_info = secrets["google_drive"]
        creds = OAuthCredentials(
            token=None,
            refresh_token=creds_info["refresh_token"],
            token_uri=creds_info["token_uri"],
            client_id=creds_info["client_id"],
            client_secret=creds_info["client_secret"]
        )
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
        return creds
    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': '_get_drive_credentials',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        print(f"Erro ao carregar credenciais do Drive: {e}")
        return None


def _get_sheets_credentials(secrets, error_log=None):
    """Obtém as credenciais do Google Sheets usando Service Account.
    
    Args:
        secrets (dict): Dicionário contendo as credenciais do Google, incluindo a seção 'connections.gsheets'.
        error_log (list, optional): Lista para registro de erros. Se fornecida, erros serão adicionados a ela.
    
    Returns:
        google.oauth2.service_account.Credentials: Objeto de credenciais válido, ou None se houver falha.
    """
    try:
        creds_dict = secrets.get("connections", {}).get("gsheets")
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        return ServiceAccountCredentials.from_service_account_info(creds_dict, scopes=scope)
    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': '_get_sheets_credentials',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        print(f"Erro credenciais Sheets: {e}")
        return None


def _get_gspread_client(secrets, error_log=None):
    """Inicializa e autoriza um cliente gspread para interagir com o Google Sheets.
    
    Args:
        secrets (dict): Dicionário contendo as credenciais do Google.
        error_log (list, optional): Lista para registro de erros. Se fornecida, erros serão adicionados a ela.
    
    Returns:
        gspread.client.Client: Cliente gspread autorizado, ou None se houver falha na autenticação.
    """
    try:
        creds = _get_sheets_credentials(secrets, error_log)
        return gspread.authorize(creds) if creds else None
    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': '_gspread_client',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        print(f"Erro ao inicializar gspread: {e}")
        return None


# =============================================================================
# FUNÇÕES DE GOOGLE SHEETS - DADOS
# =============================================================================

def carregar_dados(nome_aba, planilha_id, error_log=None):
    """Carrega os dados de uma aba específica da planilha do Google Sheets como um DataFrame do Pandas.
    
    Args:
        nome_aba (str): Nome da aba da planilha a ser carregada.
        planilha_id (str): ID da planilha no Google Drive.
        error_log (list, optional): Lista para registro de erros. Se fornecida, erros serão adicionados a ela.
    
    Returns:
        pandas.DataFrame: DataFrame com os dados da aba, ou None se houver falha.
    """
    try:
        url = f"https://docs.google.com/spreadsheets/d/{planilha_id}/gviz/tq?tqx=out:csv&sheet={nome_aba}"
        df = pd.read_csv(url)
        return df.astype(str).apply(lambda x: x.str.strip())
    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': 'carregar_dados',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        print(f"Erro ao carregar dados: {e}")
        return None


def registrar_acao(id_usuario, tipo_acao, localizacao, feedback, secrets, error_log=None):
    """Registra uma ação do usuário na planilha de Logs, incluindo geocodificação do endereço se o GPS for válido.
    
    Args:
        id_usuario (str): ID único do usuário que realizou a ação.
        tipo_acao (str): Descrição do tipo de ação (ex: 'Check‑in', 'CONCLUIU: MISSÃO').
        localizacao (str): Coordenadas GPS no formato 'lat,lon' ou string indicando ausência de GPS.
        feedback (str): Texto de feedback ou observação do usuário.
        secrets (dict): Dicionário com as credenciais do Google.
        error_log (list, optional): Lista para registro de erros. Se fornecida, erros serão adicionados a ela.
    
    Returns:
        bool: True se o registro foi bem-sucedido, False caso contrário.
    """
    try:
        loc_safe = str(localizacao) if localizacao is not None else "Não informada"
        gps_valido = validar_gps_basico(loc_safe)
        if not gps_valido:
            loc_safe = "GPS Inválido/Desativado"

        client = _get_gspread_client(secrets, error_log)
        if client is None:
            return False

        planilha = client.open_by_key(secrets["planilha"]["id"])
        aba = planilha.worksheet("Logs")
        agora_br = get_agora_br()

        endereco = "Sem GPS"
        if gps_valido:
            endereco = obter_endereco_simples(loc_safe, error_log)

        aba.append_row([
            agora_br.strftime("%Y%m%d%H%M%S"),
            str(id_usuario),
            str(tipo_acao),
            agora_br.strftime("%d/%m/%Y %H:%M:%S"),
            loc_safe,
            str(endereco),
            str(feedback)
        ])

        # Normalização da ação para pontuação
        acao_normalizada = None
        a = tipo_acao.lower()
        if "check-in" in a:
            acao_normalizada = "checkin"
        elif "check-out" in a:
            acao_normalizada = "checkout"
        elif "concluiu" in a or "missão" in a:
            acao_normalizada = "missao"
        elif "ação:" in a and "instagram" in a:
            acao_normalizada = "insta_engage"
        elif "ação:" in a and "whatsapp" in a:
            acao_normalizada = "whatsapp"
        elif "talk_team" in a:
            acao_normalizada = "talk_team"

        if acao_normalizada:
            u = st.session_state.get("usuario_logado", {})
            nome = u.get("Nome", "Usuario")
            cargo = u.get("Cargo", "").lower()

            atualizar_pontuacao_usuario(
                id_usuario=id_usuario,
                nome=nome,
                cargo=cargo,
                acao=acao_normalizada,
                planilha_id=secrets["planilha"]["id"],
                secrets=secrets,
                error_log=error_log
            )

        return True

    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': 'registrar_acao',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        print(f"Erro ao registrar ação: {e}")
        return False


def registrar_novo_contrato_admin(id_usuario, nome_arquivo, link_original, secrets, error_log=None):
    """Adiciona uma nova linha na planilha de Contratos, registrando um novo documento enviado pelo Admin.
    
    Args:
        id_usuario (str): ID do usuário para o qual o contrato foi criado.
        nome_arquivo (str): Nome do arquivo do contrato.
        link_original (str): Link do Google Drive onde o arquivo original está armazenado.
        secrets (dict): Dicionário com as credenciais do Google.
        error_log (list, optional): Lista para registro de erros. Se fornecida, erros serão adicionados a ela.
    
    Returns:
        bool: True se o registro foi bem-sucedido, False caso contrário.
    """
    try:
        client = _get_gspread_client(secrets, error_log)
        if client is None:
            return False

        planilha = client.open_by_key(secrets["planilha"]["id"])
        aba = planilha.worksheet("Contratos")

        aba.append_row([
            str(id_usuario),
            str(nome_arquivo),
            str(link_original),
            "Aguardando Assinatura",
            ""
        ])
        return True
    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': 'registrar_novo_contrato_admin',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        print(f"Erro ao registrar contrato: {e}")
        return False


def atualizar_contrato_enviado(id_usuario, nome_arquivo, link_drive, secrets, error_log=None):
    """Atualiza o status e o link do contrato assinado na planilha de Contratos, localizando a linha correspondente.
    
    Args:
        id_usuario (str): ID do usuário associado ao contrato.
        nome_arquivo (str): Nome do arquivo do contrato.
        link_drive (str): Link do Google Drive onde o contrato assinado está armazenado.
        secrets (dict): Dicionário com as credenciais do Google.
        error_log (list, optional): Lista para registro de erros. Se fornecida, erros serão adicionados a ela.
    
    Returns:
        bool: True se a atualização foi bem-sucedida, False caso contrário.
    """
    try:
        client = _get_gspread_client(secrets, error_log)
        if client is None:
            return False

        planilha = client.open_by_key(secrets["planilha"]["id"])
        aba = planilha.worksheet("Contratos")
        dados = aba.get_all_records()
        linha_para_atualizar = None

        for i, linha in enumerate(dados, start=2):
            if str(linha.get('ID_Usuario')) == str(id_usuario) and \
                    str(linha.get('Nome_Arquivo')) == str(nome_arquivo):
                linha_para_atualizar = i
                break

        if linha_para_atualizar:
            cabecalho = aba.row_values(1)

            if 'Link_Assinado' in cabecalho:
                col_link = cabecalho.index('Link_Assinado') + 1
                aba.update_cell(linha_para_atualizar, col_link, link_drive)

            if 'Status' in cabecalho:
                col_status = cabecalho.index('Status') + 1
                aba.update_cell(linha_para_atualizar, col_status, "Assinado / Em Análise")

            return True
        return False
    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': 'atualizar_contrato_enviado',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        print(f"Falha ao atualizar contrato: {e}")
        return False


# =============================================================================
# FUNÇÕES DE GOOGLE DRIVE - UPLOAD
# =============================================================================

def salvar_foto_drive(foto_arquivo, nome_arquivo, secrets, error_log=None):
    """Salva uma foto (objeto BytesIO) no Google Drive e define permissão de leitura pública.
    
    Args:
        foto_arquivo (io.BytesIO): Objeto em memória contendo os dados da imagem JPEG.
        nome_arquivo (str): Nome que será dado ao arquivo no Drive.
        secrets (dict): Dicionário com as credenciais do Google e o ID da pasta de fotos.
        error_log (list, optional): Lista para registro de erros. Se fornecida, erros serão adicionados a ela.
    
    Returns:
        str: Link de visualização (webViewLink) da foto no Google Drive, ou None se houver falha.
    """
    try:
        creds = _get_drive_credentials(secrets, error_log)
        if not creds:
            return None

        drive_service = build('drive', 'v3', credentials=creds)
        id_pasta_fotos = secrets["google_drive"]["id_pasta_fotos"]

        file_metadata = {'name': nome_arquivo, 'parents': [id_pasta_fotos]}
        foto_bytes = io.BytesIO(foto_arquivo.getvalue())
        media = MediaIoBaseUpload(foto_bytes, mimetype='image/jpeg', resumable=False)

        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        drive_service.permissions().create(
            fileId=file.get('id'),
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()

        return file.get('webViewLink')
    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': 'salvar_foto_drive',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        print(f"Erro no Drive (Foto): {e}")
        return None


def salvar_documento_drive(doc_arquivo, nome_arquivo, secrets, error_log=None):
    """Salva um documento PDF (objeto BytesIO) no Google Drive e define permissão de leitura pública.
    
    Args:
        doc_arquivo (io.BytesIO): Objeto em memória contendo os dados do documento PDF.
        nome_arquivo (str): Nome que será dado ao arquivo no Drive.
        secrets (dict): Dicionário com as credenciais do Google e o ID da pasta de contratos.
        error_log (list, optional): Lista para registro de erros. Se fornecida, erros serão adicionados a ela.
    
    Returns:
        str: Link de visualização (webViewLink) do documento no Google Drive, ou None se houver falha.
    """
    try:
        creds = _get_drive_credentials(secrets, error_log)
        if not creds:
            return None

        drive_service = build('drive', 'v3', credentials=creds)
        id_pasta_contratos = secrets["google_drive"]["id_pasta_contratos"]

        file_metadata = {'name': nome_arquivo, 'parents': [id_pasta_contratos]}
        doc_bytes = io.BytesIO(doc_arquivo.getvalue())
        media = MediaIoBaseUpload(doc_bytes, mimetype='application/pdf', resumable=False)

        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        drive_service.permissions().create(
            fileId=file.get('id'),
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()

        return file.get('webViewLink')
    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': 'salvar_documento_drive',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        print(f"Erro no Drive (Docs): {e}")
        return None


# =============================================================================
# FUNÇÕES DE API EXTERNA
# =============================================================================

def obter_endereco_simples(coords_str, error_log=None):
    """Converte coordenadas GPS (lat,lon) em um endereço simplificado (rua ou bairro) usando a API Nominatim (OpenStreetMap).
    
    Args:
        coords_str (str): Coordenadas no formato 'lat,lon'.
        error_log (list, optional): Lista para registro de erros. Se fornecida, erros serão adicionados a ela.
    
    Returns:
        str: Endereço simplificado (ex: 'Rua X, Bairro Y') ou uma mensagem de erro se a geocodificação falhar.
    """
    c_str = str(coords_str) if coords_str is not None else ""

    if not c_str or "GPS" in c_str or "informada" in c_str or "," not in c_str:
        return "Local não identificado"

    try:
        geolocator = Nominatim(user_agent="comando2026_geocoder")
        location = geolocator.reverse(c_str, timeout=10)
        address = location.raw.get('address', {})

        rua = address.get('road', '')
        bairro = address.get('suburb', '')
        cidade = address.get('city', address.get('town', ''))

        if rua:
            return f"{rua}, {bairro}".strip(", ")
        return f"{bairro}, {cidade}".strip(", ")
    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': 'obter_endereco_simples',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        print(f"Erro ao obter endereço: {e}")
        return "Endereço indisponível"


# =============================================================================
# FUNÇÕES DE GESTÃO DE GRUPOS E MACRO_GRUPOS (COM CACHE)
# =============================================================================

@st.cache_data(ttl=120)
def carregar_macro_grupos_cached(planilha_id):
    """Carrega e retorna uma lista única e ordenada de todos os 'Macro_Grupos' da planilha 'Grupos', com cache de 2 minutos.
    
    Args:
        planilha_id (str): ID da planilha no Google Drive.
    
    Returns:
        list: Lista de strings com os nomes dos Macro_Grupos, ou uma lista vazia se houver falha.
    """
    try:
        # Usa URL pública para evitar chamada de API
        url = f"https://docs.google.com/spreadsheets/d/{planilha_id}/gviz/tq?out:csv&sheet=Grupos"
        df = pd.read_csv(url)

        # Extrai Macro_Grupos únicos (excluindo vazios)
        if 'Macro_Grupo' in df.columns:
            macro_grupos = list(set([
                str(val).strip()
                for val in df['Macro_Grupo'].dropna().unique()
                if str(val).strip()
            ]))
            return sorted(macro_grupos)
        return []
    except Exception as e:
        print(f"Erro ao carregar Macro_Grupos: {e}")
        return []


@st.cache_data(ttl=120)
def carregar_grupos_completos_cached(planilha_id):
    """Carrega todos os grupos da planilha 'Grupos', filtrando e removendo entradas de Macro_Grupos (ID iniciado com '_MACRO_'), com cache de 2 minutos.
    
    Args:
        planilha_id (str): ID da planilha no Google Drive.
    
    Returns:
        list: Lista de dicionários, onde cada dicionário representa um grupo com seus dados, ou uma lista vazia se houver falha.
    """
    try:
        # Usa URL pública para evitar chamada de API
        url = f"https://docs.google.com/spreadsheets/d/{planilha_id}/gviz/tq?out=CSV&sheet=Grupos"
        df = pd.read_csv(url)

        # ✅ FILTRA: Exclui linhas que são apenas Macro_Grupos (ID começa com '_MACRO_')
        df_filtrado = df[~df['ID_Grupo'].astype(str).str.startswith('_MACRO_')]

        # Converte para lista de dicionários
        dados = df_filtrado.to_dict('records')
        return dados
    except Exception as e:
        print(f"Erro ao carregar Grupos: {e}")
        return []


def criar_novo_grupo(nome_grupo, macro_grupo, link_grupo, secrets, error_log=None):
    """Cria um novo grupo na planilha 'Grupos', verificando se já não existe um grupo com o mesmo nome.
    
    Args:
        nome_grupo (str): Nome do grupo a ser criado (será convertido para maiúsculas).
        macro_grupo (str): Nome do Macro_Grupo ao qual o grupo pertence.
        link_grupo (str): Link do grupo no WhatsApp.
        secrets (dict): Dicionário com as credenciais do Google.
        error_log (list, optional): Lista para registro de erros. Se fornecida, erros serão adicionados a ela.
    
    Returns:
        tuple: (bool, str) indicando sucesso e uma mensagem de feedback (ex: True, "Grupo criado com sucesso").
    """
    try:
        client = _get_gspread_client(secrets, error_log)
        if client is None:
            return False, "Erro de conexão"

        planilha = client.open_by_key(secrets["planilha"]["id"])
        aba = planilha.worksheet("Grupos")

        # Verifica se já existe
        dados = aba.get_all_records()
        for row in dados:
            if str(row.get('ID_Grupo', '')).upper() == str(nome_grupo).upper():
                return False, "Grupo já existe"

        # Adiciona novo grupo
        aba.append_row([
            str(nome_grupo).upper(),
            str(macro_grupo).strip(),
            str(link_grupo).strip()
        ])

        # Limpa cache após criação
        carregar_macro_grupos_cached.clear()
        carregar_grupos_completos_cached.clear()

        return True, "Grupo criado com sucesso"
    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': 'criar_novo_grupo',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        return False, f"Erro: {str(e)}"


def criar_novo_macro_grupo(nome_macro, secrets, error_log=None):
    """Cria um novo 'Macro_Grupo' na planilha 'Grupos', adicionando uma entrada especial com ID '_MACRO_...', e limpa o cache associado.
    
    Args:
        nome_macro (str): Nome do Macro_Grupo a ser criado.
        secrets (dict): Dicionário com as credenciais do Google.
        error_log (list, optional): Lista para registro de erros. Se fornecida, erros serão adicionados a ela.
    
    Returns:
        tuple: (bool, str) indicando sucesso e uma mensagem de feedback (ex: True, "Macro_Grupo criado com sucesso").
    """
    try:
        client = _get_gspread_client(secrets, error_log)
        if client is None:
            return False, "Erro de conexão"

        planilha = client.open_by_key(secrets["planilha"]["id"])
        aba = planilha.worksheet("Grupos")

        # Verifica se já existe
        dados = aba.get_all_records()
        for row in dados:
            if str(row.get('Macro_Grupo', '')).strip().upper() == str(nome_macro).upper():
                return False, "Macro_Grupo já existe"

        # Adiciona entrada
        aba.append_row([
            f"_MACRO_{nome_macro.upper().replace(' ', '_')}",
            str(nome_macro).strip(),
            ""
        ])

        # Limpa cache após criação
        carregar_macro_grupos_cached.clear()
        carregar_grupos_completos_cached.clear()

        return True, "Macro_Grupo criado com sucesso"
    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': 'criar_novo_macro_grupo',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        return False, f"Erro: {str(e)}"


# =============================================================================
# FUNÇÕES DE DIAGNÓSTICO E SUPORTE TÉCNICO
# =============================================================================

def diagnosticar_conexoes(secrets, error_log=None):
    """Testa todas as conexões do sistema (Sheets, Drive, Planilha, Cache) e retorna um dicionário com o status de cada uma.
    
    Args:
        secrets (dict): Dicionário com as credenciais do Google.
        error_log (list, optional): Lista para registro de erros. Se fornecida, erros serão adicionados a ela.
    
    Returns:
        dict: Dicionário com chaves 'sheets', 'drive', 'planilha', 'cache', cada uma contendo um subdicionário com 'status' (✅/❌) e 'msg'.
    """
    resultados = {
        'sheets': {'status': '❌', 'msg': ''},
        'drive': {'status': '❌', 'msg': ''},
        'planilha': {'status': '❌', 'msg': ''},
        'cache': {'status': '❌', 'msg': ''}
    }

    # Teste Google Sheets
    try:
        client = _get_gspread_client(secrets, error_log)
        if client:
            resultados['sheets'] = {'status': '✅', 'msg': 'Conectado'}
            planilha = client.open_by_key(secrets["planilha"]["id"])
            resultados['planilha'] = {'status': '✅', 'msg': f'{planilha.title}'}
        else:
            resultados['sheets'] = {'status': '❌', 'msg': 'Falha na autenticação'}
    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': 'diagnosticar_conexoes.sheets',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        resultados['sheets'] = {'status': '❌', 'msg': str(e)}

    # Teste Google Drive
    try:
        creds = _get_drive_credentials(secrets, error_log)
        if creds:
            resultados['drive'] = {'status': '✅', 'msg': 'Conectado'}
        else:
            resultados['drive'] = {'status': '❌', 'msg': 'Falha na autenticação'}
    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': 'diagnosticar_conexoes.drive',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        resultados['drive'] = {'status': '❌', 'msg': str(e)}

    # Teste Cache
    try:
        carregar_macro_grupos_cached(secrets["planilha"]["id"])
        resultados['cache'] = {'status': '✅', 'msg': 'Funcionando'}
    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': 'diagnosticar_conexoes.cache',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        resultados['cache'] = {'status': '❌', 'msg': str(e)}

    return resultados


def obter_logs_erros(error_log_session, limite=50):
    """Retorna uma lista dos últimos erros registrados na sessão atual, limitada a um número máximo de entradas.
    
    Args:
        error_log_session (list): Lista de dicionários contendo os logs de erro da sessão.
        limite (int, optional): Número máximo de erros a serem retornados. Padrão é 50.
    
    Returns:
        list: Lista de dicionários com os logs de erro mais recentes.
    """
    if not error_log_session:
        return []

    return error_log_session[-limite:]


def contar_chamadas_api():
    """Retorna um dicionário com uma estimativa do uso das APIs do sistema (Sheets, Drive, Cache).
    
    Returns:
        dict: Dicionário com chaves 'sheets_api', 'drive_api', 'cache_hits' e suas respectivas descrições.
    """
    # Isso é mais informativo, já que gviz não conta como API call
    return {
        'sheets_api': '0 (usando gviz)',
        'drive_api': 'Variável (uploads)',
        'cache_hits': 'Ativo (ttl=120s)'
    }


def simular_acao_usuario(id_usuario, tipo_acao, secrets, error_log=None):
    """Simula a execução de uma ação de usuário, gerando dados de exemplo sem gravar na planilha.
    
    Args:
        id_usuario (str): ID do usuário que está sendo simulado.
        tipo_acao (str): Tipo de ação a ser simulada (ex: 'Check-in').
        secrets (dict): Dicionário com as credenciais do Google.
        error_log (list, optional): Lista para registro de erros. Se fornecida, erros serão adicionados a ela.
    
    Returns:
        dict: Dicionário com os dados simulados (ID, ação, horário, GPS de teste, endereço de teste).
    """
    try:
        return {
            'id_usuario': id_usuario,
            'tipo_acao': tipo_acao,
            'timestamp': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
            'status': 'SIMULAÇÃO (não gravado)',
            'gps_teste': '-15.7801,-47.9292',
            'endereco_teste': obter_endereco_simples('-15.7801,-47.9292', error_log)
        }
    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': 'simular_acao_usuario',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        return {
            'id_usuario': id_usuario,
            'tipo_acao': tipo_acao,
            'timestamp': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
            'status': 'SIMULAÇÃO FALHOU',
            'erro': str(e)
        }


# -------------------------------------------------------------------------
# G A M I F I C A Ç Ã O   –   FUNÇÕES AUXILIARES
# -------------------------------------------------------------------------
def _ws_leaderboard(planilha_id, secrets, error_log=None):
    """
    Retorna a Worksheet da aba **Leaderboard** (mesma planilha usada nas demais funções).

    **Novas colunas** (ordem abaixo):
        id_usuario, nome, cargo, pontos_total, ultima_atualizacao,
        pontos_dia, data_dia, tipo_acao, pontos_ganhos

    Caso a aba ainda não exista, a exceção será propagada ao chamador.
    """
    client = _get_gspread_client(secrets, error_log)
    planilha = client.open_by_key(planilha_id)
    return planilha.worksheet("Leaderboard")


def atualizar_pontuacao_usuario(
        id_usuario: str,
        nome: str,
        cargo: str,
        acao: str,
        planilha_id: str,
        secrets,
        error_log=None) -> bool:
    """
    Registra **uma linha nova** na aba Leaderboard a cada ação do usuário.

    Estrutura da aba (colunas na ordem exata):
        1. id_usuario
        2. nome
        3. cargo
        4. pontos_total          – somatório acumulado (apenas se ganhar pontos)
        5. ultima_atualizacao   – timestamp da última gravação que gerou pontos
        6. pontos_dia           – contagem de ações que geraram pontos hoje
        7. data_dia             – data (dd/mm/yyyy) referente a ``pontos_dia``
        8. tipo_acao            – código interno da ação (ex: "checkin")
        9. pontos_ganhos        – pontos efetivamente concedidos nesta ação
    """
    from utils.gamification import PONTUACAO, LIMITE_DIARIO

    try:
        ws = _ws_leaderboard(planilha_id, secrets, error_log)

        # ---------------------------------------------------------
        # 1️⃣  Obter todas as linhas já existentes (para cálculos)
        # ---------------------------------------------------------
        registros = ws.get_all_records()
        linhas_usuario = [r for r in registros if str(r.get('id_usuario')) == str(id_usuario)]

        # ---------------------------------------------------------
        # 2️⃣  Determinar o total acumulado já existente
        # ---------------------------------------------------------
        if linhas_usuario:
            total_atual = max([int(r.get('pontos_total', 0) or 0) for r in linhas_usuario])
        else:
            total_atual = 0

        # ---------------------------------------------------------
        # 3️⃣  Determinar contagem de ações hoje (para limite diário)
        # ---------------------------------------------------------
        hoje_str = get_agora_br().strftime("%d/%m/%Y")
        acoes_hoje = [
            r for r in linhas_usuario
            if r.get('data_dia') == hoje_str and r.get('tipo_acao') == acao
        ]
        limite = LIMITE_DIARIO.get(acao, None)          # None → sem limite
        limite_atingido = (limite is not None and len(acoes_hoje) >= limite)

        # ---------------------------------------------------------
        # 4️⃣  Calcular pontos que deverão ser creditados nesta ação
        # ---------------------------------------------------------
        ganho = 0 if limite_atingido else PONTUACAO.get(acao, 0)

        # Atualiza total e pontos do dia somente se houver ganho
        novo_total = total_atual + ganho

        # Se for a primeira ação do usuário ou se o dia mudou, reseta pontos_dia
        if linhas_usuario:
            # última linha gravada do usuário (pela data de atualização)
            ultima_linha = max(
                linhas_usuario,
                key=lambda r: r.get('ultima_atualizacao', '')
            )
            pontos_dia_atual = int(ultima_linha.get('pontos_dia') or 0)
            data_dia_atual = ultima_linha.get('data_dia')
            if data_dia_atual != hoje_str:
                pontos_dia_atual = 0
        else:
            pontos_dia_atual = 0

        novo_pontos_dia = pontos_dia_atual + (1 if ganho > 0 else 0)

        # ---------------------------------------------------------
        # 5️⃣  Gravar a nova linha
        # ---------------------------------------------------------
        ws.append_row([
            str(id_usuario),                # id_usuario
            str(nome),                     # nome
            str(cargo),                    # cargo
            novo_total,                    # pontos_total
            get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),  # ultima_atualizacao
            novo_pontos_dia,               # pontos_dia
            hoje_str,                      # data_dia
            acao,                          # tipo_acao
            ganho                          # pontos_ganhos
        ])

        # ---------------------------------------------------------
        # 6️⃣  Retorno
        # ---------------------------------------------------------
        return True

    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': 'atualizar_pontuacao_usuario',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        print(f"Erro ao atualizar pontuação: {e}")
        return False


def registrar_acao_com_pontuacao(
        id_usuario: str,
        tipo_acao: str,
        localizacao,
        feedback,
        secrets,
        error_log=None) -> bool:
    """
    Wrapper que (a) registra a ação na aba **Logs** (mantém histórico)
    e (b) converte a ação para o código interno da gamificação, atualizando a pontuação do usuário.
    Sempre retorna o resultado da gravação em Logs (True/False).
    """
    # Função depreciada – redireciona para registrar_acao que já contém
    # a lógica completa de registro + pontuação.
    return registrar_acao(
        id_usuario=id_usuario,
        tipo_acao=tipo_acao,
        localizacao=localizacao,
        feedback=feedback,
        secrets=secrets,
        error_log=error_log
    )


# =============================================================================
# NOVAS FUNÇÕES DE GESTÃO DE MATERIAIS
# =============================================================================

def registrar_material_supervisor(
        id_usuario: str,
        nome_usuario: str,
        tipo_material: str,
        qnt_total: int,          # ← quantidade **total** que o grupo recebeu
        qnt_usada: int,          # ← quantidade **já utilizada**
        secrets,
        id_grupo: str | None = None,
        error_log=None) -> bool:
    """
    Registra a entrega/atualização de material para um colaborador ou grupo.
    Atualiza a coluna ``quantidade_restante`` com base no total recebido
    e na quantidade já utilizada (total - usada).

    Params:
        id_usuario (str): Identificador do colaborador ou do grupo.
        nome_usuario (str): Nome do colaborador ou do grupo.
        tipo_material (str): Nome do material (ex.: “Água”, “Máscara”).
        qnt_total (int): Quantidade total recebida neste registro.
        qnt_usada (int): Quantidade já utilizada (ou seja, que já saiu do estoque).
        secrets (dict): Credenciais do Google.
        id_grupo (str | None): Identificador do grupo (opcional).
        error_log (list, optional): Lista de erros.

    Returns:
        bool: True se a gravação ocorreu sem erro.
    """
    try:
        # 1️⃣ cliente gspread
        client = _get_gspread_client(secrets, error_log)
        if client is None:
            return False

        # 2️⃣ aba “Materiais” (deve existir na planilha)
        planilha = client.open_by_key(secrets["planilha"]["id"])
        aba = planilha.worksheet("Materiais")

        # 3️⃣ ler registros já existentes do usuário + tipo
        dados = aba.get_all_records()
        linhas_filtradas = [
            r for r in dados
            if str(r.get('id_usuario')).strip() == str(id_usuario).strip()
            and str(r.get('tipo_material')).strip().lower()
                == str(tipo_material).strip().lower()
        ]

        # 4️⃣ quantidade_restante anterior (último registro)
        if linhas_filtradas:
            ultima = max(linhas_filtradas,
                         key=lambda r: r.get('data_registro', ''))
            restante_anterior = int(ultima.get('quantidade_restante', 0))
        else:
            restante_anterior = 0

        # 5️⃣ nova quantidade restante – calculamos a partir do total e da usada
        try:
            total = int(qnt_total)
            usada = int(qnt_usada)
        except Exception:
            total = int(qnt_total) if isinstance(qnt_total, (int, float, str)) else 0
            usada = int(qnt_usada) if isinstance(qnt_usada, (int, float, str)) else 0

        nova_restante = max(0, total - usada)

        # 6️⃣ inserir nova linha
        agora = get_agora_br().strftime("%d/%m/%Y %H:%M:%S")
        nova_linha = [
            str(id_usuario),               # id_usuario
            str(nome_usuario),             # nome_usuario
            agora,                         # data_registro
            str(tipo_material).strip(),    # tipo_material (nome livre)
            total,                        # quantidade_total recebida
            int(nova_restante)            # quantidade_restante
        ]
        if id_grupo is not None:
            nova_linha.append(str(id_grupo))

        aba.append_row(nova_linha)

        return True

    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': 'registrar_material_supervisor',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        print(f"Erro ao registrar material: {e}")
        return False


@st.cache_data(ttl=120)
def obter_resumo_materiais(id_usuario: str, _secrets):
    """
    Gera um DataFrame *agregado* de materiais para o usuário/grupo indicado.
    As colunas retornadas são:
        - tipo_material
        - total_recebido
        - restante
    """
    try:
        client = _get_gspread_client(_secrets)
        aba = client.open_by_key(_secrets["planilha"]["id"]).worksheet("Materiais")
        df = pd.DataFrame(aba.get_all_records())

        if df.empty:
            return pd.DataFrame()

        filtro = df['id_usuario'].astype(str) == str(id_usuario).strip()
        df_user = df[filtro][['tipo_material',
                               'quantidade_total' if 'quantidade_total' in df.columns else 'quantidade_recebida',
                               'quantidade_restante']].copy()

        col_qtd = 'quantidade_total' if 'quantidade_total' in df_user.columns else 'quantidade_recebida'
        df_user = df_user.rename(columns={col_qtd: 'total_recebido',
                                          'quantidade_restante': 'restante'})

        resumo = (
            df_user
            .groupby('tipo_material')
            .agg(total_recebido=('total_recebido', 'sum'),
                 restante=('restante', 'last'))
            .reset_index()
        )
        return resumo
    except Exception as e:
        print(f"Erro ao gerar resumo de materiais: {e}")
        return pd.DataFrame()


# -------------------------------------------------------------------------
# 2️⃣ FUNÇÃO PARA OBTER OS REGISTROS “BRUTOS” DE UM GRUPO
# -------------------------------------------------------------------------
def obter_materiais_por_grupo(id_usuario: str, _secrets):
    """
    Retorna um DataFrame **não agregado** contendo, para o ``id_usuario`` (grupo),
    as colunas:
        - ``tipo_material``
        - ``quantidade_total``  (coluna “quantidade_total” ou, se ainda não existir, a antiga “quantidade_recebida”)
        - ``quantidade_restante``
    
    Essa função é usada pelo componente de edição, pois permite que o supervisor
    veja o estoque atual e altere os valores.
    """
    try:
        client = _get_gspread_client(_secrets)
        aba = client.open_by_key(_secrets["planilha"]["id"]).worksheet("Materiais")
        df = pd.DataFrame(aba.get_all_records())

        if df.empty:
            return pd.DataFrame()

        filtro = df['id_usuario'].astype(str) == str(id_usuario).strip()
        df_grp = df[filtro][['tipo_material',
                             'quantidade_total' if 'quantidade_total' in df.columns else 'quantidade_recebida',
                             'quantidade_restante']].copy()

        # Renomeia para garantir nomes consistentes para o frontend
        col_qtd = 'quantidade_total' if 'quantidade_total' in df_grp.columns else 'quantidade_recebida'
        df_grp = df_grp.rename(columns={col_qtd: 'quantidade_total'})
        return df_grp.reset_index(drop=True)
    except Exception as e:
        print(f"Erro ao obter materiais por grupo: {e}")
        return pd.DataFrame()


# -------------------------------------------------------------------------
# 3️⃣ FUNÇÃO DE ATUALIZAÇÃO DE UMA LINHA DE MATERIAL
# -------------------------------------------------------------------------
def atualizar_material_grupo(
        id_usuario: str,
        tipo_material: str,
        novo_total: int,
        novo_restante: int,
        _secrets,
        error_log=None) -> bool:
    """
    Busca a **última** linha da aba “Materiais” que corresponde ao
    ``id_usuario`` + ``tipo_material`` e atualiza as colunas
    ``quantidade_total`` e ``quantidade_restante`` com os novos valores.
    Se a coluna ``quantidade_total`` ainda não existir (planilha antiga),
    cria‑a ao atualizar.
    """
    try:
        client = _get_gspread_client(_secrets, error_log)
        if client is None:
            return False

        planilha = client.open_by_key(_secrets["planilha"]["id"])
        aba = planilha.worksheet("Materiais")

        # 1️⃣ Obter cabeçalho e garantir colunas
        cabecalho = aba.row_values(1)
        if 'quantidade_total' not in cabecalho:
            aba.update('A1', cabecalho + ['quantidade_total'])
            cabecalho.append('quantidade_total')
        if 'quantidade_restante' not in cabecalho:
            aba.update('A1', cabecalho + ['quantidade_restante'])
            cabecalho.append('quantidade_restante')

        col_total = cabecalho.index('quantidade_total') + 1
        col_rest = cabecalho.index('quantidade_restante') + 1

        # 2️⃣ Procurar a linha que corresponde ao usuário + tipo (última ocorrência)
        linhas = aba.get_all_records()
        linha_alvo = None
        for i, linha in enumerate(linhas, start=2):  # começa na linha 2 (abaixo do cabeçalho)
            if str(linha.get('id_usuario')).strip() == str(id_usuario).strip() and \
               str(linha.get('tipo_material')).strip().lower() == str(tipo_material).strip().lower():
                linha_alvo = i  # guarda sempre a última encontrada

        if linha_alvo is None:
            # Não encontrou → nada a atualizar
            return False

        # 3️⃣ Atualizar as duas colunas
        aba.update_cell(linha_alvo, col_total, int(novo_total))
        aba.update_cell(linha_alvo, col_rest, int(novo_restante))
        return True
    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': 'atualizar_material_grupo',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        print(f"Erro ao atualizar material: {e}")
        return False
