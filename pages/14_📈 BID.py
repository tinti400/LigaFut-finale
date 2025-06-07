# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
import pandas as pd

st.set_page_config(page_title="📋 BID da LigaFut", layout="wide")
st.title("📋 BID da LigaFut")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 🔄 Recupera movimentações
try:
    mov_ref = supabase.table("movimentacoes").select("*").order("data", desc=True).limit(500).execute()
    movimentacoes = mov_ref.data
except Exception as e:
    st.error(f"Erro ao buscar movimentações: {e}")
    movimentacoes = []

# 🔁 Mapeia os IDs dos times para nomes
try:
    times_res = supabase.table("times").select("id", "nome").execute()
    times_map = {t["id"]: t["nome"] for t in times_res.data}
except Exception as e:
    st.error(f"Erro ao buscar nomes dos times: {e}")
    times_map = {}

# 🔍 Filtros
st.sidebar.markdown("### 🎯 Filtros")
nome_jogador = st.sidebar.text_input("Buscar por jogador").lower()
tipo_mov = st.sidebar.selectbox("Tipo de movimentação", ["Todos", "compra", "venda"])
categoria = st.sidebar.selectbox("Categoria", ["Todas", "mercado", "proposta", "leilao"])

# 📊 Agrupar por data
hoje = datetime.now().date()
onteontem = hoje - timedelta(days=2)
def formatar_data(data):
    dt = datetime.fromisoformat(data).date()
    if dt == hoje:
        return "Hoje"
    elif dt == hoje - timedelta(days=1):
        return "Ontem"
    elif dt == onteontem:
        return "Anteontem"
    else:
        return dt.strftime("%d/%m/%Y")

# 📋 Aplica filtros
filtradas = []
for mov in movimentacoes:
    if nome_jogador and nome_jogador not in mov.get("jogador", "").lower():
        continue
    if tipo_mov != "Todos" and mov.get("tipo") != tipo_mov:
        continue
    if categoria != "Todas" and mov.get("categoria") != categoria:
        continue
    filtradas.append(mov)

# 📋 Agrupa por data
agrupadas = {}
for mov in filtradas:
    data_chave = formatar_data(mov.get("data", ""))
    agrupadas.setdefault(data_chave, []).append(mov)

# 📦 Exportar CSV
if st.sidebar.button("⬇️ Exportar CSV"):
    if filtradas:
        df_export = pd.DataFrame(filtradas)
        csv = df_export.to_csv(index=False).encode("utf-8")
        st.sidebar.download_button("Baixar CSV", csv, "movimentacoes_ligafut.csv", "text/csv")
    else:
        st.sidebar.warning("Nenhuma movimentação para exportar.")

# 📋 Exibe
if not filtradas:
    st.info("Nenhuma movimentação registrada com os filtros selecionados.")
else:
    for data_exibicao in sorted(agrupadas.keys(), reverse=True):
        st.markdown(f"## 📅 {data_exibicao}")
        for mov in agrupadas[data_exibicao]:
            jogador = mov.get("jogador", "Desconhecido")
            tipo = mov.get("tipo", "N/A").capitalize()
            cat = mov.get("categoria", "N/A").capitalize()
            valor = mov.get("valor", 0)
            data = mov.get("data", "")
            id_time = mov.get("id_time", "")
            nome_time = times_map.get(id_time, "Desconhecido")
            destino = mov.get("destino", "")
            origem = mov.get("origem", "")

            try:
                data_formatada = datetime.fromisoformat(data).strftime('%d/%m/%Y %H:%M')
            except:
                data_formatada = "Data inválida"

            valor_str = f"R$ {abs(valor):,.0f}".replace(",", ".")
            icone = "📢" if cat.lower() == "leilao" else ("📤" if cat.lower() == "proposta" else ("🟢" if valor >= 0 else "🔴"))

            with st.container():
                st.markdown("---")
                col1, col2 = st.columns([1, 6])
                with col1:
                    st.markdown(f"<span style='font-size:28px'>{icone}</span>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"**🕒 {data_formatada}** — **{nome_time}**")
                    st.markdown(f"**👤 Jogador:** {jogador}")
                    st.markdown(f"**💬 Tipo:** {tipo} — **📂 Categoria:** {cat}")
                    st.markdown(f"**💰 Valor:** {valor_str}")
                    if origem:
                        st.markdown(f"**↩️ Origem:** {origem}")
                    if destino:
                        st.markdown(f"**➡️ Destino:** {destino}")

