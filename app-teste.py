import streamlit as st
import streamlit.components.v1 as components
import json
import pandas as pd
import re
import os
import base64

# Links oficiais dos Web Apps do Google Apps Script
APPS_SCRIPT_SAC_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbyGRxQBo5j-gWQ4OEeGFqfwzgjcfQRzDKE2kKbyQeSvOKOdIMr1snR8YV766KBfE7RY9w/exec"

st.set_page_config(
    page_title="Painel Executivo de Gestão & SAC",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        max-width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# CARREGAMENTO DO LOGOTIPO
# ==============================================================================
def obter_logo_base64():
    pastas_busca = [
        os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() else "",
        os.getcwd(),
        "."
    ]
    nomes_alvo = [
        "Logotipo.PNG", "Logotipo.png", "logotipo.PNG", "logotipo.png",
        "LOGOTIPO.PNG", "logo.PNG", "logo.png"
    ]
    for pasta in pastas_busca:
        if not pasta:
            continue
        for nome in nomes_alvo:
            candidato = os.path.join(pasta, nome)
            if os.path.isfile(candidato):
                ext = os.path.splitext(candidato)[1].lower().replace(".", "")
                mime = "jpeg" if ext in ["jpg", "jpeg"] else "png"
                with open(candidato, "rb") as f:
                    return f"data:image/{mime};base64,{base64.b64encode(f.read()).decode('utf-8')}"
    return ""

logo_base64_src = obter_logo_base64()

# IDs e GIDs de Planilhas
SPREADSHEET_SAC_ID = "1YUS9AwQti0Gl79X-TGCIqZSkOfF0bE0BX5gyDClo3rc"
GID_SAC_CHAMADOS = "0"
GID_SAC_CLIENTES = "1332839106"

SPREADSHEET_SAC_CONFIG_ID = "1vOa6QpGPZ6rZ1doT2RRU1SAXWR5usPzv"
GID_SAC_CONFIGS = "1833376686"
GID_SAC_USUARIOS = "772646879"

URL_CSV_SAC_CHAMADOS = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_SAC_ID}/export?format=csv&gid={GID_SAC_CHAMADOS}"
URL_CSV_SAC_CLIENTES = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_SAC_ID}/export?format=csv&gid={GID_SAC_CLIENTES}"
URL_CSV_SAC_CONFIGS = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_SAC_CONFIG_ID}/export?format=csv&gid={GID_SAC_CONFIGS}"
URL_CSV_SAC_USUARIOS = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_SAC_CONFIG_ID}/export?format=csv&gid={GID_SAC_USUARIOS}"

@st.cache_data(ttl=5)
def carregar_dados_sac():
    clientes_dados = []
    cidades_clientes = []
    try:
        df_cli = pd.read_csv(URL_CSV_SAC_CLIENTES, dtype=str)
        if df_cli is not None and not df_cli.empty:
            col_a = df_cli.columns[0]
            col_b = df_cli.columns[1] if len(df_cli.columns) > 1 else col_a
            col_f = df_cli.columns[5] if len(df_cli.columns) > 5 else df_cli.columns[-1]
            for _, r in df_cli.iterrows():
                cli = str(r[col_a]).strip() if pd.notna(r[col_a]) else ""
                loc = str(r[col_b]).strip() if pd.notna(r[col_b]) else ""
                cid = str(r[col_f]).strip() if pd.notna(r[col_f]) else ""
                if cli and cli.lower() not in ["nan", "cliente"]:
                    clientes_dados.append({
                        "cliente": cli,
                        "local": loc,
                        "cidade": cid
                    })
                    if cid and cid.lower() not in ["nan", "cidade", "filial", "filial responsável"]:
                        cidades_clientes.append(cid)
    except Exception:
        pass

    formas_pagamento = []
    problemas = []
    descricoes = []
    try:
        df_cfg = pd.read_csv(URL_CSV_SAC_CONFIGS, dtype=str)
        if df_cfg is not None and not df_cfg.empty:
            if len(df_cfg.columns) > 0:
                col_a = df_cfg.columns[0]
                formas_pagamento = [str(x).strip() for x in df_cfg[col_a].dropna().unique() if str(x).strip() and str(x).lower() not in ["nan", "forma de pagamento", "forma"]]
            if len(df_cfg.columns) > 11:
                col_l = df_cfg.columns[11]
                problemas = [str(x).strip() for x in df_cfg[col_l].dropna().unique() if str(x).strip() and str(x).lower() not in ["nan", "problemas", "problema"]]
            if len(df_cfg.columns) > 13:
                col_n = df_cfg.columns[13]
                descricoes = [str(x).strip() for x in df_cfg[col_n].dropna().unique() if str(x).strip() and str(x).lower() not in ["nan", "descrição", "descricao"]]
    except Exception:
        pass

    usuarios_validos = []
    try:
        df_usr = pd.read_csv(URL_CSV_SAC_USUARIOS, dtype=str)
        if df_usr is not None and not df_usr.empty:
            col_u = df_usr.columns[0]
            col_s = df_usr.columns[1] if len(df_usr.columns) > 1 else col_u
            for _, r in df_usr.iterrows():
                u = str(r[col_u]).strip() if pd.notna(r[col_u]) else ""
                s = str(r[col_s]).strip() if pd.notna(r[col_s]) else ""
                if u and u.lower() not in ["nan", "usuario", "usuário"]:
                    usuarios_validos.append({"usuario": u, "senha": s})
    except Exception:
        pass

    maior_sac_ano = {}
    chamados_salvos = []
    try:
        df_ch = pd.read_csv(URL_CSV_SAC_CHAMADOS, dtype=str)
        if df_ch is not None and not df_ch.empty:
            cols = [c.strip() for c in df_ch.columns]
            
            def get_col(candidates):
                for cand in candidates:
                    for c in cols:
                        if c.lower() == cand.lower():
                            return c
                return None

            col_chamado = get_col(["Chamado", "chamado"]) or cols[0]
            col_data = get_col(["Data", "data"]) or (cols[1] if len(cols) > 1 else "")
            col_cli = get_col(["Cliente", "cliente"]) or (cols[2] if len(cols) > 2 else "")
            col_loc = get_col(["Local Interno", "local interno", "localInterno"]) or (cols[3] if len(cols) > 3 else "")
            col_cid = get_col(["Filial Responsável", "Filial Responsavel", "Cidade", "cidade"]) or (cols[4] if len(cols) > 4 else "")
            col_desc = get_col(["Descrição", "Descricao", "descricao"]) or (cols[5] if len(cols) > 5 else "")
            col_prod = get_col(["Produto", "produto"]) or (cols[6] if len(cols) > 6 else "")
            col_dt_trans = get_col(["Data da Transação", "Data da Transacao", "dataTransacao"]) or (cols[7] if len(cols) > 7 else "")
            col_hr_trans = get_col(["Hora da Transação", "Hora da Transacao", "horaTransacao"]) or (cols[8] if len(cols) > 8 else "")
            col_val = get_col(["Valor", "Valor(R$)", "valor"]) or (cols[9] if len(cols) > 9 else "")
            col_nome = get_col(["Nome/Sobrenome", "Nome", "nomeSobrenome"]) or (cols[10] if len(cols) > 10 else "")
            col_cel = get_col(["Celular", "celular"]) or (cols[11] if len(cols) > 11 else "")
            col_prob = get_col(["Problemas", "Problema", "problemas"]) or (cols[12] if len(cols) > 12 else "")
            col_pag = get_col(["Forma de Pagamento", "Forma Pagamento", "formaPgto"]) or (cols[13] if len(cols) > 13 else "")
            col_reemb = get_col(["Reembolso", "reembolso", "Reebolso"])
            col_pix = get_col(["Pix - Reembolso", "Pix", "pix"])
            col_atend = get_col(["Atendente", "atendente"])
            col_dthr = get_col(["Data/Hora do lançamento", "Data/Hora", "dataHoraLancamento"])

            for idx, r in df_ch.iterrows():
                val = str(r[col_chamado]).strip() if col_chamado and pd.notna(r[col_chamado]) else ""
                if not val or val.lower() in ["nan", "chamado"]:
                    continue

                m = re.search(r'SAC-(\d{4})-(\d+)', val, re.IGNORECASE)
                if m:
                    ano = m.group(1)
                    seq = int(m.group(2))
                    maior_sac_ano[ano] = max(maior_sac_ano.get(ano, 0), seq)

                def get_val(col_name):
                    return str(r[col_name]).strip() if col_name and col_name in r and pd.notna(r[col_name]) else ""

                chamados_salvos.append({
                    "linha": idx + 2,
                    "chamado": val,
                    "data": get_val(col_data),
                    "cliente": get_val(col_cli),
                    "localInterno": get_val(col_loc),
                    "cidade": get_val(col_cid),
                    "descricao": get_val(col_desc),
                    "produto": get_val(col_prod),
                    "dataTransacao": get_val(col_dt_trans),
                    "horaTransacao": get_val(col_hr_trans),
                    "valor": get_val(col_val),
                    "nomeSobrenome": get_val(col_nome),
                    "celular": get_val(col_cel),
                    "problemas": get_val(col_prob),
                    "formaPgto": get_val(col_pag),
                    "reembolso": get_val(col_reemb),
                    "pix": get_val(col_pix),
                    "atendente": get_val(col_atend),
                    "dataHoraLancamento": get_val(col_dthr)
                })
    except Exception:
        pass

    chamados_salvos.reverse()

    return {
        "clientes": clientes_dados,
        "formas_pagamento": sorted(formas_pagamento),
        "cidades": sorted(list(set(cidades_clientes))),
        "problemas": sorted(problemas),
        "descricoes": sorted(descricoes),
        "usuarios": usuarios_validos,
        "maior_sac_ano": maior_sac_ano,
        "chamados": chamados_salvos
    }

