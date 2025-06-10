# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import pandas as pd
from utils import registrar_movimentacao

st.set_page_config(page_title="Elenco - LigaFut", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login e sessão única
if "usuario_id" not in st.session_state or "session_id" not in st.session_state:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

res = supabase.table("usuarios").select("session_id").eq("id", st.session_state["usuario_id"]).execute()
if res.data and res.data[0]["session_id"] != st.session_state["session_id"]:
    st.error("⚠️ Sua sessão foi encerrada em outro dispositivo.")
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.stop()

# 📅 Dados do time logado
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

# 🎯 Cabeçalho
st.markdown("<h1 style='text-align: center;'>👥 Elenco do Técnico</h1><hr>", unsafe_allow_html=True)

# 📄 Upload de planilha para importar elenco
st.subheader("📅 Importar jogadores via planilha Excel")
arquivo = st.file_uploader("Selecione um arquivo .xlsx com as colunas: nome, posicao, overall, valor", type="xlsx")

if arquivo:
    try:
        df = pd.read_excel(arquivo)
        for _, row in df.iterrows():
            supabase.table("elenco").insert({
                "nome": row["nome"],
                "posicao": row["posicao"],
                "overall": int(row["overall"]),
                "valor": float(row["valor"]),
                "id_time": id_time
            }).execute()
        st.success("Elenco importado com sucesso!")
        st.experimental_rerun()
    except Exception as e:
        st.error(f"Erro ao importar elenco: {e}")

# 🔍 Filtro de busca
filtro_posicao = st.selectbox("Filtrar por posição", ["Todos", "GL", "ZAG", "LD", "LE", "VOL", "MC", "MD", "ME", "PD", "PE", "SA", "CA"])
filtro_nome = st.text_input("Buscar por nome").lower()

if st.button("🔄 Limpar filtros"):
    st.experimental_rerun()

# 📝 Carrega elenco do time
try:
    response = supabase.table("elenco").select("*").eq("id_time", id_time).execute()
    elenco = response.data
except Exception as e:
    st.error(f"Erro ao carregar elenco: {e}")
    elenco = []

# 🎯 Aplica filtros
elenco_filtrado = []
for jogador in elenco:
    if filtro_posicao != "Todos" and jogador.get("posicao") != filtro_posicao:
        continue
    if filtro_nome and filtro_nome not in jogador.get("nome", "").lower():
        continue
    elenco_filtrado.append(jogador)

# 📊 Estatísticas
media_overall = round(sum(j["overall"] for j in elenco_filtrado) / len(elenco_filtrado), 1) if elenco_filtrado else 0
valor_total = sum(j["valor"] for j in elenco_filtrado)

# 💰 Verifica saldo
saldo_res = supabase.table("times").select("saldo").eq("id", id_time).execute()
saldo = saldo_res.data[0]["saldo"] if saldo_res.data else 0

# 📈 Exibe stats
st.markdown("### 💰 Saldo atual: **R$ {:,.0f}**".format(saldo).replace(",", "."))
st.markdown("### 📅 Jogadores no elenco: {} / {}".format(len(elenco_filtrado), len(elenco)))
st.markdown("### 📊 Estatísticas:")
st.markdown("- Média de Overall: **{}**".format(media_overall))
st.markdown("- Valor total do elenco: **R$ {:,.0f}**".format(valor_total).replace(",", "."))

# 📊 Exibe elenco
if not elenco_filtrado:
    st.info("Nenhum jogador encontrado com os filtros selecionados.")
else:
    for jogador in elenco_filtrado:
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])
        col1.markdown(f"**{jogador['nome']}**")
        col2.markdown(f"**Posição:** {jogador['posicao']}")
        col3.markdown(f"**Overall:** {jogador['overall']}")
        col4.markdown("**Valor:** R$ {:,.0f}".format(jogador["valor"]).replace(",", "."))

        if col5.button(f"Vender {jogador['nome']}", key=f"vender_{jogador['id']}"):
            try:
                # Remover do elenco
                supabase.table("elenco").delete().eq("id", jogador["id"]).execute()

                # Inserir no mercado
                supabase.table("mercado_transferencias").insert({
                    "nome": jogador["nome"],
                    "posicao": jogador["posicao"],
                    "overall": jogador["overall"],
                    "valor": jogador["valor"],
                    "id_time": id_time,
                    "time_origem": nome_time
                }).execute()

                # Registrar movimentação (saldo atualizado no utils)
                registrar_movimentacao(
                    id_time=id_time,
                    jogador=jogador["nome"],
                    valor=jogador["valor"],
                    tipo="Mercado",
                    categoria="Venda",
                    destino="Mercado"
                )

                st.success(f"{jogador['nome']} foi vendido para o mercado por R$ {int(jogador['valor'] * 0.7):,}".replace(",", "."))
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Erro ao vender jogador: {e}")


