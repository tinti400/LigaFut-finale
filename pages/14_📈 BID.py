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

# 🔄 Carrega todas movimentações
try:
    mov_ref = supabase.table("movimentacoes").select("*").order("data", desc=True).execute()
    todas_movs = mov_ref.data
except Exception as e:
    st.error(f"Erro ao buscar movimentações: {e}")
    todas_movs = []

# 🎛️ Filtros
filtro_time = st.selectbox("Filtrar por time", ["Todos"] + list(times_map.values()))
filtro_tipo = st.selectbox("Filtrar por tipo", ["Todos", "compra", "venda"])
filtro_categoria = st.selectbox("Filtrar por categoria", ["Todos", "mercado", "leilao", "proposta"])

# Aplica filtros
movimentacoes = []
for mov in todas_movs:
    nome_time = times_map.get(mov.get("id_time", ""), "Desconhecido")

    if filtro_time != "Todos" and nome_time != filtro_time:
        continue
    if filtro_tipo != "Todos" and mov.get("tipo") != filtro_tipo:
        continue
    if filtro_categoria != "Todos" and mov.get("categoria") != filtro_categoria:
        continue

    mov["nome_time"] = nome_time
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
        jogador = mov.get("jogador", "Desconhecido")
        tipo = mov.get("tipo", "N/A").capitalize()
        categoria = mov.get("categoria", "N/A").capitalize()
        valor = mov.get("valor", 0)
        data = mov.get("data", "")
        nome_time = mov.get("nome_time", "Desconhecido")
        destino = mov.get("destino", "")
        origem = mov.get("origem", "")

        try:
            data_formatada = datetime.fromisoformat(data).strftime('%d/%m/%Y %H:%M')
        except:
            data_formatada = "Data inválida"

        valor_str = f"R$ {abs(valor):,.0f}".replace(",", ".")

        # Ícones e estilo por categoria
        if categoria.lower() == "leilao":
            icone = "📢"
            cor_fundo = "#fff3cd"  # amarelo claro
        elif categoria.lower() == "proposta":
            icone = "📤"
            cor_fundo = "#f8f9fa"
        elif valor >= 0:
            icone = "🟢"
            cor_fundo = "#f8f9fa"
        else:
            icone = "🔴"
            cor_fundo = "#f8f9fa"

        cor_valor = "green" if valor >= 0 else "red"

        st.markdown(f"""
            <div style='background-color:{cor_fundo}; padding:15px; border-radius:10px; margin-bottom:20px'>
                <h5 style='margin-bottom:10px'>{icone} {data_formatada} — <strong>{nome_time}</strong></h5>
                <p><strong>👤 Jogador:</strong> {jogador}</p>
                <p><strong>💬 Tipo:</strong> {tipo} — <strong>📂 Categoria:</strong> {categoria}</p>
                <p><strong>💰 Valor:</strong> <span style='color:{cor_valor}'>{valor_str}</span></p>
                {"<p><strong>↩️ Origem:</strong> " + origem + "</p>" if origem else ""}
                {"<p><strong>➡️ Destino:</strong> " + destino + "</p>" if destino else ""}
            </div>
        """, unsafe_allow_html=True)
