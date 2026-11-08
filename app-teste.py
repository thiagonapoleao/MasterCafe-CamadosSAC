import streamlit as st
import pandas as pd
from datetime import datetime
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import streamlit.components.v1 as components
import altair as alt
import os
import base64

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Gestão de Conferência de Mercadorias",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Função utilitária para codificação de imagem em Base64
def carregar_imagem_base64(caminho_imagem: str) -> str:
    if os.path.exists(caminho_imagem):
        with open(caminho_imagem, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""

# --- DESIGN SYSTEM CORPORATIVO: COMPACTAÇÃO PRECISA E EQUILIBRADA ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"], [class*="st-"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        font-size: 12.5px !important;
        color: #1e293b;
    }

    /* Container Centralizado com Menos Folga Superior */
    .block-container {
        max-width: 1240px !important;
        margin-left: auto !important;
        margin-right: auto !important;
        padding-top: 0.6rem !important;
        padding-bottom: 1.8rem !important;
        padding-left: 1.2rem !important;
        padding-right: 1.2rem !important;
    }

    /* Top Bar Container Slim */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.topbar-wrapper-marker) {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        padding: 3px 8px !important;
        margin-bottom: 14px !important;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04) !important;
    }

    /* Bloco da Logo e Título com Encaixe Preciso */
    .brand-box {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 0;
    }
    .brand-logo-img {
        height: 28px;
        max-width: 85px;
        object-fit: contain;
        display: block;
    }
    .brand-logo-icon {
        width: 28px;
        height: 28px;
        min-width: 28px;
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
        color: #ffffff;
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        box-shadow: 0 2px 6px rgba(29, 78, 216, 0.25);
    }
    .brand-text-col {
        display: flex;
        flex-direction: column;
        justify-content: center;
        line-height: 1.1;
    }
    .brand-title {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 12px !important;
        font-weight: 800 !important;
        color: #0f172a !important;
        letter-spacing: -0.2px;
        white-space: nowrap;
    }
    .brand-subtitle {
        font-size: 8px !important;
        font-weight: 700 !important;
        color: #64748b !important;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }

    /* BOTÕES DA TOPBAR: Altura Reduzida e Tipografia Ajustada */
    .nav-btn-active button,
    .nav-btn-inactive button,
    .nav-btn-sync button {
        height: 26px !important;
        min-height: 26px !important;
        max-height: 26px !important;
        padding: 0 4px !important;
        font-size: 10px !important;
        font-weight: 600 !important;
        border-radius: 5px !important;
        letter-spacing: -0.2px !important;
        white-space: nowrap !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.15s ease !important;
    }
    .nav-btn-active button *,
    .nav-btn-inactive button *,
    .nav-btn-sync button * {
        font-size: 10px !important;
        line-height: 1 !important;
    }

    /* BOTÃO ATIVO: Destaque Azul Primário com Foco Nítido */
    .nav-btn-active button {
        background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%) !important;
        border: 1px solid #1d4ed8 !important;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.28), 0 2px 5px rgba(29, 78, 216, 0.3) !important;
        transform: scale(1.01) !important;
    }
    .nav-btn-active button,
    .nav-btn-active button *,
    .nav-btn-active button p,
    .nav-btn-active button span {
        color: #ffffff !important;
        fill: #ffffff !important;
        font-weight: 700 !important;
    }

    /* BOTÃO INATIVO: Superfície Clara Neutra */
    .nav-btn-inactive button {
        background-color: #f8fafc !important;
        background-image: none !important;
        border: 1px solid #cbd5e1 !important;
        box-shadow: none !important;
    }
    .nav-btn-inactive button,
    .nav-btn-inactive button *,
    .nav-btn-inactive button p,
    .nav-btn-inactive button span {
        color: #334155 !important;
        fill: #334155 !important;
        font-weight: 600 !important;
    }
    .nav-btn-inactive button:hover {
        background-color: #eff6ff !important;
        border-color: #93c5fd !important;
    }
    .nav-btn-inactive button:hover,
    .nav-btn-inactive button:hover * {
        color: #1d4ed8 !important;
    }

    /* BOTÃO SINCRONIZAR */
    .nav-btn-sync button {
        background-color: #ffffff !important;
        background-image: none !important;
        border: 1px solid #cbd5e1 !important;
    }
    .nav-btn-sync button,
    .nav-btn-sync button *,
    .nav-btn-sync button p,
    .nav-btn-sync button span {
        color: #1d4ed8 !important;
        font-size: 11px !important;
        font-weight: 700 !important;
    }
    .nav-btn-sync button:hover {
        background-color: #eff6ff !important;
        border-color: #2563eb !important;
    }

    /* BOTÕES DE AÇÃO DO CORPO */
    div.stButton:not(.nav-btn-active):not(.nav-btn-inactive):not(.nav-btn-sync):not(.danger-btn) > button {
        background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%) !important;
        border: 1px solid #1d4ed8 !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        padding: 6px 16px !important;
        font-size: 11.5px !important;
        letter-spacing: 0.1px !important;
        box-shadow: 0 3px 8px rgba(29, 78, 216, 0.22) !important;
        transition: all 0.15s ease !important;
    }
    div.stButton:not(.nav-btn-active):not(.nav-btn-inactive):not(.nav-btn-sync):not(.danger-btn) > button,
    div.stButton:not(.nav-btn-active):not(.nav-btn-inactive):not(.nav-btn-sync):not(.danger-btn) > button * {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    div.stButton:not(.nav-btn-active):not(.nav-btn-inactive):not(.nav-btn-sync):not(.danger-btn) > button:hover {
        background: linear-gradient(135deg, #1e40af 0%, #1d4ed8 100%) !important;
        box-shadow: 0 0 0 2.5px rgba(37, 99, 235, 0.3), 0 5px 12px rgba(29, 78, 216, 0.3) !important;
    }

    /* BOTÃO DE AÇÃO PERIGOSA (EXCLUSÃO / VERMELHO) */
    .danger-btn button {
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%) !important;
        border: 1px solid #b91c1c !important;
        border-radius: 6px !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 11.5px !important;
        box-shadow: 0 3px 8px rgba(220, 38, 38, 0.25) !important;
        transition: all 0.15s ease !important;
    }
    .danger-btn button:hover {
        background: linear-gradient(135deg, #b91c1c 0%, #991b1b 100%) !important;
        box-shadow: 0 0 0 2.5px rgba(239, 68, 68, 0.35), 0 5px 12px rgba(185, 28, 28, 0.35) !important;
    }
    .danger-btn button * {
        color: #ffffff !important;
        font-weight: 700 !important;
    }

    /* Tipografia de Cabeçalho da Página */
    .main-title {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 16.5px !important;
        font-weight: 700 !important;
        color: #0f172a !important;
        margin-bottom: 2px !important;
        padding-bottom: 4px !important;
        border-bottom: 1.5px solid #e2e8f0 !important;
        letter-spacing: -0.2px !important;
    }
    .sub-title {
        font-size: 11px !important;
        color: #64748b !important;
        margin-bottom: 12px !important;
    }

    /* Grid de Métricas / KPIs Compactas */
    .metric-container {
        display: flex;
        gap: 10px;
        margin-bottom: 16px;
        flex-wrap: wrap;
    }
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 8px 12px;
        flex: 1;
        min-width: 150px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03);
    }
    .metric-card span {
        font-size: 9.5px !important;
        color: #64748b;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.4px;
        display: block;
    }
    .metric-card strong {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 14.5px !important;
        color: #0f172a;
        margin-top: 2px;
        font-weight: 700;
        display: block;
    }

    /* Dica de Teclado */
    .keyboard-hint {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 4px 8px;
        border-radius: 5px;
        font-size: 10.5px !important;
        color: #334155;
        display: inline-flex;
        align-items: center;
        gap: 5px;
        margin-bottom: 8px;
    }
    .keyboard-hint kbd {
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
        border-bottom-width: 2px;
        padding: 1px 4px;
        border-radius: 3px;
        font-weight: 700;
        font-size: 9.5px !important;
        color: #0f172a;
    }

    /* Box de Divergência */
    .divergence-box {
        background-color: #fffbeb;
        border: 1px solid #fde68a;
        border-radius: 6px;
        padding: 9px 12px;
        margin-top: 8px;
        margin-bottom: 10px;
        font-size: 11px !important;
    }

    /* Box de Alerta Vermelho / Exclusão */
    .danger-box {
        background-color: #fef2f2;
        border: 1px solid #fecaca;
        border-radius: 6px;
        padding: 10px 14px;
        margin-top: 8px;
        margin-bottom: 12px;
        font-size: 11px !important;
    }

    /* Formulários e Inputs Compactos */
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div,
    input, textarea, select {
        font-size: 11.5px !important;
        border-radius: 5px !important;
    }
    label p {
        font-size: 11px !important;
        font-weight: 600 !important;
        color: #0f172a !important;
    }

    [data-testid="stDataFrame"] div, [data-testid="stDataEditor"] div {
        font-size: 11px !important;
    }

    /* Formatação de Impressão */
    @media print {
        header, .stSidebar, .stButton, [data-testid="stToolbar"], footer, .no-print, [data-testid="stVerticalBlockBorderWrapper"]:has(.topbar-wrapper-marker) {
            display: none !important;
        }
        .block-container {
            max-width: 100% !important;
            padding: 0 !important;
        }
        .printable-area {
            display: block !important;
            width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            border: 1px solid #1e293b !important;
            padding: 3px 5px !important;
            font-size: 9.5px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- 2. CONFIGURAÇÃO DA API & SESSÃO RESILIENTE ---
API_URL = "https://script.google.com/macros/s/AKfycbx6Dvaz55Vd9gzOmG5HHhvdrkRSF9w1kx4Ie7mxrWcQnjjOj1rf0ND7JIGEb1Jk-yCi/exec"

def get_session():
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=1.5,
        status_forcelist=[500, 502, 503, 504],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

# --- 3. COMUNICAÇÃO HTTP COM GOOGLE APPS SCRIPT ---
def enviar_dados_apps_script(payload: dict) -> dict:
    try:
        session = get_session()
        payload_str = json.dumps(payload, default=str)
        headers = {"Content-Type": "text/plain;charset=utf-8"}
        
        response = session.post(
            API_URL,
            data=payload_str,
            headers=headers,
            allow_redirects=True,
            timeout=60
        )
        
        if response.status_code != 200:
            return {"status": "error", "message": f"HTTP {response.status_code}: {response.text[:200]}"}
        
        try:
            return response.json()
        except Exception:
            return {"status": "error", "message": f"Resposta inválida da API: {response.text[:250]}"}
    except Exception as ex:
        return {"status": "error", "message": f"Falha de conexão: {str(ex)}"}

def normalizar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    if "remessa" in df.columns:
        df["remessa"] = df["remessa"].fillna("").astype(str)
        df["remessa"] = df["remessa"].str.replace(r"\.0$", "", regex=True).str.strip()

    for col in ["produto", "descricao", "local", "conferente", "observacao"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()

    return df

@st.cache_data(ttl=180, show_spinner=False)
def carregar_dados_planilha_cached():
    try:
        session = get_session()
        r = session.get(f"{API_URL}?action=listar", allow_redirects=True, timeout=60)
        if r.status_code == 200:
            try:
                dados = r.json()
                if isinstance(dados, list):
                    df = pd.DataFrame(dados)
                    return normalizar_dataframe(df)
            except Exception:
                pass
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def carregar_dados_planilha():
    try:
        return carregar_dados_planilha_cached()
    except Exception as e:
        st.error(f"Erro ao buscar registros da planilha: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300, show_spinner=False)
def carregar_lista_conferentes():
    try:
        session = get_session()
        r = session.get(f"{API_URL}?action=get_conferentes", allow_redirects=True, timeout=40)
        if r.status_code == 200:
            try:
                lista = r.json()
                if isinstance(lista, list) and len(lista) > 0:
                    return sorted([str(x).strip() for x in lista if str(x).strip()])
            except Exception:
                return []
        return []
    except Exception:
        return []

def enviar_cadastro_conferente(nome):
    payload = {"action": "cadastrar_conferente", "nome": nome}
    res = enviar_dados_apps_script(payload)
    carregar_lista_conferentes.clear()
    return res

def enviar_importacao_planilha(linhas):
    payload = {"action": "importar", "linhas": linhas}
    res = enviar_dados_apps_script(payload)
    carregar_dados_planilha_cached.clear()
    return res

def enviar_atualizacao_conferencia(itens):
    payload = {"action": "atualizar", "itens": itens}
    res = enviar_dados_apps_script(payload)
    carregar_dados_planilha_cached.clear()
    return res

def enviar_exclusao_remessa(remessa: str) -> dict:
    payload = {"action": "excluir_remessa", "remessa": str(remessa).strip()}
    res = enviar_dados_apps_script(payload)
    carregar_dados_planilha_cached.clear()
    return res

def formatar_data_br(data_val):
    if data_val is None or pd.isna(data_val):
        return datetime.now().strftime("%d/%m/%Y")
    
    val_str = str(data_val).strip()
    if val_str in ["", "nan", "None", "00:00:00"]:
        return datetime.now().strftime("%d/%m/%Y")

    if len(val_str) == 10 and val_str[2] == "/" and val_str[5] == "/":
        return val_str

    try:
        dt = pd.to_datetime(val_str, errors="coerce", dayfirst=True)
        if pd.notna(dt):
            return dt.strftime("%d/%m/%Y")
    except Exception:
        pass

    if " " in val_str:
        partes = val_str.split(" ")
        for p in partes:
            if "/" in p and len(p) == 10:
                return p

    return datetime.now().strftime("%d/%m/%Y")

def injetar_atalho_teclado_tab():
    components.html("""
    <script>
    (function() {
        const parentDoc = window.parent.document;
        parentDoc.addEventListener('keydown', function(e) {
            if ((e.key === 'Tab' || e.key === 'Enter') && !e.shiftKey) {
                const active = parentDoc.activeElement;
                if (active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA')) {
                    const downEvent = new KeyboardEvent('keydown', {
                        key: 'ArrowDown',
                        code: 'ArrowDown',
                        keyCode: 40,
                        which: 40,
                        bubbles: true,
                        cancelable: true
                    });
                    
                    if (e.key === 'Tab') {
                        e.preventDefault();
                        active.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true }));
                        setTimeout(() => {
                            parentDoc.dispatchEvent(downEvent);
                        }, 20);
                    }
                }
            }
        }, true);
    })();
    </script>
    """, height=0, width=0)

# --- 4. EXTRAÇÃO DO EXCEL ---
def extrair_excel(uploaded_file):
    itens = []
    df_raw = pd.read_excel(uploaded_file, header=None, dtype=str)
    
    linha_cabecalho = None
    idx_col_prod = None
    idx_col_desc = None
    idx_col_qtd = None

    for r_idx in range(min(50, len(df_raw))):
        linha = df_raw.iloc[r_idx]
        linha_limpa = [str(val).strip().lower() for val in linha.dropna()]
        texto_linha = " ".join(linha_limpa)

        if any(termo in texto_linha for termo in ["produto", "código", "codigo", "item"]):
            linha_cabecalho = r_idx
            
            for c_idx, val in enumerate(linha):
                if pd.isna(val):
                    continue
                v = str(val).strip().lower()
                
                if any(k in v for k in ["produto", "código", "codigo", "item"]) and idx_col_prod is None:
                    idx_col_prod = c_idx
                elif any(k in v for k in ["descri", "nome", "especifica"]) and idx_col_desc is None:
                    idx_col_desc = c_idx
                elif any(k in v for k in ["quant", "qtd"]) and not any(k in v for k in ["lote", "série", "serie"]):
                    idx_col_qtd = c_idx
            break

    if linha_cabecalho is None:
        return itens

    if idx_col_prod is None:
        idx_col_prod = 0
    if idx_col_desc is None and len(df_raw.columns) > 1:
        idx_col_desc = 1

    for r_idx in range(linha_cabecalho + 1, len(df_raw)):
        linha = df_raw.iloc[r_idx]

        if linha.dropna().empty:
            continue

        cod = str(linha.iloc[idx_col_prod]).strip() if idx_col_prod < len(linha) and pd.notna(linha.iloc[idx_col_prod]) else ""
        desc = str(linha.iloc[idx_col_desc]).strip() if idx_col_desc is not None and idx_col_desc < len(linha) and pd.notna(linha.iloc[idx_col_desc]) else ""

        cod_lower = cod.lower()
        if not cod or cod_lower in ["none", "nan", "total", "subtotal", "produto", "código", "codigo", ""]:
            continue

        qtd = 0.0
        if idx_col_qtd is not None and idx_col_qtd < len(linha) and pd.notna(linha.iloc[idx_col_qtd]):
            qtd_str = str(linha.iloc[idx_col_qtd]).strip().replace(".", "").replace(",", ".")
            try:
                qtd = float(qtd_str)
            except ValueError:
                qtd = 0.0
        else:
            for val in reversed(linha):
                if pd.notna(val):
                    val_str = str(val).strip().replace(".", "").replace(",", ".")
                    try:
                        qtd = float(val_str)
                        break
                    except ValueError:
                        continue

        itens.append({
            "Produto": cod,
            "Descricao": desc if desc.lower() not in ["none", "nan"] else "",
            "Quantidade": qtd
        })

    return itens

# --- 5. NAVEGAÇÃO SUPERIOR ENVOLVIDA EM CONTAINER (TOP BAR SLIM) ---
if "menu_selecionado" not in st.session_state:
    st.session_state.menu_selecionado = "Dashboard de Resumo"

opcoes_menu = [
    ("📊 Dashboard", "Dashboard de Resumo"),
    ("📥 Importar", "Importar Remessa"),
    ("🖨️ Folha Cega", "Folha de Impressão Cega"),
    ("🔍 Conferir", "Digitar Conferência Cega"),
    ("👤 Conferentes", "Cadastrar Novo Conferente")
]

# Preparação do logotipo em Base64
img_b64 = carregar_imagem_base64("Logotipo.png")
if img_b64:
    logo_html = f'<img src="data:image/png;base64,{img_b64}" class="brand-logo-img" alt="Logo">'
else:
    logo_html = '<div class="brand-logo-icon">📦</div>'

# Proporção Compacta e Precisa
with st.container(border=True):
    st.markdown('<div class="topbar-wrapper-marker" style="display:none;"></div>', unsafe_allow_html=True)
    
    col_brand, c1, c2, c3, c4, c5, col_sync = st.columns([2.5, 1.05, 1.0, 1.15, 1.0, 1.15, 0.4], vertical_alignment="center")

    with col_brand:
        st.markdown(f"""
        <div class="brand-box">
            {logo_html}
            <div class="brand-text-col">
                <span class="brand-title">ESTOQUE & CONFERÊNCIA</span>
                <span class="brand-subtitle">Gestão Integrada</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    nav_cols = [c1, c2, c3, c4, c5]
    for idx, (label_icone, chave_menu) in enumerate(opcoes_menu):
        with nav_cols[idx]:
            is_active = (st.session_state.menu_selecionado == chave_menu)
            classe_css = "nav-btn-active" if is_active else "nav-btn-inactive"
            
            st.markdown(f'<div class="{classe_css}">', unsafe_allow_html=True)
            if st.button(label_icone, key=f"nav_top_{chave_menu}", use_container_width=True):
                if st.session_state.menu_selecionado != chave_menu:
                    st.session_state.menu_selecionado = chave_menu
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    with col_sync:
        st.markdown('<div class="nav-btn-sync">', unsafe_allow_html=True)
        if st.button("🔄", key="btn_top_sync", help="Sincronizar dados com a planilha Google", use_container_width=True):
            carregar_dados_planilha_cached.clear()
            carregar_lista_conferentes.clear()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

menu = st.session_state.menu_selecionado

# ==============================================================================
# OPÇÃO: DASHBOARD DE RESUMO (ALTAIR COM PALETA CORPORATIVA SLATE/INDIGO)
# ==============================================================================
if menu == "Dashboard de Resumo":
    st.markdown('<div class="main-title">📊 Resumo Gerencial de Conferência Cega</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Monitoramento de produtividade, divergências e acuracidade em tempo real.</div>', unsafe_allow_html=True)

    with st.spinner("Compilando indicadores..."):
        df_raw = carregar_dados_planilha()

    if df_raw.empty:
        st.info("Nenhum registro encontrado na aba Conferencia para gerar o resumo.")
    else:
        df = df_raw.copy()
        
        data_col = df["data_importacao"] if "data_importacao" in df.columns else pd.Series(index=df.index, dtype=str)
        dt_parsed = pd.to_datetime(data_col, format="%d/%m/%Y", errors="coerce")
        dt_parsed = dt_parsed.fillna(pd.to_datetime(data_col, errors="coerce", dayfirst=True))
        
        df["dt_parsed"] = pd.to_datetime(dt_parsed, errors="coerce")
        df["dt_parsed"] = df["dt_parsed"].fillna(pd.Timestamp.now().normalize())

        df["ano"] = df["dt_parsed"].dt.year.astype(str)
        df["mes_num"] = df["dt_parsed"].dt.month
        df["mes_nome"] = df["dt_parsed"].dt.strftime("%B")
        df["mes_ano"] = df["dt_parsed"].dt.strftime("%m/%Y")
        df["ano_mes_sort"] = df["dt_parsed"].dt.strftime("%Y-%m")
        df["dia_str"] = df["dt_parsed"].dt.strftime("%d/%m/%Y")

        df["quantidade"] = pd.to_numeric(df.get("quantidade", 0), errors="coerce").fillna(0.0)
        df["conferencia"] = pd.to_numeric(df.get("conferencia", None), errors="coerce")
        df["divergencia"] = pd.to_numeric(df.get("divergencia", None), errors="coerce")

        col_f1, col_f2 = st.columns([2, 2])
        with col_f1:
            confs_unicos = sorted([str(c).strip() for c in df.get("conferente", pd.Series()).dropna().unique() if str(c).strip() != ""])
            lista_confs = ["TODOS"] + confs_unicos
            filtro_conf = st.selectbox("Filtrar por Conferente:", lista_confs)
        with col_f2:
            remessas_unicas = sorted([str(r).strip() for r in df.get("remessa", pd.Series()).dropna().unique() if str(r).strip() not in ["", "nan", "None"]])
            remessas_todas = ["TODAS"] + remessas_unicas
            filtro_rem = st.selectbox("Filtrar por Remessa:", remessas_todas)

        df_filtrado = df.copy()
        if filtro_conf != "TODOS" and "conferente" in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado["conferente"] == filtro_conf]
        if filtro_rem != "TODAS" and "remessa" in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado["remessa"] == filtro_rem]

        total_remessas = df_filtrado["remessa"].nunique() if "remessa" in df_filtrado.columns else 0
        total_itens = len(df_filtrado)
        itens_conferidos = df_filtrado[df_filtrado["conferencia"].notna()]
        total_conferidos = len(itens_conferidos)
        
        itens_sem_erro = df_filtrado[df_filtrado["divergencia"] == 0]
        itens_com_erro = df_filtrado[(df_filtrado["divergencia"].notna()) & (df_filtrado["divergencia"] != 0)]
        
        taxa_acuracia = (len(itens_sem_erro) / total_conferidos * 100) if total_conferidos > 0 else 100.0

        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-card" style="border-top: 3px solid #1d4ed8;">
                <span>Remessas Auditadas</span>
                <strong>{total_remessas}</strong>
            </div>
            <div class="metric-card" style="border-top: 3px solid #64748b;">
                <span>Itens Conferidos</span>
                <strong>{total_conferidos} de {total_itens}</strong>
            </div>
            <div class="metric-card" style="border-top: 3px solid {'#059669' if taxa_acuracia >= 98 else '#dc2626'};">
                <span>Acuracidade Físico x Remessa</span>
                <strong style="color: {'#059669' if taxa_acuracia >= 98 else '#dc2626'};">{taxa_acuracia:.1f}%</strong>
            </div>
            <div class="metric-card" style="border-top: 3px solid {'#dc2626' if len(itens_com_erro) > 0 else '#059669'};">
                <span>Itens com Divergência</span>
                <strong style="color: {'#dc2626' if len(itens_com_erro) > 0 else '#059669'};">{len(itens_com_erro)}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.write("---")

        col_g1, col_g2 = st.columns(2)

        # ----------------- GRÁFICO 1: EVOLUÇÃO MENSAL COM FILTRO DE ANO -----------------
        with col_g1:
            st.markdown("##### 📅 Conferências Realizadas por Mês")
            
            df_conferidos_base = df_filtrado[df_filtrado["conferencia"].notna()].copy()
            anos_disponiveis = sorted(df_conferidos_base["ano"].dropna().unique().tolist(), reverse=True)
            
            if anos_disponiveis:
                ano_atual_str = str(datetime.now().year)
                idx_ano_default = anos_disponiveis.index(ano_atual_str) if ano_atual_str in anos_disponiveis else 0
                
                filtro_ano_graf1 = st.selectbox(
                    "Filtrar Ano do Gráfico:",
                    ["TODOS OS ANOS"] + anos_disponiveis,
                    index=idx_ano_default + 1 if ano_atual_str in anos_disponiveis else 0,
                    key="sel_ano_graf1"
                )
                
                if filtro_ano_graf1 != "TODOS OS ANOS":
                    df_graf_mes_base = df_conferidos_base[df_conferidos_base["ano"] == filtro_ano_graf1]
                else:
                    df_graf_mes_base = df_conferidos_base
            else:
                df_graf_mes_base = df_conferidos_base

            df_mes = (
                df_graf_mes_base.groupby(["ano_mes_sort", "mes_ano"])
                .size()
                .reset_index(name="Qtd")
                .sort_values("ano_mes_sort")
            )

            if not df_mes.empty:
                max_val_mes = float(df_mes["Qtd"].max() * 1.18) if df_mes["Qtd"].max() > 0 else 10.0
                barras_mes = alt.Chart(df_mes).mark_bar(color="#1d4ed8", cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
                    x=alt.X("mes_ano:N", title="Mês/Ano", sort=alt.SortField(field="ano_mes_sort", order="ascending"), axis=alt.Axis(labelAngle=0, labelColor="#64748b", titleColor="#475569")),
                    y=alt.Y("Qtd:Q", title="Qtd. Itens", scale=alt.Scale(domain=[0, max_val_mes]), axis=alt.Axis(labelColor="#64748b", titleColor="#475569"))
                )
                textos_mes = barras_mes.mark_text(
                    align="center",
                    baseline="bottom",
                    dy=-4,
                    fontSize=11,
                    fontWeight=600,
                    color="#0f172a"
                ).encode(
                    text="Qtd:Q"
                )
                chart_mes = (barras_mes + textos_mes).properties(height=260)
                st.altair_chart(chart_mes, use_container_width=True)
            else:
                st.info("Sem dados suficientes para a evolução mensal no filtro selecionado.")

        # ----------------- GRÁFICO 2: VOLUME POR DIA COM FILTRO DE MÊS/ANO -----------------
        with col_g2:
            st.markdown("##### 📊 Volume de Conferência por Dia")
            
            meses_anos_disponiveis = (
                df_conferidos_base[["ano_mes_sort", "mes_ano"]]
                .drop_duplicates()
                .sort_values("ano_mes_sort", ascending=False)
            )

            if not meses_anos_disponiveis.empty:
                lista_opcoes_mes_ano = meses_anos_disponiveis["mes_ano"].tolist()
                mes_ano_atual = datetime.now().strftime("%m/%Y")
                idx_mes_default = lista_opcoes_mes_ano.index(mes_ano_atual) if mes_ano_atual in lista_opcoes_mes_ano else 0

                filtro_mes_ano_dia = st.selectbox(
                    "Filtrar Mês/Ano Específico:",
                    lista_opcoes_mes_ano,
                    index=idx_mes_default,
                    key="sel_mes_ano_graf2"
                )

                df_graf_dia_base = df_conferidos_base[df_conferidos_base["mes_ano"] == filtro_mes_ano_dia]
            else:
                df_graf_dia_base = df_conferidos_base

            df_dia = (
                df_graf_dia_base.groupby(["dt_parsed", "dia_str"])
                .size()
                .reset_index(name="Qtd")
                .sort_values("dt_parsed")
            )

            if not df_dia.empty:
                max_val_dia = float(df_dia["Qtd"].max() * 1.18) if df_dia["Qtd"].max() > 0 else 10.0
                barras_dia = alt.Chart(df_dia).mark_bar(color="#0f172a", cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
                    x=alt.X("dia_str:N", title=f"Data ({filtro_mes_ano_dia if 'filtro_mes_ano_dia' in locals() else 'Período'})", sort=alt.SortField(field="dt_parsed", order="ascending"), axis=alt.Axis(labelAngle=-45, labelColor="#64748b", titleColor="#475569")),
                    y=alt.Y("Qtd:Q", title="Qtd. Itens", scale=alt.Scale(domain=[0, max_val_dia]), axis=alt.Axis(labelColor="#64748b", titleColor="#475569"))
                )
                textos_dia = barras_dia.mark_text(
                    align="center",
                    baseline="bottom",
                    dy=-4,
                    fontSize=11,
                    fontWeight=600,
                    color="#0f172a"
                ).encode(
                    text="Qtd:Q"
                )
                chart_dia = (barras_dia + textos_dia).properties(height=260)
                st.altair_chart(chart_dia, use_container_width=True)
            else:
                st.info("Sem conferências realizadas no Mês/Ano selecionado.")

        st.write("---")
        col_e1, col_e2 = st.columns(2)

        with col_e1:
            st.markdown("##### ⚠️ Diagnóstico Geral de Divergências")
            
            def classificar_erro(div):
                if pd.isna(div):
                    return "Pendente"
                elif div == 0:
                    return "Sem Divergência"
                elif div < 0:
                    return "Falta Física"
                else:
                    return "Sobra Física"

            df_status = df_filtrado.copy()
            df_status["Diagnóstico"] = df_status["divergencia"].apply(classificar_erro)
            df_resumo_erros = df_status["Diagnóstico"].value_counts().reset_index()
            df_resumo_erros.columns = ["Diagnóstico", "Qtd. Itens"]
            df_resumo_erros["Percentual (%)"] = ((df_resumo_erros["Qtd. Itens"] / len(df_status)) * 100).round(1)

            st.dataframe(
                df_resumo_erros,
                column_config={
                    "Diagnóstico": "Diagnóstico",
                    "Qtd. Itens": st.column_config.NumberColumn("Qtd. Itens", format="%d"),
                    "Percentual (%)": st.column_config.NumberColumn("Percentual", format="%.1f%%")
                },
                hide_index=True,
                use_container_width=True
            )

        with col_e2:
            st.markdown("##### 🏷️ Ranking de Produtos com Maior Divergência")
            df_erros_itens = df_filtrado[df_filtrado["divergencia"].fillna(0) != 0].copy()
            
            if not df_erros_itens.empty and "produto" in df_erros_itens.columns:
                df_top_erros = df_erros_itens.groupby(["produto", "descricao"])["divergencia"].count().reset_index(name="Ocorrências")
                df_top_erros = df_top_erros.sort_values("Ocorrências", ascending=False).head(10)
                st.dataframe(
                    df_top_erros,
                    column_config={
                        "produto": "Código",
                        "descricao": "Descrição do Produto",
                        "Ocorrências": st.column_config.NumberColumn("Qtd. Divergências", format="%d")
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.success("🎉 Nenhuma divergência registrada no filtro atual!")

# ==============================================================================
# OPÇÃO: IMPORTAR REMESSA (Aba Conferencia) - COM BLOQUEIO DE DUPLICIDADE
# ==============================================================================
elif menu == "Importar Remessa":
    st.markdown('<div class="main-title">📥 Importação de Remessa</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        num_remessa = st.text_input("Número da Remessa *", placeholder="Ex: 268326")
    with col2:
        nome_local_input = st.text_input("Local / Estoque de Destino *", placeholder="Ex: S.R. EMBALAGENS")

    arquivo_excel = st.file_uploader("Selecione o arquivo da Remessa", type=["xlsx", "xls"])

    if st.button("Processar e Salvar", type="primary"):
        if not num_remessa or not nome_local_input or not arquivo_excel:
            st.error("Preencha todos os campos obrigatórios e anexe o arquivo.")
        else:
            remessa_limpa = str(num_remessa).strip()
            nome_local = str(nome_local_input).strip().upper()

            # --- VALIDAÇÃO CONTRA DUPLICIDADE DE REMESSA ---
            with st.spinner("Verificando se a remessa já existe na base..."):
                df_existente = carregar_dados_planilha()
                remessas_cadastradas = []
                if not df_existente.empty and "remessa" in df_existente.columns:
                    remessas_cadastradas = [
                        str(r).strip() for r in df_existente["remessa"].dropna().unique()
                        if str(r).strip() not in ["", "nan", "None"]
                    ]

            if remessa_limpa in remessas_cadastradas:
                st.error(f"⛔ **Importação Bloqueada:** O número de remessa **{remessa_limpa}** já existe na aba Conferencia. Se precisar reimportá-la, acesse a aba 'Conferir' e exclua a remessa antiga primeiro.")
            else:
                with st.spinner("Processando linhas a partir da coluna 'Produto'..."):
                    itens = extrair_excel(arquivo_excel)

                if not itens:
                    st.warning("Nenhum item válido encontrado no arquivo. Verifique se o cabeçalho possui a coluna 'Produto' ou 'Código'.")
                else:
                    data_importacao = datetime.now().strftime("%d/%m/%Y")
                    
                    linhas_para_sheets = []
                    for item in itens:
                        linhas_para_sheets.append([
                            remessa_limpa,                  # A: Remessa
                            nome_local,                     # B: Estoque
                            data_importacao,                # C: Horario / Data
                            str(item["Produto"]).strip(),   # D: Codigo
                            str(item["Descricao"]).strip(), # E: Descrição
                            float(item["Quantidade"]),      # F: Quantidade
                            "",                             # G: Conferencia
                            "",                             # H: Divergencia
                            "",                             # I: Conferente
                            ""                              # J: Justificativa para Divergencia
                        ])

                    with st.spinner("Gravando linhas na aba Conferencia..."):
                        res = enviar_importacao_planilha(linhas_para_sheets)
                        if res.get("status") == "success":
                            st.success(f"✅ {len(linhas_para_sheets)} itens gravados com sucesso para a remessa **{remessa_limpa}** (Estoque: **{nome_local}**)!")
                            df_preview = pd.DataFrame(itens)
                            st.dataframe(df_preview, use_container_width=True)
                        else:
                            st.error(f"Erro: {res.get('message', 'Falha ao processar requisição')}")

# ==============================================================================
# OPÇÃO: FOLHA DE IMPRESSÃO CEGA (ECONÔMICA)
# ==============================================================================
elif menu == "Folha de Impressão Cega":
    st.markdown('<div class="main-title">🖨️ Folha de Separação / Contagem Cega</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Gere a folha física com formato compacto para economia de papel.</div>', unsafe_allow_html=True)

    with st.spinner("Consultando dados..."):
        df = carregar_dados_planilha()

    if df.empty:
        st.info("Nenhuma remessa encontrada na aba Conferencia.")
    else:
        remessas_disponiveis = [
            str(r).strip() for r in df["remessa"].dropna().unique().tolist()
            if str(r).strip() not in ["", "nan", "None"]
        ]
        remessa_selecionada = st.selectbox("Selecione a Remessa para Gerar a Impressão:", [""] + remessas_disponiveis)

        if remessa_selecionada:
            remessa_busca = str(remessa_selecionada).strip()
            dados_remessa = df[df["remessa"].astype(str).str.strip() == remessa_busca].copy()

            if dados_remessa.empty:
                st.warning("Nenhum item localizado para a remessa selecionada.")
            else:
                data_cad = formatar_data_br(dados_remessa["data_importacao"].iloc[0])
                local_cad = str(dados_remessa["local"].iloc[0]).upper()

                linhas_tabela = ""
                for _, row in dados_remessa.iterrows():
                    cod_item = str(row.get('produto', ''))
                    desc_item = str(row.get('descricao', ''))
                    linhas_tabela += (
                        "<tr>"
                        f"<td style='border: 1px solid #94a3b8; padding: 4px 6px; font-weight: 700; font-size: 9.5px; color: #0f172a;'>{cod_item}</td>"
                        f"<td style='border: 1px solid #94a3b8; padding: 4px 6px; font-size: 9.5px; line-height: 1.2; color: #334155;'>{desc_item}</td>"
                        "<td style='border: 1px solid #94a3b8; padding: 4px 6px; height: 22px;'></td>"
                        "</tr>"
                    )

                documento_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            color: #0f172a;
            margin: 0;
            padding: 4px;
            background-color: #ffffff;
        }}
        .header-box {{
            border-bottom: 2px solid #1d4ed8;
            padding-bottom: 6px;
            margin-bottom: 8px;
        }}
        .header-title {{
            font-size: 13.5px;
            font-weight: 800;
            margin: 0 0 3px 0;
            color: #1d4ed8;
            letter-spacing: 0.2px;
            text-transform: uppercase;
        }}
        .header-meta {{
            display: flex;
            gap: 16px;
            font-size: 10px;
            color: #475569;
            font-weight: 600;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 6px;
        }}
        th {{
            border: 1px solid #1d4ed8;
            background-color: #eff6ff;
            padding: 5px 6px;
            font-size: 10px;
            text-align: left;
            font-weight: 700;
            color: #1e40af;
        }}
        .signature-box {{
            margin-top: 24px;
            display: flex;
            justify-content: space-between;
            font-size: 9.5px;
            color: #475569;
            padding-top: 4px;
        }}
        .btn-imprimir {{
            background: #1d4ed8;
            color: white;
            border: none;
            padding: 7px 16px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 5px;
            cursor: pointer;
            margin-bottom: 8px;
            box-shadow: 0 2px 6px rgba(29, 78, 216, 0.3);
            transition: all 0.15s ease;
        }}
        .btn-imprimir:hover {{
            background: #1e40af;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.35);
        }}
        @media print {{
            .btn-imprimir {{
                display: none !important;
            }}
            body {{
                padding: 0;
            }}
            @page {{
                margin: 6mm;
            }}
        }}
    </style>
</head>
<body>
    <button class="btn-imprimir" onclick="window.print()">🖨️ Imprimir Folha Econômica</button>

    <div class="header-box">
        <div class="header-title">FOLHA DE CONFERÊNCIA FÍSICA (CONTAGEM CEGA)</div>
        <div class="header-meta">
            <div>REMESSA: <strong>{remessa_selecionada}</strong></div>
            <div>LOCAL: <strong>{local_cad}</strong></div>
            <div>DATA: <strong>{data_cad}</strong></div>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th style="width: 18%;">CÓDIGO</th>
                <th style="width: 62%;">DESCRIÇÃO DO PRODUTO</th>
                <th style="width: 20%; text-align: center;">QTD. CONFERIDA</th>
            </tr>
        </thead>
        <tbody>
            {linhas_tabela}
        </tbody>
    </table>

    <div class="signature-box">
        <div>Assinatura do Conferente: _____________________________________</div>
        <div>Data da Conferência: ____/____/________</div>
    </div>
</body>
</html>"""

                altura_calculada = max(360, 100 + (len(dados_remessa) * 26))
                components.html(documento_html, height=altura_calculada, scrolling=True)

# ==============================================================================
# OPÇÃO: DIGITAR CONFERÊNCIA CEGA & EXCLUSÃO DIRETA DA REMESSA
# ==============================================================================
elif menu == "Digitar Conferência Cega":
    st.markdown('<div class="main-title">🔍 Digitação de Conferência Cega e Validação</div>', unsafe_allow_html=True)

    with st.spinner("Buscando registros..."):
        df = carregar_dados_planilha()

    if df.empty:
        st.info("Nenhuma remessa encontrada para conferência.")
    else:
        remessas = [
            str(r).strip() for r in df["remessa"].dropna().unique().tolist()
            if str(r).strip() not in ["", "nan", "None"]
        ]

        # Estado para controlar o modal de confirmação de exclusão
        if "mostrar_confirmacao_excluir" not in st.session_state:
            st.session_state.mostrar_confirmacao_excluir = False

        col_pesquisa, col_btn_del = st.columns([3.5, 1.5], vertical_alignment="bottom")

        with col_pesquisa:
            remessa_pesquisa = st.selectbox(
                "Pesquisar pelo Número da Remessa:",
                [""] + remessas,
                key="sel_remessa_conferencia"
            )

        with col_btn_del:
            if remessa_pesquisa:
                st.markdown('<div class="danger-btn">', unsafe_allow_html=True)
                if st.button("🗑️ Excluir Remessa", key="btn_abrir_excluir", use_container_width=True):
                    st.session_state.mostrar_confirmacao_excluir = not st.session_state.mostrar_confirmacao_excluir
                st.markdown('</div>', unsafe_allow_html=True)

        # PAINEL DE CONFIRMAÇÃO DE EXCLUSÃO DA REMESSA
        if remessa_pesquisa and st.session_state.mostrar_confirmacao_excluir:
            remessa_alvo_del = str(remessa_pesquisa).strip()
            total_linhas_del = len(df[df["remessa"].astype(str).str.strip() == remessa_alvo_del])

            st.markdown(f"""
            <div class="danger-box">
                <strong style="color: #991b1b; font-size: 12px;">⚠️ EXCLUIR TODA A REMESSA {remessa_alvo_del}</strong><br>
                <span style="color: #7f1d1d;">
                    Esta ação apagará <strong>todos os {total_linhas_del} itens</strong> desta remessa permanentemente da aba <strong>Conferencia</strong>.
                </span>
            </div>
            """, unsafe_allow_html=True)

            c_conf, c_btn1, c_btn2 = st.columns([2.5, 1.2, 1], vertical_alignment="center")
            with c_conf:
                chk_autoriza = st.checkbox(f"Confirmar exclusão definitiva da remessa {remessa_alvo_del}", key="chk_del_def")
            with c_btn1:
                st.markdown('<div class="danger-btn">', unsafe_allow_html=True)
                if st.button("Confirmar Exclusão", key="btn_confirmar_del_final", use_container_width=True):
                    if not chk_autoriza:
                        st.error("Marque a caixa de confirmação primeiro.")
                    else:
                        with st.spinner(f"Excluindo remessa {remessa_alvo_del}..."):
                            res_del = enviar_exclusao_remessa(remessa_alvo_del)
                            if res_del.get("status") == "success":
                                st.session_state.mostrar_confirmacao_excluir = False
                                carregar_dados_planilha_cached.clear()
                                st.success(f"✅ Remessa {remessa_alvo_del} excluída com sucesso!")
                                st.rerun()
                            else:
                                st.error(f"Erro: {res_del.get('message', 'Falha na API')}")
                st.markdown('</div>', unsafe_allow_html=True)
            with c_btn2:
                if st.button("Cancelar", key="btn_cancela_del", use_container_width=True):
                    st.session_state.mostrar_confirmacao_excluir = False
                    st.rerun()

        if remessa_pesquisa:
            remessa_alvo = str(remessa_pesquisa).strip()
            itens_remessa = df[df["remessa"].astype(str).str.strip() == remessa_alvo].copy()

            if itens_remessa.empty:
                st.warning("Nenhum item localizado para a remessa selecionada.")
            else:
                local_atual = str(itens_remessa["local"].iloc[0]).upper()
                data_atual_br = formatar_data_br(itens_remessa["data_importacao"].iloc[0])

                itens_remessa["quantidade"] = pd.to_numeric(itens_remessa["quantidade"], errors="coerce").fillna(0.0)
                itens_remessa["conferencia"] = pd.to_numeric(itens_remessa["conferencia"], errors="coerce")
                itens_remessa["divergencia"] = pd.to_numeric(itens_remessa["divergencia"], errors="coerce")

                ja_conferida = itens_remessa["conferencia"].notna().any()
                itens_divergentes = itens_remessa[itens_remessa["divergencia"].fillna(1) != 0].copy()

                if ja_conferida and len(itens_divergentes) > 0:
                    modo_reconferencia = True
                    dados_trabalho = itens_divergentes.copy()
                    st.warning(f"⚠️ **Segunda Conferência (Apenas Divergências):** Foram identificados **{len(itens_divergentes)} item(ns)** divergentes. Reconte apenas os itens listados abaixo.")
                elif ja_conferida and len(itens_divergentes) == 0:
                    modo_reconferencia = False
                    dados_trabalho = itens_remessa.copy()
                    st.success("✨ **Remessa 100% Conferida e Sem Divergências!** Todos os itens foram validados com sucesso.")
                else:
                    modo_reconferencia = False
                    dados_trabalho = itens_remessa.copy()
                    st.info("📋 **Primeira Conferência (Contagem Cega):** Digite a quantidade física contada para cada produto.")

                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-card" style="border-top: 3px solid #1d4ed8;">
                        <span>Remessa</span>
                        <strong>{remessa_alvo}</strong>
                    </div>
                    <div class="metric-card" style="border-top: 3px solid #64748b;">
                        <span>Local / Depósito</span>
                        <strong>{local_atual}</strong>
                    </div>
                    <div class="metric-card" style="border-top: 3px solid #64748b;">
                        <span>Data de Importação</span>
                        <strong>{data_atual_br}</strong>
                    </div>
                    <div class="metric-card" style="border-top: 3px solid #0f172a;">
                        <span>Itens a Conferir</span>
                        <strong>{len(dados_trabalho)}</strong>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                lista_conferentes = carregar_lista_conferentes()
                conferente_anterior = ""
                if "conferente" in dados_trabalho.columns and dados_trabalho["conferente"].dropna().any():
                    conferente_anterior = str(dados_trabalho["conferente"].dropna().iloc[0]).strip().upper()

                if not lista_conferentes:
                    st.warning("⚠️ Nenhum conferente localizado na coluna D da aba 'Local-Estoque'.")
                    nome_conferente_final = ""
                else:
                    idx_default = 0
                    if conferente_anterior in lista_conferentes:
                        idx_default = lista_conferentes.index(conferente_anterior) + 1
                    
                    nome_conferente_sel = st.selectbox(
                        "Selecione o Conferente Responsável *",
                        ["-- Selecione o conferente --"] + lista_conferentes,
                        index=idx_default
                    )
                    nome_conferente_final = "" if nome_conferente_sel == "-- Selecione o conferente --" else nome_conferente_sel

                dados_trabalho["conferencia"] = dados_trabalho["conferencia"].fillna(0.0)
                df_editavel = dados_trabalho[["row_index", "produto", "descricao", "conferencia"]].copy()

                st.markdown("""
                <div class="keyboard-hint">
                    <span style="font-size: 13px; color: #1d4ed8; font-weight: 800; line-height: 1;">⇊</span>
                    <span><strong>Agilidade de Digitação:</strong> Digite o valor e aperte <kbd>Enter</kbd> para salvar e descer direto para o próximo produto.</span>
                </div>
                """, unsafe_allow_html=True)

                injetar_atalho_teclado_tab()

                editado = st.data_editor(
                    df_editavel,
                    column_config={
                        "row_index": None,
                        "produto": st.column_config.TextColumn("Código", disabled=True),
                        "descricao": st.column_config.TextColumn("Descrição", disabled=True),
                        "conferencia": st.column_config.NumberColumn(
                            "Conferência (Físico)",
                            min_value=0.0,
                            step=1.0,
                            format="%.2f",
                            required=True
                        ),
                    },
                    use_container_width=True,
                    hide_index=True,
                    key=f"editor_conferencia_{remessa_alvo}_{modo_reconferencia}"
                )

                mapa_esperado = dados_trabalho.set_index("row_index")["quantidade"].to_dict()
                itens_com_divergencia_detectada = []

                for _, row in editado.iterrows():
                    r_id = int(row["row_index"])
                    conf_val = float(row["conferencia"])
                    qtd_esp = mapa_esperado.get(r_id, 0.0)
                    if conf_val - qtd_esp != 0:
                        itens_com_divergencia_detectada.append({
                            "row_index": r_id,
                            "produto": str(row["produto"]),
                            "descricao": str(row["descricao"]),
                            "conferido": conf_val,
                            "divergencia": conf_val - qtd_esp
                        })

                st.write("---")
                autorizar_divergencia = st.checkbox("⚠️ Autorizar encerramento/finalização da conferência com divergência")
                justificativas_itens = {}

                if autorizar_divergencia:
                    if len(itens_com_divergencia_detectada) == 0:
                        st.info("✨ Não há itens divergentes no momento. Ao salvar, todos os itens constarão como conferidos sem divergência.")
                    else:
                        st.markdown("""
                        <div class="divergence-box">
                            <strong style="color: #92400e;">📝 Justificativa Individual por Item Divergente</strong><br>
                            <span style="font-size: 11px; color: #78350f;">
                                Informe a justificativa específica para cada produto que apresentou divergência. Ela será gravada na linha exata do produto (Coluna J).
                            </span>
                        </div>
                        """, unsafe_allow_html=True)

                        for item_div in itens_com_divergencia_detectada:
                            r_id = item_div["row_index"]
                            label_item = f"Produto: {item_div['produto']} - {item_div['descricao']} (Qtd Físico: {item_div['conferido']:.2f})"
                            
                            obs_anterior = ""
                            if "observacao" in dados_trabalho.columns:
                                linha_orig = dados_trabalho[dados_trabalho["row_index"] == r_id]
                                if not linha_orig.empty and pd.notna(linha_orig["observacao"].iloc[0]):
                                    obs_anterior = str(linha_orig["observacao"].iloc[0]).strip()

                            justificativas_itens[r_id] = st.text_input(
                                f"Justificativa para {label_item} *",
                                value=obs_anterior,
                                placeholder="Ex: Mercadoria avariada / Sobra de lote / Falta confirmada no fornecedor",
                                key=f"justificativa_item_{r_id}"
                            )

                if st.button("⚖️ Comparar e Gravar", type="primary"):
                    if not nome_conferente_final:
                        st.error("⚠️ Selecione o **Nome do Conferente** na lista antes de gravar.")
                    else:
                        justificativas_pendentes = False
                        if autorizar_divergencia:
                            for it in itens_com_divergencia_detectada:
                                r_id = it["row_index"]
                                if not str(justificativas_itens.get(r_id, "")).strip():
                                    justificativas_pendentes = True
                                    break

                        if autorizar_divergencia and justificativas_pendentes:
                            st.error("⚠️ Você optou por autorizar a divergência. É **obrigatório** preencher a justificativa para todos os produtos divergentes listados acima.")
                        else:
                            with st.spinner("Gravando conferência na aba Conferencia..."):
                                itens_atualizar = []
                                resultados_exibicao = []

                                for _, row in editado.iterrows():
                                    r_id = int(row["row_index"])
                                    conf_val = float(row["conferencia"])
                                    qtd_esp = mapa_esperado.get(r_id, 0.0)
                                    div_val = conf_val - qtd_esp

                                    obs_do_item = ""
                                    if div_val != 0 and autorizar_divergencia:
                                        obs_do_item = str(justificativas_itens.get(r_id, "")).strip().upper()

                                    itens_atualizar.append({
                                        "row_index": r_id,
                                        "conferencia": conf_val,
                                        "divergencia": div_val,
                                        "conferente": nome_conferente_final,
                                        "observacao": obs_do_item
                                    })

                                    status = "Correto (Sem Divergência)" if div_val == 0 else "Divergente"
                                    resultados_exibicao.append({
                                        "produto": row["produto"],
                                        "descricao": row["descricao"],
                                        "conferencia": conf_val,
                                        "conferente": nome_conferente_final,
                                        "status": status,
                                        "justificativa": obs_do_item,
                                        "_tem_erro": (div_val != 0)
                                    })

                                res = enviar_atualizacao_conferencia(itens_atualizar)

                                if res.get("status") == "success":
                                    msg_sucesso = f"✅ Dados gravados com sucesso! Conferente: **{nome_conferente_final}**."
                                    if autorizar_divergencia and len(itens_com_divergencia_detectada) > 0:
                                        msg_sucesso += " Justificativas lançadas na linha de cada produto divergente (Coluna J)."
                                    st.success(msg_sucesso)
                                    
                                    df_resultado = pd.DataFrame(resultados_exibicao)
                                    
                                    # Formatação de Contraste no Styler
                                    def colorir_status(val):
                                        if "Divergente" in str(val):
                                            return "background-color: #fef2f2; color: #991b1b; font-weight: 700; border: 1px solid #fecaca;"
                                        else:
                                            return "background-color: #ecfdf5; color: #065f46; font-weight: 600; border: 1px solid #a7f3d0;"

                                    st.write("### 📊 Resultado da Conferência")
                                    
                                    colunas_tabela = ["produto", "descricao", "conferencia", "conferente", "status"]
                                    if autorizar_divergencia:
                                        colunas_tabela.append("justificativa")

                                    df_mostrar = df_resultado[colunas_tabela]
                                    styler_res = df_mostrar.style
                                    if hasattr(styler_res, "map"):
                                        styler_res = styler_res.map(colorir_status, subset=["status"])
                                    else:
                                        styler_res = styler_res.applymap(colorir_status, subset=["status"])

                                    st.dataframe(
                                        styler_res,
                                        column_config={
                                            "produto": "Código",
                                            "descricao": "Descrição",
                                            "conferencia": st.column_config.NumberColumn("Qtd. Conferida", format="%.2f"),
                                            "conferente": "Conferente",
                                            "status": "Situação da Contagem",
                                            "justificativa": "Justificativa (Coluna J)"
                                        },
                                        use_container_width=True
                                    )

                                    total_erros = df_resultado["_tem_erro"].sum()
                                    if total_erros == 0:
                                        st.balloons()
                                        st.success("🎉 **Perfeito!** Todos os itens batem com a remessa.")
                                    else:
                                        if autorizar_divergencia:
                                            st.info("ℹ️ **Conferência Finalizada com Justificativa:** As pendências foram autorizadas e registradas nos itens específicos.")
                                        else:
                                            st.warning(f"⚠️ **Atenção:** Existem **{total_erros} item(ns) divergente(s)**. Busque a remessa novamente para realizar a segunda conferência ou marque a opção de autorizar a divergência com justificativa item a item.")
                                else:
                                    mensagem_erro = res.get("message", "Falha na comunicação com a planilha")
                                    st.error(f"Erro ao salvar: {mensagem_erro}")

# ==============================================================================
# OPÇÃO: CADASTRAR NOVO CONFERENTE (Aba Local-Estoque - Coluna D)
# ==============================================================================
elif menu == "Cadastrar Novo Conferente":
    st.markdown('<div class="main-title">👤 Cadastro de Conferente</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Os conferentes são lidos e gravados na Coluna D da aba <strong>Local-Estoque</strong>.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        novo_conferente = st.text_input("Nome Completo do Conferente *", placeholder="Ex: JOÃO SILVA")
        if st.button("Cadastrar Conferente", type="primary"):
            if not novo_conferente.strip():
                st.error("Informe o nome do conferente para realizar o cadastro.")
            else:
                nome_formatado = novo_conferente.strip().upper()
                with st.spinner("Salvando novo conferente..."):
                    res = enviar_cadastro_conferente(nome_formatado)
                    if res.get("status") == "success":
                        st.success(f"✅ Conferente **{nome_formatado}** cadastrado com sucesso!")
                        st.balloons()
                    else:
                        mensagem_erro = res.get("message", "Falha de comunicação")
                        st.error(f"Erro ao cadastrar: {mensagem_erro}")

    st.write("---")
    st.write("#### 👥 Conferentes Atualmente Cadastrados:")
    conferentes_atuais = carregar_lista_conferentes()
    if conferentes_atuais:
        df_conf = pd.DataFrame(conferentes_atuais, columns=["Nome do Conferente"])
        st.dataframe(df_conf, use_container_width=True)
    else:
        st.info("Nenhum conferente localizado até o momento.")