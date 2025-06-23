# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import math

st.set_page_config(page_title="📈 BID da LigaFut", layout="wide")
st.title("📈 BID da LigaFut")

# 🔐 Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 🔁 Mapeia nomes dos times
try:
    times_res = supabase.table("times").select("id", "nome").execute()
    times_map = {t["id"]: t["nome"] for t in times_res.data}
except Exception as e:
    st.error(f"Erro ao buscar times: {e}")
    times_map = {}

# 🔄 Carrega BID
try:
    bid_res = supabase.table("bid").select("*").order("data", desc=True).execute()
    todas_movs = bid_res.data
except Exception as e:
    st.error(f"Erro ao buscar BID: {e}")
    todas_movs = []

# 🎛️ Filtros
filtro_time = st.selectbox("Filtrar por time", ["Todos"] + list(times_map.values()))
filtro_tipo = st.selectbox("Filtrar por tipo", ["Todos", "compra", "venda"])
filtro_categoria = st.selectbox("Filtrar por categoria", ["Todos", "mercado", "leilao", "proposta"])

# Aplica filtros
movimentacoes = []
for mov in todas_movs:
    nome_time_origem = times_map.get(mov.get("id_time_origem", ""), "Desconhecido")
    nome_time_destino = times_map.get(mov.get("id_time_destino", ""), "Desconhecido")

    if filtro_time != "Todos" and filtro_time not in [nome_time_origem, nome_time_destino]:
        continue
    if filtro_tipo != "Todos" and mov.get("tipo") != filtro_tipo:
        continue
    if filtro_categoria != "Todos" and mov.get("categoria") != filtro_categoria:
        continue

    mov["nome_time_origem"] = nome_time_origem
    mov["nome_time_destino"] = nome_time_destino
    movimentacoes.append(mov)

# 📄 Paginação
por_pagina = 50
total_paginas = math.ceil(len(movimentacoes) / por_pagina)
pagina = st.number_input("Página", min_value=1, max_value=max(1, total_paginas), value=1, step=1)

inicio = (pagina - 1) * por_pagina
fim = inicio + por_pagina
movs_paginados = movimentacoes[inicio:fim]

# 📋 Exibição
if not movs_paginados:
    st.info("Nenhuma movimentação encontrada.")
else:
    for mov in movs_paginados:
        jogador = mov.get("jogador_nome", "Desconhecido")
        posicao = mov.get("jogador_posicao", "-")
        tipo = mov.get("tipo", "N/A").capitalize()
        categoria = mov.get("categoria", "N/A").capitalize()
        valor = mov.get("valor", 0)
        data = mov.get("data", "")
        origem = mov.get("nome_time_origem", "Desconhecido")
        destino = mov.get("nome_time_destino", "Desconhecido")

        try:
            data_formatada = datetime.fromisoformat(data).strftime('%d/%m/%Y %H:%M')
        except:
            data_formatada = "Data inválida"

        valor_str = f"R$ {valor:,.0f}".replace(",", ".")

        # Ícones por tipo/categoria
        if categoria.lower() == "leilao":
            icone = "📢"
        elif categoria.lower() == "proposta":
            icone = "📤"
        elif categoria.lower() == "mercado":
            icone = "🏪"
        else:
            icone = "🔁"

        cor_valor = "green" if tipo.lower() == "compra" else "red"

        with st.container():
            st.markdown("---")
            col1, col2 = st.columns([1, 6])
            with col1:
                st.markdown(f"<span style='font-size:28px'>{icone}</span>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"**🕒 {data_formatada}** — **{destino}**")
                st.markdown(f"**👤 Jogador:** {jogador} ({posicao})")
                st.markdown(f"**💬 Tipo:** {tipo} — **📂 Categoria:** {categoria}")
                st.markdown(f"**💰 Valor:** <span style='color:{cor_valor}'>{valor_str}</span>", unsafe_allow_html=True)
                st.markdown(f"**↩️ Origem:** {origem}")
                st.markdown(f"**➡️ Destino:** {destino}")
