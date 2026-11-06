# -*- coding: utf-8 -*-
from datetime import datetime
import io
import json
import os
import urllib.request
import pandas as pd
import plotly.express as px
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Dashboard Executivo SAC - Master Café",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CONFIGURAÇÃO CENTRALIZADA DA PLANILHA E WEBHOOK ---
SHEET_BASE_ID = "1YUS9AwQti0Gl79X-TGCIqZSkOfF0bE0BX5gyDClo3rc"
GID_CHAMADOS = "0"
GID_CLIENTES = "1332839106"
GID_DADOS = "1815476457"
GID_USUARIOS = "437161325"
WEBHOOK_URL_DEFAULT = "https://script.google.com/macros/s/AKfycbyGRxQBo5j-gWQ4OEeGFqfwzgjcfQRzDKE2kKbyQeSvOKOdIMr1snR8YV766KBfE7RY9w/exec"

# --- CSS POWER BI EXECUTIVE THEME + COMPACT FORM ---
st.markdown(
    """
<style>
    .main { 
        background-color: #0f172a; 
        color: #f8fafc; 
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
    }
    
    /* Header Card Power BI Style */
    .header-card {
        background: linear-gradient(90deg, #1e293b 0%, #0f172a 100%);
        padding: 16px 20px;
        border-radius: 8px;
        border: 1px solid #334155;
        border-left: 6px solid #0284c7;
        margin-bottom: 14px;
    }
    .header-title {
        color: #ffffff !important;
        font-weight: 700;
        font-size: 1.65rem;
        margin-bottom: 2px;
        letter-spacing: -0.5px;
    }
    .header-subtitle {
        color: #94a3b8 !important;
        font-size: 0.90rem;
        font-weight: 400;
    }

    /* Cards de KPI no padrão Power BI Card Visual */
    .stMetric { 
        background-color: #1e293b !important; 
        padding: 16px !important; 
        border-radius: 8px !important; 
        border: 1px solid #334155 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    div[data-testid="stMetricValue"] { 
        color: #38bdf8 !important; 
        font-weight: 700 !important; 
        font-size: 1.8rem !important; 
        font-family: 'Segoe UI', sans-serif !important;
    }
    div[data-testid="stMetricLabel"], 
    div[data-testid="stMetricLabel"] > label,
    div[data-testid="stMetricLabel"] p { 
        color: #94a3b8 !important; 
        font-size: 0.80rem !important; 
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Cards de Insights */
    .insight-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.15);
    }

    /* Estilos compactos para formulário do SAC */
    .compact-section-title {
        font-size: 0.88rem;
        font-weight: 700;
        color: #38bdf8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 6px;
        margin-bottom: 4px;
        border-bottom: 1px solid #334155;
        padding-bottom: 2px;
    }

    div[data-testid="stVerticalBlock"] > div.element-container {
        margin-bottom: -4px !important;
    }
    div[data-testid="stForm"] {
        border: 1px solid #334155 !important;
        background-color: #111827 !important;
        border-radius: 8px !important;
        padding: 16px 20px !important;
    }
    div[data-testid="stTextInput"] label, 
    div[data-testid="stSelectbox"] label, 
    div[data-testid="stDateInput"] label {
        font-size: 0.80rem !important;
        font-weight: 600 !important;
        color: #cbd5e1 !important;
        margin-bottom: -2px !important;
    }
    div[data-baseweb="input"] > div, 
    div[data-baseweb="select"] > div {
        min-height: 36px !important;
        height: 36px !important;
        padding-top: 0px !important;
        padding-bottom: 0px !important;
    }
</style>
""",
    unsafe_allow_html=True,
)


# --- FUNÇÃO DE ESTILIZAÇÃO POWER BI PARA PLOTLY ---
def apply_powerbi_theme(fig, title="", height=320):
    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>" if title else "",
            font=dict(family="Segoe UI, Roboto, sans-serif", size=13, color="#cbd5e1"),
            x=0.01,
            y=0.96,
        ),
        paper_bgcolor="#1e293b",
        plot_bgcolor="#1e293b",
        font=dict(family="Segoe UI, Roboto, sans-serif", size=11, color="#94a3b8"),
        margin=dict(l=20, r=20, t=45 if title else 25, b=25),
        height=height,
        hoverlabel=dict(
            bgcolor="#0f172a",
            font_size=12,
            font_family="Segoe UI",
            font_color="#ffffff",
            bordercolor="#334155",
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor="#334155",
            gridwidth=1,
            griddash="dot",
            linecolor="#334155",
            tickfont=dict(color="#94a3b8", size=10),
            title_font=dict(color="#cbd5e1", size=11),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#334155",
            gridwidth=1,
            griddash="dot",
            linecolor="#334155",
            tickfont=dict(color="#94a3b8", size=10),
            title_font=dict(color="#cbd5e1", size=11),
        ),
    )
    fig.update_traces(
        textposition="outside",
        cliponaxis=False,
        textfont=dict(color="#f8fafc", size=10, family="Segoe UI"),
    )
    return fig


# --- CANVAS COM NUMERAÇÃO DE PÁGINAS PARA REPORTLAB ---
class NumberedCanvas(canvas.Canvas):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawString(
            36, 22, "Master Café SAC — Relatório Gerencial e Operacional Completo"
        )
        self.drawRightString(
            576, 22, f"Página {self._pageNumber} de {page_count}"
        )
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(36, 34, 576, 34)
        self.restoreState()


