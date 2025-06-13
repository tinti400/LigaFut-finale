# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
from utils import registrar_movimentacao

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="👥 Elenco", layout="wide")
st.title("👥 Elenco do Time")

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

usuario_id = st.session_state["usuario_id"]
id_time = st.session_state.get("id_time", "")
nome_time = st.session_state.get("nome_time", "")

# ⚙️ Verifica se é admin
res_admin = supabase.table("admins").select("email").eq("email", st.session_state.get("usuario", "")).execute()
eh_admin = bool(res_admin.data)

# 📥 Importação de jogadores via planilha XLSX (permitido a todos)
with st.expander("📥 Importar jogadores via planilha (.xlsx)"):
    arquivo = st.file_uploader("Selecione a planilha", type=["xlsx"])
    if arquivo:
        try:
            df = pd.read_excel(arquivo)
            for _, row in df.iterrows():
                jogador_data = {
                    "nome": row["nome"],
                    "posicao": row["posição"],
                    "overall": int(row["overall"]),
                    "valor": int(float(row["valor"])),
                    "id_time": id_time
                }
                supabase.table("elenco").insert(jogador_data).execute()
            st.success("✅ Jogadores importados com sucesso!")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Erro ao importar: {e}")

# 🔁 Carregar elenco
res = supabase.table("elenco").select("*").eq("id_time", id_time).execute()
elenco = res.data

# 💰 Buscar saldo do time
res_saldo = supabase.table("times").select("saldo").eq("id", id_time).execute()
saldo = res_saldo.data[0]["saldo"] if res_saldo.data else 0

st.markdown(f"**💸 Saldo em caixa:** R$ {saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

# 📋 Exibir elenco estilo planilha
if elenco:
    st.markdown("### 📄 Lista de Jogadores")
    for jogador in elenco:
        col1, col2, col3, col4, col5, col6 = st.columns([2, 3, 1, 2, 2, 1])
        with col1:
            st.markdown(f"**{jogador['posicao']}**")
        with col2:
            st.markdown(f"{jogador['nome']}")
        with col3:
            st.markdown(f"{jogador['overall']}")
        with col4:
            st.markdown(f"R$ {jogador['valor']:,.0f}".replace(",", "."))
        with col5:
            if st.button("💰 Vender", key=f"vender_{jogador['id']}"):
                if len(elenco) <= 1:
                    st.warning("⚠️ O elenco não pode ficar vazio.")
                else:
                    valor_recebido = round(jogador['valor'] * 0.7, 2)
                    novo_saldo = saldo + valor_recebido

                    # Atualiza saldo
                    supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

                    # Remove do elenco
                    supabase.table("elenco").delete().eq("id", jogador["id"]).execute()

                    # Adiciona ao mercado
                    jogador_market = {
                        "nome": jogador["nome"],
                        "posicao": jogador["posicao"],
                        "overall": jogador["overall"],
                        "valor": jogador["valor"]
                    }
                    supabase.table("mercado_transferencias").insert(jogador_market).execute()

                    # Registra movimentação
                    registrar_movimentacao(
                        id_time=id_time,
                        jogador=jogador["nome"],
                        tipo="mercado",
                        categoria="venda",
                        valor=valor_recebido,
                        origem=nome_time,
                        destino="Mercado"
                    )

                    st.success(f"{jogador['nome']} foi vendido por R$ {valor_recebido:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    st.experimental_rerun()
        with col6:
            if eh_admin and st.button("🗑️", key=f"del_{jogador['id']}"):
                supabase.table("elenco").delete().eq("id", jogador["id"]).execute()
                st.success(f"Jogador {jogador['nome']} excluído do elenco.")
                st.experimental_rerun()
else:
    st.info("Nenhum jogador no elenco ainda.")
