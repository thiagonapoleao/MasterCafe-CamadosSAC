import streamlit as st
import streamlit.components.v1 as components
import json
import pandas as pd
import re
import os
import base64

# Links oficiais dos Web Apps do Google Apps Script
APPS_SCRIPT_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbyEr_l9ulBrh04iFybET96bMlLRydzF3epQSMZXBBr5rAbqBm2M4jW_zPrR3dDcqiUZGg/exec"
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
SPREADSHEET_ID = "1iWjdaZLAp5hi9YIhmfSO4cPBn6fkfDjef8PAdZp1nsY"
GID_BASE_PECAS = "270834817"
GID_ORDEM_COMPRA = "643448898"
GID_RETIRADA_PECAS = "1232857188"

# Planilha de Destino das Ocorrências do SAC
SPREADSHEET_SAC_ID = "1YUS9AwQti0Gl79X-TGCIqZSkOfF0bE0BX5gyDClo3rc"
GID_SAC_CHAMADOS = "0"

# Planilha de Apoio para Pré-listas e Usuários do SAC
SPREADSHEET_SAC_CONFIG_ID = "1vOa6QpGPZ6rZ1doT2RRU1SAXWR5usPzv"
GID_SAC_CLIENTES = "400904478"
GID_SAC_CONFIGS = "1833376686"
GID_SAC_USUARIOS = "772646879"

URL_CSV_CATALOGO = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={GID_BASE_PECAS}"
URL_CSV_ORDENS = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={GID_ORDEM_COMPRA}"
URL_CSV_RETIRADAS = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={GID_RETIRADA_PECAS}"

URL_CSV_SAC_CHAMADOS = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_SAC_ID}/export?format=csv&gid={GID_SAC_CHAMADOS}"
URL_CSV_SAC_CLIENTES = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_SAC_CONFIG_ID}/export?format=csv&gid={GID_SAC_CLIENTES}"
URL_CSV_SAC_CONFIGS = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_SAC_CONFIG_ID}/export?format=csv&gid={GID_SAC_CONFIGS}"
URL_CSV_SAC_USUARIOS = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_SAC_CONFIG_ID}/export?format=csv&gid={GID_SAC_USUARIOS}"

@st.cache_data(ttl=5)
def carregar_catalogo_planilha():
    df = None
    try:
        df = pd.read_csv(URL_CSV_CATALOGO, dtype=str)
    except Exception:
        pass

    if df is None or df.empty:
        return []

    col_a = df.columns[0]
    col_b = df.columns[1] if len(df.columns) > 1 else col_a
    col_c = df.columns[2] if len(df.columns) > 2 else col_a
    col_f = df.columns[5] if len(df.columns) > 5 else df.columns[-1]

    catalogo = []
    for _, row in df.iterrows():
        cod = str(row[col_a]).strip() if pd.notna(row[col_a]) else ""
        desc = str(row[col_b]).strip() if pd.notna(row[col_b]) else ""
        cat = str(row[col_c]).strip() if pd.notna(row[col_c]) else "Geral"
        forn = str(row[col_f]).strip() if pd.notna(row[col_f]) else ""

        if cod and desc and cod.lower() not in ["nan", "produto", "código", "codigo"]:
            catalogo.append({
                "codigo": cod,
                "descricao": desc,
                "categoria": cat,
                "fornecedor": forn
            })
    return catalogo

@st.cache_data(ttl=5)
def obter_dados_ordens():
    df = None
    try:
        df = pd.read_csv(URL_CSV_ORDENS, dtype=str)
    except Exception:
        pass

    ocs_existentes = []
    if df is not None and not df.empty:
        col_oc = df.columns[0] if len(df.columns) > 0 else ""
        col_cod = df.columns[1] if len(df.columns) > 1 else ""
        col_prod = df.columns[2] if len(df.columns) > 2 else ""
        col_cat = df.columns[3] if len(df.columns) > 3 else ""
        col_data = df.columns[4] if len(df.columns) > 4 else ""
        col_mes = df.columns[5] if len(df.columns) > 5 else ""
        col_g_custo = df.columns[6] if len(df.columns) > 6 else ""
        col_qt = df.columns[7] if len(df.columns) > 7 else ""
        col_qt_aprov = df.columns[8] if len(df.columns) > 8 else ""
        col_venda = df.columns[10] if len(df.columns) > 10 else ""
        col_forn = df.columns[11] if len(df.columns) > 11 else ""
        col_obs = df.columns[13] if len(df.columns) > 13 else ""

        for _, r in df.iterrows():
            oc_val = str(r[col_oc]).strip() if pd.notna(r[col_oc]) else ""
            if not oc_val or oc_val.lower() in ["nan", "ordem de compra"]:
                continue

            match = re.search(r'OC-(\d{4})-(\d+)', oc_val, re.IGNORECASE)
            seq_num = 0
            ano_str = "2026"
            if match:
                ano_str = match.group(1)
                seq_num = int(match.group(2))

            obs_val = str(r[col_obs]) if pd.notna(r[col_obs]) else ""
            solic = obs_val.replace("Solicitante:", "").strip() if "Solicitante:" in obs_val else ""

            def to_float(val):
                if not val or pd.isna(val): return 0.0
                s = str(val).replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
                try: return float(s)
                except: return 0.0

            valor_coluna_g = to_float(r.get(col_g_custo, 0))
            qt_val = int(to_float(r.get(col_qt, 1)))
            qt_ap = int(to_float(r.get(col_qt_aprov, qt_val)))
            venda_u = to_float(r.get(col_venda, 0))
            mes_val = str(r.get(col_mes, "")).strip()

            ocs_existentes.append({
                "oc": oc_val,
                "seq_num": seq_num,
                "ano": ano_str,
                "mes": mes_val,
                "data": str(r.get(col_data, "")).strip(),
                "solicitante": solic,
                "fornecedor": str(r.get(col_forn, "")).strip(),
                "codigoPeca": str(r.get(col_cod, "")).strip(),
                "peca": str(r.get(col_prod, "")).strip(),
                "categoria": str(r.get(col_cat, "")).strip(),
                "qt": qt_val,
                "qtAprovada": qt_ap,
                "qtNaoAprovada": max(0, qt_val - qt_ap),
                "custoUnit": (valor_coluna_g / qt_ap) if qt_ap > 0 else valor_coluna_g,
                "vendaUnit": venda_u if venda_u > 0 else ((valor_coluna_g / qt_ap * 1.70) if qt_ap > 0 else 0),
                "custoTotal": valor_coluna_g
            })

    ocs_existentes.sort(key=lambda x: (x.get("ano", "0000"), x.get("seq_num", 0), x.get("oc", "")), reverse=True)
    return ocs_existentes

@st.cache_data(ttl=5)
def obter_dados_retiradas():
    df = None
    try:
        df = pd.read_csv(URL_CSV_RETIRADAS, dtype=str)
    except Exception:
        pass

    retiradas = []
    if df is not None and not df.empty:
        cols = list(df.columns)
        for idx, r in df.iterrows():
            data_val = str(r[cols[0]]).strip() if len(cols) > 0 and pd.notna(r[cols[0]]) else ""
            if not data_val or data_val.lower() in ["data", "nan"]:
                continue
            
            def to_int(v):
                try: return int(float(str(v).replace(",", ".")))
                except: return 1

            retiradas.append({
                "id": str(idx),
                "linha": idx + 2,
                "data": data_val,
                "tecnico": str(r[cols[1]]).strip() if len(cols) > 1 and pd.notna(r[cols[1]]) else "-",
                "cliente": str(r[cols[2]]).strip() if len(cols) > 2 and pd.notna(r[cols[2]]) else "-",
                "os": str(r[cols[3]]).strip() if len(cols) > 3 and pd.notna(r[cols[3]]) else "-",
                "codigo": str(r[cols[4]]).strip() if len(cols) > 4 and pd.notna(r[cols[4]]) else "-",
                "descricao": str(r[cols[5]]).strip() if len(cols) > 5 and pd.notna(r[cols[5]]) else "-",
                "novaUsada": str(r[cols[6]]).strip() if len(cols) > 6 and pd.notna(r[cols[6]]) else "Nova",
                "quantidade": to_int(r[cols[7]]) if len(cols) > 7 and pd.notna(r[cols[7]]) else 1,
                "devolvida": str(r[cols[8]]).strip() if len(cols) > 8 and pd.notna(r[cols[8]]) else "Não"
            })

    retiradas.reverse()
    return retiradas

@st.cache_data(ttl=5)
def carregar_dados_sac():
    clientes_dados = []
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
            col_cid = get_col(["Cidade", "cidade"]) or (cols[4] if len(cols) > 4 else "")
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
        "problemas": sorted(problemas),
        "descricoes": sorted(descricoes),
        "usuarios": usuarios_validos,
        "maior_sac_ano": maior_sac_ano,
        "chamados": chamados_salvos
    }

catalogo_pecas = carregar_catalogo_planilha()
total_itens_carregados = len(catalogo_pecas)