dados_sac = carregar_dados_sac()
dados_sac_json = json.dumps(dados_sac, ensure_ascii=False)
total_chamados_carregados = len(dados_sac["chamados"])

html_code = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dashboard Executivo - Gestão SAC</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2"></script>
  <script src="https://unpkg.com/lucide@latest"></script>
  <style>
    body {{ 
      font-family: 'Inter', system-ui, -apple-system, sans-serif; 
      background-color: #f1f5f9; 
      color: #1e293b; 
    }}
    .kpi-card {{
      background-color: #ffffff;
      border: 1px solid #e2e8f0;
      transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    .kpi-card:hover {{
      transform: translateY(-2px);
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }}
    .nav-btn.active {{ 
      background-color: #0284c7; 
      color: #ffffff; 
      box-shadow: 0 4px 6px -1px rgba(2, 132, 199, 0.25);
    }}
    .nav-btn.inactive {{ 
      background-color: #ffffff; 
      color: #64748b; 
      border: 1px solid #e2e8f0; 
    }}
  </style>
</head>
<body class="bg-slate-100 min-h-screen">

  <iframe name="target_post_frame" id="target_post_frame" style="display:none; width:0; height:0; border:0;"></iframe>
  <form id="hiddenSACSubmissionForm" action="{APPS_SCRIPT_SAC_WEBAPP_URL}" method="POST" target="target_post_frame" style="display:none;">
    <input type="hidden" name="data" id="hiddenSACSubmissionData">
  </form>

  <!-- MODAL DE PROCESSAMENTO / AÇÃO EM ANDAMENTO -->
  <div id="modalLoadingAcao" class="hidden fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
    <div class="bg-white rounded-3xl p-6 sm:p-8 max-w-sm w-full shadow-2xl border border-slate-100 flex flex-col items-center text-center space-y-4 animate-in fade-in zoom-in duration-200">
      <div id="modalIconContainer" class="w-16 h-16 rounded-2xl bg-sky-50 text-sky-600 flex items-center justify-center shadow-inner">
        <svg id="modalSpinner" class="animate-spin h-8 w-8 text-sky-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
        </svg>
        <i id="modalIconCheck" data-lucide="check" class="hidden w-8 h-8 text-emerald-600"></i>
        <i id="modalIconTrash" data-lucide="trash-2" class="hidden w-8 h-8 text-rose-600"></i>
      </div>
      <div>
        <h3 id="modalLoadingTitle" class="text-base font-bold text-slate-900">Processando Ação...</h3>
        <p id="modalLoadingSub" class="text-xs text-slate-500 mt-1">Sua solicitação está sendo transmitida e registrada na planilha Chamados.</p>
      </div>
      <div id="modalProgressBar" class="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
        <div class="bg-sky-500 h-full w-2/3 animate-pulse"></div>
      </div>
    </div>
  </div>

  <!-- Header Superior -->
  <header class="sticky top-0 z-40 bg-white/95 border-b border-slate-200 backdrop-blur-md px-6 py-3">
    <div class="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
      <div class="flex items-center gap-4">
        <div class="flex items-center justify-center p-1 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden" style="height: 54px; min-width: 54px;">
          <img id="headerLogoImg" src="{logo_base64_src}" alt="Logotipo" class="max-h-12 w-auto object-contain" onerror="this.style.display='none'; document.getElementById('headerFallbackIcon').style.display='flex';">
          <div id="headerFallbackIcon" style="display: {'none' if logo_base64_src else 'flex'};" class="w-10 h-10 bg-amber-700 text-white rounded-lg items-center justify-center font-black text-sm">
            ☕
          </div>
        </div>
        <div>
          <h1 class="text-xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            Painel Executivo de Gestão & SAC
          </h1>
          <p class="text-xs text-slate-500">Controle Operacional, Atendimento & Análises · {total_chamados_carregados} chamados registrados</p>
        </div>
      </div>
      
      <!-- Navegação Entre Páginas -->
      <div class="flex items-center gap-2 bg-slate-100 p-1.5 rounded-2xl border border-slate-200 flex-wrap">
        <button id="navDashboardSAC" type="button" class="nav-btn active flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition" onclick="switchPage('dashboardSAC')">
          <i data-lucide="bar-chart-3" class="w-4 h-4"></i>
          Dashboard SAC
        </button>
        <button id="navSAC" type="button" class="nav-btn inactive flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition" onclick="switchPage('sac')">
          <i data-lucide="headphones" class="w-4 h-4"></i>
          Lançamento SAC
        </button>
        <button type="button" onclick="executarRefresh()" title="Clique para recarregar da planilha" class="inline-flex items-center px-3 py-1.5 rounded-xl text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-300 hover:bg-emerald-100 cursor-pointer transition">
          <span class="w-2 h-2 rounded-full bg-emerald-500 mr-2 animate-pulse"></span> Sincronizar 🔄
        </button>
      </div>
    </div>
  </header>

  <main class="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">

    <!-- PÁGINA 1: DASHBOARD SAC -->
    <div id="pageDashboardSAC" class="space-y-6">
      <section class="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-2 text-sm font-semibold text-slate-700">
            <i data-lucide="sliders" class="w-4 h-4 text-sky-500"></i>
            <span>Filtros do Painel SAC</span>
          </div>
          <span id="badgeFiltroSAC" class="text-xs font-medium text-slate-500">Filtrando: Todos os chamados</span>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label class="block text-xs font-medium text-slate-500 mb-1">Cliente</label>
            <select id="filterSACCliente" class="w-full text-sm rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 text-slate-800">
              <option value="ALL">Todos os Clientes</option>
            </select>
          </div>

          <div>
            <label class="block text-xs font-medium text-slate-500 mb-1">Produto</label>
            <select id="filterSACProduto" class="w-full text-sm rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 text-slate-800">
              <option value="ALL">Todos os Produtos</option>
              <option value="Café">Café</option>
              <option value="Snaky">Snaky</option>
            </select>
          </div>

          <div>
            <label class="block text-xs font-medium text-slate-500 mb-1">Atendente</label>
            <select id="filterSACAtendente" class="w-full text-sm rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 text-slate-800">
              <option value="ALL">Todos os Atendentes</option>
            </select>
          </div>

          <div class="flex items-end">
            <button id="btnLimparFiltrosSAC" class="w-full py-2 px-4 rounded-xl border border-slate-300 bg-slate-100 text-xs font-semibold text-slate-600 hover:bg-slate-200 transition flex items-center justify-center gap-1.5 cursor-pointer">
              <i data-lucide="rotate-ccw" class="w-3.5 h-3.5"></i>
              Limpar Filtros
            </button>
          </div>
        </div>
      </section>

      <!-- CARDS KPIS DO SAC -->
      <section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <div class="kpi-card p-4 rounded-2xl shadow-sm flex flex-col justify-between">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Total de Chamados</span>
            <span class="p-1.5 rounded-lg bg-sky-50 text-sky-600"><i data-lucide="headphones" class="w-4 h-4"></i></span>
          </div>
          <div class="mt-3">
            <span id="kpiSACTotal" class="text-xl font-bold tracking-tight text-slate-800">0</span>
            <p id="kpiSACTotalSub" class="text-[11px] text-slate-400 mt-0.5">Ocorrências registradas</p>
          </div>
        </div>

        <div class="kpi-card p-4 rounded-2xl shadow-sm flex flex-col justify-between border-emerald-200">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-semibold text-emerald-600 uppercase tracking-wider">Valor Ressarcido</span>
            <span class="p-1.5 rounded-lg bg-emerald-50 text-emerald-600"><i data-lucide="badge-dollar-sign" class="w-4 h-4"></i></span>
          </div>
          <div class="mt-3">
            <span id="kpiSACValorTotal" class="text-xl font-bold tracking-tight text-emerald-600">R$ 0,00</span>
            <p class="text-[11px] text-slate-400 mt-0.5">Soma total de reembolsos</p>
          </div>
        </div>

        <div class="kpi-card p-4 rounded-2xl shadow-sm flex flex-col justify-between border-amber-200">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-semibold text-amber-600 uppercase tracking-wider">Chamados Café</span>
            <span class="p-1.5 rounded-lg bg-amber-50 text-amber-600"><i data-lucide="coffee" class="w-4 h-4"></i></span>
          </div>
          <div class="mt-3 flex items-baseline justify-between">
            <div>
              <span id="kpiSACCafé" class="text-xl font-bold tracking-tight text-amber-700">0</span>
              <p class="text-[11px] text-slate-400 mt-0.5">Linha de Bebidas</p>
            </div>
            <span id="kpiSACCaféPct" class="text-xs font-semibold px-2 py-0.5 rounded-md bg-amber-100 text-amber-800">0%</span>
          </div>
        </div>

        <div class="kpi-card p-4 rounded-2xl shadow-sm flex flex-col justify-between border-indigo-200">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-semibold text-indigo-600 uppercase tracking-wider">Chamados Snaky</span>
            <span class="p-1.5 rounded-lg bg-indigo-50 text-indigo-600"><i data-lucide="cookie" class="w-4 h-4"></i></span>
          </div>
          <div class="mt-3 flex items-baseline justify-between">
            <div>
              <span id="kpiSACSnaky" class="text-xl font-bold tracking-tight text-indigo-600">0</span>
              <p class="text-[11px] text-slate-400 mt-0.5">Máquinas de Snacks</p>
            </div>
            <span id="kpiSACSnakyPct" class="text-xs font-semibold px-2 py-0.5 rounded-md bg-indigo-100 text-indigo-800">0%</span>
          </div>
        </div>

        <div class="kpi-card p-4 rounded-2xl shadow-sm flex flex-col justify-between">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Clientes Únicos</span>
            <span class="p-1.5 rounded-lg bg-blue-50 text-blue-600"><i data-lucide="building" class="w-4 h-4"></i></span>
          </div>
          <div class="mt-3">
            <span id="kpiSACClientes" class="text-xl font-bold tracking-tight text-slate-800">0</span>
            <p class="text-[11px] text-slate-400 mt-0.5">Pontos atendidos</p>
          </div>
        </div>

        <div class="kpi-card p-4 rounded-2xl shadow-sm flex flex-col justify-between">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Ticket Médio</span>
            <span class="p-1.5 rounded-lg bg-cyan-50 text-cyan-600"><i data-lucide="calculator" class="w-4 h-4"></i></span>
          </div>
          <div class="mt-3">
            <span id="kpiSACTicketMedio" class="text-xl font-bold tracking-tight text-slate-800">R$ 0,00</span>
            <p class="text-[11px] text-slate-400 mt-0.5">Média por chamado</p>
          </div>
        </div>
      </section>

      <!-- GRÁFICOS DO DASHBOARD SAC -->
      <section class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div class="flex items-center justify-between mb-3">
            <div>
              <h3 class="font-bold text-base text-slate-800 flex items-center gap-2">
                <i data-lucide="bar-chart-2" class="w-4 h-4 text-sky-600"></i>
                Top 10 Problemas Mais Frequentes
              </h3>
              <p class="text-xs text-slate-400">Classificação de ocorrências recorrentes no SAC</p>
            </div>
            <span class="text-[11px] font-semibold px-2 py-0.5 rounded bg-sky-50 text-sky-700 border border-sky-200">Ocorrências</span>
          </div>
          <div class="relative h-80"><canvas id="chartTopProblemasSAC"></canvas></div>
        </div>

        <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div class="flex items-center justify-between mb-3">
            <div>
              <h3 class="font-bold text-base text-slate-800 flex items-center gap-2">
                <i data-lucide="users" class="w-4 h-4 text-emerald-600"></i>
                Chamados por Atendente
              </h3>
              <p class="text-xs text-slate-400">Volume de atendimentos realizados por operador</p>
            </div>
            <span class="text-[11px] font-semibold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">Volume</span>
          </div>
          <div class="relative h-80"><canvas id="chartAtendentesSAC"></canvas></div>
        </div>
      </section>
    </div>

    <!-- PÁGINA 2: LANÇAMENTO SAC -->
    <div id="pageSAC" class="hidden space-y-6">

      <!-- TELA DE LOGIN / AUTENTICAÇÃO -->
      <div id="sacAuthScreen" class="max-w-md mx-auto my-8 bg-white p-8 rounded-3xl border border-slate-200 shadow-xl space-y-6">
        <div class="text-center space-y-2">
          <div class="w-14 h-14 bg-sky-100 text-sky-700 rounded-2xl flex items-center justify-center mx-auto shadow-inner">
            <i data-lucide="lock" class="w-7 h-7"></i>
          </div>
          <h2 class="text-xl font-black text-slate-900">Acesso Restrito ao SAC</h2>
          <p class="text-xs text-slate-500">Validação oficial na aba "Usuarios" (Colunas A e B)</p>
        </div>

        <form id="sacLoginForm" onsubmit="realizarLoginSAC(event)" class="space-y-4">
          <div>
            <label class="block text-xs font-bold text-slate-700 mb-1">Usuário *</label>
            <input type="text" id="sacLoginUser" placeholder="Digite seu usuário..." required class="w-full text-sm rounded-xl border border-slate-300 bg-slate-50 px-3.5 py-2.5 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500 font-medium">
          </div>
          <div>
            <label class="block text-xs font-bold text-slate-700 mb-1">Senha *</label>
            <input type="password" id="sacLoginPass" placeholder="••••••••" required class="w-full text-sm rounded-xl border border-slate-300 bg-slate-50 px-3.5 py-2.5 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500">
          </div>
          <div id="sacLoginErro" class="hidden p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-semibold flex items-center gap-2">
            <i data-lucide="alert-circle" class="w-4 h-4"></i>
            <span>Usuário ou senha incorretos!</span>
          </div>
          <button type="submit" class="w-full py-2.5 px-4 rounded-xl bg-sky-600 hover:bg-sky-700 text-white font-bold text-xs shadow-md shadow-sky-600/25 transition flex items-center justify-center gap-2 cursor-pointer">
            <i data-lucide="log-in" class="w-4 h-4"></i>
            Acessar Formulário do SAC
          </button>
        </form>
      </div>

      <!-- PAINEL DO FORMULÁRIO DO SAC -->
      <div id="sacMainPanel" class="hidden space-y-6">

        <!-- ALERTA DE EDIÇÃO DE CHAMADO -->
        <div id="alertSACEditMode" class="hidden p-4 rounded-2xl bg-amber-50 border border-amber-300 text-amber-900 flex justify-between items-center shadow-sm">
          <div class="flex items-center gap-3">
            <div class="p-2 bg-amber-500 text-white rounded-xl"><i data-lucide="edit-3" class="w-5 h-5"></i></div>
            <div>
              <p class="text-sm font-bold">Modo de Edição de Chamado: <span id="labelSACEditChamado" class="font-mono text-amber-800">SAC-0000-0000</span></p>
              <p class="text-xs text-amber-700">Você está alterando este chamado do SAC. Ao salvar, os dados serão atualizados na planilha.</p>
            </div>
          </div>
          <button type="button" onclick="cancelarEdicaoSAC()" class="px-3 py-1.5 bg-amber-200 hover:bg-amber-300 rounded-xl text-xs font-bold text-amber-900 transition cursor-pointer">
            Cancelar Edição ✕
          </button>
        </div>

        <!-- MENSAGEM NO TOPO DINÂMICA (SUCESSO / EDIÇÃO / EXCLUSÃO) -->
        <div id="alertSACSuccess" class="hidden p-5 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-900 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-sm transition">
          <div class="flex items-center gap-3">
            <div id="alertSACIconBadge" class="p-2 bg-emerald-600 text-white rounded-xl">
              <i id="alertSACLucideIcon" data-lucide="check-circle" class="w-5 h-5"></i>
            </div>
            <div>
              <p id="alertSACSuccessTitle" class="text-sm font-bold">Ação realizada com sucesso!</p>
              <p id="alertSACSuccessSub" class="text-xs text-emerald-700">A planilha oficial foi atualizada em tempo real.</p>
            </div>
          </div>
          <button type="button" onclick="document.getElementById('alertSACSuccess').classList.add('hidden')" class="px-3 py-2 rounded-xl hover:bg-emerald-100 text-xs font-semibold text-emerald-800 transition cursor-pointer">
            Fechar
          </button>
        </div>

        <section class="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-4 mb-6 border-b border-slate-100 gap-4">
            <div class="flex items-center gap-3">
              <div class="p-2.5 bg-sky-600 text-white rounded-xl shadow-lg shadow-sky-500/25">
                <i data-lucide="headphones" class="w-6 h-6"></i>
              </div>
              <div>
                <h2 id="sacFormTitleText" class="text-base font-bold text-slate-900">Lançamento de Ocorrências do SAC</h2>
                <p class="text-xs text-slate-500">Registro de chamados, ressarcimentos e reembolsos · Aba: Chamados</p>
              </div>
            </div>
            <div class="flex items-center gap-3">
              <div class="text-right">
                <span class="text-[10px] uppercase font-bold text-slate-400 block">Atendente Conectado</span>
                <span id="labelSACAtendenteLogado" class="text-xs font-bold text-sky-800 bg-sky-50 px-2.5 py-1 rounded-lg border border-sky-200">Operador</span>
              </div>
              <button type="button" onclick="realizarLogoutSAC()" title="Sair do SAC" class="p-2 rounded-xl border border-slate-200 hover:bg-rose-50 text-slate-500 hover:text-rose-600 transition cursor-pointer">
                <i data-lucide="log-out" class="w-4 h-4"></i>
              </button>
            </div>
          </div>

          <form id="sacForm" onsubmit="handleSACSubmit(event)" class="space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 p-5 rounded-2xl bg-slate-50/90 border border-slate-200">
              
              <!-- Chamado com Trava Atômica e Prévia de Numeração -->
              <div>
                <label class="block text-xs font-bold text-sky-900 mb-1">Chamado (Automático) *</label>
                <input type="text" id="sacChamado" readonly class="w-full text-sm font-mono font-black rounded-xl border border-sky-300 bg-white px-3.5 py-2 text-sky-700 cursor-not-allowed shadow-inner" placeholder="[Automático do Servidor]">
                <span class="text-[10px] text-slate-400 mt-0.5 block">🔒 Número atômico gerado no envio</span>
              </div>

              <!-- Data do Chamado -->
              <div>
                <label class="block text-xs font-semibold text-slate-700 mb-1">Data *</label>
                <input type="date" id="sacData" required class="w-full text-sm rounded-xl border border-slate-300 bg-white px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500">
              </div>

              <!-- Cliente (Travado na pré-lista da aba Clientes coluna A) -->
              <div>
                <label class="block text-xs font-semibold text-slate-700 mb-1">Cliente *</label>
                <input list="listaSACClientes" id="sacCliente" placeholder="Selecione o cliente..." required onchange="validarInputComLista('sacCliente', 'listaSACClientes', 'Cliente', true)" onblur="validarInputComLista('sacCliente', 'listaSACClientes', 'Cliente', true)" class="w-full text-sm font-semibold rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500">
                <datalist id="listaSACClientes"></datalist>
              </div>

              <!-- Local Interno (Travado nos locais do cliente selecionado da aba Clientes coluna B) -->
              <div>
                <label class="block text-xs font-semibold text-slate-700 mb-1">Local Interno *</label>
                <select id="sacLocalInterno" required onchange="aoMudarLocalInternoSAC()" class="w-full text-sm rounded-xl border border-slate-300 bg-white px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500">
                  <option value="">Selecione primeiro o Cliente...</option>
                </select>
              </div>

              <!-- Filial Responsável (Antiga Cidade, vinculada ao Cliente/Local da aba Clientes coluna F com datalist) -->
              <div>
                <label class="block text-xs font-semibold text-slate-700 mb-1">Filial Responsável *</label>
                <input list="listaSACCidades" id="sacCidade" placeholder="Filial de atendimento..." required onchange="validarInputComLista('sacCidade', 'listaSACCidades', 'Filial Responsável')" onblur="validarInputComLista('sacCidade', 'listaSACCidades', 'Filial Responsável')" class="w-full text-sm rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500">
                <datalist id="listaSACCidades"></datalist>
              </div>

              <!-- Descrição (Travada na pré-lista da coluna N) -->
              <div class="md:col-span-2 lg:col-span-3">
                <label class="block text-xs font-semibold text-slate-700 mb-1">Descrição *</label>
                <input list="listaSACDescricoes" id="sacDescricao" placeholder="Selecione a descrição do ocorrido..." required onchange="validarInputComLista('sacDescricao', 'listaSACDescricoes', 'Descrição')" onblur="validarInputComLista('sacDescricao', 'listaSACDescricoes', 'Descrição')" class="w-full text-sm rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500">
                <datalist id="listaSACDescricoes"></datalist>
              </div>

              <!-- Produto (Começa limpo/vazio) -->
              <div>
                <label class="block text-xs font-semibold text-slate-700 mb-1">Produto *</label>
                <select id="sacProduto" required class="w-full text-sm font-semibold rounded-xl border border-slate-300 bg-white px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500">
                  <option value="" selected disabled>Selecione o Produto...</option>
                  <option value="Café">Café</option>
                  <option value="Snaky">Snaky</option>
                </select>
              </div>

              <!-- Data da Transação (Começa Zerado/Vazio e é OBRIGATÓRIO) -->
              <div>
                <label class="block text-xs font-semibold text-slate-700 mb-1">Data da Transação *</label>
                <input type="date" id="sacDataTransacao" required class="w-full text-sm rounded-xl border border-slate-300 bg-white px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500">
              </div>

              <!-- Hora da Transação (Começa Zerado/Vazio e é OBRIGATÓRIO) -->
              <div>
                <label class="block text-xs font-semibold text-slate-700 mb-1">Hora da Transação *</label>
                <input type="time" id="sacHoraTransacao" required class="w-full text-sm rounded-xl border border-slate-300 bg-white px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500">
              </div>

              <!-- Valor (R$) -->
              <div>
                <label class="block text-xs font-semibold text-emerald-800 mb-1">Valor (R$) *</label>
                <input type="number" step="0.01" min="0" id="sacValor" placeholder="0,00" required class="w-full text-sm font-bold rounded-xl border border-emerald-300 bg-white px-3 py-2 text-emerald-900 focus:outline-none focus:ring-2 focus:ring-emerald-500">
              </div>

              <!-- Nome / Sobrenome -->
              <div class="md:col-span-2">
                <label class="block text-xs font-semibold text-slate-700 mb-1">Nome / Sobrenome *</label>
                <input type="text" id="sacNome" placeholder="Ex: João Da Silva" required onblur="formatarNomeProprio(this)" class="w-full text-sm rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500">
              </div>

              <!-- Celular -->
              <div class="md:col-span-2">
                <label class="block text-xs font-semibold text-slate-700 mb-1">Celular *</label>
                <input type="text" id="sacCelular" placeholder="(00) 00000-0000" required class="w-full text-sm rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500">
              </div>

              <!-- Problemas (Travado na pré-lista da coluna L) -->
              <div class="md:col-span-2">
                <label class="block text-xs font-semibold text-slate-700 mb-1">Problemas *</label>
                <input list="listaSACProblemas" id="sacProblema" placeholder="Selecione o problema..." required onchange="validarInputComLista('sacProblema', 'listaSACProblemas', 'Problemas')" onblur="validarInputComLista('sacProblema', 'listaSACProblemas', 'Problemas')" class="w-full text-sm rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500">
                <datalist id="listaSACProblemas"></datalist>
              </div>

              <!-- Forma de Pagamento (Travada na pré-lista da coluna A) -->
              <div class="md:col-span-2">
                <label class="block text-xs font-semibold text-slate-700 mb-1">Forma de Pagamento *</label>
                <input list="listaSACFormasPgto" id="sacFormaPgto" placeholder="Selecione a forma de pagamento..." required onchange="validarInputComLista('sacFormaPgto', 'listaSACFormasPgto', 'Forma de Pagamento')" onblur="validarInputComLista('sacFormaPgto', 'listaSACFormasPgto', 'Forma de Pagamento')" class="w-full text-sm rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500">
                <datalist id="listaSACFormasPgto"></datalist>
              </div>

              <!-- Reembolso (Não obrigatório) -->
              <div class="md:col-span-2">
                <label class="block text-xs font-bold text-sky-900 mb-1">Reembolso</label>
                <input type="text" id="sacReembolso" placeholder="Como foi feito o reembolso (Ex: Pix, Crédito Máquina, Dinheiro)..." class="w-full text-sm rounded-xl border border-sky-300 bg-white px-3.5 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500">
              </div>

              <!-- Pix - Reembolso -->
              <div class="md:col-span-2">
                <label class="block text-xs font-semibold text-slate-700 mb-1">Pix - Reembolso</label>
                <input type="text" id="sacPix" placeholder="Chave Pix (CPF, Celular, E-mail ou Aleatória)..." class="w-full text-sm rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500">
              </div>

              <!-- Atendente -->
              <div>
                <label class="block text-xs font-semibold text-slate-700 mb-1">Atendente *</label>
                <input type="text" id="sacAtendente" readonly class="w-full text-sm font-semibold rounded-xl border border-slate-300 bg-slate-100 px-3 py-2 text-slate-700 cursor-not-allowed">
              </div>

              <!-- Data/Hora Lançamento -->
              <div>
                <label class="block text-xs font-semibold text-slate-700 mb-1">Data/Hora Lançamento</label>
                <input type="text" id="sacDataHoraAuto" readonly value="Automático no Envio" class="w-full text-sm rounded-xl border border-slate-300 bg-slate-100 px-3 py-2 text-slate-500 cursor-not-allowed">
              </div>

            </div>

            <div class="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
              <button type="button" onclick="limparFormSAC()" class="px-5 py-2.5 rounded-xl border border-slate-300 bg-white text-xs font-semibold text-slate-600 hover:bg-slate-50 transition cursor-pointer">
                Limpar Campos
              </button>
              <button type="submit" id="btnSalvarSAC" class="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-sky-600 text-white text-xs font-bold shadow-lg shadow-sky-500/25 hover:bg-sky-700 transition cursor-pointer">
                <i data-lucide="send" class="w-4 h-4"></i>
                <span id="btnSalvarSACText">Lançar Ocorrência SAC</span>
              </button>
            </div>
          </form>
        </section>

        <!-- LISTA DE TODOS OS CHAMADOS REALIZADOS (HISTÓRICO COM EDITAR E EXCLUIR) -->
        <section class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-3 border-b border-slate-100">
            <div>
              <h2 class="text-base font-bold flex items-center gap-2 text-slate-800">
                <i data-lucide="list-checks" class="w-4 h-4 text-sky-600"></i>
                Chamados Realizados no SAC
              </h2>
              <p class="text-xs text-slate-500">Histórico completo de ocorrências registradas na aba Chamados</p>
            </div>
            <div class="flex items-center gap-3">
              <div class="relative">
                <i data-lucide="search" class="w-4 h-4 text-slate-400 absolute left-3 top-2.5"></i>
                <input type="text" id="searchSACChamados" placeholder="Buscar chamado, cliente, cliente/nome..." oninput="filtrarChamadosSAC()" class="text-xs pl-9 pr-3 py-2 rounded-xl border border-slate-300 bg-slate-50 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500 w-64">
              </div>
              <span id="badgeContadorSAC" class="text-xs px-2.5 py-1 rounded-lg bg-sky-50 text-sky-700 font-bold border border-sky-200">
                0 chamado(s)
              </span>
            </div>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs text-slate-600">
              <thead class="bg-slate-50 uppercase font-semibold text-slate-500">
                <tr>
                  <th class="py-2.5 px-3 rounded-l-lg">Ações</th>
                  <th class="py-2.5 px-3 font-mono">Chamado</th>
                  <th class="py-2.5 px-3">Data</th>
                  <th class="py-2.5 px-3">Cliente</th>
                  <th class="py-2.5 px-3">Local</th>
                  <th class="py-2.5 px-3">Filial</th>
                  <th class="py-2.5 px-3">Produto</th>
                  <th class="py-2.5 px-3 text-right">Valor</th>
                  <th class="py-2.5 px-3">Nome Cliente</th>
                  <th class="py-2.5 px-3">Reembolso</th>
                  <th class="py-2.5 px-3">Atendente</th>
                  <th class="py-2.5 px-3 rounded-r-lg">Data Lançamento</th>
                </tr>
              </thead>
              <tbody id="tableSACChamadosBody" class="divide-y divide-slate-100">
                <tr>
                  <td colspan="12" class="text-center py-6 text-slate-400 font-semibold">Nenhum chamado registrado ainda.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

      </div>
    </div>

  </main>

  <script>
    lucide.createIcons();
    Chart.register(ChartDataLabels);

    const APPS_SCRIPT_SAC_URL = "{APPS_SCRIPT_SAC_WEBAPP_URL}";
    const dadosSAC = {dados_sac_json};
    let listaChamadosSAC = Array.isArray(dadosSAC.chamados) ? dadosSAC.chamados : [];
    let chamadoEmEdicao = null;
    
    // Tratamento seguro de Storage
    let atendenteSACLogado = "";
    try {{
      atendenteSACLogado = sessionStorage.getItem('sac_atendente_conectado') || "";
    }} catch(e) {{}}

    // =========================================================================
    // TRAVAMENTO RÍGIDO DE PRÉ-LISTA
    // =========================================================================
    function obterValoresDeDatalist(datalistId) {{
      const dl = document.getElementById(datalistId);
      if (!dl) return [];
      return Array.from(dl.options).map(opt => (opt.value || '').trim());
    }}

    function validarInputComLista(inputId, datalistId, nomeAmigavel, dispararCascataCliente = false) {{
      const input = document.getElementById(inputId);
      if (!input) return false;
      const valor = (input.value || '').trim();
      if (!valor) return true;

      const opcoesValidas = obterValoresDeDatalist(datalistId);
      const achado = opcoesValidas.find(item => item.toLowerCase() === valor.toLowerCase());

      if (!achado) {{
        alert('⛔ Bloqueio de Segurança:\\nO valor digitado no campo "' + nomeAmigavel + '" não está cadastrado na base de dados.\\nPor favor, selecione exclusivamente um dos itens disponíveis na listagem.');
        input.value = '';
        if (dispararCascataCliente) {{
          document.getElementById('sacLocalInterno').innerHTML = '<option value="">Selecione primeiro o Cliente...</option>';
          document.getElementById('sacCidade').value = '';
        }}
        setTimeout(() => {{ input.focus(); }}, 50);
        return false;
      }} else {{
        input.value = achado;
        if (dispararCascataCliente) {{
          aoMudarClienteSAC();
        }}
        return true;
      }}
    }}

    // CONTROLE DINÂMICO DE MODAL DE PROCESSAMENTO
    function abrirModalLoading(titulo, subtitulo, tipoAcao = 'loading') {{
      const modal = document.getElementById('modalLoadingAcao');
      if (!modal) return;

      document.getElementById('modalLoadingTitle').innerText = titulo;
      document.getElementById('modalLoadingSub').innerText = subtitulo;

      const spinner = document.getElementById('modalSpinner');
      const iconCheck = document.getElementById('modalIconCheck');
      const iconTrash = document.getElementById('modalIconTrash');
      const progressBar = document.getElementById('modalProgressBar');
      const badge = document.getElementById('modalIconContainer');

      spinner.classList.add('hidden');
      iconCheck.classList.add('hidden');
      iconTrash.classList.add('hidden');
      progressBar.classList.remove('hidden');

      if (tipoAcao === 'loading') {{
        spinner.classList.remove('hidden');
        badge.className = "w-16 h-16 rounded-2xl bg-sky-50 text-sky-600 flex items-center justify-center shadow-inner";
      }} else if (tipoAcao === 'sucesso') {{
        iconCheck.classList.remove('hidden');
        progressBar.classList.add('hidden');
        badge.className = "w-16 h-16 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center shadow-inner";
      }} else if (tipoAcao === 'excluir') {{
        iconTrash.classList.remove('hidden');
        progressBar.classList.add('hidden');
        badge.className = "w-16 h-16 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center shadow-inner";
      }}

      modal.classList.remove('hidden');
      lucide.createIcons();
    }}

    function fecharModalLoading() {{
      const modal = document.getElementById('modalLoadingAcao');
      if (modal) modal.classList.add('hidden');
    }}

    // EXIBE MENSAGEM NO BANNER DO TOPO COM ATUALIZAÇÃO DE TIPO
    function exibirMensagemTopo(titulo, subtitulo, tipo = 'sucesso') {{
      const alertBox = document.getElementById('alertSACSuccess');
      const alertTitle = document.getElementById('alertSACSuccessTitle');
      const alertSub = document.getElementById('alertSACSuccessSub');
      const iconBadge = document.getElementById('alertSACIconBadge');
      const lucideIcon = document.getElementById('alertSACLucideIcon');

      if (!alertBox) return;

      alertTitle.innerText = titulo;
      alertSub.innerText = subtitulo;

      if (tipo === 'excluir') {{
        alertBox.className = "p-5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-900 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-sm transition";
        iconBadge.className = "p-2 bg-rose-600 text-white rounded-xl";
        lucideIcon.setAttribute('data-lucide', 'trash-2');
      }} else if (tipo === 'editar') {{
        alertBox.className = "p-5 rounded-2xl bg-amber-50 border border-amber-300 text-amber-900 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-sm transition";
        iconBadge.className = "p-2 bg-amber-600 text-white rounded-xl";
        lucideIcon.setAttribute('data-lucide', 'edit-3');
      }} else {{
        alertBox.className = "p-5 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-900 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-sm transition";
        iconBadge.className = "p-2 bg-emerald-600 text-white rounded-xl";
        lucideIcon.setAttribute('data-lucide', 'check-circle');
      }}

      alertBox.classList.remove('hidden');
      alertBox.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
      lucide.createIcons();
    }}

    // ENVIO DESACOPLADO E INSTANTÂNEO
    function enviarParaPlanilhaGarantido(payload) {{
      const endpoint = APPS_SCRIPT_SAC_URL;
      const strData = JSON.stringify(payload);

      if (navigator.sendBeacon) {{
        try {{
          const blob = new Blob([strData], {{ type: 'text/plain;charset=utf-8' }});
          navigator.sendBeacon(endpoint, blob);
          return Promise.resolve(true);
        }} catch (err) {{}}
      }}

      try {{
        fetch(endpoint, {{
          method: "POST",
          mode: "no-cors",
          headers: {{ "Content-Type": "text/plain;charset=utf-8" }},
          body: strData
        }}).catch(() => {{}});
      }} catch (err) {{}}

      return Promise.resolve(true);
    }}

    function executarRefresh() {{
      window.parent.location.reload();
    }}

    function formatCurrency(val) {{
      return (val || 0).toLocaleString('pt-BR', {{ style: 'currency', currency: 'BRL' }});
    }}

    // =========================================================================
    // NAVEGAÇÃO ENTRE PÁGINAS (Dashboard SAC x Lançamento SAC)
    // =========================================================================
    function switchPage(page) {{
      try {{
        sessionStorage.setItem('aba_ativa_atual', page);
      }} catch(e) {{}}

      const pages = {{
        dashboardSAC: document.getElementById('pageDashboardSAC'),
        sac: document.getElementById('pageSAC')
      }};

      const buttons = {{
        dashboardSAC: document.getElementById('navDashboardSAC'),
        sac: document.getElementById('navSAC')
      }};

      Object.keys(pages).forEach(key => {{
        if (pages[key]) pages[key].classList.add('hidden');
        if (buttons[key]) {{
          buttons[key].classList.remove('active');
          buttons[key].classList.add('inactive');
        }}
      }});

      if (pages[page]) {{
        pages[page].classList.remove('hidden');
      }}
      if (buttons[page]) {{
        buttons[page].classList.add('active');
        buttons[page].classList.remove('inactive');
      }}

      if (page === 'dashboardSAC') {{
        atualizarDashboardSAC();
      }} else if (page === 'sac') {{
        verificarSessaoSAC();
      }}

      lucide.createIcons();
    }}

    // =========================================================================
    // ROTINAS SAC COM GERAÇÃO CONCORRENTE SEM DUPLICIDADE
    // =========================================================================
    function verificarSessaoSAC() {{
      const authScreen = document.getElementById('sacAuthScreen');
      const mainPanel = document.getElementById('sacMainPanel');

      if (atendenteSACLogado) {{
        authScreen.classList.add('hidden');
        mainPanel.classList.remove('hidden');
        document.getElementById('labelSACAtendenteLogado').innerText = atendenteSACLogado;
        document.getElementById('sacAtendente').value = atendenteSACLogado;
        inicializarFormularioSAC();
        renderizarTabelaChamadosSAC();
      }} else {{
        authScreen.classList.remove('hidden');
        mainPanel.classList.add('hidden');
      }}
    }}

    function realizarLoginSAC(e) {{
      e.preventDefault();
      const u = (document.getElementById('sacLoginUser').value || '').trim();
      const p = (document.getElementById('sacLoginPass').value || '').trim();
      const erroBox = document.getElementById('sacLoginErro');

      const userValido = dadosSAC.usuarios.find(x => x.usuario.toLowerCase() === u.toLowerCase() && x.senha === p);

      if (userValido) {{
        erroBox.classList.add('hidden');
        atendenteSACLogado = userValido.usuario;
        try {{
          sessionStorage.setItem('sac_atendente_conectado', atendenteSACLogado);
        }} catch(e) {{}}
        verificarSessaoSAC();
      }} else {{
        erroBox.classList.remove('hidden');
      }}
    }}

    function realizarLogoutSAC() {{
      atendenteSACLogado = "";
      try {{
        sessionStorage.removeItem('sac_atendente_conectado');
      }} catch(e) {{}}
      document.getElementById('sacLoginForm').reset();
      verificarSessaoSAC();
    }}

    function calcularPreviaProximoChamado(ano) {{
      let maior = dadosSAC.maior_sac_ano[ano] || 0;
      listaChamadosSAC.forEach(c => {{
        if (c.chamado) {{
          const m = c.chamado.match(new RegExp('SAC-' + ano + '-(\\\\d+)', 'i'));
          if (m) {{
            const seq = parseInt(m[1], 10);
            if (seq > maior) maior = seq;
          }}
        }}
      }});
      const proximo = String(maior + 1).padStart(4, '0');
      return 'SAC-' + ano + '-' + proximo;
    }}

    function inicializarFormularioSAC() {{
      if (chamadoEmEdicao) return;

      const anoAtual = new Date().getFullYear();
      document.getElementById('sacChamado').value = calcularPreviaProximoChamado(anoAtual);
      document.getElementById('sacData').value = new Date().toISOString().split('T')[0];
      
      // Produto começa limpo/vazio
      document.getElementById('sacProduto').value = "";
      
      // Data e Hora de transação começam ZERADOS/VAZIOS
      document.getElementById('sacDataTransacao').value = "";
      document.getElementById('sacHoraTransacao').value = "";
      document.getElementById('sacReembolso').value = "";
      document.getElementById('sacPix').value = "";
      document.getElementById('sacValor').value = "";
      document.getElementById('sacNome').value = "";
      document.getElementById('sacCelular').value = "";
      document.getElementById('sacProblema').value = "";
      document.getElementById('sacDescricao').value = "";
      document.getElementById('sacFormaPgto').value = "";
      document.getElementById('sacCliente').value = "";
      document.getElementById('sacCidade').value = "";
      
      const selectLocal = document.getElementById('sacLocalInterno');
      selectLocal.innerHTML = '<option value="">Selecione primeiro o Cliente...</option>';

      // Datalist de Clientes da aba Clientes coluna A
      const dlCli = document.getElementById('listaSACClientes');
      dlCli.innerHTML = '';
      const clientesUnicos = [...new Set(dadosSAC.clientes.map(c => c.cliente).filter(Boolean))].sort();
      clientesUnicos.forEach(cli => {{
        const opt = document.createElement('option');
        opt.value = cli;
        dlCli.appendChild(opt);
      }});

      // Datalist de Filiais Responsáveis da aba Clientes coluna F
      const dlCid = document.getElementById('listaSACCidades');
      dlCid.innerHTML = '';
      const cidadesGerais = dadosSAC.cidades && dadosSAC.cidades.length > 0 
        ? dadosSAC.cidades 
        : [...new Set(dadosSAC.clientes.map(c => c.cidade).filter(Boolean))].sort();
      cidadesGerais.forEach(cid => {{
        const opt = document.createElement('option');
        opt.value = cid;
        dlCid.appendChild(opt);
      }});

      // Datalist de Descrições da coluna N
      const dlDesc = document.getElementById('listaSACDescricoes');
      dlDesc.innerHTML = '';
      dadosSAC.descricoes.forEach(d => {{
        const opt = document.createElement('option');
        opt.value = d;
        dlDesc.appendChild(opt);
      }});

      // Datalist de Problemas da coluna L
      const dlProb = document.getElementById('listaSACProblemas');
      dlProb.innerHTML = '';
      dadosSAC.problemas.forEach(p => {{
        const opt = document.createElement('option');
        opt.value = p;
        dlProb.appendChild(opt);
      }});

      // Datalist de Formas de Pagamento da coluna A
      const dlPgto = document.getElementById('listaSACFormasPgto');
      dlPgto.innerHTML = '';
      dadosSAC.formas_pagamento.forEach(f => {{
        const opt = document.createElement('option');
        opt.value = f;
        dlPgto.appendChild(opt);
      }});
    }}

    function aoMudarClienteSAC() {{
      const cli = (document.getElementById('sacCliente').value || '').trim();
      const selectLocal = document.getElementById('sacLocalInterno');
      selectLocal.innerHTML = '<option value="">Selecione o Local Interno...</option>';

      if (!cli) return;

      const locaisDoCliente = dadosSAC.clientes.filter(c => c.cliente.toLowerCase() === cli.toLowerCase());
      if (locaisDoCliente.length === 0) return;

      const locaisUnicos = [...new Set(locaisDoCliente.map(l => l.local).filter(Boolean))].sort();
      locaisUnicos.forEach(loc => {{
        const opt = document.createElement('option');
        opt.value = loc;
        opt.textContent = loc;
        selectLocal.appendChild(opt);
      }});

      if (locaisUnicos.length === 1) {{
        selectLocal.value = locaisUnicos[0];
        aoMudarLocalInternoSAC();
      }}
    }}

    function aoMudarLocalInternoSAC() {{
      const cli = (document.getElementById('sacCliente').value || '').trim();
      const loc = document.getElementById('sacLocalInterno').value;
      if (!cli || !loc) return;

      const achado = dadosSAC.clientes.find(c => c.cliente.toLowerCase() === cli.toLowerCase() && c.local === loc);
      if (achado && achado.cidade) {{
        document.getElementById('sacCidade').value = achado.cidade;
      }}
    }}

    function formatarNomeProprio(input) {{
      if (!input.value) return;
      input.value = input.value
        .toLowerCase()
        .split(' ')
        .map(palavra => palavra.charAt(0).toUpperCase() + palavra.slice(1))
        .join(' ');
    }}

    function limparFormSAC() {{
      chamadoEmEdicao = null;
      document.getElementById('sacForm').reset();
      
      document.getElementById('sacProduto').value = "";
      document.getElementById('sacLocalInterno').innerHTML = '<option value="">Selecione primeiro o Cliente...</option>';
      document.getElementById('sacCidade').value = "";
      document.getElementById('sacDataTransacao').value = "";
      document.getElementById('sacHoraTransacao').value = "";
      document.getElementById('sacReembolso').value = "";
      document.getElementById('sacPix').value = "";
      document.getElementById('sacValor').value = "";
      document.getElementById('sacNome').value = "";
      document.getElementById('sacCelular').value = "";
      document.getElementById('sacProblema').value = "";
      document.getElementById('sacDescricao').value = "";
      document.getElementById('sacFormaPgto').value = "";
      document.getElementById('sacCliente').value = "";

      document.getElementById('alertSACEditMode').classList.add('hidden');
      document.getElementById('sacFormTitleText').innerText = "Lançamento de Ocorrências do SAC";
      document.getElementById('btnSalvarSACText').innerText = "Lançar Ocorrência SAC";
      
      const anoAtual = new Date().getFullYear();
      document.getElementById('sacChamado').value = calcularPreviaProximoChamado(anoAtual);
      document.getElementById('sacData').value = new Date().toISOString().split('T')[0];
      document.getElementById('sacAtendente').value = atendenteSACLogado;

      lucide.createIcons();
    }}

    function editarChamadoSAC(numeroChamado) {{
      const item = listaChamadosSAC.find(c => c.chamado === numeroChamado);
      if (!item) return;

      chamadoEmEdicao = item;
      document.getElementById('sacChamado').value = item.chamado;
      document.getElementById('sacData').value = item.data;
      document.getElementById('sacCliente').value = item.cliente;
      aoMudarClienteSAC();
      document.getElementById('sacLocalInterno').value = item.localInterno;
      document.getElementById('sacCidade').value = item.cidade;
      document.getElementById('sacDescricao').value = item.descricao;
      document.getElementById('sacProduto').value = item.produto || '';
      document.getElementById('sacDataTransacao').value = item.dataTransacao || '';
      document.getElementById('sacHoraTransacao').value = item.horaTransacao || '';
      
      const vLimpo = parseFloat(String(item.valor).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')) || 0;
      document.getElementById('sacValor').value = vLimpo || '';
      document.getElementById('sacNome').value = item.nomeSobrenome;
      document.getElementById('sacCelular').value = item.celular;
      document.getElementById('sacProblema').value = item.problemas;
      document.getElementById('sacFormaPgto').value = item.formaPgto;
      document.getElementById('sacReembolso').value = item.reembolso || '';
      document.getElementById('sacPix').value = item.pix || '';
      document.getElementById('sacAtendente').value = item.atendente || atendenteSACLogado;

      document.getElementById('alertSACEditMode').classList.remove('hidden');
      document.getElementById('labelSACEditChamado').innerText = item.chamado;
      document.getElementById('sacFormTitleText').innerText = 'Edição da Ocorrência: ' + item.chamado;
      document.getElementById('btnSalvarSACText').innerText = 'Salvar Alterações';

      document.getElementById('sacForm').scrollIntoView({{ behavior: 'smooth', block: 'start' }});
      lucide.createIcons();
    }}

    function cancelarEdicaoSAC() {{
      limparFormSAC();
    }}

    function excluirChamadoSAC(numeroChamado) {{
      if (!confirm('Deseja realmente excluir o chamado ' + numeroChamado + '? Esta ação solicitará a remoção na planilha.')) {{
        return;
      }}

      // ATUALIZA MODAL INFORMANDO A EXCLUSÃO
      abrirModalLoading(
        'Excluindo Ocorrência...',
        'Removendo a ocorrência ' + numeroChamado + ' da planilha oficial Chamados.',
        'loading'
      );

      const item = listaChamadosSAC.find(c => c.chamado === numeroChamado);

      const payloadExcluir = {{
        "action": "excluir",
        "acao": "excluir",
        "tipo": "excluir_sac",
        "Chamado": numeroChamado,
        "chamado": numeroChamado,
        "linha": item && item.linha ? item.linha : ""
      }};

      enviarParaPlanilhaGarantido(payloadExcluir);

      listaChamadosSAC = listaChamadosSAC.filter(c => c.chamado !== numeroChamado);
      renderizarTabelaChamadosSAC();

      if (chamadoEmEdicao && chamadoEmEdicao.chamado === numeroChamado) {{
        limparFormSAC();
      }}

      // ATUALIZA MODAL E MENSAGEM DO TOPO COM STATUS DE EXCLUSÃO
      setTimeout(() => {{
        abrirModalLoading(
          'Chamado Excluído!',
          'A ocorrência ' + numeroChamado + ' foi removida da base com sucesso.',
          'excluir'
        );

        exibirMensagemTopo(
          '🗑️ Chamado ' + numeroChamado + ' excluído!',
          'A ocorrência foi removida do sistema e da planilha oficial.',
          'excluir'
        );

        setTimeout(fecharModalLoading, 1000);
      }}, 500);
    }}

    function filtrarChamadosSAC() {{
      const termo = (document.getElementById('searchSACChamados')?.value || '').trim().toLowerCase();
      if (!termo) {{
        renderizarTabelaChamadosSAC(listaChamadosSAC);
        return;
      }}
      const filtrados = listaChamadosSAC.filter(c => 
        (c.chamado && c.chamado.toLowerCase().includes(termo)) ||
        (c.cliente && c.cliente.toLowerCase().includes(termo)) ||
        (c.nomeSobrenome && c.nomeSobrenome.toLowerCase().includes(termo)) ||
        (c.localInterno && c.localInterno.toLowerCase().includes(termo)) ||
        (c.cidade && c.cidade.toLowerCase().includes(termo)) ||
        (c.problemas && c.problemas.toLowerCase().includes(termo))
      );
      renderizarTabelaChamadosSAC(filtrados);
    }}

    function renderizarTabelaChamadosSAC(lista = listaChamadosSAC) {{
      const tbody = document.getElementById('tableSACChamadosBody');
      const badge = document.getElementById('badgeContadorSAC');
      if (badge) badge.innerText = lista.length + ' chamado(s)';

      if (!lista || lista.length === 0) {{
        tbody.innerHTML = '<tr><td colspan="12" class="text-center py-6 text-slate-400 font-semibold">Nenhuma ocorrência encontrada.</td></tr>';
        return;
      }}

      tbody.innerHTML = lista.map(c => `
        <tr class="hover:bg-slate-50 transition">
          <td class="py-2 px-3 whitespace-nowrap">
            <div class="flex items-center gap-1.5">
              <button type="button" onclick="editarChamadoSAC('${{c.chamado}}')" title="Editar chamado ${{c.chamado}}" class="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-sky-50 hover:bg-sky-100 text-sky-700 text-xs font-bold border border-sky-200 transition cursor-pointer">
                <i data-lucide="edit-2" class="w-3 h-3"></i>
                Editar
              </button>
              <button type="button" onclick="excluirChamadoSAC('${{c.chamado}}')" title="Excluir chamado ${{c.chamado}}" class="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-700 text-xs font-bold border border-rose-200 transition cursor-pointer">
                <i data-lucide="trash-2" class="w-3 h-3"></i>
                Excluir
              </button>
            </div>
          </td>
          <td class="py-2.5 px-3 font-mono font-bold text-sky-700">${{c.chamado}}</td>
          <td class="py-2.5 px-3">${{c.data || '-'}}</td>
          <td class="py-2.5 px-3 font-semibold text-slate-800">${{c.cliente || '-'}}</td>
          <td class="py-2.5 px-3 text-slate-600">${{c.localInterno || '-'}}</td>
          <td class="py-2.5 px-3 text-slate-600">${{c.cidade || '-'}}</td>
          <td class="py-2.5 px-3 font-medium text-slate-700">${{c.produto || '-'}}</td>
          <td class="py-2.5 px-3 text-right font-bold text-emerald-700">${{c.valor ? (String(c.valor).includes('R$') ? c.valor : 'R$ ' + c.valor) : 'R$ 0,00'}}</td>
          <td class="py-2.5 px-3 font-medium text-slate-800">${{c.nomeSobrenome || '-'}}</td>
          <td class="py-2.5 px-3 text-sky-900 font-semibold">${{c.reembolso || '-'}}</td>
          <td class="py-2.5 px-3 font-medium text-slate-600">${{c.atendente || '-'}}</td>
          <td class="py-2.5 px-3 text-slate-400 text-[11px]">${{c.dataHoraLancamento || '-'}}</td>
        </tr>
      `).join('');

      lucide.createIcons();
    }}

    function handleSACSubmit(e) {{
      e.preventDefault();

      // VALIDAÇÕES RÍGIDAS DE PRÉ-LISTA ANTES DO SUBMIT
      const cliValido = validarInputComLista('sacCliente', 'listaSACClientes', 'Cliente');
      if (!cliValido) return;

      const selectLocal = document.getElementById('sacLocalInterno');
      if (!selectLocal.value) {{
        alert('⛔ Bloqueio de Segurança:\\nPor favor, selecione um Local Interno vinculado ao cliente.');
        selectLocal.focus();
        return;
      }}

      const cidValida = validarInputComLista('sacCidade', 'listaSACCidades', 'Filial Responsável');
      if (!cidValida) return;

      const descValida = validarInputComLista('sacDescricao', 'listaSACDescricoes', 'Descrição');
      if (!descValida) return;

      const probValido = validarInputComLista('sacProblema', 'listaSACProblemas', 'Problemas');
      if (!probValido) return;

      const pgtoValido = validarInputComLista('sacFormaPgto', 'listaSACFormasPgto', 'Forma de Pagamento');
      if (!pgtoValido) return;

      const selectProduto = document.getElementById('sacProduto');
      if (!selectProduto.value) {{
        alert('⛔ Bloqueio de Segurança:\\nPor favor, selecione o Produto (Café ou Snaky).');
        selectProduto.focus();
        return;
      }}

      const ehEdicao = (chamadoEmEdicao !== null);
      let chamado = document.getElementById('sacChamado').value.trim();
      const anoAtual = new Date().getFullYear();

      if (!ehEdicao) {{
        chamado = calcularPreviaProximoChamado(anoAtual);
      }}

      // Validação de duplicidade
      const chamadoExiste = listaChamadosSAC.some(c => c.chamado.toUpperCase() === chamado.toUpperCase());
      if (!ehEdicao && chamadoExiste) {{
        alert('⛔ Chamado Duplicado! O número "' + chamado + '" já existe.');
        document.getElementById('sacChamado').value = calcularPreviaProximoChamado(anoAtual);
        return;
      }}

      // ATUALIZAÇÃO DO MODAL PARA O INÍCIO DA TRANSMISSÃO
      abrirModalLoading(
        ehEdicao ? 'Atualizando Ocorrência...' : 'Lançando no Sistema...',
        ehEdicao ? 'Gravando alterações do chamado ' + chamado + ' na planilha Chamados.' : 'Registrando a ocorrência ' + chamado + ' na planilha oficial.',
        'loading'
      );

      const data = document.getElementById('sacData').value;
      const cliente = document.getElementById('sacCliente').value.trim();
      const localInterno = document.getElementById('sacLocalInterno').value;
      const cidade = document.getElementById('sacCidade').value.trim();
      const descricao = document.getElementById('sacDescricao').value.trim();
      const produto = document.getElementById('sacProduto').value;
      const dataTransacao = document.getElementById('sacDataTransacao').value;
      const horaTransacao = document.getElementById('sacHoraTransacao').value;
      const valor = parseFloat(document.getElementById('sacValor').value) || 0;
      const nomeSobrenome = document.getElementById('sacNome').value.trim();
      const celular = document.getElementById('sacCelular').value.trim();
      const problemas = document.getElementById('sacProblema').value.trim();
      const formaPgto = document.getElementById('sacFormaPgto').value.trim();
      const reembolso = document.getElementById('sacReembolso').value.trim();
      const pix = document.getElementById('sacPix').value.trim();
      const atendente = atendenteSACLogado || document.getElementById('sacAtendente').value;
      
      const agora = new Date();
      const dataHoraLancamento = agora.toLocaleDateString('pt-BR') + ' ' + agora.toLocaleTimeString('pt-BR');

      const payloadSAC = {{
        "acao": ehEdicao ? "editar" : "inserir",
        "action": ehEdicao ? "editar" : "inserir",
        "linha": ehEdicao && chamadoEmEdicao.linha ? chamadoEmEdicao.linha : "",
        "Chamado": chamado,
        "Data": data,
        "Cliente": cliente,
        "Local Interno": localInterno,
        "Cidade": cidade,
        "Descrição": descricao,
        "Produto": produto,
        "Data da Transação": dataTransacao,
        "Hora da Transação": horaTransacao,
        "Valor": valor,
        "Nome/Sobrenome": nomeSobrenome,
        "Celular": celular,
        "Problemas": problemas,
        "Forma de Pagamento": formaPgto,
        "Reembolso": reembolso,
        "Pix - Reembolso": pix,
        "Atendente": atendente,
        "Data/Hora do lançamento": dataHoraLancamento
      }};

      // 1. Envia em segundo plano
      enviarParaPlanilhaGarantido(payloadSAC);

      // 2. Atualiza a lista visual imediatamente
      const novoItem = {{
        linha: ehEdicao && chamadoEmEdicao.linha ? chamadoEmEdicao.linha : listaChamadosSAC.length + 2,
        chamado,
        data,
        cliente,
        localInterno,
        cidade,
        descricao,
        produto,
        dataTransacao,
        horaTransacao,
        valor: formatCurrency(valor),
        nomeSobrenome,
        celular,
        problemas,
        formaPgto,
        reembolso,
        pix,
        atendente,
        dataHoraLancamento
      }};

      if (ehEdicao) {{
        listaChamadosSAC = listaChamadosSAC.map(c => c.chamado === chamado ? novoItem : c);
      }} else {{
        listaChamadosSAC.unshift(novoItem);
      }}

      const m = chamado.match(/SAC-(\d{{4}})-(\d+)/i);
      if (m) {{
        const ano = m[1];
        const seq = parseInt(m[2], 10);
        dadosSAC.maior_sac_ano[ano] = Math.max(dadosSAC.maior_sac_ano[ano] || 0, seq);
      }}

      // 3. Limpeza total do formulário
      limparFormSAC();
      renderizarTabelaChamadosSAC();

      // 4. ATUALIZAÇÃO DO MODAL E DA MENSAGEM NO TOPO APÓS A CONCLUSÃO
      setTimeout(() => {{
        abrirModalLoading(
          ehEdicao ? 'Ocorrência Atualizada!' : 'Lançamento Concluído!',
          ehEdicao ? 'As alterações do chamado ' + chamado + ' foram salvas com sucesso.' : 'O chamado ' + chamado + ' foi registrado na planilha oficial com sucesso.',
          'sucesso'
        );

        exibirMensagemTopo(
          ehEdicao ? '✅ Ocorrência ' + chamado + ' atualizada com sucesso!' : '✅ Ocorrência ' + chamado + ' lançada com sucesso!',
          'Cliente: ' + cliente + ' (' + localInterno + ') · Filial: ' + cidade + ' · Atendente: ' + atendente + ' · Valor: ' + formatCurrency(valor),
          ehEdicao ? 'editar' : 'sucesso'
        );

        setTimeout(fecharModalLoading, 1000);
      }}, 500);
    }}

    // =========================================================================
    // DASHBOARD SAC
    // =========================================================================
    const filterSACCliente = document.getElementById('filterSACCliente');
    const filterSACProduto = document.getElementById('filterSACProduto');
    const filterSACAtendente = document.getElementById('filterSACAtendente');

    function getHorizontalSACBarOptions() {{
      const textColor = '#475569';
      const gridColor = 'rgba(226, 232, 240, 0.7)';
      return {{
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        layout: {{ padding: {{ right: 40, left: 10, top: 10, bottom: 10 }} }},
        plugins: {{
          legend: {{ display: false }},
          tooltip: {{
            backgroundColor: '#ffffff',
            titleColor: '#0f172a',
            bodyColor: '#334155',
            borderColor: '#e2e8f0',
            borderWidth: 1,
            padding: 10,
            callbacks: {{
              label: (context) => 'Ocorrências: ' + context.raw.toLocaleString('pt-BR')
            }}
          }},
          datalabels: {{
            anchor: 'end',
            align: 'right',
            offset: 4,
            color: '#0f172a',
            font: {{ family: 'Inter', weight: 'bold', size: 10 }},
            formatter: (v) => v ? v.toLocaleString('pt-BR') : ''
          }}
        }},
        scales: {{
          x: {{
            grid: {{ color: gridColor }},
            ticks: {{ color: textColor, font: {{ size: 10 }} }},
            beginAtZero: true
          }},
          y: {{
            grid: {{ display: false }},
            ticks: {{ color: textColor, font: {{ size: 10, weight: '600' }} }}
          }}
        }}
      }};
    }}

    const chartTopProblemasSAC = new Chart(document.getElementById('chartTopProblemasSAC').getContext('2d'), {{
      type: 'bar',
      data: {{ labels: [], datasets: [{{ data: [], backgroundColor: 'rgba(2, 132, 199, 0.85)', borderRadius: 6 }}] }},
      options: getHorizontalSACBarOptions()
    }});

    const chartAtendentesSAC = new Chart(document.getElementById('chartAtendentesSAC').getContext('2d'), {{
      type: 'bar',
      data: {{ labels: [], datasets: [{{ data: [], backgroundColor: 'rgba(16, 185, 129, 0.85)', borderRadius: 6 }}] }},
      options: getHorizontalSACBarOptions()
    }});

    function inicializarFiltrosDashboardSAC() {{
      const clientesUnicos = [...new Set(listaChamadosSAC.map(c => c.cliente).filter(Boolean))].sort();
      filterSACCliente.innerHTML = '<option value="ALL">Todos os Clientes</option>';
      clientesUnicos.forEach(cli => {{
        const opt = document.createElement('option');
        opt.value = cli;
        opt.textContent = cli;
        filterSACCliente.appendChild(opt);
      }});

      const atendentesUnicos = [...new Set(listaChamadosSAC.map(c => c.atendente).filter(Boolean))].sort();
      filterSACAtendente.innerHTML = '<option value="ALL">Todos os Atendentes</option>';
      atendentesUnicos.forEach(a => {{
        const opt = document.createElement('option');
        opt.value = a;
        opt.textContent = a;
        filterSACAtendente.appendChild(opt);
      }});
    }}
    inicializarFiltrosDashboardSAC();

    function parseValorNumerico(v) {{
      if (!v) return 0;
      const s = String(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.');
      const n = parseFloat(s);
      return isNaN(n) ? 0 : n;
    }}

    function atualizarDashboardSAC() {{
      const cliVal = filterSACCliente.value;
      const prodVal = filterSACProduto.value;
      const atendVal = filterSACAtendente.value;

      const filtrados = listaChamadosSAC.filter(item => {{
        const matchCli = (cliVal === 'ALL' || (item.cliente && item.cliente.toLowerCase() === cliVal.toLowerCase()));
        const matchProd = (prodVal === 'ALL' || (item.produto && item.produto.toLowerCase() === prodVal.toLowerCase()));
        const matchAtend = (atendVal === 'ALL' || (item.atendente && item.atendente.toLowerCase() === atendVal.toLowerCase()));
        return matchCli && matchProd && matchAtend;
      }});

      document.getElementById('badgeFiltroSAC').innerText = 'Filtrando: Cliente [' + cliVal + '] · Produto [' + prodVal + '] · Atendente [' + atendVal + ']';

      const totalChamados = filtrados.length;
      let somaValor = 0;
      let chamadosCafe = 0;
      let chamadosSnaky = 0;

      filtrados.forEach(c => {{
        somaValor += parseValorNumerico(c.valor);
        const pLower = (c.produto || '').toLowerCase();
        if (pLower.includes('café') || pLower.includes('cafe')) chamadosCafe++;
        else if (pLower.includes('snaky') || pLower.includes('snack')) chamadosSnaky++;
      }});

      const pctCafe = totalChamados > 0 ? Math.round((chamadosCafe / totalChamados) * 100) : 0;
      const pctSnaky = totalChamados > 0 ? Math.round((chamadosSnaky / totalChamados) * 100) : 0;
      const ticketMedio = totalChamados > 0 ? (somaValor / totalChamados) : 0;

      document.getElementById('kpiSACTotal').innerText = totalChamados.toLocaleString('pt-BR');
      document.getElementById('kpiSACTotalSub').innerText = totalChamados + ' ocorrências registradas';

      document.getElementById('kpiSACValorTotal').innerText = formatCurrency(somaValor);
      document.getElementById('kpiSACCafé').innerText = chamadosCafe.toLocaleString('pt-BR');
      document.getElementById('kpiSACCaféPct').innerText = pctCafe + '%';
      document.getElementById('kpiSACSnaky').innerText = chamadosSnaky.toLocaleString('pt-BR');
      document.getElementById('kpiSACSnakyPct').innerText = pctSnaky + '%';
      document.getElementById('kpiSACClientes').innerText = new Set(filtrados.map(c => c.cliente)).size;
      document.getElementById('kpiSACTicketMedio').innerText = formatCurrency(ticketMedio);

      // Gráfico de Problemas
      const probContagem = {{}};
      filtrados.forEach(c => {{
        const p = (c.problemas || 'Outros').trim();
        probContagem[p] = (probContagem[p] || 0) + 1;
      }});
      const truncar = (t, max = 28) => t.length > max ? t.substring(0, max) + '...' : t;
      const top10Problemas = Object.entries(probContagem).map(([nome, qt]) => ({{ nome, qt }})).sort((a,b) => b.qt - a.qt).slice(0, 10);
      chartTopProblemasSAC.data.labels = top10Problemas.map(p => truncar(p.nome));
      chartTopProblemasSAC.data.datasets[0].data = top10Problemas.map(p => p.qt);
      chartTopProblemasSAC.update();

      // Gráfico de Atendentes
      const atendContagem = {{}};
      filtrados.forEach(c => {{
        const a = (c.atendente || 'Não Informado').trim();
        atendContagem[a] = (atendContagem[a] || 0) + 1;
      }});
      const topAtendentes = Object.entries(atendContagem).map(([nome, qt]) => ({{ nome, qt }})).sort((a,b) => b.qt - a.qt).slice(0, 10);
      chartAtendentesSAC.data.labels = topAtendentes.map(a => truncar(a.nome));
      chartAtendentesSAC.data.datasets[0].data = topAtendentes.map(a => a.qt);
      chartAtendentesSAC.update();
    }}

    [filterSACCliente, filterSACProduto, filterSACAtendente].forEach(el => el.addEventListener('change', atualizarDashboardSAC));
    document.getElementById('btnLimparFiltrosSAC').addEventListener('click', () => {{
      filterSACCliente.value = 'ALL';
      filterSACProduto.value = 'ALL';
      filterSACAtendente.value = 'ALL';
      atualizarDashboardSAC();
    }});

    // =========================================================================
    // INICIALIZAÇÃO DA ABA ATIVA
    // =========================================================================
    let abaInicial = 'dashboardSAC';
    try {{
      abaInicial = sessionStorage.getItem('aba_ativa_atual') || 'dashboardSAC';
      if (abaInicial !== 'dashboardSAC' && abaInicial !== 'sac') {{
        abaInicial = 'dashboardSAC';
      }}
    }} catch(e) {{}}
    
    switchPage(abaInicial);
  </script>
</body>
</html>
"""

components.html(html_code, height=2700, scrolling=True)