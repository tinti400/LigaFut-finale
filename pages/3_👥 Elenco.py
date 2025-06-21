# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import pandas as pd
from utils import registrar_movimentacao

st.set_page_config(page_title="Elenco - LigaFut", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or "id_time" not in st.session_state:
    st.warning("⚠️ Você precisa estar logado para acessar esta página.")
    st.stop()

usuario_id = st.session_state["usuario_id"]
id_time = st.session_state["id_time"]
nome_time = st.session_state.get("nome_time", "")
email_usuario = st.session_state.get("usuario", "")

# ⚙️ Verifica se é admin
res_admin = supabase.table("admins").select("email").eq("email", email_usuario).execute()
is_admin = len(res_admin.data) > 0

st.title(f"👥 Elenco do {nome_time}")

# 💰 Buscar saldo
res_saldo = supabase.table("times").select("saldo").eq("id", id_time).execute()
saldo = res_saldo.data[0]["saldo"] if res_saldo.data else 0

# 📦 Buscar elenco
res = supabase.table("elenco").select("*").eq("id_time", id_time).execute()
jogadores = res.data if res.data else []

# 📊 Estatísticas
quantidade = len(jogadores)
valor_total = sum(j.get("valor", 0) for j in jogadores)

st.markdown(f"""
<div style='text-align:center;'>
    <h3 style='color:green;'>💰 Saldo em caixa: <strong>R$ {saldo:,.0f}</strong></h3>
    <h4>👥 Jogadores no elenco: <strong>{quantidade}</strong> | 📈 Valor total do elenco: <strong>R$ {valor_total:,.0f}</strong></h4>
</div>
""".replace(",", "."), unsafe_allow_html=True)

st.markdown("---")

# 🧹 Limpar elenco (ADM)
if is_admin and jogadores:
    if st.button("🧹 Limpar elenco COMPLETO"):
        try:
            supabase.table("elenco").delete().eq("id_time", id_time).execute()
            st.success("✅ Elenco limpo com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao limpar elenco: {e}")

# Separar jogadores por classificação
titulares = [j for j in jogadores if j.get("classificacao") == "titular"]
reservas = [j for j in jogadores if j.get("classificacao") == "reserva"]
negociaveis = [j for j in jogadores if j.get("classificacao") == "negociavel"]
sem_classificacao = [j for j in jogadores if j.get("classificacao") not in ["titular", "reserva", "negociavel"]]

# Tabs
aba1, aba2, aba3, aba4 = st.tabs(["🟢 Titulares", "🟡 Reservas", "🔴 Negociáveis", "⚪ Sem Classificação"])

abas_e_jogadores = {
    aba1: titulares,
    aba2: reservas,
    aba3: negociaveis,
    aba4: sem_classificacao
}

# Exibir jogadores por aba
for aba, lista_jogadores in abas_e_jogadores.items():
    with aba:
        if not lista_jogadores:
            st.info("Nenhum jogador nesta categoria.")
            continue

        for jogador in lista_jogadores:
            col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 2.5, 1.5, 1.5, 2.5, 2, 2.5])

            with col1:
                imagem = jogador.get("imagem_url", "")
                if imagem:
                    st.markdown(f"<img src='{imagem}' width='60' style='border-radius: 50%; border: 2px solid #ddd;'/>", unsafe_allow_html=True)
                else:
                    st.markdown("<div style='width:60px;height:60px;border-radius:50%;border:2px solid #ddd;background:#eee;'></div>", unsafe_allow_html=True)

            with col2:
                st.markdown(f"**{jogador.get('nome', 'Sem nome')}**")
                st.markdown(f"🌍 {jogador.get('nacionalidade', 'Desconhecida')}")

            with col3:
                st.markdown(f"📌 {jogador.get('posicao', '-')}")

            with col4:
                st.markdown(f"⭐ {jogador.get('overall', '-')}")

            with col5:
                valor_formatado = "R$ {:,.0f}".format(jogador.get("valor", 0)).replace(",", ".")
                origem = jogador.get("origem", "Desconhecida")
                st.markdown(f"💰 **{valor_formatado}**")
                st.markdown(f"🏟️ {origem}")

            with col6:
                classificacao_atual = jogador.get("classificacao", "")
                nova_classificacao = st.selectbox(
                    "Classificar",
                    ["titular", "reserva", "negociavel"],
                    index=["titular", "reserva", "negociavel"].index(classificacao_atual) if classificacao_atual in ["titular", "reserva", "negociavel"] else 0,
                    key=f"class_{jogador['id']}"
                )
                if nova_classificacao != classificacao_atual:
                    try:
                        supabase.table("elenco").update({"classificacao": nova_classificacao}).eq("id", jogador["id"]).execute()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao atualizar classificação: {e}")

            with col7:
                if st.button(f"💸 Vender {jogador['nome']}", key=f"vender_{jogador['id']}"):
                    try:
                        supabase.table("elenco").delete().eq("id", jogador["id"]).execute()
                        supabase.table("mercado_transferencias").insert({
                            "nome": jogador["nome"],
                            "posicao": jogador["posicao"],
                            "overall": jogador["overall"],
                            "valor": jogador["valor"],
                            "id_time": id_time,
                            "time_origem": nome_time,
                            "imagem_url": jogador.get("imagem_url", ""),
                            "nacionalidade": jogador.get("nacionalidade", "Desconhecida"),
                            "origem": origem
                        }).execute()
                        registrar_movimentacao(
                            id_time=id_time,
                            jogador=jogador["nome"],
                            valor=round(jogador["valor"] * 0.7),
                            tipo="mercado",
                            categoria="venda",
                            destino="Mercado"
                        )
                        st.success(f"{jogador['nome']} foi vendido com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao vender jogador: {e}")