# --- GERADOR DE RELATÓRIO PDF COMPLETO ---
def generate_full_pdf_report(
    df_filtered,
    tot_chamados,
    tot_reembolso,
    top_cli,
    top_falha,
    active_filters,
):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=45,
    )
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        name="DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        name="DocSubtitle",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#64748b"),
        leading=13,
    )
    section_style = ParagraphStyle(
        name="SectionTitle",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0284c7"),
        spaceBefore=10,
        spaceAfter=6,
    )
    table_cell = ParagraphStyle(
        name="TableCell",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1e293b"),
    )
    table_header = ParagraphStyle(
        name="TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.whitesmoke,
    )

    # 1. Cabeçalho Principal
    elements.append(
        Paragraph("☕ Master Café — Relatório Executivo do SAC", title_style)
    )
    dt_now = datetime.now().strftime("%d/%m/%Y às %H:%M")
    elements.append(
        Paragraph(
            f"Relatório Consolidado de Gestão da Qualidade, Atendimento e Reembolsos • Gerado em: <b>{dt_now}</b>",
            subtitle_style,
        )
    )
    elements.append(Spacer(1, 8))
    elements.append(
        HRFlowable(
            width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=10
        )
    )

    # 2. Quadro de Filtros Ativos
    filtros_txt = "<b>Escopo do Relatório:</b> Base Geral Consolidada"
    t_filtros = Table(
        [[Paragraph(filtros_txt, table_cell)]],
        colWidths=[540],
    )
    t_filtros.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    elements.append(t_filtros)
    elements.append(Spacer(1, 10))

    # 3. Cartões de KPIs Principais
    elements.append(
        Paragraph("1. Principais Indicadores de Desempenho (KPIs)", section_style)
    )
    reembolso_str = (
        f"R$ {tot_reembolso:,.2f}".replace(",", "v")
        .replace(".", ",")
        .replace("v", ".")
    )
    tkt_medio = (tot_reembolso / tot_chamados) if tot_chamados > 0 else 0
    tkt_medio_str = (
        f"R$ {tkt_medio:,.2f}".replace(",", "v")
        .replace(".", ",")
        .replace("v", ".")
    )

    kpi_card_data = [
        [
            Paragraph("<b>TOTAL DE CHAMADOS</b>", subtitle_style),
            Paragraph("<b>TOTAL REEMBOLSADO</b>", subtitle_style),
            Paragraph("<b>TICKET MÉDIO REEMBOLSO</b>", subtitle_style),
            Paragraph("<b>PRINCIPAL CLIENTE</b>", subtitle_style),
        ],
        [
            Paragraph(
                f"<font size=13 color='#0284c7'><b>{tot_chamados:,}</b></font>".replace(
                    ",", "."
                ),
                styles["Normal"],
            ),
            Paragraph(
                f"<font size=13 color='#10b981'><b>{reembolso_str}</b></font>",
                styles["Normal"],
            ),
            Paragraph(
                f"<font size=12 color='#f59e0b'><b>{tkt_medio_str}</b></font>",
                styles["Normal"],
            ),
            Paragraph(
                f"<font size=9><b>{str(top_cli)[:25]}</b></font>",
                styles["Normal"],
            ),
        ],
    ]
    t_kpis = Table(kpi_card_data, colWidths=[135, 140, 135, 130])
    t_kpis.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    elements.append(t_kpis)
    elements.append(Spacer(1, 12))

    # 4. Tabela Mensal Consolidada
    elements.append(
        Paragraph("2. Demonstrativo Mensal Consolidado", section_style)
    )
    months_valid = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]
    summary_mes = (
        df_filtered.groupby("Mês_Clean")
        .agg(Chamados=("Valor", "count"), Reembolso=("Valor", "sum"))
        .reindex(months_valid)
        .dropna(how="all")
        .reset_index()
    )

    t_mes_data = [[
        Paragraph("Mês de Referência", table_header),
        Paragraph("Chamados", table_header),
        Paragraph("Reembolso Total (R$)", table_header),
        Paragraph("Ticket Médio (R$)", table_header),
    ]]
    for _, row in summary_mes.iterrows():
        val_f = (
            f"R$ {row['Reembolso']:,.2f}".replace(",", "v")
            .replace(".", ",")
            .replace("v", ".")
        )
        tkt = (row["Reembolso"] / row["Chamados"]) if row["Chamados"] > 0 else 0
        tkt_f = (
            f"R$ {tkt:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
        )
        t_mes_data.append([
            Paragraph(str(row["Mês_Clean"]), table_cell),
            Paragraph(
                f"{int(row['Chamados']):,}".replace(",", "."), table_cell
            ),
            Paragraph(val_f, table_cell),
            Paragraph(tkt_f, table_cell),
        ])

    t_mes_tab = Table(t_mes_data, colWidths=[150, 110, 150, 130])
    t_mes_tab.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#f8fafc")],
                ),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("PADDING", (0, 0), (-1, -1), 4.5),
            ]
        )
    )
    elements.append(t_mes_tab)
    elements.append(Spacer(1, 14))

    doc.build(elements, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()


# --- CARREGAMENTO DE DADOS AUXILIARES (CLIENTES, DADOS/APOIO E USUÁRIOS) ---
@st.cache_data(ttl=600)
def load_auxiliary_data():
    """Carrega dados das abas Clientes, Dados e Usuarios com os novos GIDs."""
    # 1. Clientes (gid=1332839106): Coluna A: Cliente, B: Local Interno, F: Cidade
    url_clientes = f"https://docs.google.com/spreadsheets/d/{SHEET_BASE_ID}/export?format=csv&gid={GID_CLIENTES}"
    try:
        df_raw_cli = pd.read_csv(url_clientes)
        df_clientes = pd.DataFrame()
        df_clientes["Cliente"] = df_raw_cli.iloc[:, 0].dropna().astype(str).str.strip()
        df_clientes["Local Interno"] = df_raw_cli.iloc[:, 1].fillna("").astype(str).str.strip() if df_raw_cli.shape[1] > 1 else ""
        df_clientes["Cidade"] = df_raw_cli.iloc[:, 5].fillna("").astype(str).str.strip() if df_raw_cli.shape[1] > 5 else ""
        df_clientes = df_clientes[df_clientes["Cliente"] != ""]
    except Exception:
        df_clientes = pd.DataFrame(columns=["Cliente", "Local Interno", "Cidade"])

    # 2. Dados / Apoio (gid=1815476457): Coluna A: Forma de Pagamento, L (índice 11): Problemas, N (índice 13): Descrição
    url_dados = f"https://docs.google.com/spreadsheets/d/{SHEET_BASE_ID}/export?format=csv&gid={GID_DADOS}"
    try:
        df_apoio = pd.read_csv(url_dados, header=None)
        formas_pagamento = [str(x).strip() for x in df_apoio.iloc[:, 0].dropna().unique() if str(x).strip() and str(x).strip().lower() != "nan"] if df_apoio.shape[1] > 0 else []
        problemas_list = [str(x).strip() for x in df_apoio.iloc[:, 11].dropna().unique() if str(x).strip() and str(x).strip().lower() != "nan"] if df_apoio.shape[1] > 11 else []
        descricao_list = [str(x).strip() for x in df_apoio.iloc[:, 13].dropna().unique() if str(x).strip() and str(x).strip().lower() != "nan"] if df_apoio.shape[1] > 13 else []
    except Exception:
        formas_pagamento, problemas_list, descricao_list = [], [], []

    # 3. Usuários (gid=437161325): Coluna A: Usuario, Coluna B: Senha
    url_usuarios = f"https://docs.google.com/spreadsheets/d/{SHEET_BASE_ID}/export?format=csv&gid={GID_USUARIOS}"
    try:
        df_usuarios = pd.read_csv(url_usuarios, header=None)
        df_usuarios.columns = ["Usuario", "Senha"] + list(df_usuarios.columns[2:])
        usuarios_dict = dict(zip(df_usuarios["Usuario"].astype(str).str.strip(), df_usuarios["Senha"].astype(str).str.strip()))
    except Exception:
        usuarios_dict = {}

    return df_clientes, formas_pagamento, problemas_list, descricao_list, usuarios_dict


# --- CARREGAMENTO E PARSER UNIVERSAL DE DATA DO DASHBOARD (ABA CHAMADOS) ---
@st.cache_data(ttl=600)
def load_data():
    # Aba Chamados: gid=0
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_BASE_ID}/export?format=csv&gid={GID_CHAMADOS}"

    try:
        df = pd.read_csv(url)
    except Exception as e:
        st.error(f"Erro ao carregar dados da aba Chamados: {e}")
        df = pd.DataFrame()

    def parse_smart_date(val):
        if pd.isna(val):
            return None
        val_str = str(val).strip()
        if not val_str or val_str.lower() in ["nan", "none", "nat", ""]:
            return None

        try:
            val_num = float(val_str)
            if 35000 <= val_num <= 65000:
                return pd.to_datetime(val_num, unit="D", origin="1899-12-30").date()
        except (ValueError, TypeError):
            pass

        data_pura = val_str.split(" ")[0].split("T")[0].strip()

        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%Y"):
            try:
                return datetime.strptime(data_pura, fmt).date()
            except ValueError:
                continue

        try:
            dt = pd.to_datetime(data_pura, dayfirst=True, errors="coerce")
            if pd.notna(dt):
                return dt.date()
        except Exception:
            pass

        return None

    if "Data" in df.columns:
        df["Data_Date"] = df["Data"].apply(parse_smart_date)
        df["Data_Str"] = df["Data_Date"].apply(
            lambda d: d.strftime("%d/%m/%Y") if pd.notna(d) and d is not None else ""
        )
        df["Ano"] = df["Data_Date"].apply(
            lambda d: str(d.year) if pd.notna(d) and d is not None else "Não informado"
        )
    else:
        df["Data_Date"] = None
        df["Data_Str"] = ""
        df["Ano"] = "Não informado"

    month_map = {
        "Janeiro": "Janeiro", "janeiro": "Janeiro",
        "Fevereiro": "Fevereiro", "Março": "Março",
        "Abril": "Abril", "Maio": "Maio", "Junho": "Junho",
        "Julho": "Julho", "Agosto": "Agosto",
        "Setembro": "Setembro", "setembro": "Setembro",
        "Outubro": "Outubro", "Novembro": "Novembro", "Dezembro": "Dezembro",
    }

    if "Mês" in df.columns:
        df["Mês_Clean"] = (
            df["Mês"]
            .fillna("")
            .astype(str)
            .str.capitalize()
            .str.strip()
            .map(month_map)
        )
    else:
        df["Mês_Clean"] = "Não informado"

    if "$" in df.columns:
        df["Valor"] = pd.to_numeric(
            df["$"]
            .astype(str)
            .str.replace("R$", "", regex=False)
            .str.replace(",", ".")
            .str.strip(),
            errors="coerce",
        ).fillna(0)
    elif "Valor" in df.columns:
        df["Valor"] = pd.to_numeric(
            df["Valor"]
            .astype(str)
            .str.replace("R$", "", regex=False)
            .str.replace(",", ".")
            .str.strip(),
            errors="coerce",
        ).fillna(0)
    else:
        df["Valor"] = 0.0

    df["Cliente"] = (
        df["Cliente"].fillna("Não informado").astype(str)
        if "Cliente" in df.columns
        else "Não informado"
    )
    df["Local Interno"] = (
        df["Local Interno"].fillna("Não informado").astype(str)
        if "Local Interno" in df.columns
        else "Não informado"
    )
    df["Problemas"] = (
        df["Problemas"].fillna("Outros").astype(str)
        if "Problemas" in df.columns
        else "Outros"
    )
    df["Descrição"] = (
        df["Descrição"].fillna("Sem descrição").astype(str)
        if "Descrição" in df.columns
        else "Sem descrição"
    )

    return df


