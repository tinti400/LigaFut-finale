# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
from dateutil.parser import parse
import pandas as pd

st.set_page_config(page_title="Painel do Técnico", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state.usuario_id:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 📥 Dados do time logado
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

# 🔢 Buscar saldo
try:
    saldo_res = supabase.table("times").select("saldo").eq("id", id_time).execute()
    saldo = saldo_res.data[0]["saldo"] if saldo_res.data else 0
except Exception as e:
    st.error(f"Erro ao carregar saldo: {e}")
    saldo = 0

# 🎯 Cabeçalho
st.markdown("<h1 style='text-align: center;'>🧑‍💼 Painel do Técnico</h1><hr>", unsafe_allow_html=True)
st.markdown(f"### 🏷️ Time: {nome_time} &nbsp;&nbsp;&nbsp;&nbsp; 💰 Saldo: R$ {saldo:,.0f}".replace(",", "."))

# 🔄 Tabs com movimentações
aba = st.radio("📂 Selecione o tipo de movimentação", ["📥 Entradas", "💸 Saídas", "📊 Resumo"])

try:
    dados = supabase.table("movimentacoes").select("*") \
        .eq("id_time", id_time).order("data", desc=True).limit(200).execute().data

    if not dados:
        st.info("Nenhuma movimentação registrada ainda.")
    else:
        entradas, saidas = [], []
        total_entrada, total_saida = 0, 0

        for m in dados:
            data_formatada = parse(m["data"]).strftime("%d/%m %H:%M") if m.get("data") else "Data inválida"
            jogador = m.get("jogador", "Desconhecido")
            valor = m.get("valor", 0)
            origem = m.get("origem", "")
            destino = m.get("destino", "")
            tipo = m.get("tipo", "").capitalize()
            categoria = m.get("categoria", "").lower()

            detalhes = f"do {origem}" if origem else f"para {destino}" if destino else "-"
            icone = "🟢" if categoria == "venda" else "🔴"

            linha = {
                "Data": data_formatada,
                "Jogador": f"{icone} {jogador}",
                "Valor (R$)": f"R$ {abs(valor):,.0f}".replace(",", "."),
                "Tipo": tipo,
                "Categoria": categoria.capitalize(),
                "Detalhes": detalhes
            }

            if categoria == "venda":
                entradas.append(linha)
                total_entrada += valor
            elif categoria == "compra":
                saidas.append(linha)
                total_saida += valor

        # 🧾 Exibição por aba
        if aba == "📥 Entradas":
            st.dataframe(pd.DataFrame(entradas), use_container_width=True)

        elif aba == "💸 Saídas":
            st.dataframe(pd.DataFrame(saidas), use_container_width=True)

        elif aba == "📊 Resumo":
            col1, col2, col3 = st.columns(3)
            with col1:
                st.success(f"💰 Total Entradas\n\nR$ {total_entrada:,.0f}".replace(",", "."))
            with col2:
                st.error(f"💸 Total Saídas\n\nR$ {total_saida:,.0f}".replace(",", "."))
            with col3:
                saldo_liquido = total_entrada - total_saida
                if saldo_liquido >= 0:
                    st.success(f"📈 Lucro\n\nR$ {saldo_liquido:,.0f}".replace(",", "."))
                else:
                    st.error(f"📉 Prejuízo\n\nR$ {abs(saldo_liquido):,.0f}".replace(",", "."))

except Exception as e:
    st.error(f"Erro ao carregar movimentações: {e}")
