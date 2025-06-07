import streamlit as st
from supabase import create_client
from datetime import datetime
from utils import registrar_movimentacao

st.set_page_config(page_title="Elenco - LigaFut", layout="wide")

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

# 🎯 Cabeçalho
st.markdown("<h1 style='text-align: center;'>👥 Elenco do Técnico</h1><hr>", unsafe_allow_html=True)

# 📤 Upload de planilha para importar elenco
st.subheader("📥 Importar jogadores via planilha Excel")
arquivo = st.file_uploader("Selecione um arquivo .xlsx com as colunas: nome, posicao, overall, valor", type="xlsx")

if arquivo:
    import pandas as pd
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

# 📥 Carrega elenco do time
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

# 💰 Verifica saldo
saldo_res = supabase.table("times").select("saldo").eq("id", id_time).execute()
saldo = saldo_res.data[0]["saldo"] if saldo_res.data else 0

# 📋 Exibe elenco
st.markdown(f"### 💰 Saldo atual: **R$ {saldo:,.0f}**".replace(",", "."))

if not elenco_filtrado:
    st.info("Nenhum jogador encontrado com os filtros selecionados.")
else:
    for jogador in elenco_filtrado:
        col1, col2, col3, col4, col5, col6 = st.columns([2, 3, 2, 2, 2, 2])
        col1.markdown(f"**{jogador['nome']}**")
        col2.markdown(f"**Posição:** {jogador['posicao']}")
        col3.markdown(f"**Overall:** {jogador['overall']}")
        col4.markdown(f"**Valor:** R$ {jogador['valor']:,.0f}".replace(",", "."))

        # Vender jogador
        if st.button(f"Vender {jogador['nome']}", key=f"vender_{jogador['id']}"):
            try:
                valor_total = jogador["valor"]
                valor_recebido = round(valor_total * 0.7)

                # Atualiza saldo
                novo_saldo = saldo + valor_recebido
                supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

                # Remove do elenco
                supabase.table("elenco").delete().eq("id", jogador["id"]).execute()

                # Insere no mercado (com id_time para rastrear origem)
                supabase.table("mercado_transferencias").insert({
                    "nome": jogador["nome"],
                    "posicao": jogador["posicao"],
                    "overall": jogador["overall"],
                    "valor": jogador["valor"],
                    "id_time": id_time,
                    "time_origem": nome_time
                }).execute()

                # Registra movimentação
                registrar_movimentacao(id_time=id_time, jogador=jogador["nome"], valor=valor_recebido, tipo="Venda", categoria="Mercado")

                st.success(f"{jogador['nome']} foi vendido para o mercado por R$ {valor_recebido:,.0f}".replace(",", "."))
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Erro ao vender jogador: {e}")
