# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from dateutil.parser import parse

st.set_page_config(page_title="📊 Painel do Técnico", layout="wide")

# 🔐 Supabase
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

st.markdown("<h1 style='text-align: center;'>📊 Painel do Técnico</h1><hr>", unsafe_allow_html=True)
st.markdown(f"### 🏷️ Time: {nome_time} &nbsp;&nbsp;&nbsp;&nbsp; 💰 Saldo: R$ {saldo:,.0f}".replace(",", "."))

# 📂 Tipo de movimentação
aba = st.radio("Filtrar:", ["📥 Entradas", "💸 Saídas", "📊 Resumo"])

try:
    # 📦 Carregar todas as movimentações
    dados = supabase.table("movimentacoes").select("*").order("data", desc=True).execute().data
    if not dados:
        st.info("Nenhuma movimentação registrada.")
        st.stop()

    entradas, saidas = [], []
    total_entrada, total_saida = 0, 0
    nome_norm = nome_time.strip().lower()

    for mov in dados:
        origem = mov.get("origem", "") or ""
        destino = mov.get("destino", "") or ""
        jogador = mov.get("jogador", "Desconhecido")
        valor = mov.get("valor", 0)
        tipo = mov.get("tipo", "").capitalize()
        categoria = mov.get("categoria", "-")

        # Normaliza para comparação
        origem_norm = origem.strip().lower()
        destino_norm = destino.strip().lower()

        linha = {
            "jogador": jogador,
            "valor": valor,
            "categoria": categoria,
            "tipo": tipo,
            "origem": origem,
            "destino": destino,
        }

        if destino_norm == nome_norm:
            entradas.append(linha)
            total_entrada += valor
        elif origem_norm == nome_norm:
            saidas.append(linha)
            total_saida += valor

    # 🎯 Exibição
    def exibir_movimentacoes(lista, icone, cor):
        for item in lista:
            st.markdown("---")
            col1, col2, col3 = st.columns([3, 3, 2])
            col1.markdown(f"**{icone} {item['jogador']}**")
            col2.markdown(f"🧾 {item['tipo']} - {item['categoria']}")
            if icone == "🟢":
                col3.markdown(f"💰 <span style='color:green'>R$ {item['valor']:,.0f}</span>", unsafe_allow_html=True)
            else:
                col3.markdown(f"💸 <span style='color:red'>R$ {item['valor']:,.0f}</span>", unsafe_allow_html=True)

    if aba == "📥 Entradas":
        st.markdown("### 📥 Entradas")
        exibir_movimentacoes(entradas, "🟢", "green")
    elif aba == "💸 Saídas":
        st.markdown("### 💸 Saídas")
        exibir_movimentacoes(saidas, "🔴", "red")
    elif aba == "📊 Resumo":
        saldo_liquido = total_entrada - total_saida
        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Total de Entradas", f"R$ {total_entrada:,.0f}".replace(",", "."))
        col2.metric("💸 Total de Saídas", f"R$ {total_saida:,.0f}".replace(",", "."))
        col3.metric(
            "📈 Lucro/Prejuízo",
            f"R$ {saldo_liquido:,.0f}".replace(",", "."),
            delta=f"{'+' if saldo_liquido >= 0 else '-'}R$ {abs(saldo_liquido):,.0f}".replace(",", ".")
        )

except Exception as e:
    st.error(f"Erro ao carregar movimentações: {e}")