df = load_data()
df_clientes_raw, opt_formas_pagamento, opt_problemas, opt_descricao, dict_usuarios = load_auxiliary_data()

# --- CONTROLE DE NAVEGAÇÃO LATERAL COM BOTÕES ---
if "pagina_ativa" not in st.session_state:
    st.session_state.pagina_ativa = "dashboard"

st.sidebar.markdown("### 🧭 Menu Principal")

col_btn1, col_btn2 = st.sidebar.columns(2)
with col_btn1:
    btn_dash = st.button("📊 Dashboard", use_container_width=True, type="primary" if st.session_state.pagina_ativa == "dashboard" else "secondary")
with col_btn2:
    btn_sac = st.button("📝 SAC", use_container_width=True, type="primary" if st.session_state.pagina_ativa == "sac" else "secondary")

if btn_dash:
    st.session_state.pagina_ativa = "dashboard"
    st.rerun()

if btn_sac:
    st.session_state.pagina_ativa = "sac"
    st.rerun()

# ==============================================================================
# 1. ABA DE LANÇAMENTO DE OCORRÊNCIAS DO SAC (COMPACTA + JS MÁSCARAS)
# ==============================================================================
if st.session_state.pagina_ativa == "sac":
    st.markdown(
        """
        <div class="header-card">
            <div class="header-title">📝 Central de Lançamento de Ocorrências — SAC</div>
            <div class="header-subtitle">Registro ágil de ocorrências, transações e reembolsos</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Controle de Sessão do Atendente
    if "atendente_logado" not in st.session_state:
        st.session_state.atendente_logado = None

    if not st.session_state.atendente_logado:
        st.subheader("🔐 Autenticação de Atendente")
        st.caption("Insira suas credenciais cadastradas na aba 'Usuarios' para liberar o lançamento.")
        
        col_log1, _ = st.columns([1, 1.8])
        with col_log1:
            with st.form("form_login_sac"):
                login_user = st.text_input("Usuário:")
                login_pass = st.text_input("Senha:", type="password")
                btn_login = st.form_submit_button("Acessar Painel de Lançamento", use_container_width=True)

                if btn_login:
                    u_clean = login_user.strip()
                    p_clean = login_pass.strip()
                    if u_clean in dict_usuarios and str(dict_usuarios[u_clean]) == p_clean:
                        st.session_state.atendente_logado = u_clean
                        st.success(f"Bem-vindo(a), {u_clean}!")
                        st.rerun()
                    else:
                        st.error("Usuário ou senha inválidos. Verifique os dados cadastrados na aba 'Usuarios'.")
    else:
        # Usuário autenticado
        col_topo1, col_topo2 = st.columns([3.5, 1.2])
        with col_topo1:
            st.success(f"👤 Atendente conectado: **{st.session_state.atendente_logado}**")
        with col_topo2:
            if st.button("🚪 Sair / Trocar Usuário", use_container_width=True):
                st.session_state.atendente_logado = None
                st.rerun()

        # Gerar número automático do chamado: SAC-AAAA-XXXX
        ano_atual_str = str(datetime.now().year)
        chamados_ano_count = len(df[df["Ano"] == ano_atual_str]) + 1 if not df.empty else 1
        num_chamado_gerado = f"SAC-{ano_atual_str}-{chamados_ano_count:04d}"

        # Lista de Clientes (Coluna A da aba Clientes)
        lista_clientes = [""] + sorted(list(set(df_clientes_raw["Cliente"].dropna().tolist())))

        # INJEÇÃO DO JAVASCRIPT DE FORMATAÇÃO E MÁSCARAS
        components.html(
            """
            <script>
            (function() {
                const parentDoc = window.parent.document;

                function applyMasks() {
                    // Máscara de Moeda R$ 0,00
                    const valorInputs = parentDoc.querySelectorAll('input[aria-label*="Valor"], input[placeholder*="0,00"]');
                    valorInputs.forEach(input => {
                        if (!input.dataset.masked) {
                            input.dataset.masked = "true";
                            input.addEventListener('input', function(e) {
                                let v = e.target.value.replace(/\\D/g, '');
                                v = (v / 100).toFixed(2) + '';
                                v = v.replace(".", ",");
                                v = v.replace(/(\\d)(?=(\\d{3})+(?!\\d))/g, '$1.');
                                e.target.value = v ? 'R$ ' + v : '';
                            });
                        }
                    });

                    // Máscara de Celular (00) 00000-0000
                    const telInputs = parentDoc.querySelectorAll('input[aria-label*="Celular"], input[placeholder*="(00)"]');
                    telInputs.forEach(input => {
                        if (!input.dataset.masked) {
                            input.dataset.masked = "true";
                            input.addEventListener('input', function(e) {
                                let v = e.target.value.replace(/\\D/g, '');
                                if (v.length > 11) v = v.slice(0, 11);
                                if (v.length > 6) {
                                    e.target.value = `(${v.slice(0,2)}) ${v.slice(2,7)}-${v.slice(7)}`;
                                } else if (v.length > 2) {
                                    e.target.value = `(${v.slice(0,2)}) ${v.slice(2)}`;
                                } else if (v.length > 0) {
                                    e.target.value = `(${v}`;
                                }
                            });
                        }
                    });

                    // Máscara de Hora HH:MM
                    const horaInputs = parentDoc.querySelectorAll('input[aria-label*="Hora da Transação"], input[placeholder*="HH:MM"]');
                    horaInputs.forEach(input => {
                        if (!input.dataset.masked) {
                            input.dataset.masked = "true";
                            input.addEventListener('input', function(e) {
                                let v = e.target.value.replace(/\\D/g, '');
                                if (v.length > 4) v = v.slice(0, 4);
                                if (v.length > 2) {
                                    e.target.value = `${v.slice(0,2)}:${v.slice(2)}`;
                                } else {
                                    e.target.value = v;
                                }
                            });
                        }
                    });

                    // Máscara de Data da Transação DD/MM/AAAA
                    const dataInputs = parentDoc.querySelectorAll('input[aria-label*="Data da Transação"], input[placeholder*="DD/MM/AAAA"]');
                    dataInputs.forEach(input => {
                        if (!input.dataset.masked) {
                            input.dataset.masked = "true";
                            input.addEventListener('input', function(e) {
                                let v = e.target.value.replace(/\\D/g, '');
                                if (v.length > 8) v = v.slice(0, 8);
                                if (v.length > 4) {
                                    e.target.value = `${v.slice(0,2)}/${v.slice(2,4)}/${v.slice(4)}`;
                                } else if (v.length > 2) {
                                    e.target.value = `${v.slice(0,2)}/${v.slice(2)}`;
                                } else {
                                    e.target.value = v;
                                }
                            });
                        }
                    });
                }

                applyMasks();
                const observer = new MutationObserver(applyMasks);
                observer.observe(parentDoc.body, { childList: true, subtree: true });
            })();
            </script>
            """,
            height=0,
            width=0,
        )

        # FORMULÁRIO COMPACTO E LINEAR
        st.markdown(f"#### 📋 Formulário de Abertura — `{num_chamado_gerado}`")

        # LINHA 1: Identificação e Dados Gerais
        st.markdown('<div class="compact-section-title">1. Dados Operacionais & Localização</div>', unsafe_allow_html=True)
        r1_c1, r1_c2, r1_c3, r1_c4 = st.columns([1.1, 1, 1.2, 1.3])
        with r1_c1:
            st.text_input("Chamado", value=num_chamado_gerado, disabled=True)
        with r1_c2:
            data_chamado = st.date_input("Data do Chamado", value=datetime.now().date(), format="DD/MM/YYYY")
        with r1_c3:
            produto_sel = st.selectbox("Produto", ["", "Café", "Snaky"], index=0)
        with r1_c4:
            cliente_sel = st.selectbox("Cliente", lista_clientes, index=0, key="sac_cliente_sel")

        # LINHA 2: Localização e Classificação da Falha
        locais_validos = [""]
        if cliente_sel:
            sub_cli = df_clientes_raw[df_clientes_raw["Cliente"] == cliente_sel]
            locais_unicos = sorted([loc for loc in sub_cli["Local Interno"].dropna().unique() if str(loc).strip()])
            locais_validos = [""] + locais_unicos

        cidade_sugerida = ""
        if cliente_sel:
            sub_loc = df_clientes_raw[(df_clientes_raw["Cliente"] == cliente_sel)]
            sub_loc_cidades = [c for c in sub_loc["Cidade"].dropna().unique() if str(c).strip()]
            cidade_sugerida = sub_loc_cidades[0] if sub_loc_cidades else ""

        r2_c1, r2_c2, r2_c3, r2_c4 = st.columns([1.2, 1, 1.1, 1.3])
        with r2_c1:
            local_interno_sel = st.selectbox("Local Interno", locais_validos, index=0, key="sac_local_interno_sel")
        with r2_c2:
            cidade_sel = st.text_input("Cidade", value=cidade_sugerida, placeholder="Cidade do Local")
        with r2_c3:
            problema_sel = st.selectbox("Problema", [""] + opt_problemas, index=0, key="sac_problema_sel")
        with r2_c4:
            descricao_sel = st.selectbox("Descrição", [""] + opt_descricao, index=0, key="sac_descricao_sel")

        # LINHA 3: Transação e Solicitante
        st.markdown('<div class="compact-section-title">2. Transação Financeira & Solicitante</div>', unsafe_allow_html=True)
        r3_c1, r3_c2, r3_c3, r3_c4 = st.columns([1, 0.9, 1, 1.2])
        with r3_c1:
            data_transacao_txt = st.text_input("Data Transação", placeholder="DD/MM/AAAA", key="sac_dt_transacao")
        with r3_c2:
            hora_transacao_txt = st.text_input("Hora Transação", placeholder="HH:MM", key="sac_hr_transacao")
        with r3_c3:
            valor_transacao_txt = st.text_input("Valor Reembolso", placeholder="0,00", key="sac_valor_transacao")
        with r3_c4:
            forma_pagamento_sel = st.selectbox("Forma de Pagamento", [""] + opt_formas_pagamento, index=0, key="sac_forma_pagamento_sel")

        # LINHA 4: Chave Pix e Contato
        r4_c1, r4_c2, r4_c3 = st.columns([1.5, 1.3, 1.2])
        with r4_c1:
            pix_reembolso = st.text_input("Pix - Reembolso", placeholder="CPF, e-mail, celular ou chave aleatória", key="sac_pix_reembolso")
        with r4_c2:
            nome_cliente = st.text_input("Nome/Sobrenome", placeholder="Nome completo do solicitante", key="sac_nome_cliente")
        with r4_c3:
            celular_cliente = st.text_input("Celular", placeholder="(00) 00000-0000", key="sac_celular_cliente")

        data_hora_lancamento = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        btn_salvar_chamado = st.button("💾 Gravar Lançamento do Chamado", use_container_width=True, type="primary")

        if btn_salvar_chamado:
            if not cliente_sel:
                st.error("Por favor, selecione um Cliente.")
            elif not local_interno_sel:
                st.error("Por favor, selecione um Local Interno.")
            elif not problema_sel:
                st.error("Por favor, selecione o Problema.")
            elif not nome_cliente.strip():
                st.error("Por favor, informe o Nome/Sobrenome do cliente.")
            else:
                nome_formatado = nome_cliente.strip().title()

                try:
                    val_limpo = float(
                        valor_transacao_txt.replace("R$", "")
                        .replace(".", "")
                        .replace(",", ".")
                        .strip()
                    ) if valor_transacao_txt.strip() else 0.0
                except ValueError:
                    val_limpo = 0.0

                novo_registro = {
                    "Chamado": num_chamado_gerado,
                    "Data": data_chamado.strftime("%d/%m/%Y"),
                    "Cliente": cliente_sel,
                    "Local Interno": local_interno_sel,
                    "Cidade": cidade_sel.strip(),
                    "Descrição": descricao_sel,
                    "Produto": produto_sel,
                    "Data da Transação": data_transacao_txt.strip(),
                    "Hora da Transação": hora_transacao_txt.strip(),
                    "Valor": val_limpo,
                    "Nome/Sobrenome": nome_formatado,
                    "Celular": celular_cliente.strip(),
                    "Problemas": problema_sel,
                    "Forma de Pagamento": forma_pagamento_sel,
                    "Pix - Reembolso": pix_reembolso.strip(),
                    "Atendente": st.session_state.atendente_logado,
                    "Data/Hora do lançamento": data_hora_lancamento,
                }

                # Prioriza a URL dos secrets se definida; caso contrário usa a URL informada
                webhook_url = st.secrets.get("GOOGLE_SHEET_WEBHOOK_URL", WEBHOOK_URL_DEFAULT)
                gravacao_ok = False

                if webhook_url:
                    try:
                        req_data = json.dumps(novo_registro).encode("utf-8")
                        req = urllib.request.Request(
                            webhook_url,
                            data=req_data,
                            headers={"Content-Type": "application/json"}
                        )
                        with urllib.request.urlopen(req, timeout=15) as response:
                            res_body = response.read().decode("utf-8")
                            st.info(f"Resposta do Webhook: {res_body}")
                            gravacao_ok = True
                    except Exception as err:
                        st.error(f"Erro ao disparar webhook: {err}")
                else:
                    st.error("URL do Webhook não encontrada.")

                if gravacao_ok:
                    st.success(f"✅ Chamado **{num_chamado_gerado}** registrado com sucesso para **{nome_formatado}**!")
                    st.json(novo_registro)

# ==============================================================================
# 2. ABA DO DASHBOARD EXECUTIVO
# ==============================================================================
elif st.session_state.pagina_ativa == "dashboard":

    hoje = datetime.now().date()
    datas_validas = df["Data_Date"].dropna()
    min_data_calendario = min(datas_validas.min(), hoje) if not datas_validas.empty else hoje
    max_data_calendario = max(datas_validas.max(), hoje) if not datas_validas.empty else hoje

    meses_do_ano = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
        7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
    }
    mes_atual_num = datetime.now().month
    mes_atual_nome = meses_do_ano.get(mes_atual_num, "Janeiro")
    mes_anterior_num = 12 if mes_atual_num == 1 else mes_atual_num - 1
    mes_anterior_nome = meses_do_ano.get(mes_anterior_num, "Dezembro")

    months_order = [
        "Todos", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
    ]

    idx_mes_atual = months_order.index(mes_atual_nome) if mes_atual_nome in months_order else len(months_order) - 1

    filtered_df = df.copy()

    total_chamados = len(filtered_df)
    total_devolvido = filtered_df["Valor"].sum()
    top_cliente = (
        filtered_df["Cliente"].value_counts().index[0]
        if len(filtered_df) > 0
        else "-"
    )
    top_problema = (
        filtered_df["Problemas"].value_counts().index[0]
        if len(filtered_df) > 0
        else "-"
    )

    # --- BOTÃO DE GERAR RELATÓRIO PDF NA BARRA LATERAL ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("📄 Relatório Executivo")

    active_filters_dict = {
        "ano": "Consolidado Geral",
    }

    pdf_full_bytes = generate_full_pdf_report(
        filtered_df,
        total_chamados,
        total_devolvido,
        top_cliente,
        top_problema,
        active_filters_dict,
    )

    st.sidebar.download_button(
        label="📥 Gerar Relatório Completo (PDF)",
        data=pdf_full_bytes,
        file_name="Relatorio_Executivo_SAC_MasterCafe_Consolidado.pdf",
        mime="application/pdf",
        help="Exportar dados consolidados em formato PDF",
        use_container_width=True,
    )

    if st.sidebar.button("🔄 Atualizar Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    # --- CABEÇALHO PRINCIPAL ---
    st.markdown(
        """
        <div class="header-card">
            <div class="header-title">☕ Master Café — Dashboard Executivo SAC</div>
            <div class="header-subtitle">Painel de Gestão da Qualidade, Atendimento e Reembolsos Financeiros</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- 1. CARDS DE KPIS ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total de Chamados", f"{total_chamados:,}".replace(",", "."))
    c2.metric(
        "Total Reembolsado",
        f"R$ {total_devolvido:,.2f}".replace(",", "v")
        .replace(".", ",")
        .replace("v", "."),
    )
    c3.metric("Principal Cliente", top_cliente)
    c4.metric("Principal Falha", top_problema)

    st.markdown("---")

    # --- 2. INSIGHTS AUTOMÁTICOS ---
    st.subheader("💡 Insights & Destaques Gerenciais Automáticos")
    i1, i2, i3 = st.columns(3)

    with i1:
        st.markdown(
            """
            <div class="insight-card" style="border-left: 4px solid #38bdf8;">
                <h4 style="color:#38bdf8; margin:0 0 8px 0; font-size: 15px;">Pico Operacional em Agosto</h4>
                <p style="font-size:13px; color:#cbd5e1; margin:0; line-height: 1.4;">Agosto concentrou o maior volume com <b>1.495 chamados</b> e <b>R$ 8.128,78</b> reembolsados, impulsionado por Senac Araraquara e Shopee SBC.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with i2:
        st.markdown(
            """
            <div class="insight-card" style="border-left: 4px solid #34d399;">
                <h4 style="color:#34d399; margin:0 0 8px 0; font-size: 15px;">Gargalo Técnico em Bebidas e Snacks</h4>
                <p style="font-size:13px; color:#cbd5e1; margin:0; line-height: 1.4;">"Produto Enroscado" e "Bebida Não Entregue" somam a maioria absoluta das reclamações, exigindo ajuste em molas e sensores.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with i3:
        st.markdown(
            """
            <div class="insight-card" style="border-left: 4px solid #fbbf24;">
                <h4 style="color:#fbbf24; margin:0 0 8px 0; font-size: 15px;">Concentração em Teleperformance</h4>
                <p style="font-size:13px; color:#cbd5e1; margin:0; line-height: 1.4;">A conta Teleperformance responde por <b>1.949 chamados</b> no acumulado do ano, representando mais de 23% de toda a demanda do SAC.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # --- 3. DESTAQUES MÊS A MÊS COM FILTROS DE COMPARAÇÃO ---
    st.markdown("### 📌 Destaques Mês a Mês & Locais Críticos")

    months_choices = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]

    default_idx_a = months_choices.index(mes_anterior_nome) if mes_anterior_nome in months_choices else len(months_choices) - 2
    default_idx_b = months_choices.index(mes_atual_nome) if mes_atual_nome in months_choices else len(months_choices) - 1

    f_c1, f_c2, _ = st.columns([1, 1, 1.2])
    with f_c1:
        mes_comp_a = st.selectbox(
            "Mês A (Mês Anterior):",
            months_choices,
            index=default_idx_a,
            key="comp_mes_a",
        )
    with f_c2:
        mes_comp_b = st.selectbox(
            "Mês B (Mês Atual - Referência Crítica):",
            months_choices,
            index=default_idx_b,
            key="comp_mes_b",
        )

    ca, cs, ct3 = st.columns([1, 1, 1.2])

    with ca:
        df_a = (
            filtered_df[filtered_df["Mês_Clean"] == mes_comp_a]["Local Interno"]
            .value_counts()
            .head(5)
            .reset_index()
        )
        df_a.columns = ["Local", "Chamados"]
        fig_a = px.bar(
            df_a,
            x="Chamados",
            y="Local",
            orientation="h",
            text="Chamados",
            color_discrete_sequence=["#f59e0b"],
        )
        fig_a.update_traces(marker=dict(line=dict(width=0)))
        fig_a.update_layout(yaxis=dict(autorange="reversed"))
        fig_a = apply_powerbi_theme(
            fig_a, title=f"Top 5 Locais — {mes_comp_a}", height=280
        )
        st.plotly_chart(fig_a, use_container_width=True)

    with cs:
        df_b = (
            filtered_df[filtered_df["Mês_Clean"] == mes_comp_b]["Local Interno"]
            .value_counts()
            .head(5)
            .reset_index()
        )
        df_b.columns = ["Local", "Chamados"]
        fig_b = px.bar(
            df_b,
            x="Chamados",
            y="Local",
            orientation="h",
            text="Chamados",
            color_discrete_sequence=["#0284c7"],
        )
        fig_b.update_traces(marker=dict(line=dict(width=0)))
        fig_b.update_layout(yaxis=dict(autorange="reversed"))
        fig_b = apply_powerbi_theme(
            fig_b, title=f"Top 5 Locais — {mes_comp_b}", height=280
        )
        st.plotly_chart(fig_b, use_container_width=True)

    with ct3:
        top3_mes_b = (
            filtered_df[filtered_df["Mês_Clean"] == mes_comp_b]["Local Interno"]
            .value_counts()
            .head(3)
            .index.tolist()
        )

        items_html = ""
        for idx, loc in enumerate(top3_mes_b, 1):
            loc_data = filtered_df[
                (filtered_df["Mês_Clean"] == mes_comp_b) & (filtered_df["Local Interno"] == loc)
            ]
            main_prob = (
                loc_data["Problemas"].value_counts().index[0]
                if len(loc_data) > 0
                else "N/A"
            )
            main_desc = (
                loc_data["Descrição"].value_counts().index[0]
                if len(loc_data) > 0
                else "N/A"
            )

            items_html += f"""
            <div style="background-color: #0f172a; border: 1px solid #334155; border-radius: 6px; padding: 10px 12px; margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <span style="font-weight: 600; color: #f8fafc; font-size: 13px;">{idx}. {loc}</span>
                    <span style="background-color: #0284c7; color: #ffffff; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 10px;">
                        {len(loc_data)} chamados
                    </span>
                </div>
                <div style="font-size: 11px; color: #94a3b8; line-height: 1.4;">
                    <div><b style="color: #cbd5e1;">Falha:</b> {main_prob}</div>
                    <div><b style="color: #cbd5e1;">Item:</b> {main_desc}</div>
                </div>
            </div>
            """

        if not items_html:
            items_html = f"<p style='color:#94a3b8; font-size:12px; margin-top:20px;'>Nenhum registro encontrado para o mês de {mes_comp_b}.</p>"

        st.markdown(
            f"""
            <div style="
                background-color: #1e293b; 
                border: 1px solid #334155; 
                border-radius: 8px; 
                padding: 16px; 
                height: 280px; 
                box-sizing: border-box; 
                overflow-y: auto; 
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
            ">
                <div style="font-family: 'Segoe UI', sans-serif; font-size: 13px; font-weight: 700; color: #cbd5e1; margin-bottom: 12px; display: flex; align-items: center; gap: 6px;">
                    <span>📌</span> Top 3 Locais Críticos ({mes_comp_b})
                </div>
                {items_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # --- 4. VALORES E CHAMADOS MENSAL (HISTÓRICO COMPLETO) ---
    g1, g2 = st.columns(2)

    with g1:
        ch_mes = (
            filtered_df.groupby("Mês_Clean")["Problemas"]
            .count()
            .reindex(months_choices)
            .fillna(0)
            .reset_index()
        )
        ch_mes.columns = ["Mês_Clean", "Chamado"]
        fig_ch = px.bar(
            ch_mes,
            x="Mês_Clean",
            y="Chamado",
            text="Chamado",
            color_discrete_sequence=["#00b4d8"],
        )
        fig_ch.update_traces(marker=dict(line=dict(width=0)))
        fig_ch = apply_powerbi_theme(
            fig_ch, title="Chamados por Mês", height=320
        )
        fig_ch.update_xaxes(title_text="")
        fig_ch.update_yaxes(title_text="Chamados")
        st.plotly_chart(fig_ch, use_container_width=True)

    with g2:
        val_mes = (
            filtered_df.groupby("Mês_Clean")["Valor"]
            .sum()
            .reindex(months_choices)
            .fillna(0)
            .reset_index()
        )
        fig_val = px.bar(
            val_mes,
            x="Mês_Clean",
            y="Valor",
            text_auto=".2f",
            color_discrete_sequence=["#10b981"],
        )
        fig_val.update_traces(marker=dict(line=dict(width=0)))
        fig_val = apply_powerbi_theme(
            fig_val, title="Valores Devolvidos por Mês em R$", height=320
        )
        fig_val.update_xaxes(title_text="")
        fig_val.update_yaxes(title_text="Reembolso (R$)")
        st.plotly_chart(fig_val, use_container_width=True)

    # --- 5. RANKINGS ANUAIS ---
    st.markdown("---")
    r1, r2 = st.columns(2)

    with r1:
        t10_cli = filtered_df["Cliente"].value_counts().head(10).reset_index()
        t10_cli.columns = ["Cliente", "Chamados"]
        fig_cli = px.bar(
            t10_cli,
            x="Chamados",
            y="Cliente",
            orientation="h",
            text="Chamados",
            color_discrete_sequence=["#6366f1"],
        )
        fig_cli.update_traces(marker=dict(line=dict(width=0)))
        fig_cli.update_layout(yaxis=dict(autorange="reversed"))
        fig_cli = apply_powerbi_theme(
            fig_cli, title="Top 10 Clientes do Período", height=350
        )
        st.plotly_chart(fig_cli, use_container_width=True)

    with r2:
        t10_loc = filtered_df["Local Interno"].value_counts().head(10).reset_index()
        t10_loc.columns = ["Local Interno", "Chamados"]
        fig_loc = px.bar(
            t10_loc,
            x="Chamados",
            y="Local Interno",
            orientation="h",
            text="Chamados",
            color_discrete_sequence=["#14b8a6"],
        )
        fig_loc.update_traces(marker=dict(line=dict(width=0)))
        fig_loc.update_layout(yaxis=dict(autorange="reversed"))
        fig_loc = apply_powerbi_theme(
            fig_loc, title="Top 10 Locais Internos do Período", height=350
        )
        st.plotly_chart(fig_loc, use_container_width=True)

    # --- 6. GRÁFICOS DIÁRIOS ---
    st.markdown("---")

    c_filtro_m1, _ = st.columns([1.2, 2.8])
    with c_filtro_m1:
        mes_graf_diario = st.selectbox(
            "📅 Filtrar Mês dos Gráficos Diários:",
            months_order,
            index=idx_mes_atual,
            key="filtro_mes_graficos_diarios"
        )

    df_datas_validas = filtered_df[filtered_df["Data_Date"].notna()].copy()
    if mes_graf_diario != "Todos":
        df_datas_validas = df_datas_validas[df_datas_validas["Mês_Clean"] == mes_graf_diario]

    col_dia_graf1, col_dia_graf2 = st.columns(2)

    with col_dia_graf1:
        if not df_datas_validas.empty:
            ch_por_dia = (
                df_datas_validas.groupby("Data_Date")
                .size()
                .reset_index(name="Quantidade de Chamados")
                .sort_values(by="Data_Date", ascending=True)
            )
            ch_por_dia["Data_Formatada"] = ch_por_dia["Data_Date"].apply(lambda d: d.strftime("%d/%m/%Y"))
            ordem_cronologica_dias = ch_por_dia["Data_Formatada"].tolist()

            titulo_ch_dia = f"Quantidade de Chamados por Dia ({mes_graf_diario})" if mes_graf_diario != "Todos" else "Quantidade de Chamados por Dia (Período Completo)"

            fig_dia_ch = px.bar(
                ch_por_dia,
                x="Data_Formatada",
                y="Quantidade de Chamados",
                text="Quantidade de Chamados",
                color_discrete_sequence=["#38bdf8"],
                category_orders={"Data_Formatada": ordem_cronologica_dias},
            )
            fig_dia_ch.update_traces(marker=dict(line=dict(width=0)))
            fig_dia_ch = apply_powerbi_theme(
                fig_dia_ch, title=titulo_ch_dia, height=340
            )
            fig_dia_ch.update_xaxes(
                title_text="Data",
                tickangle=-45,
                type="category",
                categoryorder="array",
                categoryarray=ordem_cronologica_dias
            )
            fig_dia_ch.update_yaxes(title_text="Qtd Chamados")
            st.plotly_chart(fig_dia_ch, use_container_width=True)
        else:
            st.info(f"Sem dados de chamados registrados para o mês de {mes_graf_diario}.")

    with col_dia_graf2:
        if not df_datas_validas.empty:
            val_por_dia = (
                df_datas_validas.groupby("Data_Date")["Valor"]
                .sum()
                .reset_index(name="Valor Devolvido")
                .sort_values(by="Data_Date", ascending=True)
            )
            val_por_dia["Data_Formatada"] = val_por_dia["Data_Date"].apply(lambda d: d.strftime("%d/%m/%Y"))
            ordem_cronologica_dias_val = val_por_dia["Data_Formatada"].tolist()

            titulo_val_dia = f"Valores Devolvidos por Dia em R$ ({mes_graf_diario})" if mes_graf_diario != "Todos" else "Valores Devolvidos por Dia em R$ (Período Completo)"

            fig_dia_val = px.bar(
                val_por_dia,
                x="Data_Formatada",
                y="Valor Devolvido",
                text_auto=".2f",
                color_discrete_sequence=["#10b981"],
                category_orders={"Data_Formatada": ordem_cronologica_dias_val},
            )
            fig_dia_val.update_traces(marker=dict(line=dict(width=0)))
            fig_dia_val = apply_powerbi_theme(
                fig_dia_val, title=titulo_val_dia, height=340
            )
            fig_dia_val.update_xaxes(
                title_text="Data",
                tickangle=-45,
                type="category",
                categoryorder="array",
                categoryarray=ordem_cronologica_dias_val
            )
            fig_dia_val.update_yaxes(title_text="Total Reembolsado (R$)")
            st.plotly_chart(fig_dia_val, use_container_width=True)
        else:
            st.info(f"Sem valores devolvidos registrados para o mês de {mes_graf_diario}.")

    # --- 7. FILTROS DINÂMICOS LOCAIS ---
    st.markdown("---")

    dev_col1, dev_col2 = st.columns(2)

    with dev_col1:
        st.markdown("**Top Devoluções (R$) - Filtro de Mês Dinâmico**")
        dev_month_selected = st.selectbox(
            "Mudar Mês (Top Devoluções R$)",
            months_order,
            index=idx_mes_atual,
            key="dev_month_filter",
        )

        dev_df_m = filtered_df.copy()
        if dev_month_selected != "Todos":
            dev_df_m = dev_df_m[dev_df_m["Mês_Clean"] == dev_month_selected]

        dev_loc_m = (
            dev_df_m.groupby("Local Interno")["Valor"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )
        fig_dev_m = px.bar(
            dev_loc_m,
            x="Valor",
            y="Local Interno",
            orientation="h",
            text_auto=".2f",
            color_discrete_sequence=["#10b981"],
        )
        fig_dev_m.update_traces(marker=dict(line=dict(width=0)))
        fig_dev_m.update_layout(yaxis=dict(autorange="reversed"))
        fig_dev_m = apply_powerbi_theme(
            fig_dev_m,
            title=f"Top Devoluções (R$) — {dev_month_selected}",
            height=320,
        )
        st.plotly_chart(fig_dev_m, use_container_width=True)

    with dev_col2:
        st.markdown("**Top Devoluções (R$) - Filtro de Dia Dinâmico**")
        day_dev_selected = st.date_input(
            "Mudar Dia (Top Devoluções R$):",
            value=hoje,
            min_value=min_data_calendario,
            max_value=max_data_calendario,
            format="DD/MM/YYYY",
            key="day_dev_calendar",
        )

        dev_df_d = filtered_df.copy()
        day_dev_str = day_dev_selected.strftime("%d/%m/%Y")
        dev_df_d = dev_df_d[
            (dev_df_d["Data_Date"] == day_dev_selected)
            | (dev_df_d["Data_Str"] == day_dev_str)
        ]

        dev_loc_d = (
            dev_df_d.groupby("Local Interno")["Valor"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )
        fig_dev_d = px.bar(
            dev_loc_d,
            x="Valor",
            y="Local Interno",
            orientation="h",
            text_auto=".2f",
            color_discrete_sequence=["#10b981"],
        )
        fig_dev_d.update_traces(marker=dict(line=dict(width=0)))
        fig_dev_d.update_layout(yaxis=dict(autorange="reversed"))
        fig_dev_d = apply_powerbi_theme(
            fig_dev_d,
            title=f"Top Devoluções (R$) — {day_dev_str}",
            height=320,
        )
        st.plotly_chart(fig_dev_d, use_container_width=True)

    loc_col1, loc_col2 = st.columns(2)

    with loc_col1:
        st.markdown("**Top 10 Locais Internos - Filtro de Mês (Chamados)**")
        ch_month_selected = st.selectbox(
            "Mudar Mês (Top Locais Chamados)",
            months_order,
            index=idx_mes_atual,
            key="ch_loc_month_filter",
        )

        ch_df_m = filtered_df.copy()
        if ch_month_selected != "Todos":
            ch_df_m = ch_df_m[ch_df_m["Mês_Clean"] == ch_month_selected]

        dia_loc_m = ch_df_m["Local Interno"].value_counts().head(10).reset_index()
        dia_loc_m.columns = ["Local Interno", "Chamados"]

        fig_loc_m = px.bar(
            dia_loc_m,
            x="Chamados",
            y="Local Interno",
            orientation="h",
            text="Chamados",
            color_discrete_sequence=["#38bdf8"],
        )
        fig_loc_m.update_traces(marker=dict(line=dict(width=0)))
        fig_loc_m.update_layout(yaxis=dict(autorange="reversed"))
        fig_loc_m = apply_powerbi_theme(
            fig_loc_m,
            title=f"Top 10 Locais no Mês — {ch_month_selected}",
            height=320,
        )
        st.plotly_chart(fig_loc_m, use_container_width=True)

    with loc_col2:
        st.markdown("**Top 10 Locais Internos - Filtro de Dia (Calendário)**")
        day_selected_loc = st.date_input(
            "Mudar Dia (Top Locais Chamados):",
            value=hoje,
            min_value=min_data_calendario,
            max_value=max_data_calendario,
            format="DD/MM/YYYY",
            key="day_loc_calendar",
        )

        day_df = filtered_df.copy()
        day_str_target = day_selected_loc.strftime("%d/%m/%Y")
        day_df = day_df[
            (day_df["Data_Date"] == day_selected_loc)
            | (day_df["Data_Str"] == day_str_target)
        ]

        dia_loc = day_df["Local Interno"].value_counts().head(10).reset_index()
        dia_loc.columns = ["Local Interno", "Chamados"]

        fig_dia = px.bar(
            dia_loc,
            x="Chamados",
            y="Local Interno",
            orientation="h",
            text="Chamados",
            color_discrete_sequence=["#f59e0b"],
        )
        fig_dia.update_traces(marker=dict(line=dict(width=0)))
        fig_dia.update_layout(yaxis=dict(autorange="reversed"))
        fig_dia = apply_powerbi_theme(
            fig_dia,
            title=f"Top 10 Locais no Dia — {day_str_target}",
            height=320,
        )
        st.plotly_chart(fig_dia, use_container_width=True)

    # --- 8. TABELAS DETALHADAS OPERACIONAIS ---
    st.markdown("---")
    st.markdown("### 📅 Detalhamento Operacional de Registros")

    lista_clientes_dinamica = ["Todos"] + sorted(
        [
            str(c).strip()
            for c in filtered_df["Cliente"].dropna().unique()
            if str(c).strip() not in ["Não informado", "nan", "None", ""]
        ]
    )

    tab_chamados_dia, tab_mes_cli, tab_dia_cli, tab_mes_top3, tab_dia_top3 = st.tabs(
        [
            "📋 Chamados por Dia (Completa)",
            "Por Mês e Cliente", 
            "Por Data e Cliente", 
            "Por Mês (Top 3 Locais)", 
            "Por Dia (Top 3 Locais)"
        ]
    )

    # --- ABA: TABELA DE CHAMADOS POR DIA ---
    with tab_chamados_dia:
        st.markdown("#### Chamados por Dia — Detalhamento por Local Interno, Descrição e Problema")
        
        col_d_sel1, col_d_sel2 = st.columns([1, 2])
        with col_d_sel1:
            data_analitica_sel = st.date_input(
                "📆 Escolha o Dia para Detalhar:",
                value=hoje,
                min_value=min_data_calendario,
                max_value=max_data_calendario,
                format="DD/MM/YYYY",
                key="tb_dia_detalhado_calendar"
            )
        with col_d_sel2:
            filtro_opc_loc = st.selectbox(
                "Filtrar Local Interno (Opcional):",
                ["Todos"] + sorted(filtered_df["Local Interno"].dropna().unique().tolist()),
                key="tb_dia_detalhado_loc_filtro"
            )

        df_analitico_dia = filtered_df.copy()
        data_analitica_str = data_analitica_sel.strftime("%d/%m/%Y")
        
        df_analitico_dia = df_analitico_dia[
            (df_analitico_dia["Data_Date"] == data_analitica_sel) |
            (df_analitico_dia["Data_Str"] == data_analitica_str)
        ]
        
        if filtro_opc_loc != "Todos":
            df_analitico_dia = df_analitico_dia[df_analitico_dia["Local Interno"] == filtro_opc_loc]

        if not df_analitico_dia.empty:
            tabela_detalhada = (
                df_analitico_dia.groupby(["Local Interno", "Descrição", "Problemas"])
                .agg(
                    Quantidade=("Valor", "count"),
                    Total_Reembolso=("Valor", "sum")
                )
                .reset_index()
                .sort_values(by="Quantidade", ascending=False)
                .rename(columns={"Problemas": "Problema", "Quantidade": "Quantidade de Chamados"})
            )
            
            tabela_detalhada.insert(0, "Data", data_analitica_str)

            st.markdown(
                f"**Exibindo registros da data:** `{data_analitica_str}` | "
                f"**Total de chamados no dia:** `{tabela_detalhada['Quantidade de Chamados'].sum()}` | "
                f"**Total reembolsado:** `R$ {tabela_detalhada['Total_Reembolso'].sum():,.2f}`".replace(",", "v").replace(".", ",").replace("v", ".")
            )

            st.dataframe(
                tabela_detalhada[["Data", "Local Interno", "Descrição", "Problema", "Quantidade de Chamados"]],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.warning(f"Nenhum chamado encontrado para a data '{data_analitica_str}'.")

    # --- ABA 1: POR MÊS E CLIENTE ---
    with tab_mes_cli:
        c_m1, c_m2 = st.columns([1, 1.5])
        with c_m1:
            sel_tb_mes = st.selectbox(
                "📅 Selecionar Mês:",
                months_order,
                index=idx_mes_atual,
                key="tb_cli_mes_filter",
            )
        with c_m2:
            sel_tb_cli_m = st.selectbox(
                "👤 Selecionar Cliente:",
                lista_clientes_dinamica,
                index=0,
                key="tb_cli_mes_client_filter",
            )

        df_tab_mes = filtered_df.copy()
        if sel_tb_mes != "Todos":
            df_tab_mes = df_tab_mes[df_tab_mes["Mês_Clean"] == sel_tb_mes]
        if sel_tb_cli_m != "Todos":
            df_tab_mes = df_tab_mes[df_tab_mes["Cliente"] == sel_tb_cli_m]

        if not df_tab_mes.empty:
            tabela_mes_agrupada = (
                df_tab_mes.groupby(["Problemas", "Descrição"])
                .size()
                .reset_index(name="Quantidade de Chamados")
                .sort_values(by="Quantidade de Chamados", ascending=False)
                .rename(columns={"Problemas": "Problema"})
            )
            st.markdown(
                f"**Exibindo chamados para:** Mês `'{sel_tb_mes}'` | Cliente `'{sel_tb_cli_m}'` "
                f"*(Total: {tabela_mes_agrupada['Quantidade de Chamados'].sum()} ocorrências)*"
            )
            st.dataframe(
                tabela_mes_agrupada[["Problema", "Descrição", "Quantidade de Chamados"]],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.warning(f"Nenhum registro encontrado para o mês '{sel_tb_mes}' e cliente '{sel_tb_cli_m}'.")

    # --- ABA 2: POR DATA (CALENDÁRIO) E CLIENTE ---
    with tab_dia_cli:
        c_d1, c_d2 = st.columns([1, 1.5])
        with c_d1:
            sel_tb_data = st.date_input(
                "📆 Selecionar Data no Calendário:",
                value=hoje,
                min_value=min_data_calendario,
                max_value=max_data_calendario,
                format="DD/MM/YYYY",
                key="tb_cli_dia_calendar",
            )
        with c_d2:
            sel_tb_cli_d = st.selectbox(
                "👤 Selecionar Cliente:",
                lista_clientes_dinamica,
                index=0,
                key="tb_cli_dia_client_filter",
            )

        df_tab_dia = filtered_df.copy()
        data_alvo_str = sel_tb_data.strftime("%d/%m/%Y")
        df_tab_dia = df_tab_dia[
            (df_tab_dia["Data_Date"] == sel_tb_data)
            | (df_tab_dia["Data_Str"] == data_alvo_str)
        ]
        if sel_tb_cli_d != "Todos":
            df_tab_dia = df_tab_dia[df_tab_dia["Cliente"] == sel_tb_cli_d]

        if not df_tab_dia.empty:
            tabela_dia_agrupada = (
                df_tab_dia.groupby(["Problemas", "Descrição"])
                .size()
                .reset_index(name="Quantidade de Chamados")
                .sort_values(by="Quantidade de Chamados", ascending=False)
                .rename(columns={"Problemas": "Problema"})
            )
            st.markdown(
                f"**Exibindo chamados para:** Data `'{data_alvo_str}'` | Cliente `'{sel_tb_cli_d}'` "
                f"*(Total: {tabela_dia_agrupada['Quantidade de Chamados'].sum()} ocorrências)*"
            )
            st.dataframe(
                tabela_dia_agrupada[["Problema", "Descrição", "Quantidade de Chamados"]],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.warning(f"Nenhum registro encontrado para a data '{data_alvo_str}' e cliente '{sel_tb_cli_d}'.")

    # --- ABA 3: POR MÊS (TOP 3 LOCAIS) ---
    with tab_mes_top3:
        c_m3_1, c_m3_2 = st.columns([1, 2])
        with c_m3_1:
            month_for_top3 = st.selectbox(
                "📅 Selecionar Mês:",
                months_order,
                index=idx_mes_atual,
                key="tb_top3_month_filter",
            )

        month_df_top3 = filtered_df.copy()
        if month_for_top3 != "Todos":
            month_df_top3 = month_df_top3[month_df_top3["Mês_Clean"] == month_for_top3]

        top_3_month_locals = (
            month_df_top3["Local Interno"].value_counts().head(3).index.tolist()
        )

        if top_3_month_locals:
            with c_m3_2:
                selected_top_local_m = st.selectbox(
                    "🎯 Filtrar Local Interno (Mês):",
                    ["Exibir em Abas Separadas (Top 3)"] + top_3_month_locals,
                    key="top_3_local_m_filter",
                )

            def get_month_local_table(local_name):
                c_df = month_df_top3[month_df_top3["Local Interno"] == local_name]
                tb = (
                    c_df.groupby(["Problemas", "Descrição"])
                    .size()
                    .reset_index(name="Quantidade de Chamados")
                    .sort_values(by="Quantidade de Chamados", ascending=False)
                    .rename(columns={"Problemas": "Problema"})
                )
                return tb

            if selected_top_local_m == "Exibir em Abas Separadas (Top 3)":
                tabs_m = st.tabs([f"🥇 {loc}" for loc in top_3_month_locals])
                for idx, tab in enumerate(tabs_m):
                    with tab:
                        local_item = top_3_month_locals[idx]
                        tb_local = get_month_local_table(local_item)
                        st.markdown(f"**Registros do Local no Mês ({month_for_top3}):** `{local_item}`")
                        st.dataframe(
                            tb_local[["Problema", "Descrição", "Quantidade de Chamados"]],
                            use_container_width=True,
                            hide_index=True,
                        )
            else:
                tb_single_m = get_month_local_table(selected_top_local_m)
                st.markdown(f"**Registros do Local no Mês ({month_for_top3}):** `{selected_top_local_m}`")
                st.dataframe(
                    tb_single_m[["Problema", "Descrição", "Quantidade de Chamados"]],
                    use_container_width=True,
                    hide_index=True,
                )
        else:
            st.warning(f"Nenhum registro encontrado para o mês de {month_for_top3}.")

    # --- ABA 4: POR DIA (TOP 3 LOCAIS) ---
    with tab_dia_top3:
        c_d3_1, c_d3_2 = st.columns([1.2, 1.8])
        with c_d3_1:
            chosen_date_top3 = st.date_input(
                "📆 Selecionar Data no Calendário:",
                value=hoje,
                min_value=min_data_calendario,
                max_value=max_data_calendario,
                format="DD/MM/YYYY",
                key="tb_top3_day_calendar",
            )

        day_df_top3 = filtered_df.copy()
        day_str_op_top3 = chosen_date_top3.strftime("%d/%m/%Y")
        day_df_top3 = day_df_top3[
            (day_df_top3["Data_Date"] == chosen_date_top3)
            | (day_df_top3["Data_Str"] == day_str_op_top3)
        ]

        top_3_day_locals = (
            day_df_top3["Local Interno"].value_counts().head(3).index.tolist()
        )

        if top_3_day_locals:
            with c_d3_2:
                selected_top_local_d = st.selectbox(
                    "🎯 Filtrar Local Interno (Dia):",
                    ["Exibir em Abas Separadas (Top 3)"] + top_3_day_locals,
                    key="top_3_local_d_filter",
                )

            def get_day_local_table(local_name):
                c_df = day_df_top3[day_df_top3["Local Interno"] == local_name]
                tb = (
                    c_df.groupby(["Problemas", "Descrição"])
                    .size()
                    .reset_index(name="Quantidade de Chamados")
                    .sort_values(by="Quantidade de Chamados", ascending=False)
                    .rename(columns={"Problemas": "Problema"})
                )
                return tb

            if selected_top_local_d == "Exibir em Abas Separadas (Top 3)":
                tabs_d = st.tabs([f"🥇 {loc}" for loc in top_3_day_locals])
                for idx, tab in enumerate(tabs_d):
                    with tab:
                        local_item = top_3_day_locals[idx]
                        tb_local_d = get_day_local_table(local_item)
                        st.markdown(f"**Registros do Local na Data ({day_str_op_top3}):** `{local_item}`")
                        st.dataframe(
                            tb_local_d[["Problema", "Descrição", "Quantidade de Chamados"]],
                            use_container_width=True,
                            hide_index=True,
                        )
            else:
                tb_single_d = get_day_local_table(selected_top_local_d)
                st.markdown(f"**Registros do Local na Data ({day_str_op_top3}):** `{selected_top_local_d}`")
                st.dataframe(
                    tb_single_d[["Problema", "Descrição", "Quantidade de Chamados"]],
                    use_container_width=True,
                    hide_index=True,
                )
        else:
            st.warning(f"Nenhum registro encontrado para a data {day_str_op_top3}.")