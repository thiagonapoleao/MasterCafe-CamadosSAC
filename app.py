# -*- coding: utf-8 -*-
from datetime import datetime
import io
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

st.set_page_config(
    page_title="Dashboard Executivo SAC - Master Café",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CSS POWER BI EXECUTIVE THEME ---
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
        padding: 20px 24px;
        border-radius: 8px;
        border: 1px solid #334155;
        border-left: 6px solid #0284c7;
        margin-bottom: 20px;
    }
    .header-title {
        color: #ffffff !important;
        font-weight: 700;
        font-size: 1.85rem;
        margin-bottom: 4px;
        letter-spacing: -0.5px;
    }
    .header-subtitle {
        color: #94a3b8 !important;
        font-size: 0.95rem;
        font-weight: 400;
    }

    /* Cards de KPI no padrão Power BI Card Visual */
    .stMetric { 
        background-color: #ffffff !important; 
        padding: 18px !important; 
        border-radius: 8px !important; 
        border: 1px solid #334155 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
         
    }
    div[data-testid="stMetricValue"] { 
        color: #38bdf8 !important; 
        font-weight: 700 !important; 
        font-size: 1.9rem !important; 
        font-family: 'Segoe UI', sans-serif !important;
    }
    div[data-testid="stMetricLabel"], 
    div[data-testid="stMetricLabel"] > label,
    div[data-testid="stMetricLabel"] p { 
        color: #94a3b8 !important; 
        font-size: 0.85rem !important; 
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Cards de Insights */
    .insight-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.15);
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

    # Estilos Tipográficos Customizados
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
    filtros_txt = (
        f"<b>Filtros Atuais Aplicados:</b> Mês: <code>{active_filters.get('mes')}</code> | "
        f"Cliente: <code>{active_filters.get('cliente')}</code> | "
        f"Local Interno: <code>{active_filters.get('local')}</code> | "
        f"Ocorrência: <code>{active_filters.get('problema')}</code> | "
        f"Dia: <code>{active_filters.get('dia')}</code>"
    )
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
        "Janeiro",
        "Fevereiro",
        "Março",
        "Abril",
        "Maio",
        "Junho",
        "Julho",
        "Agosto",
        "Setembro",
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

    # 5. Top 10 Clientes e Top 10 Falhas
    elements.append(
        Paragraph("3. Top 10 Clientes e Causas Mais Frequentes", section_style)
    )
    top_cli_df = (
        df_filtered.groupby("Cliente")
        .agg(Chamados=("Valor", "count"), Reembolso=("Valor", "sum"))
        .sort_values(by="Chamados", ascending=False)
        .head(10)
        .reset_index()
    )

    t_cli_data = [[
        Paragraph("Cliente / Conta", table_header),
        Paragraph("Qtd. Chamados", table_header),
        Paragraph("Impacto Financeiro (R$)", table_header),
    ]]
    for _, r in top_cli_df.iterrows():
        val_f = (
            f"R$ {r['Reembolso']:,.2f}".replace(",", "v")
            .replace(".", ",")
            .replace("v", ".")
        )
        t_cli_data.append([
            Paragraph(str(r["Cliente"])[:38], table_cell),
            Paragraph(f"{int(r['Chamados']):,}".replace(",", "."), table_cell),
            Paragraph(val_f, table_cell),
        ])

    t_cli_tab = Table(t_cli_data, colWidths=[270, 110, 160])
    t_cli_tab.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
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
    elements.append(t_cli_tab)
    elements.append(Spacer(1, 14))

    # 6. Top 10 Locais Internos Críticos
    elements.append(
        Paragraph(
            "4. Top 10 Locais Internos com Maior Volume de Demandas",
            section_style,
        )
    )
    top_loc_df = (
        df_filtered.groupby("Local Interno")
        .agg(Chamados=("Valor", "count"), Reembolso=("Valor", "sum"))
        .sort_values(by="Chamados", ascending=False)
        .head(10)
        .reset_index()
    )

    t_loc_data = [[
        Paragraph("Local Interno / Unidade", table_header),
        Paragraph("Qtd. Chamados", table_header),
        Paragraph("Total Devolvido (R$)", table_header),
    ]]
    for _, r in top_loc_df.iterrows():
        val_f = (
            f"R$ {r['Reembolso']:,.2f}".replace(",", "v")
            .replace(".", ",")
            .replace("v", ".")
        )
        t_loc_data.append([
            Paragraph(str(r["Local Interno"])[:38], table_cell),
            Paragraph(f"{int(r['Chamados']):,}".replace(",", "."), table_cell),
            Paragraph(val_f, table_cell),
        ])

    t_loc_tab = Table(t_loc_data, colWidths=[270, 110, 160])
    t_loc_tab.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
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
    elements.append(t_loc_tab)
    elements.append(Spacer(1, 14))

    # 7. Detalhamento Operacional de Registros (Amostra dos 25 mais recentes)
    elements.append(
        Paragraph(
            "5. Amostra Analítica dos Registros Filtrados (Últimos 25 Itens)",
            section_style,
        )
    )
    sample_df = df_filtered.head(25)
    t_sample_data = [[
        Paragraph("Data", table_header),
        Paragraph("Cliente", table_header),
        Paragraph("Local Interno", table_header),
        Paragraph("Problema", table_header),
        Paragraph("Valor (R$)", table_header),
    ]]
    for _, r in sample_df.iterrows():
        val_f = (
            f"R$ {r['Valor']:,.2f}".replace(",", "v")
            .replace(".", ",")
            .replace("v", ".")
        )
        t_sample_data.append([
            Paragraph(str(r["Data_Str"])[:10], table_cell),
            Paragraph(str(r["Cliente"])[:18], table_cell),
            Paragraph(str(r["Local Interno"])[:20], table_cell),
            Paragraph(str(r["Problemas"])[:20], table_cell),
            Paragraph(val_f, table_cell),
        ])

    t_sample_tab = Table(t_sample_data, colWidths=[65, 120, 145, 130, 80])
    t_sample_tab.setStyle(
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
                ("ALIGN", (4, 0), (-1, -1), "RIGHT"),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    elements.append(t_sample_tab)

    # Constrói o PDF com canvas de numeração de páginas
    doc.build(elements, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()


@st.cache_data
def load_data():
    df = pd.read_excel("Sac Master Café.xlsx")
    month_map = {
        "Janeiro": "Janeiro",
        "janeiro": "Janeiro",
        "Fevereiro": "Fevereiro",
        "Março": "Março",
        "Abril": "Abril",
        "Maio": "Maio",
        "Junho": "Junho",
        "Julho": "Julho",
        "Agosto": "Agosto",
        "Setembro": "Setembro",
        "setembro": "Setembro",
    }
    df["Mês_Clean"] = (
        df["Mês"].astype(str).str.capitalize().str.strip().map(month_map)
    )
    df["Valor"] = pd.to_numeric(
        df["$"]
        .astype(str)
        .str.replace("R$", "", regex=False)
        .str.replace(",", ".")
        .str.strip(),
        errors="coerce",
    ).fillna(0)
    df["Cliente"] = df["Cliente"].fillna("Não informado").astype(str)
    df["Local Interno"] = df["Local Interno"].fillna("Não informado").astype(str)
    df["Problemas"] = df["Problemas"].fillna("Outros").astype(str)
    df["Descrição"] = df["Descrição"].fillna("Sem descrição").astype(str)
    df["Data_Str"] = df["Data"].astype(str)
    return df


df = load_data()

# --- FILTROS GLOBAIS NA BARRA LATERAL ---
st.sidebar.title("⚙️ Filtros Executivos")

months_order = [
    "Todos",
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
]
selected_month = st.sidebar.selectbox("Mês do Ano", months_order)
clients_list = ["Todos"] + sorted(
    [c for c in df["Cliente"].unique() if c != "Não informado"]
)
selected_client = st.sidebar.selectbox("Cliente", clients_list)
locals_list = ["Todos"] + sorted(
    [l for l in df["Local Interno"].unique() if l != "Não informado"]
)
selected_local = st.sidebar.selectbox("Local Interno", locals_list)
problems_list = ["Todos"] + sorted([p for p in df["Problemas"].unique()])
selected_problem = st.sidebar.selectbox("Tipo de Ocorrência", problems_list)
days_list = ["Todos"] + sorted([d for d in df["Data_Str"].unique() if d != "nan"])
selected_day = st.sidebar.selectbox("Dia Específico", days_list)

# Filtragem Dinâmica Global
filtered_df = df.copy()
if selected_month != "Todos":
    filtered_df = filtered_df[filtered_df["Mês_Clean"] == selected_month]
if selected_client != "Todos":
    filtered_df = filtered_df[filtered_df["Cliente"] == selected_client]
if selected_local != "Todos":
    filtered_df = filtered_df[filtered_df["Local Interno"] == selected_local]
if selected_problem != "Todos":
    filtered_df = filtered_df[filtered_df["Problemas"] == selected_problem]
if selected_day != "Todos":
    filtered_df = filtered_df[filtered_df["Data_Str"] == selected_day]

# --- CABEÇALHO & BOTÃO GERAR RELATÓRIO COMPLETO EM PDF ---
col_head, col_btn = st.columns([3.3, 1.2])

with col_head:
    st.markdown(
        """
        <div class="header-card">
            <div class="header-title">☕ Master Café — Dashboard Executivo SAC</div>
            <div class="header-subtitle">Painel de Gestão da Qualidade, Atendimento e Reembolsos Financeiros</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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

# Empacota os filtros ativos para impressão no relatório
active_filters_dict = {
    "mes": selected_month,
    "cliente": selected_client,
    "local": selected_local,
    "problema": selected_problem,
    "dia": selected_day,
}

# Geração de binário do Relatório Completo em PDF
pdf_full_bytes = generate_full_pdf_report(
    filtered_df,
    total_chamados,
    total_devolvido,
    top_cliente,
    top_problema,
    active_filters_dict,
)

with col_btn:
    st.write("")
    st.download_button(
        label="📥 Gerar Relatório Completo (PDF)",
        data=pdf_full_bytes,
        file_name=f"Relatorio_Executivo_SAC_MasterCafe_{selected_month}.pdf",
        mime="application/pdf",
        help="Exportar dados completos consolidados em formato PDF multipáginas com tabelas e KPIs",
        use_container_width=True,
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

# --- 3. DESTAQUES MÊS A MÊS COM FILTROS DE COMPARAÇÃO & LOCAIS CRÍTICOS ---
st.markdown("### 📌 Destaques Mês a Mês & Locais Críticos")

# Controles para escolha dinâmica dos meses comparados
months_choices = [
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
]
f_c1, f_c2, _ = st.columns([1, 1, 1.2])
with f_c1:
    mes_comp_a = st.selectbox(
        "Mês A:",
        months_choices,
        index=months_choices.index("Agosto")
        if "Agosto" in months_choices
        else 0,
        key="comp_mes_a",
    )
with f_c2:
    mes_comp_b = st.selectbox(
        "Mês B (Referência Crítica):",
        months_choices,
        index=months_choices.index("Setembro")
        if "Setembro" in months_choices
        else 1,
        key="comp_mes_b",
    )

ca, cs, ct3 = st.columns([1, 1, 1.2])

with ca:
    df_a = (
        df[df["Mês_Clean"] == mes_comp_a]["Local Interno"]
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
        df[df["Mês_Clean"] == mes_comp_b]["Local Interno"]
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
        df[df["Mês_Clean"] == mes_comp_b]["Local Interno"]
        .value_counts()
        .head(3)
        .index.tolist()
    )

    items_html = ""
    for idx, loc in enumerate(top3_mes_b, 1):
        loc_data = df[
            (df["Mês_Clean"] == mes_comp_b) & (df["Local Interno"] == loc)
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
        items_html = "<p style='color:#94a3b8; font-size:12px; margin-top:20px;'>Nenhum registro encontrado para o mês selecionado.</p>"

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

# --- 4. VALORES E CHAMADOS MENSAL ---
g1, g2 = st.columns(2)
months_valid = [
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
]

with g1:
    ch_mes = (
        filtered_df.groupby("Mês_Clean")["Problemas"]
        .count()
        .reindex(months_valid)
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
        .reindex(months_valid)
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
        fig_cli, title="Top 10 Clientes do Ano", height=350
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
        fig_loc, title="Top 10 Locais Internos do Ano", height=350
    )
    st.plotly_chart(fig_loc, use_container_width=True)

# --- 6. FILTROS DINÂMICOS LOCAIS ---
st.markdown("---")
d1, d2 = st.columns(2)

with d1:
    st.markdown("**Top Devoluções (R$) - Filtro de Mês Dinâmico**")
    dev_month_selected = st.selectbox(
        "Mudar Mês (Top Devoluções)",
        months_order,
        index=0,
        key="dev_month_filter",
    )

    dev_df = df.copy()
    if dev_month_selected != "Todos":
        dev_df = dev_df[dev_df["Mês_Clean"] == dev_month_selected]

    dev_loc = (
        dev_df.groupby("Local Interno")["Valor"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )
    fig_dev = px.bar(
        dev_loc,
        x="Valor",
        y="Local Interno",
        orientation="h",
        text_auto=".2f",
        color_discrete_sequence=["#10b981"],
    )
    fig_dev.update_traces(marker=dict(line=dict(width=0)))
    fig_dev.update_layout(yaxis=dict(autorange="reversed"))
    fig_dev = apply_powerbi_theme(
        fig_dev,
        title=f"Top Devoluções — {dev_month_selected}",
        height=320,
    )
    st.plotly_chart(fig_dev, use_container_width=True)

with d2:
    st.markdown(
        "**Top 10 Locais Internos - Filtro de Dia Dinâmico**"
    )
    day_selected_loc = st.selectbox(
        "Mudar Dia (Top Locais)", days_list, index=0, key="day_loc_filter"
    )

    day_df = df.copy()
    if day_selected_loc != "Todos":
        day_df = day_df[day_df["Data_Str"] == day_selected_loc]

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
        title=f"Top 10 Locais no Dia — {day_selected_loc}",
        height=320,
    )
    st.plotly_chart(fig_dia, use_container_width=True)

# --- 7. TABELAS DETALHADAS ---
st.markdown("---")
st.markdown("### 📅 Detalhamento Operacional de Registros")

tab_mes_view, tab_dia_view = st.tabs(
    ["Por Mês (Top 3 Locais)", "Por Dia (Top 3 Locais)"]
)

with tab_mes_view:
    c_m1, c_m2 = st.columns([1, 2])
    with c_m1:
        month_for_table = st.selectbox(
            "📅 Selecionar Mês:", months_order, index=9, key="tb_month_filter"
        )

    month_df = df.copy()
    if month_for_table != "Todos":
        month_df = month_df[month_df["Mês_Clean"] == month_for_table]

    top_3_month_locals = (
        month_df["Local Interno"].value_counts().head(3).index.tolist()
    )

    if top_3_month_locals:
        with c_m2:
            selected_top_local_m = st.selectbox(
                "🎯 Filtrar Local Interno (Mês):",
                ["Exibir em Abas Separadas (Top 3)"] + top_3_month_locals,
                key="top_3_local_m_filter",
            )

        def get_month_local_table(local_name):
            c_df = month_df[month_df["Local Interno"] == local_name]
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
                    st.markdown(
                        f"**Registros do Local no Mês ({month_for_table}):**"
                        f" `{local_item}`"
                    )
                    st.dataframe(
                        tb_local[
                            ["Problema", "Descrição", "Quantidade de Chamados"]
                        ],
                        use_container_width=True,
                        hide_index=True,
                    )
        else:
            tb_single_m = get_month_local_table(selected_top_local_m)
            st.markdown(
                f"**Registros do Local no Mês ({month_for_table}):**"
                f" `{selected_top_local_m}`"
            )
            st.dataframe(
                tb_single_m[["Problema", "Descrição", "Quantidade de Chamados"]],
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.warning("Nenhum registro encontrado para o mês selecionado.")

with tab_dia_view:
    c_d1, c_d2 = st.columns([1, 2])
    with c_d1:
        day_for_table = st.selectbox(
            "📆 Selecionar Dia:", days_list, index=0, key="tb_day_filter"
        )

    day_df_tb = df.copy()
    if day_for_table != "Todos":
        day_df_tb = day_df_tb[day_df_tb["Data_Str"] == day_for_table]

    top_3_day_locals = (
        day_df_tb["Local Interno"].value_counts().head(3).index.tolist()
    )

    if top_3_day_locals:
        with c_d2:
            selected_top_local_d = st.selectbox(
                "🎯 Filtrar Local Interno (Dia):",
                ["Exibir em Abas Separadas (Top 3)"] + top_3_day_locals,
                key="top_3_local_d_filter",
            )

        def get_day_local_table(local_name):
            c_df = day_df_tb[day_df_tb["Local Interno"] == local_name]
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
                    st.markdown(
                        f"**Registros do Local no Dia ({day_for_table}):**"
                        f" `{local_item}`"
                    )
                    st.dataframe(
                        tb_local_d[
                            ["Problema", "Descrição", "Quantidade de Chamados"]
                        ],
                        use_container_width=True,
                        hide_index=True,
                    )
        else:
            tb_single_d = get_day_local_table(selected_top_local_d)
            st.markdown(
                f"**Registros do Local no Dia ({day_for_table}):**"
                f" `{selected_top_local_d}`"
            )
            st.dataframe(
                tb_single_d[["Problema", "Descrição", "Quantidade de Chamados"]],
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.warning("Nenhum registro encontrado para o dia selecionado.")