ocs_planilha = obter_dados_ordens()
ocs_planilha_json = json.dumps(ocs_planilha, ensure_ascii=False)

retiradas_planilha = obter_dados_retiradas()
retiradas_json = json.dumps(retiradas_planilha, ensure_ascii=False)

dados_sac = carregar_dados_sac()
dados_sac_json = json.dumps(dados_sac, ensure_ascii=False)

html_code = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dashboard Executivo - Operações & SAC</title>
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
  <form id="hiddenSubmissionForm" action="{APPS_SCRIPT_WEBAPP_URL}" method="POST" target="target_post_frame" style="display:none;">
    <input type="hidden" name="data" id="hiddenSubmissionData">
  </form>

  <form id="hiddenSACSubmissionForm" action="{APPS_SCRIPT_SAC_WEBAPP_URL}" method="POST" target="target_post_frame" style="display:none;">
    <input type="hidden" name="data" id="hiddenSACSubmissionData">
  </form>

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
          <p class="text-xs text-slate-500">Controle Operacional, Análises & Atendimento · {total_itens_carregados} itens no catálogo</p>
        </div>
      </div>
      
      <!-- Navegação Blindada -->
      <div class="flex items-center gap-2 bg-slate-100 p-1.5 rounded-2xl border border-slate-200 flex-wrap">
        <button id="navDashboardRetiradas" type="button" class="nav-btn active flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition" onclick="switchPage('dashboardRetiradas')">
          <i data-lucide="package-search" class="w-4 h-4"></i>
          Dashboard Retiradas
        </button>
        <button id="navDashboard" type="button" class="nav-btn inactive flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition" onclick="switchPage('dashboard')">
          <i data-lucide="layout-dashboard" class="w-4 h-4"></i>
          Dashboard Solicitações
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

    <!-- PÁGINA 1: DASHBOARD DE RETIRADAS -->
    <div id="pageDashboardRetiradas" class="space-y-6">
      <section class="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-2 text-sm font-semibold text-slate-700">
            <i data-lucide="sliders" class="w-4 h-4 text-amber-500"></i>
            <span>Filtros do Painel de Retiradas</span>
          </div>
          <span id="badgeFiltroRetirada" class="text-xs font-medium text-slate-500">Filtrando: Todos os registros</span>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label class="block text-xs font-medium text-slate-500 mb-1">Técnico</label>
            <select id="filterRetiradaTecnico" class="w-full text-sm rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 text-slate-800">
              <option value="ALL">Todos os Técnicos</option>
            </select>
          </div>

          <div>
            <label class="block text-xs font-medium text-slate-500 mb-1">Status Devolução</label>
            <select id="filterRetiradaDevolvida" class="w-full text-sm rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 text-slate-800">
              <option value="ALL">Todos os Status</option>
              <option value="Não">Não Devolvidas (Pendentes)</option>
              <option value="Sim">Devolvidas</option>
              <option value="Instalação Nova">Instalação Nova</option>
            </select>
          </div>

          <div>
            <label class="block text-xs font-medium text-slate-500 mb-1">Condição</label>
            <select id="filterRetiradaCondicao" class="w-full text-sm rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 text-slate-800">
              <option value="ALL">Todas as Condições</option>
              <option value="Nova">Nova</option>
              <option value="Usada">Usada</option>
            </select>
          </div>

          <div class="flex items-end">
            <button id="btnLimparFiltrosRetirada" class="w-full py-2 px-4 rounded-xl border border-slate-300 bg-slate-100 text-xs font-semibold text-slate-600 hover:bg-slate-200 transition flex items-center justify-center gap-1.5">
              <i data-lucide="rotate-ccw" class="w-3.5 h-3.5"></i>
              Limpar Filtros
            </button>
          </div>
        </div>
      </section>

      <!-- CARDS KPIS RETIRADAS -->
      <section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <div class="kpi-card p-4 rounded-2xl shadow-sm flex flex-col justify-between">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Total de Retiradas</span>
            <span class="p-1.5 rounded-lg bg-blue-50 text-blue-600"><i data-lucide="package" class="w-4 h-4"></i></span>
          </div>
          <div class="mt-3">
            <span id="kpiRetiradaTotal" class="text-xl font-bold tracking-tight text-slate-800">0</span>
            <p id="kpiRetiradaTotalSub" class="text-[11px] text-slate-400 mt-0.5">Total: 0 peças retiradas</p>
          </div>
        </div>

        <div class="kpi-card p-4 rounded-2xl shadow-sm flex flex-col justify-between border-rose-200">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-semibold text-rose-600 uppercase tracking-wider">Não Devolvidas</span>
            <span class="p-1.5 rounded-lg bg-rose-50 text-rose-600"><i data-lucide="alert-circle" class="w-4 h-4"></i></span>
          </div>
          <div class="mt-3 flex items-baseline justify-between">
            <div>
              <span id="kpiRetiradaNaoDevolvidas" class="text-xl font-bold tracking-tight text-rose-600">0 un</span>
              <p class="text-[11px] text-slate-400 mt-0.5">Pendentes de devolução</p>
            </div>
            <span id="kpiRetiradaNaoDevolvidasPct" class="text-xs font-semibold px-2 py-0.5 rounded-md bg-rose-100 text-rose-800">0%</span>
          </div>
        </div>

        <div class="kpi-card p-4 rounded-2xl shadow-sm flex flex-col justify-between border-emerald-200">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-semibold text-emerald-600 uppercase tracking-wider">Peças Devolvidas</span>
            <span class="p-1.5 rounded-lg bg-emerald-50 text-emerald-600"><i data-lucide="check-circle" class="w-4 h-4"></i></span>
          </div>
          <div class="mt-3 flex items-baseline justify-between">
            <div>
              <span id="kpiRetiradaDevolvidas" class="text-xl font-bold tracking-tight text-emerald-600">0 un</span>
              <p class="text-[11px] text-slate-400 mt-0.5">Retornaram ao almox.</p>
            </div>
            <span id="kpiRetiradaDevolvidasPct" class="text-xs font-semibold px-2 py-0.5 rounded-md bg-emerald-100 text-emerald-800">0%</span>
          </div>
        </div>

        <div class="kpi-card p-4 rounded-2xl shadow-sm flex flex-col justify-between">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-semibold text-indigo-600 uppercase tracking-wider">Instalação Nova</span>
            <span class="p-1.5 rounded-lg bg-indigo-50 text-indigo-600"><i data-lucide="sparkles" class="w-4 h-4"></i></span>
          </div>
          <div class="mt-3">
            <span id="kpiRetiradaInstalacao" class="text-xl font-bold tracking-tight text-indigo-600">0 un</span>
            <p class="text-[11px] text-slate-400 mt-0.5">Instaladas em clientes</p>
          </div>
        </div>

        <div class="kpi-card p-4 rounded-2xl shadow-sm flex flex-col justify-between">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Técnicos Ativos</span>
            <span class="p-1.5 rounded-lg bg-cyan-50 text-cyan-600"><i data-lucide="wrench" class="w-4 h-4"></i></span>
          </div>
          <div class="mt-3">
            <span id="kpiRetiradaTecnicos" class="text-xl font-bold tracking-tight text-slate-800">0</span>
            <p class="text-[11px] text-slate-400 mt-0.5">Técnicos com retiradas</p>
          </div>
        </div>

        <div class="kpi-card p-4 rounded-2xl shadow-sm flex flex-col justify-between">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Clientes Atendidos</span>
            <span class="p-1.5 rounded-lg bg-amber-50 text-amber-600"><i data-lucide="map-pin" class="w-4 h-4"></i></span>
          </div>
          <div class="mt-3">
            <span id="kpiRetiradaClientes" class="text-xl font-bold tracking-tight text-slate-800">0</span>
            <p class="text-[11px] text-slate-400 mt-0.5">Locais únicos</p>
          </div>
        </div>
      </section>

      <!-- GRÁFICOS DO DASHBOARD DE RETIRADAS -->
      <section class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div class="flex items-center justify-between mb-3">
            <div>
              <h3 class="font-bold text-base text-slate-800 flex items-center gap-2">
                <i data-lucide="bar-chart-2" class="w-4 h-4 text-amber-600"></i>
                Top 10 Peças Mais Retiradas (Quantidade)
              </h3>
              <p class="text-xs text-slate-400">Total de peças que saíram para atendimento</p>
            </div>
            <span class="text-[11px] font-semibold px-2 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200">Unidades</span>
          </div>
          <div class="relative h-80"><canvas id="chartTopPecasRetiradas"></canvas></div>
        </div>

        <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div class="flex items-center justify-between mb-3">
            <div>
              <h3 class="font-bold text-base text-slate-800 flex items-center gap-2">
                <i data-lucide="users" class="w-4 h-4 text-blue-600"></i>
                Retiradas por Técnico (Volume de Peças)
              </h3>
              <p class="text-xs text-slate-400">Distribuição do volume demandado por técnico</p>
            </div>
            <span class="text-[11px] font-semibold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">Por Técnico</span>
          </div>
          <div class="relative h-80"><canvas id="chartRetiradasPorTecnico"></canvas></div>
        </div>
      </section>

      <!-- TABELA GERAL DE RETIRADAS -->
      <section class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-3 border-b border-slate-100">
          <div>
            <h2 class="text-base font-bold flex items-center gap-2 text-slate-800">
              <i data-lucide="list" class="w-4 h-4 text-amber-500"></i>
              Histórico Completo de Retiradas
            </h2>
            <p class="text-xs text-slate-500">Todas as saídas registradas na planilha</p>
          </div>
          <div class="relative">
            <i data-lucide="search" class="w-4 h-4 text-slate-400 absolute left-3 top-2.5"></i>
            <input type="text" id="searchRetiradasGeral" placeholder="Buscar técnico, OS, peça..." oninput="atualizarDashboardRetiradas()" class="text-xs pl-9 pr-3 py-2 rounded-xl border border-slate-300 bg-slate-50 text-slate-800 focus:outline-none focus:ring-2 focus:ring-amber-500 w-64">
          </div>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs text-slate-600">
            <thead class="bg-slate-50 uppercase font-semibold text-slate-500">
              <tr>
                <th class="py-2.5 px-3 rounded-l-lg">Data</th>
                <th class="py-2.5 px-3">Técnico</th>
                <th class="py-2.5 px-3">Cliente</th>
                <th class="py-2.5 px-3 font-mono">OS</th>
                <th class="py-2.5 px-3 font-mono">Código</th>
                <th class="py-2.5 px-3">Descrição</th>
                <th class="py-2.5 px-3 text-center">Condição</th>
                <th class="py-2.5 px-3 text-center">Qt</th>
                <th class="py-2.5 px-3 text-center rounded-r-lg">Status (Coluna I)</th>
              </tr>
            </thead>
            <tbody id="tableRetiradasGeralBody" class="divide-y divide-slate-100"></tbody>
          </table>
        </div>
      </section>
    </div>

    <!-- PÁGINA 2: DASHBOARD SOLICITAÇÕES -->
    <div id="pageDashboard" class="hidden space-y-6">
      <section class="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-2 text-sm font-semibold text-slate-700">
            <i data-lucide="sliders" class="w-4 h-4 text-blue-500"></i>
            <span>Filtros do Painel de Solicitações</span>
          </div>
          <span id="activeFilterBadge" class="text-xs font-medium text-slate-500">Filtrando: Todos os registros</span>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <div>
            <label class="block text-xs font-medium text-slate-500 mb-1">Ano</label>
            <select id="filterYear" class="w-full text-sm rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 text-slate-800">
              <option value="ALL">Todos os Anos</option>
            </select>
          </div>

          <div>
            <label class="block text-xs font-medium text-slate-500 mb-1">Mês</label>
            <select id="filterMonth" class="w-full text-sm rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 text-slate-800">
              <option value="ALL">Todos os Meses</option>
            </select>
          </div>

          <div>
            <label class="block text-xs font-medium text-slate-500 mb-1">Categoria de Peças</label>
            <select id="filterCategory" class="w-full text-sm rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 text-slate-800">
              <option value="ALL">Todas as Categorias</option>
            </select>
          </div>

          <div>
            <label class="block text-xs font-medium text-slate-500 mb-1">Solicitante</label>
            <select id="filterRequester" class="w-full text-sm rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 text-slate-800">
              <option value="ALL">Todos os Solicitantes</option>
            </select>
          </div>

          <div class="flex items-end">
            <button id="resetFilters" class="w-full py-2 px-4 rounded-xl border border-slate-300 bg-slate-100 text-xs font-semibold text-slate-600 hover:bg-slate-200 transition flex items-center justify-center gap-1.5">
              <i data-lucide="rotate-ccw" class="w-3.5 h-3.5"></i>
              Limpar Filtros
            </button>
          </div>
        </div>
      </section>

      <!-- CARDS KPIS SOLICITAÇÕES -->
      <section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <div class="kpi-card p-4 rounded-2xl shadow-sm flex flex-col justify-between">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Valor Compras (Custo)</span>
            <span class="p-1.5 rounded-lg bg-amber-50 text-amber-600"><i data-lucide="badge-dollar-sign" class="w-4 h-4"></i></span>
          </div>
          <div class="mt-3">
            <span id="kpiTotalCost" class="text-xl font-bold tracking-tight text-amber-600">R$ 0,00</span>
            <p class="text-[11px] text-slate-400 mt-0.5">Soma direta da Coluna G</p>
          </div>
        </div>

        <div class="kpi-card p-4 rounded-2xl shadow-sm flex flex-col justify-between">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Total de Pedidos</span>
            <span class="p-1.5 rounded-lg bg-blue-50 text-blue-600"><i data-lucide="clipboard-list" class="w-4 h-4"></i></span>
          </div>
          <div class="mt-3">
            <span id="kpiTotalRequests" class="text-xl font-bold tracking-tight text-slate-800">0</span>
            <p class="text-[11px] text-slate-400 mt-0.5">Ordens registradas</p>
          </div>
        </div>

        <div class="kpi-card p-4 rounded-2xl shadow-sm flex flex-col justify-between">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Qtde Solicitada</span>
            <span class="p-1.5 rounded-lg bg-indigo-50 text-indigo-600"><i data-lucide="boxes" class="w-4 h-4"></i></span>
          </div>
          <div class="mt-3">
            <span id="kpiItemsQty" class="text-xl font-bold tracking-tight text-slate-800">0 un</span>
            <p class="text-[11px] text-slate-400 mt-0.5">Peças pedidas</p>
          </div>
        </div>

        <div class="kpi-card p-4 rounded-2xl shadow-sm flex flex-col justify-between border-emerald-200">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-semibold text-emerald-600 uppercase tracking-wider">Peças Atendidas</span>
            <span class="p-1.5 rounded-lg bg-emerald-50 text-emerald-600"><i data-lucide="check-circle-2" class="w-4 h-4"></i></span>
          </div>
          <div class="mt-3 flex items-baseline justify-between">
            <div>
              <span id="kpiApprovedQty" class="text-xl font-bold tracking-tight text-emerald-600">0 un</span>
              <p class="text-[11px] text-slate-400 mt-0.5">Aprovadas</p>
            </div>
            <span id="kpiApprovedPercent" class="text-xs font-semibold px-2 py-0.5 rounded-md bg-emerald-100 text-emerald-800">0%</span>
          </div>
        </div>

        <div class="kpi-card p-4 rounded-2xl shadow-sm flex flex-col justify-between border-rose-200">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-semibold text-rose-600 uppercase tracking-wider">Não Atendidas</span>
            <span class="p-1.5 rounded-lg bg-rose-50 text-rose-600"><i data-lucide="x-circle" class="w-4 h-4"></i></span>
          </div>
          <div class="mt-3 flex items-baseline justify-between">
            <div>
              <span id="kpiUnapprovedQty" class="text-xl font-bold tracking-tight text-rose-600">0 un</span>
              <p class="text-[11px] text-slate-400 mt-0.5">Pendentes</p>
            </div>
            <span id="kpiUnapprovedPercent" class="text-xs font-semibold px-2 py-0.5 rounded-md bg-rose-100 text-rose-800">0%</span>
          </div>
        </div>

        <div class="kpi-card p-4 rounded-2xl shadow-sm flex flex-col justify-between">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Custo Médio / OC</span>
            <span class="p-1.5 rounded-lg bg-cyan-50 text-cyan-600"><i data-lucide="calculator" class="w-4 h-4"></i></span>
          </div>
          <div class="mt-3">
            <span id="kpiAvgCost" class="text-xl font-bold tracking-tight text-slate-800">R$ 0,00</span>
            <p class="text-[11px] text-slate-400 mt-0.5">Média por pedido</p>
          </div>
        </div>
      </section>

      <!-- GRÁFICOS: EVOLUÇÃO MENSAL EM QUANTIDADE E VALOR -->
      <section class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div class="flex items-center justify-between mb-3">
            <div>
              <h3 class="font-bold text-base text-slate-800 flex items-center gap-2">
                <i data-lucide="calendar" class="w-4 h-4 text-blue-600"></i>
                Peças Solicitadas por Mês (Quantidade)
              </h3>
              <p class="text-xs text-slate-400">Total de peças solicitadas e atendidas por mês</p>
            </div>
            <span class="text-[11px] font-semibold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">Mensal (Unidades)</span>
          </div>
          <div class="relative h-80"><canvas id="chartPecasPorMesQt"></canvas></div>
        </div>

        <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div class="flex items-center justify-between mb-3">
            <div>
              <h3 class="font-bold text-base text-slate-800 flex items-center gap-2">
                <i data-lucide="line-chart" class="w-4 h-4 text-emerald-600"></i>
                Valor Solicitado por Mês (R$ Custo Total)
              </h3>
              <p class="text-xs text-slate-400">Impacto financeiro acumulado das ordens a cada mês (Coluna G)</p>
            </div>
            <span class="text-[11px] font-semibold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">Mensal (R$)</span>
          </div>
          <div class="relative h-80"><canvas id="chartPecasPorMesValor"></canvas></div>
        </div>
      </section>

      <!-- GRÁFICOS TOP 10 SOLICITAÇÕES -->
      <section class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div class="flex items-center justify-between mb-3">
            <div>
              <h3 class="font-bold text-base text-slate-800 flex items-center gap-2">
                <i data-lucide="bar-chart-2" class="w-4 h-4 text-sky-600"></i>
                Top 10 Peças Mais Solicitadas (Quantidade)
              </h3>
              <p class="text-xs text-slate-400">Total de unidades demandadas por peça no período filtrado</p>
            </div>
            <span class="text-[11px] font-semibold px-2 py-0.5 rounded bg-sky-50 text-sky-700 border border-sky-200">Unidades</span>
          </div>
          <div class="relative h-80"><canvas id="chartTopPecasQt"></canvas></div>
        </div>

        <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div class="flex items-center justify-between mb-3">
            <div>
              <h3 class="font-bold text-base text-slate-800 flex items-center gap-2">
                <i data-lucide="trending-up" class="w-4 h-4 text-emerald-600"></i>
                Top 10 Peças por Impacto Financeiro (Custo Total)
              </h3>
              <p class="text-xs text-slate-400">Peças com maior representatividade financeira no período</p>
            </div>
            <span class="text-[11px] font-semibold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">R$ Total</span>
          </div>
          <div class="relative h-80"><canvas id="chartTopPecasCusto"></canvas></div>
        </div>
      </section>

      <section class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <h3 class="font-bold text-base text-slate-800 mb-2">Distribuição por Categoria</h3>
          <div class="relative h-64"><canvas id="chartCategoryDist"></canvas></div>
        </div>

        <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <h3 class="font-bold text-base text-slate-800 mb-2">Soma de Custo por Fornecedor (R$)</h3>
          <div class="relative h-64"><canvas id="chartSupplierCost"></canvas></div>
        </div>
      </section>

      <!-- TABELA RESUMO SOLICITAÇÕES -->
      <section class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4 pb-3 border-b border-slate-100">
          <div>
            <h2 class="text-base font-bold flex items-center gap-2 text-slate-800">
              <i data-lucide="table" class="w-4 h-4 text-blue-500"></i>
              Resumo Detalhado por Peça Solicitada
            </h2>
            <p class="text-xs text-slate-500">Consolidado com Código da Peça, Descrição e Custo Total (Coluna G)</p>
          </div>

          <div class="flex items-center gap-3">
            <div class="relative">
              <i data-lucide="search" class="w-4 h-4 text-slate-400 absolute left-3 top-2.5"></i>
              <input type="text" id="tableSearch" placeholder="Buscar código ou descrição..." class="text-xs pl-9 pr-3 py-2 rounded-xl border border-slate-300 bg-slate-50 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 w-56 sm:w-72">
            </div>
            <span id="tableCountBadge" class="text-xs px-2.5 py-1 rounded-lg bg-slate-100 text-slate-600 font-semibold">0 itens</span>
          </div>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs text-slate-600">
            <thead class="bg-slate-50 uppercase font-semibold text-slate-500">
              <tr>
                <th class="py-3 px-4 rounded-l-lg">Código da Peça</th>
                <th class="py-3 px-4">Descrição da Peça / Produto</th>
                <th class="py-3 px-4">Categoria</th>
                <th class="py-3 px-4 text-center">Qtde Total</th>
                <th class="py-3 px-4 text-center text-emerald-600">Atendidas</th>
                <th class="py-3 px-4 text-center text-rose-600">Não Atendidas</th>
                <th class="py-3 px-4 text-center">Nº Pedidos</th>
                <th class="py-3 px-4 text-right rounded-r-lg">Custo Total (R$)</th>
              </tr>
            </thead>
            <tbody id="tableBody" class="divide-y divide-slate-100"></tbody>
          </table>
        </div>
      </section>
    </div>

    <!-- PÁGINA 3: LANÇAMENTO SAC -->
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

        <div id="alertSACSuccess" class="hidden p-5 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-900 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-sm transition">
          <div class="flex items-center gap-3">
            <div class="p-2 bg-emerald-600 text-white rounded-xl">
              <i data-lucide="check-circle" class="w-5 h-5"></i>
            </div>
            <div>
              <p id="alertSACSuccessTitle" class="text-sm font-bold">Ocorrência SAC lançada com sucesso!</p>
              <p id="alertSACSuccessSub" class="text-xs text-emerald-700">Gravado na aba Chamados da planilha oficial.</p>
            </div>
          </div>
          <button type="button" onclick="document.getElementById('alertSACSuccess').classList.add('hidden')" class="px-3 py-2 rounded-xl hover:bg-emerald-100 text-xs font-semibold text-emerald-800 transition">
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
              
              <!-- Chamado Automático SAC-AAAA-XXXX -->
              <div>
                <label class="block text-xs font-bold text-sky-900 mb-1">Chamado (Automático) *</label>
                <input type="text" id="sacChamado" readonly class="w-full text-sm font-mono font-black rounded-xl border border-sky-300 bg-white px-3.5 py-2 text-sky-700 cursor-not-allowed shadow-inner">
              </div>

              <!-- Data do Chamado -->
              <div>
                <label class="block text-xs font-semibold text-slate-700 mb-1">Data *</label>
                <input type="date" id="sacData" required class="w-full text-sm rounded-xl border border-slate-300 bg-white px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500">
              </div>

              <!-- Cliente -->
              <div>
                <label class="block text-xs font-semibold text-slate-700 mb-1">Cliente *</label>
                <input list="listaSACClientes" id="sacCliente" placeholder="Selecione o cliente..." required onchange="aoMudarClienteSAC()" oninput="aoMudarClienteSAC()" class="w-full text-sm font-semibold rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500">
                <datalist id="listaSACClientes"></datalist>
              </div>

              <!-- Local Interno (Filtro por cliente) -->
              <div>
                <label class="block text-xs font-semibold text-slate-700 mb-1">Local Interno *</label>
                <select id="sacLocalInterno" required onchange="aoMudarLocalInternoSAC()" class="w-full text-sm rounded-xl border border-slate-300 bg-white px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500">
                  <option value="">Selecione primeiro o Cliente...</option>
                </select>
              </div>

              <!-- Cidade -->
              <div>
                <label class="block text-xs font-semibold text-slate-700 mb-1">Cidade *</label>
                <input type="text" id="sacCidade" placeholder="Cidade correspondente" required class="w-full text-sm rounded-xl border border-slate-300 bg-slate-100 px-3.5 py-2 text-slate-800">
              </div>

              <!-- Descrição -->
              <div class="md:col-span-2 lg:col-span-3">
                <label class="block text-xs font-semibold text-slate-700 mb-1">Descrição *</label>
                <input list="listaSACDescricoes" id="sacDescricao" placeholder="Selecione ou digite a descrição do ocorrido..." required class="w-full text-sm rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500">
                <datalist id="listaSACDescricoes"></datalist>
              </div>

              <!-- Produto -->
              <div>
                <label class="block text-xs font-semibold text-slate-700 mb-1">Produto *</label>
                <select id="sacProduto" required class="w-full text-sm font-semibold rounded-xl border border-slate-300 bg-white px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500">
                  <option value="Café">Café</option>
                  <option value="Snaky">Snaky</option>
                </select>
              </div>

              <!-- Data da Transação (Começa Zerado/Vazio) -->
              <div>
                <label class="block text-xs font-semibold text-slate-700 mb-1">Data da Transação</label>
                <input type="date" id="sacDataTransacao" class="w-full text-sm rounded-xl border border-slate-300 bg-white px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500">
              </div>

              <!-- Hora da Transação (Começa Zerado/Vazio) -->
              <div>
                <label class="block text-xs font-semibold text-slate-700 mb-1">Hora da Transação</label>
                <input type="time" id="sacHoraTransacao" class="w-full text-sm rounded-xl border border-slate-300 bg-white px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500">
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

              <!-- Problemas -->
              <div class="md:col-span-2">
                <label class="block text-xs font-semibold text-slate-700 mb-1">Problemas *</label>
                <input list="listaSACProblemas" id="sacProblema" placeholder="Selecione ou digite o problema..." required class="w-full text-sm rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500">
                <datalist id="listaSACProblemas"></datalist>
              </div>

              <!-- Forma de Pagamento -->
              <div class="md:col-span-2">
                <label class="block text-xs font-semibold text-slate-700 mb-1">Forma de Pagamento *</label>
                <input list="listaSACFormasPgto" id="sacFormaPgto" placeholder="Selecione a forma de pagamento..." required class="w-full text-sm rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500">
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
                  <td colspan="11" class="text-center py-6 text-slate-400 font-semibold">Nenhum chamado registrado ainda.</td>
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

    const APPS_SCRIPT_URL = "{APPS_SCRIPT_WEBAPP_URL}";
    const APPS_SCRIPT_SAC_URL = "{APPS_SCRIPT_SAC_WEBAPP_URL}";
    const SPREADSHEET_SAC_ID = "{SPREADSHEET_SAC_ID}";

    let rawOrdersData = {ocs_planilha_json};
    let rawRetiradasData = {retiradas_json};
    const dadosSAC = {dados_sac_json};
    let listaChamadosSAC = Array.isArray(dadosSAC.chamados) ? dadosSAC.chamados : [];
    let chamadoEmEdicao = null;
    
    // Tratamento seguro de Storage
    let atendenteSACLogado = "";
    try {{
      atendenteSACLogado = sessionStorage.getItem('sac_atendente_conectado') || "";
    }} catch(e) {{}}

    // ENVIO RÁPIDO E NÃO-BLOQUEANTE (Fire and Forget com Fallback imediato)
    function enviarParaPlanilhaGarantido(payload, isSAC = false) {{
      const endpoint = isSAC ? APPS_SCRIPT_SAC_URL : APPS_SCRIPT_URL;

      // Dispara fetch assíncrono direto com text/plain para contornar preflight CORS
      try {{
        fetch(endpoint, {{
          method: "POST",
          mode: "no-cors",
          headers: {{ "Content-Type": "text/plain;charset=utf-8" }},
          body: JSON.stringify(payload)
        }}).catch(() => {{}});
      }} catch (e) {{}}

      // Fallback em formulário invisível garantindo envio via iframe
      try {{
        const form = document.getElementById(isSAC ? 'hiddenSACSubmissionForm' : 'hiddenSubmissionForm');
        const input = document.getElementById(isSAC ? 'hiddenSACSubmissionData' : 'hiddenSubmissionData');
        if (form && input) {{
          input.value = JSON.stringify(payload);
          form.submit();
        }}
      }} catch (e) {{}}

      return Promise.resolve(true);
    }}

    function executarRefresh() {{
      window.parent.location.reload();
    }}

    // =========================================================================
    // NAVEGAÇÃO ENTRE PÁGINAS CORRIGIDA
    // =========================================================================
    function switchPage(page) {{
      try {{
        sessionStorage.setItem('aba_ativa_atual', page);
      }} catch(e) {{}}

      const pages = {{
        dashboardRetiradas: document.getElementById('pageDashboardRetiradas'),
        dashboard: document.getElementById('pageDashboard'),
        sac: document.getElementById('pageSAC')
      }};

      const buttons = {{
        dashboardRetiradas: document.getElementById('navDashboardRetiradas'),
        dashboard: document.getElementById('navDashboard'),
        sac: document.getElementById('navSAC')
      }};

      // Resetar visibilidade e classes
      Object.keys(pages).forEach(key => {{
        if (pages[key]) pages[key].classList.add('hidden');
        if (buttons[key]) {{
          buttons[key].classList.remove('active');
          buttons[key].classList.add('inactive');
        }}
      }});

      // Ativar página selecionada
      if (pages[page]) {{
        pages[page].classList.remove('hidden');
      }}
      if (buttons[page]) {{
        buttons[page].classList.add('active');
        buttons[page].classList.remove('inactive');
      }}

      // Ações específicas de cada página
      if (page === 'dashboardRetiradas') {{
        atualizarDashboardRetiradas();
      }} else if (page === 'dashboard') {{
        updateDashboard();
      }} else if (page === 'sac') {{
        verificarSessaoSAC();
      }}

      lucide.createIcons();
    }}

    // =========================================================================
    // ROTINAS SAC
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

    function gerarNumeroChamadoSAC(ano) {{
      let maior = dadosSAC.maior_sac_ano[ano] || 0;
      listaChamadosSAC.forEach(c => {{
        if (c.chamado) {{
          const m = c.chamado.match(new RegExp('SAC-' + ano + '-(\\\\d+)', 'i'));
          if (m) {{
            const seq = parseInt(m[1]);
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
      document.getElementById('sacChamado').value = gerarNumeroChamadoSAC(anoAtual);
      document.getElementById('sacData').value = new Date().toISOString().split('T')[0];
      
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

      const dlCli = document.getElementById('listaSACClientes');
      dlCli.innerHTML = '';
      const clientesUnicos = [...new Set(dadosSAC.clientes.map(c => c.cliente).filter(Boolean))].sort();
      clientesUnicos.forEach(cli => {{
        const opt = document.createElement('option');
        opt.value = cli;
        dlCli.appendChild(opt);
      }});

      const dlDesc = document.getElementById('listaSACDescricoes');
      dlDesc.innerHTML = '';
      dadosSAC.descricoes.forEach(d => {{
        const opt = document.createElement('option');
        opt.value = d;
        dlDesc.appendChild(opt);
      }});

      const dlProb = document.getElementById('listaSACProblemas');
      dlProb.innerHTML = '';
      dadosSAC.problemas.forEach(p => {{
        const opt = document.createElement('option');
        opt.value = p;
        dlProb.appendChild(opt);
      }});

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
      document.getElementById('sacCidade').value = '';

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
      document.getElementById('alertSACEditMode').classList.add('hidden');
      document.getElementById('sacFormTitleText').innerText = "Lançamento de Ocorrências do SAC";
      document.getElementById('btnSalvarSACText').innerText = "Lançar Ocorrência SAC";
      inicializarFormularioSAC();
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
      document.getElementById('sacProduto').value = item.produto || 'Café';
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

    async function excluirChamadoSAC(numeroChamado) {{
      if (!confirm('Deseja realmente excluir o chamado ' + numeroChamado + '? Esta ação solicitará a remoção na planilha.')) {{
        return;
      }}

      const item = listaChamadosSAC.find(c => c.chamado === numeroChamado);

      const payloadExcluir = {{
        "action": "excluir",
        "acao": "excluir",
        "tipo": "excluir_sac",
        "Chamado": numeroChamado,
        "chamado": numeroChamado,
        "linha": item && item.linha ? item.linha : ""
      }};

      enviarParaPlanilhaGarantido(payloadExcluir, true);

      listaChamadosSAC = listaChamadosSAC.filter(c => c.chamado !== numeroChamado);
      renderizarTabelaChamadosSAC();

      if (chamadoEmEdicao && chamadoEmEdicao.chamado === numeroChamado) {{
        limparFormSAC();
      }}
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
        (c.problemas && c.problemas.toLowerCase().includes(termo))
      );
      renderizarTabelaChamadosSAC(filtrados);
    }}

    function renderizarTabelaChamadosSAC(lista = listaChamadosSAC) {{
      const tbody = document.getElementById('tableSACChamadosBody');
      const badge = document.getElementById('badgeContadorSAC');
      if (badge) badge.innerText = lista.length + ' chamado(s)';

      if (!lista || lista.length === 0) {{
        tbody.innerHTML = '<tr><td colspan="11" class="text-center py-6 text-slate-400 font-semibold">Nenhuma ocorrência encontrada.</td></tr>';
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

    let enviandoSAC = false;
    async function handleSACSubmit(e) {{
      e.preventDefault();
      if (enviandoSAC) return;

      const chamado = document.getElementById('sacChamado').value.trim();
      const ehEdicao = (chamadoEmEdicao !== null);

      // BARRAR DUPLICIDADE
      const chamadoExiste = listaChamadosSAC.some(c => c.chamado.toUpperCase() === chamado.toUpperCase());
      if (!ehEdicao && chamadoExiste) {{
        alert('⛔ Chamado Duplicado! O número "' + chamado + '" já existe no sistema.');
        const anoAtual = new Date().getFullYear();
        document.getElementById('sacChamado').value = gerarNumeroChamadoSAC(anoAtual);
        return;
      }}

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

      enviandoSAC = true;
      const btn = document.getElementById('btnSalvarSAC');
      btn.disabled = true;

      // Monta payload
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

      // Dispara o envio não-bloqueante
      enviarParaPlanilhaGarantido(payloadSAC, true);

      // Atualiza a tabela na tela imediatamente
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
        const seq = parseInt(m[2]);
        dadosSAC.maior_sac_ano[ano] = Math.max(dadosSAC.maior_sac_ano[ano] || 0, seq);
      }}

      // Limpa os campos do formulário imediatamente
      limparFormSAC();
      renderizarTabelaChamadosSAC();

      enviandoSAC = false;
      btn.disabled = false;

      const alertBox = document.getElementById('alertSACSuccess');
      document.getElementById('alertSACSuccessTitle').innerText = ehEdicao ?
        '✅ Ocorrência ' + chamado + ' atualizada com sucesso!' :
        '✅ Ocorrência ' + chamado + ' lançada com sucesso!';
      document.getElementById('alertSACSuccessSub').innerText = 'Cliente: ' + cliente + ' (' + localInterno + ') · Atendente: ' + atendente + ' · Valor: ' + formatCurrency(valor);
      alertBox.classList.remove('hidden');
      alertBox.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
      lucide.createIcons();
    }}

    // =========================================================================
    // DASHBOARD RETIRADAS
    // =========================================================================
    const filterRetTecnico = document.getElementById('filterRetiradaTecnico');
    const filterRetDevolvida = document.getElementById('filterRetiradaDevolvida');
    const filterRetCondicao = document.getElementById('filterRetiradaCondicao');

    function getHorizontalRetiradaBarOptions() {{
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
              label: (context) => 'Quantidade: ' + context.raw.toLocaleString('pt-BR') + ' un'
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

    const chartTopPecasRetiradas = new Chart(document.getElementById('chartTopPecasRetiradas').getContext('2d'), {{
      type: 'bar',
      data: {{ labels: [], datasets: [{{ data: [], backgroundColor: 'rgba(217, 119, 6, 0.85)', borderRadius: 6 }}] }},
      options: getHorizontalRetiradaBarOptions()
    }});

    const chartRetiradasPorTecnico = new Chart(document.getElementById('chartRetiradasPorTecnico').getContext('2d'), {{
      type: 'bar',
      data: {{ labels: [], datasets: [{{ data: [], backgroundColor: 'rgba(2, 132, 199, 0.85)', borderRadius: 6 }}] }},
      options: getHorizontalRetiradaBarOptions()
    }});

    function inicializarFiltrosRetiradas() {{
      const tecnicosUnicos = [...new Set(rawRetiradasData.map(r => r.tecnico).filter(Boolean))].sort();
      filterRetTecnico.innerHTML = '<option value="ALL">Todos os Técnicos</option>';
      tecnicosUnicos.forEach(t => {{
        const opt = document.createElement('option');
        opt.value = t;
        opt.textContent = t;
        filterRetTecnico.appendChild(opt);
      }});
    }}
    inicializarFiltrosRetiradas();

    function atualizarDashboardRetiradas() {{
      const tecVal = filterRetTecnico.value;
      const devVal = filterRetDevolvida.value;
      const condVal = filterRetCondicao.value;
      const searchVal = (document.getElementById('searchRetiradasGeral')?.value || '').trim().toLowerCase();

      const filtrados = rawRetiradasData.filter(item => {{
        const matchTec = (tecVal === 'ALL' || item.tecnico === tecVal);
        const matchDev = (devVal === 'ALL' || item.devolvida.toLowerCase() === devVal.toLowerCase());
        const matchCond = (condVal === 'ALL' || item.novaUsada.toLowerCase() === condVal.toLowerCase());
        const matchSearch = !searchVal || (
          (item.tecnico && item.tecnico.toLowerCase().includes(searchVal)) ||
          (item.os && item.os.toLowerCase().includes(searchVal)) ||
          (item.cliente && item.cliente.toLowerCase().includes(searchVal)) ||
          (item.codigo && item.codigo.toLowerCase().includes(searchVal)) ||
          (item.descricao && item.descricao.toLowerCase().includes(searchVal))
        );
        return matchTec && matchDev && matchCond && matchSearch;
      }});

      document.getElementById('badgeFiltroRetirada').innerText = 'Filtrando: Técnico [' + tecVal + '] · Status [' + devVal + '] · Condição [' + condVal + ']';

      const totalRegistrosRetirada = filtrados.length;
      let totalPecas = 0;
      let naoDevolvidas = 0;
      let devolvidas = 0;
      let instalacoes = 0;

      filtrados.forEach(r => {{
        const q = parseInt(r.quantidade) || 1;
        totalPecas += q;
        const stLower = (r.devolvida || '').toLowerCase();
        if (stLower === 'não' || stLower === 'nao') naoDevolvidas += q;
        else if (stLower === 'sim') devolvidas += q;
        else if (stLower.includes('instalação') || stLower.includes('instalacao')) instalacoes += q;
      }});

      const pctNaoDevolvidas = totalPecas > 0 ? Math.round((naoDevolvidas / totalPecas) * 100) : 0;
      const pctDevolvidas = totalPecas > 0 ? Math.round((devolvidas / totalPecas) * 100) : 0;

      document.getElementById('kpiRetiradaTotal').innerText = totalRegistrosRetirada.toLocaleString('pt-BR');
      document.getElementById('kpiRetiradaTotalSub').innerText = 'Total: ' + totalPecas.toLocaleString('pt-BR') + ' peças retiradas';

      document.getElementById('kpiRetiradaNaoDevolvidas').innerText = naoDevolvidas.toLocaleString('pt-BR') + ' un';
      document.getElementById('kpiRetiradaNaoDevolvidasPct').innerText = pctNaoDevolvidas + '%';
      document.getElementById('kpiRetiradaDevolvidas').innerText = devolvidas.toLocaleString('pt-BR') + ' un';
      document.getElementById('kpiRetiradaDevolvidasPct').innerText = pctDevolvidas + '%';
      document.getElementById('kpiRetiradaInstalacao').innerText = instalacoes.toLocaleString('pt-BR') + ' un';
      document.getElementById('kpiRetiradaTecnicos').innerText = new Set(filtrados.map(r => r.tecnico)).size;
      document.getElementById('kpiRetiradaClientes').innerText = new Set(filtrados.map(r => r.cliente)).size;

      const pecasContagem = {{}};
      filtrados.forEach(r => {{
        const nome = (r.descricao || r.codigo || 'Peça').trim();
        pecasContagem[nome] = (pecasContagem[nome] || 0) + (parseInt(r.quantidade) || 1);
      }});
      const truncar = (t, max = 28) => t.length > max ? t.substring(0, max) + '...' : t;
      const top10Pecas = Object.entries(pecasContagem).map(([nome, qt]) => ({{ nome, qt }})).sort((a,b) => b.qt - a.qt).slice(0, 10);
      chartTopPecasRetiradas.data.labels = top10Pecas.map(p => truncar(p.nome));
      chartTopPecasRetiradas.data.datasets[0].data = top10Pecas.map(p => p.qt);
      chartTopPecasRetiradas.update();

      const tecContagem = {{}};
      filtrados.forEach(r => {{
        const t = (r.tecnico || 'Indefinido').trim();
        tecContagem[t] = (tecContagem[t] || 0) + (parseInt(r.quantidade) || 1);
      }});
      const topTecnicos = Object.entries(tecContagem).map(([nome, qt]) => ({{ nome, qt }})).sort((a,b) => b.qt - a.qt).slice(0, 10);
      chartRetiradasPorTecnico.data.labels = topTecnicos.map(t => truncar(t.nome));
      chartRetiradasPorTecnico.data.datasets[0].data = topTecnicos.map(t => t.qt);
      chartRetiradasPorTecnico.update();

      const tbGeral = document.getElementById('tableRetiradasGeralBody');
      if (filtrados.length === 0) {{
        tbGeral.innerHTML = '<tr><td colspan="9" class="text-center py-6 text-slate-400 font-semibold">Nenhuma retirada encontrada.</td></tr>';
      }} else {{
        tbGeral.innerHTML = filtrados.map(item => {{
          const dLower = (item.devolvida || '').toLowerCase();
          let badgeClass = 'bg-rose-100 text-rose-800';
          if (dLower === 'sim') badgeClass = 'bg-emerald-100 text-emerald-800';
          else if (dLower.includes('instalação') || dLower.includes('instalacao')) badgeClass = 'bg-indigo-100 text-indigo-800';

          return `
            <tr class="hover:bg-slate-50 transition">
              <td class="py-2.5 px-3">${{item.data}}</td>
              <td class="py-2.5 px-3 font-semibold text-slate-800">${{item.tecnico}}</td>
              <td class="py-2.5 px-3">${{item.cliente}}</td>
              <td class="py-2.5 px-3 font-mono font-bold text-blue-700">${{item.os}}</td>
              <td class="py-2.5 px-3 font-mono text-slate-600">${{item.codigo}}</td>
              <td class="py-2.5 px-3 font-medium text-slate-800">${{item.descricao}}</td>
              <td class="py-2.5 px-3 text-center"><span class="px-2 py-0.5 rounded text-[10px] bg-slate-100 text-slate-700 font-semibold">${{item.novaUsada}}</span></td>
              <td class="py-2.5 px-3 text-center font-bold text-slate-800">${{item.quantidade}} un</td>
              <td class="py-2.5 px-3 text-center"><span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold ${{badgeClass}}">${{item.devolvida}}</span></td>
            </tr>
          `;
        }}).join('');
      }}
      lucide.createIcons();
    }}

    [filterRetTecnico, filterRetDevolvida, filterRetCondicao].forEach(el => el.addEventListener('change', atualizarDashboardRetiradas));
    document.getElementById('btnLimparFiltrosRetirada').addEventListener('click', () => {{
      filterRetTecnico.value = 'ALL';
      filterRetDevolvida.value = 'ALL';
      filterRetCondicao.value = 'ALL';
      document.getElementById('searchRetiradasGeral').value = '';
      atualizarDashboardRetiradas();
    }});

    // =========================================================================
    // DASHBOARD SOLICITAÇÕES
    // =========================================================================
    function formatCurrency(val) {{
      return (val || 0).toLocaleString('pt-BR', {{ style: 'currency', currency: 'BRL' }});
    }}

    const filterYear = document.getElementById('filterYear');
    const filterMonth = document.getElementById('filterMonth');
    const filterCategory = document.getElementById('filterCategory');
    const filterRequester = document.getElementById('filterRequester');
    const resetFiltersBtn = document.getElementById('resetFilters');
    const activeFilterBadge = document.getElementById('activeFilterBadge');

    const kpiTotalCost = document.getElementById('kpiTotalCost');
    const kpiTotalRequests = document.getElementById('kpiTotalRequests');
    const kpiItemsQty = document.getElementById('kpiItemsQty');
    const kpiApprovedQty = document.getElementById('kpiApprovedQty');
    const kpiApprovedPercent = document.getElementById('kpiApprovedPercent');
    const kpiUnapprovedQty = document.getElementById('kpiUnapprovedQty');
    const kpiUnapprovedPercent = document.getElementById('kpiUnapprovedPercent');
    const kpiAvgCost = document.getElementById('kpiAvgCost');

    const tableBody = document.getElementById('tableBody');
    const tableSearch = document.getElementById('tableSearch');
    const tableCountBadge = document.getElementById('tableCountBadge');

    function populateDropdowns() {{
      filterYear.innerHTML = '<option value="ALL">Todos os Anos</option>';
      filterMonth.innerHTML = '<option value="ALL">Todos os Meses</option>';
      filterCategory.innerHTML = '<option value="ALL">Todas as Categorias</option>';
      filterRequester.innerHTML = '<option value="ALL">Todos os Solicitantes</option>';

      const years = [...new Set(rawOrdersData.map(d => d.ano).filter(Boolean))].sort();
      const months = [...new Set(rawOrdersData.map(d => d.mes).filter(Boolean))];
      const categories = [...new Set(rawOrdersData.map(d => d.categoria).filter(Boolean))].sort();
      const requesters = [...new Set(rawOrdersData.map(d => d.solicitante).filter(Boolean))].sort();

      years.forEach(y => {{ const opt = document.createElement('option'); opt.value = y; opt.textContent = y; filterYear.appendChild(opt); }});
      months.forEach(m => {{ const opt = document.createElement('option'); opt.value = m; opt.textContent = m; filterMonth.appendChild(opt); }});
      categories.forEach(c => {{ const opt = document.createElement('option'); opt.value = c; opt.textContent = c; filterCategory.appendChild(opt); }});
      requesters.forEach(r => {{ const opt = document.createElement('option'); opt.value = r; opt.textContent = r; filterRequester.appendChild(opt); }});
    }}
    populateDropdowns();

    function getHorizontalBarOptions(isCurrency = false) {{
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
              label: (context) => isCurrency ? 'Custo: ' + formatCurrency(context.raw) : 'Quantidade: ' + context.raw.toLocaleString('pt-BR') + ' un'
            }}
          }},
          datalabels: {{
            anchor: 'end',
            align: 'right',
            offset: 4,
            color: '#0f172a',
            font: {{ family: 'Inter', weight: 'bold', size: 10 }},
            formatter: (v) => {{
              if (!v) return '';
              return isCurrency ? formatCurrency(v) : v.toLocaleString('pt-BR');
            }}
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

    const chartPecasPorMesQt = new Chart(document.getElementById('chartPecasPorMesQt').getContext('2d'), {{
      type: 'bar',
      data: {{
        labels: [],
        datasets: [
          {{ label: 'Qt Solicitada', data: [], backgroundColor: 'rgba(2, 132, 199, 0.85)', borderRadius: 6 }},
          {{ label: 'Qt Atendida', data: [], backgroundColor: 'rgba(16, 185, 129, 0.85)', borderRadius: 6 }}
        ]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        layout: {{ padding: {{ top: 22, bottom: 6, left: 6, right: 6 }} }},
        plugins: {{
          legend: {{ display: true, position: 'top', labels: {{ font: {{ family: 'Inter', size: 11, weight: '600' }}, color: '#334155', boxWidth: 12 }} }},
          datalabels: {{
            anchor: 'end',
            align: 'top',
            offset: 2,
            color: '#0f172a',
            font: {{ family: 'Inter', weight: 'bold', size: 10 }},
            formatter: (v) => v ? v.toLocaleString('pt-BR') : ''
          }}
        }},
        scales: {{
          x: {{ grid: {{ color: 'rgba(226, 232, 240, 0.8)' }}, ticks: {{ color: '#64748b', font: {{ size: 10 }} }} }},
          y: {{ grid: {{ color: 'rgba(226, 232, 240, 0.8)' }}, ticks: {{ color: '#64748b', font: {{ size: 10 }} }}, beginAtZero: true }}
        }}
      }}
    }});

    const chartPecasPorMesValor = new Chart(document.getElementById('chartPecasPorMesValor').getContext('2d'), {{
      type: 'bar',
      data: {{
        labels: [],
        datasets: [{{ label: 'Valor Total (R$)', data: [], backgroundColor: 'rgba(16, 185, 129, 0.85)', borderRadius: 8 }}]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        layout: {{ padding: {{ top: 22, bottom: 6, left: 6, right: 6 }} }},
        plugins: {{
          legend: {{ display: false }},
          datalabels: {{
            anchor: 'end',
            align: 'top',
            offset: 2,
            color: '#0f172a',
            font: {{ family: 'Inter', weight: 'bold', size: 10 }},
            formatter: (v) => v ? formatCurrency(v) : ''
          }}
        }},
        scales: {{
          x: {{ grid: {{ color: 'rgba(226, 232, 240, 0.8)' }}, ticks: {{ color: '#64748b', font: {{ size: 10 }} }} }},
          y: {{ grid: {{ color: 'rgba(226, 232, 240, 0.8)' }}, ticks: {{ color: '#64748b', font: {{ size: 10 }} }}, beginAtZero: true }}
        }}
      }}
    }});

    const chartTopPecasQt = new Chart(document.getElementById('chartTopPecasQt').getContext('2d'), {{
      type: 'bar',
      data: {{ labels: [], datasets: [{{ data: [], backgroundColor: 'rgba(2, 132, 199, 0.85)', borderRadius: 6 }}] }},
      options: getHorizontalBarOptions(false)
    }});

    const chartTopPecasCusto = new Chart(document.getElementById('chartTopPecasCusto').getContext('2d'), {{
      type: 'bar',
      data: {{ labels: [], datasets: [{{ data: [], backgroundColor: 'rgba(16, 185, 129, 0.85)', borderRadius: 6 }}] }},
      options: getHorizontalBarOptions(true)
    }});

    const chartCategory = new Chart(document.getElementById('chartCategoryDist').getContext('2d'), {{
      type: 'doughnut',
      data: {{ labels: [], datasets: [{{ data: [], backgroundColor: ['#0284c7', '#06b6d4', '#f59e0b', '#6366f1', '#10b981'], borderWidth: 2, borderColor: '#ffffff' }}] }},
      options: {{ responsive: true, maintainAspectRatio: false, cutout: '62%' }}
    }});

    const chartSupplier = new Chart(document.getElementById('chartSupplierCost').getContext('2d'), {{
      type: 'bar',
      data: {{ labels: [], datasets: [{{ data: [], backgroundColor: 'rgba(245, 158, 11, 0.85)', borderRadius: 8 }}] }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        layout: {{ padding: {{ top: 22, bottom: 6, left: 6, right: 6 }} }},
        plugins: {{
          legend: {{ display: false }},
          datalabels: {{
            anchor: 'end',
            align: 'top',
            offset: 2,
            color: '#0f172a',
            font: {{ family: 'Inter', weight: 'bold', size: 11 }},
            formatter: (v) => v ? formatCurrency(v) : ''
          }}
        }},
        scales: {{
          x: {{ grid: {{ color: 'rgba(226, 232, 240, 0.8)' }}, ticks: {{ color: '#64748b', font: {{ size: 10 }} }} }},
          y: {{ grid: {{ color: 'rgba(226, 232, 240, 0.8)' }}, ticks: {{ color: '#64748b', font: {{ size: 10 }} }}, beginAtZero: true }}
        }}
      }}
    }});

    function normalizarMes(item) {{
      if (item.mes && item.mes.trim()) return item.mes.trim();
      if (item.data) {{
        const partes = item.data.split(/[-/]/);
        if (partes.length >= 2) {{
          let m = parseInt(partes[1], 10);
          const nomes = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"];
          if (!isNaN(m) && m >= 1 && m <= 12) return nomes[m - 1];
        }}
      }}
      return "Outros";
    }}

    function updateDashboard() {{
      const yearVal = filterYear.value;
      const monthVal = filterMonth.value;
      const catVal = filterCategory.value;
      const reqVal = filterRequester.value;
      const searchVal = tableSearch.value.trim().toLowerCase();

      const filtered = rawOrdersData.filter(item => {{
        const matchYear = (yearVal === 'ALL' || item.ano === yearVal);
        const matchMonth = (monthVal === 'ALL' || item.mes === monthVal);
        const matchCat = (catVal === 'ALL' || item.categoria === catVal);
        const matchReq = (reqVal === 'ALL' || item.solicitante === reqVal);
        return matchYear && matchMonth && matchCat && matchReq;
      }});

      activeFilterBadge.innerText = 'Filtrando: Ano [' + yearVal + '] · Mês [' + monthVal + '] · Categoria [' + catVal + ']';

      const totalCusto = filtered.reduce((acc, cur) => acc + (cur.custoTotal || 0), 0);
      const totalItens = filtered.reduce((acc, cur) => acc + (cur.qt || 0), 0);
      const totalAtendidas = filtered.reduce((acc, cur) => acc + (cur.qtAprovada || 0), 0);
      const totalNaoAtendidas = filtered.reduce((acc, cur) => acc + (cur.qtNaoAprovada || 0), 0);
      
      const ocsUnicas = new Set(filtered.map(f => f.oc)).size;
      const avgCost = ocsUnicas > 0 ? (totalCusto / ocsUnicas) : 0;

      const pctAtendidas = totalItens > 0 ? Math.round((totalAtendidas / totalItens) * 100) : 0;
      const pctNaoAtendidas = totalItens > 0 ? (100 - pctAtendidas) : 0;

      kpiTotalCost.innerText = formatCurrency(totalCusto);
      kpiTotalRequests.innerText = ocsUnicas;
      kpiItemsQty.innerText = totalItens.toLocaleString('pt-BR') + ' un';
      kpiApprovedQty.innerText = totalAtendidas.toLocaleString('pt-BR') + ' un';
      kpiApprovedPercent.innerText = pctAtendidas + '%';
      kpiUnapprovedQty.innerText = totalNaoAtendidas.toLocaleString('pt-BR') + ' un';
      kpiUnapprovedPercent.innerText = pctNaoAtendidas + '%';
      kpiAvgCost.innerText = formatCurrency(avgCost);

      const mesesOrdem = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
      ];
      const dadosPorMes = {{}};
      mesesOrdem.forEach(m => {{ dadosPorMes[m] = {{ qtTotal: 0, qtAtendida: 0, valorTotal: 0 }}; }});

      filtered.forEach(item => {{
        const m = normalizarMes(item);
        if (!dadosPorMes[m]) dadosPorMes[m] = {{ qtTotal: 0, qtAtendida: 0, valorTotal: 0 }};
        dadosPorMes[m].qtTotal += (item.qt || 0);
        dadosPorMes[m].qtAtendida += (item.qtAprovada || 0);
        dadosPorMes[m].valorTotal += (item.custoTotal || 0);
      }});

      let mesesAtivos = mesesOrdem.filter(m => (dadosPorMes[m].qtTotal > 0 || dadosPorMes[m].valorTotal > 0));
      if (mesesAtivos.length === 0) mesesAtivos = mesesOrdem.slice(0, 6);

      chartPecasPorMesQt.data.labels = mesesAtivos;
      chartPecasPorMesQt.data.datasets[0].data = mesesAtivos.map(m => dadosPorMes[m].qtTotal);
      chartPecasPorMesQt.data.datasets[1].data = mesesAtivos.map(m => dadosPorMes[m].qtAtendida);
      chartPecasPorMesQt.update();

      chartPecasPorMesValor.data.labels = mesesAtivos;
      chartPecasPorMesValor.data.datasets[0].data = mesesAtivos.map(m => dadosPorMes[m].valorTotal);
      chartPecasPorMesValor.update();

      const pecasAgrupadas = {{}};
      filtered.forEach(item => {{
        const nomePeca = (item.peca || item.codigoPeca || 'Indefinida').trim();
        if (!pecasAgrupadas[nomePeca]) pecasAgrupadas[nomePeca] = {{ qt: 0, custo: 0 }};
        pecasAgrupadas[nomePeca].qt += (item.qt || 0);
        pecasAgrupadas[nomePeca].custo += (item.custoTotal || 0);
      }});

      const listaAgrupada = Object.entries(pecasAgrupadas).map(([nome, vals]) => ({{ nome, qt: vals.qt, custo: vals.custo }}));
      const truncarTexto = (txt, max = 28) => txt.length > max ? txt.substring(0, max) + '...' : txt;

      const top10Qt = [...listaAgrupada].sort((a, b) => b.qt - a.qt).slice(0, 10);
      chartTopPecasQt.data.labels = top10Qt.map(p => truncarTexto(p.nome));
      chartTopPecasQt.data.datasets[0].data = top10Qt.map(p => p.qt);
      chartTopPecasQt.update();

      const top10Custo = [...listaAgrupada].sort((a, b) => b.custo - a.custo).slice(0, 10);
      chartTopPecasCusto.data.labels = top10Custo.map(p => truncarTexto(p.nome));
      chartTopPecasCusto.data.datasets[0].data = top10Custo.map(p => p.custo);
      chartTopPecasCusto.update();

      const catCounts = {{}};
      filtered.forEach(d => {{ if(d.categoria) catCounts[d.categoria] = (catCounts[d.categoria] || 0) + (d.qt || 0); }});
      chartCategory.data.labels = Object.keys(catCounts);
      chartCategory.data.datasets[0].data = Object.values(catCounts);
      chartCategory.update();

      const supplierCosts = {{}};
      filtered.forEach(d => {{ if(d.fornecedor) supplierCosts[d.fornecedor] = (supplierCosts[d.fornecedor] || 0) + (d.custoTotal || 0); }});
      chartSupplier.data.labels = Object.keys(supplierCosts);
      chartSupplier.data.datasets[0].data = Object.values(supplierCosts);
      chartSupplier.update();

      renderTable(filtered, searchVal);
    }}

    function renderTable(dataList, searchTerm) {{
      const grouped = {{}};
      dataList.forEach(item => {{
        const key = item.codigoPeca || item.peca;
        if (!grouped[key]) {{
          grouped[key] = {{
            codigoPeca: item.codigoPeca || '—',
            peca: item.peca,
            categoria: item.categoria,
            qtTotal: 0,
            qtAtendida: 0,
            qtNaoAtendida: 0,
            pedidosCount: 0,
            custoTotal: 0
          }};
        }}
        grouped[key].qtTotal += (item.qt || 0);
        grouped[key].qtAtendida += (item.qtAprovada || 0);
        grouped[key].qtNaoAtendida += (item.qtNaoAprovada || 0);
        grouped[key].pedidosCount += 1;
        grouped[key].custoTotal += (item.custoTotal || 0);
      }});

      let itemsArray = Object.values(grouped);
      if (searchTerm) {{
        itemsArray = itemsArray.filter(i => 
          (i.peca && i.peca.toLowerCase().includes(searchTerm)) || 
          (i.codigoPeca && i.codigoPeca.toLowerCase().includes(searchTerm)) || 
          (i.categoria && i.categoria.toLowerCase().includes(searchTerm))
        );
      }}

      itemsArray.sort((a, b) => b.custoTotal - a.custoTotal);
      tableCountBadge.innerText = itemsArray.length + ' itens';

      if (itemsArray.length === 0) {{
        tableBody.innerHTML = '<tr><td colspan="8" class="text-center py-8 text-slate-400">Nenhuma peça encontrada.</td></tr>';
        return;
      }}

      tableBody.innerHTML = itemsArray.map(item => `
        <tr class="hover:bg-slate-50 transition">
          <td class="py-3 px-4 font-mono font-semibold text-blue-600">${{item.codigoPeca}}</td>
          <td class="py-3 px-4 font-semibold text-slate-800">${{item.peca}}</td>
          <td class="py-3 px-4"><span class="inline-block px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-100 text-slate-700">${{item.categoria}}</span></td>
          <td class="py-3 px-4 text-center font-bold text-slate-700">${{item.qtTotal.toLocaleString('pt-BR')}} un</td>
          <td class="py-3 px-4 text-center font-semibold text-emerald-600">${{item.qtAtendida.toLocaleString('pt-BR')}} un</td>
          <td class="py-3 px-4 text-center font-semibold text-rose-500">${{item.qtNaoAtendida.toLocaleString('pt-BR')}} un</td>
          <td class="py-3 px-4 text-center text-slate-500">${{item.pedidosCount}}</td>
          <td class="py-3 px-4 text-right font-bold text-amber-600">${{formatCurrency(item.custoTotal)}}</td>
        </tr>
      `).join('');
    }}

    [filterYear, filterMonth, filterCategory, filterRequester].forEach(select => select.addEventListener('change', updateDashboard));
    tableSearch.addEventListener('input', updateDashboard);
    resetFiltersBtn.addEventListener('click', () => {{
      filterYear.value = 'ALL';
      filterMonth.value = 'ALL';
      filterCategory.value = 'ALL';
      filterRequester.value = 'ALL';
      tableSearch.value = '';
      updateDashboard();
    }});

    // Inicialização da primeira aba
    let abaInicial = 'dashboardRetiradas';
    try {{
      abaInicial = sessionStorage.getItem('aba_ativa_atual') || 'dashboardRetiradas';
    }} catch(e) {{}}
    
    switchPage(abaInicial);
  </script>
</body>
</html>
"""

components.html(html_code, height=2700, scrolling=True)