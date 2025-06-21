# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from utils import registrar_movimentacao

st.set_page_config(page_title="Mercado de Transferências - LigaFut", layout="wide")

# 🔒 Verifica se o usuário está logado
if "usuario_id" not in st.session_state or "id_time" not in st.session_state:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 🔐 Conexão
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 📌 Dados do time
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

# ✅ Verifica se o usuário é admin
is_admin = False
if "usuario" in st.session_state:
    email_usuario = st.session_state["usuario"]
    admin_check = supabase.table("admins").select("email").eq("email", email_usuario).execute()
    is_admin = bool(admin_check.data)

# 🔒 Verifica se o time está bloqueado no mercado
try:
    res_restricoes = supabase.table("times").select("restricoes").eq("id", id_time).execute()
    restricoes = res_restricoes.data[0].get("restricoes", {}) if res_restricoes.data else {}
    if restricoes.get("mercado", False):
        st.error("🚫 Seu time está proibido de acessar o Mercado de Transferências.")
        st.stop()
except Exception as e:
    st.warning(f"⚠️ Erro ao verificar restrições: {e}")

# 🔒 Verifica se o mercado está aberto
status_res = supabase.table("configuracoes").select("mercado_aberto").eq("id", "estado_mercado").execute()
mercado_aberto = status_res.data[0]["mercado_aberto"] if status_res.data else False
if not mercado_aberto:
    st.warning("🚫 O mercado está fechado no momento.")
    st.stop()

# 💰 Saldo
saldo_res = supabase.table("times").select("saldo").eq("id", str(id_time)).execute()
saldo_time = saldo_res.data[0]["saldo"] if saldo_res.data else 0
st.markdown(f"### 💰 Saldo atual: **R$ {saldo_time:,.0f}**".replace(",", "."))

# 🔍 Filtros
st.markdown("### 🔍 Filtros de Pesquisa")
filtro_nome = st.text_input("Nome do jogador").strip().lower()
filtro_nacionalidade = st.text_input("Nacionalidade").strip().lower()
filtro_posicao = st.text_input("Posição").strip().lower()
filtro_ordenacao = st.selectbox("Ordenar por", ["Nenhum", "Maior Overall", "Menor Overall", "Nome A-Z", "Nome Z-A"])

# 🗕️ Carrega jogadores do mercado
res = supabase.table("mercado_transferencias").select("*").execute()
mercado = res.data if res.data else []

# 🔍 Aplica filtros
jogadores_filtrados = [j for j in mercado if
    (filtro_nome in j["nome"].lower()) and
    (filtro_nacionalidade in j.get("nacionalidade", "").lower()) and
    (filtro_posicao in j.get("posicao", "").lower())
] if filtro_nome or filtro_nacionalidade or filtro_posicao else mercado

# 📊 Ordenação
if filtro_ordenacao == "Maior Overall":
    jogadores_filtrados.sort(key=lambda x: x.get("overall", 0), reverse=True)
elif filtro_ordenacao == "Menor Overall":
    jogadores_filtrados.sort(key=lambda x: x.get("overall", 0))
elif filtro_ordenacao == "Nome A-Z":
    jogadores_filtrados.sort(key=lambda x: x.get("nome", "").lower())
elif filtro_ordenacao == "Nome Z-A":
    jogadores_filtrados.sort(key=lambda x: x.get("nome", "").lower(), reverse=True)

# 🔢 Paginação
jogadores_por_pagina = 15
total_jogadores = len(jogadores_filtrados)
total_paginas = (total_jogadores - 1) // jogadores_por_pagina + 1
if "pagina_mercado" not in st.session_state:
    st.session_state["pagina_mercado"] = 1
pagina_atual = st.session_state["pagina_mercado"]
inicio = (pagina_atual - 1) * jogadores_por_pagina
fim = inicio + jogadores_por_pagina
jogadores_pagina = jogadores_filtrados[inicio:fim]

# 🔍 Verifica quantidade atual do elenco
res_elenco = supabase.table("elenco").select("id").eq("id_time", id_time).execute()
qtde_elenco = len(res_elenco.data) if res_elenco.data else 0

# 📒 Exibição
st.title("📈 Mercado de Transferências")
st.markdown(f"**Página {pagina_atual} de {total_paginas}**")

for jogador in jogadores_pagina:
    col1, col2, col3, col4 = st.columns([1, 2, 2, 2])
    with col1:
        try:
            st.image(jogador.get("foto") or "https://cdn-icons-png.flaticon.com/512/147/147144.png", width=60)
        except:
            st.image("https://cdn-icons-png.flaticon.com/512/147/147144.png", width=60)
    with col2:
        st.markdown(f"**{jogador.get('nome')}**")
        st.markdown(f"Posição: {jogador.get('posicao')}")
        st.markdown(f"Overall: {jogador.get('overall')}")
        st.markdown(f"Nacionalidade: {jogador.get('nacionalidade', 'N/D')}")
        st.markdown(f"Time de origem: {jogador.get('time_origem', 'N/D')}")
    with col3:
        st.markdown(f"💰 Valor: R$ {jogador.get('valor', 0):,.0f}".replace(",", "."))
    with col4:
        if qtde_elenco >= 35:
            st.warning("⚠️ Elenco cheio (35 jogadores)")
        else:
            if st.button(f"Comprar {jogador['nome']}", key=jogador["id"]):
                check = supabase.table("mercado_transferencias").select("id").eq("id", jogador["id"]).execute()
                if not check.data:
                    st.error("❌ Este jogador já foi comprado por outro time.")
                    st.experimental_rerun()
                elif saldo_time < jogador["valor"]:
                    st.error("❌ Saldo insuficiente.")
                else:
                    try:
                        supabase.table("elenco").insert({
                            "nome": jogador["nome"],
                            "posicao": jogador["posicao"],
                            "overall": jogador["overall"],
                            "valor": jogador["valor"],
                            "id_time": id_time
                        }).execute()

                        supabase.table("mercado_transferencias").delete().eq("id", jogador["id"]).execute()

                        registrar_movimentacao(
                            id_time=id_time,
                            jogador=jogador["nome"],
                            tipo="mercado",
                            categoria="compra",
                            valor=jogador["valor"],
                            origem=jogador.get("time_origem"),
                            destino=nome_time
                        )

                        st.success(f"{jogador['nome']} comprado com sucesso!")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Erro ao comprar jogador: {e}")

# 🔁 Paginação
col_nav1, col_nav2, col_nav3 = st.columns(3)
with col_nav1:
    if st.button("⬅ Página anterior") and pagina_atual > 1:
        st.session_state["pagina_mercado"] -= 1
        st.experimental_rerun()
with col_nav3:
    if st.button("➡ Próxima página") and pagina_atual < total_paginas:
        st.session_state["pagina_mercado"] += 1
        st.experimental_rerun()
