# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from utils import formatar_valor, verificar_login
import pandas as pd

st.set_page_config(page_title="Elenco - LigaFut", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
verificar_login()

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.markdown(f"<h1 style='text-align:center;'>♟️ Elenco do {nome_time}</h1><hr>", unsafe_allow_html=True)

# 🔄 Buscar dados do time
res_saldo = supabase.table("times").select("saldo").eq("id", id_time).execute()
saldo = res_saldo.data[0]["saldo"] if res_saldo.data else 0
st.markdown(f"💰 <b>Saldo em caixa:</b> <span style='color:green;'>R$ {formatar_valor(saldo)}</span>", unsafe_allow_html=True)

# 🔄 Buscar elenco
res = supabase.table("elenco").select("*").eq("id_time", id_time).execute()
jogadores = res.data if res.data else []

# 📊 Cálculos gerais
total_valor = sum(j.get("valor", 0) for j in jogadores)
for jogador in jogadores:
    if "salario" not in jogador:
        jogador["salario"] = int(jogador.get("valor", 0) * 0.01)

total_salario = sum(j.get("salario", 0) for j in jogadores)

st.markdown(f"👥 <b>Jogadores no elenco:</b> {len(jogadores)} | 📈 <b>Valor total:</b> R$ {formatar_valor(total_valor)} | 🧾 <b>Salário total:</b> R$ {formatar_valor(total_salario)}", unsafe_allow_html=True)
st.markdown("---")

# 🔍 Filtro por posição
posicoes = ["Todos"] + sorted(set(j.get("posição", "Desconhecido") for j in jogadores))
filtro_posicao = st.selectbox("📌 Filtrar por posição:", posicoes)

# 🧾 Mostrar jogadores
for jogador in jogadores:
    if filtro_posicao != "Todos" and jogador.get("posição") != filtro_posicao:
        continue

    nome = jogador.get("nome", "Desconhecido")
    posicao = jogador.get("posição", "N/D")
    overall = jogador.get("overall", "N/D")
    valor = jogador.get("valor", 0)
    salario = jogador.get("salario", 0)
    nacionalidade = jogador.get("nacionalidade", "None")
    origem = jogador.get("origem", "None")

    col1, col2, col3 = st.columns([3, 5, 3])
    with col1:
        st.markdown(f"**{nome}**")
        st.caption(f"📍 {nacionalidade}")
    with col2:
        st.markdown(f"🔁 {posicao} | ⭐ {overall}")
        st.markdown(f"💰 Valor: R$ {formatar_valor(valor)}")
        st.markdown(f"🧾 Salário: R$ {formatar_valor(salario)}")
        st.caption(f"🏠 Origem: {origem}")
    with col3:
        if st.button(f"Vender {nome}", key=f"vender_{nome}"):
            valor_mercado = valor
            valor_recebido = int(valor_mercado * 0.7)
            jogador.pop("id")  # remove id do jogador
            supabase.table("mercado_transferencias").insert({
                **jogador,
                "valor": valor_mercado
            }).execute()
            supabase.table("elenco").delete().match({
                "id_time": id_time,
                "nome": nome
            }).execute()
            novo_saldo = saldo + valor_recebido
            supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()
            st.success(f"{nome} vendido por R$ {formatar_valor(valor_recebido)}!")
            st.experimental_rerun()
