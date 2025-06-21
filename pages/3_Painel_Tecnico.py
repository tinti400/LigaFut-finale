# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from utils import verificar_login, formatar_valor
import pandas as pd

st.set_page_config(page_title="📋 Painel Técnico", page_icon="📋", layout="wide")
st.markdown("## 📋 Painel Técnico - Histórico de Movimentações")

# 🔒 Verifica login
verificar_login()

# 🔗 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 📌 Dados da sessão
id_time = st.session_state["id_time"]
nome_time = st.session_state.get("nome_time", "Seu Time")
nome_normalizado = nome_time.strip().lower()

# 🔄 Buscar movimentações
try:
    res = supabase.table("movimentacoes").select("*").order("id", desc=True).limit(500).execute()
    movimentacoes = res.data or []

    entradas, saidas = [], []

    for m in movimentacoes:
        origem = (m.get("origem") or "").strip().lower()
        destino = (m.get("destino") or "").strip().lower()
        if nome_normalizado in destino:
            entradas.append(m)
        elif nome_normalizado in origem:
            saidas.append(m)

    entradas = entradas[:4]
    saidas = saidas[:4]

    def criar_df(lista, tipo_mov):
        dados = []
        for mov in lista:
            dados.append({
                "👤 Jogador": mov.get("jogador", "Desconhecido"),
                "💰 Valor": formatar_valor(mov.get("valor", 0)),
                "📦 Tipo": mov.get("tipo", "-").capitalize(),
                "📁 Categoria": mov.get("categoria", "-").capitalize(),
                "🏷️ Origem" if tipo_mov == "entrada" else "🏷️ Destino": mov.get("origem") if tipo_mov == "entrada" else mov.get("destino"),
            })
        return pd.DataFrame(dados)

    st.markdown("### 🟢 Últimas Entradas")
    if entradas:
        df_entradas = criar_df(entradas, "entrada")
        st.dataframe(df_entradas, use_container_width=True)
    else:
        st.info("Nenhuma entrada registrada.")

    st.markdown("### 🔴 Últimas Saídas")
    if saídas := saidas:
        df_saidas = criar_df(saídas, "saida")
        st.dataframe(df_saidas, use_container_width=True)
    else:
        st.info("Nenhuma saída registrada.")

except Exception as e:
    st.error(f"Erro ao carregar movimentações: {e}")



