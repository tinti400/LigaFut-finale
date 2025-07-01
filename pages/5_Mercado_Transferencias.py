# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
from utils import registrar_movimentacao, registrar_bid

st.set_page_config(page_title="💼 Mercado de Transferências - LigaFut", layout="wide")

# ✅ Verifica sessão
if "usuario_id" not in st.session_state or "id_time" not in st.session_state or "nome_time" not in st.session_state:
    st.warning("⚠️ Você precisa estar logado para acessar esta página.")
    st.stop()

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 🌟 Dados do usuário e time
usuario_id = st.session_state["usuario_id"]
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]
email_usuario = st.session_state.get("usuario", "")

# ⚙️ Verifica se é admin
res_admin = supabase.table("admins").select("email").eq("email", email_usuario).execute()
is_admin = len(res_admin.data) > 0

# ❌ Verifica restrição ao mercado
try:
    res_restricoes = supabase.table("times").select("restricoes").eq("id", id_time).execute()
    restricoes = res_restricoes.data[0].get("restricoes", {}) if res_restricoes.data else {}
    if restricoes.get("mercado", False):
        st.error("🚫 Seu time está proibido de acessar o Mercado de Transferências.")
        st.stop()
except Exception as e:
    st.warning(f"⚠️ Erro ao verificar restrições: {e}")

# ✅ Verifica se o mercado está aberto
res_status = supabase.table("configuracoes").select("mercado_aberto").eq("id", "estado_mercado").execute()
mercado_aberto = res_status.data[0]["mercado_aberto"] if res_status.data else False
if not mercado_aberto:
    st.warning("🚫 O mercado está fechado no momento. As compras estão temporariamente indisponíveis.")

# 💰 Saldo do time
res_saldo = supabase.table("times").select("saldo").eq("id", str(id_time)).execute()
saldo_time = res_saldo.data[0]["saldo"] if res_saldo.data else 0
st.markdown(f"### 💰 Saldo atual: **R$ {saldo_time:,.0f}**".replace(",", "."))
# 🔍 Filtros
filtro_nome = st.text_input("🔎 Buscar jogador por nome")
filtro_posicao = st.selectbox("🎯 Filtrar por posição", ["Todos", "GL", "LD", "ZAG", "LE", "VOL", "MC", "MD", "ME", "PD", "PE", "SA", "CA"])
filtro_overall = st.slider("🎯 Filtrar por overall mínimo", 50, 99, 50)

# 📦 Carrega jogadores disponíveis no mercado
try:
    res_mercado = supabase.table("mercado_transferencias").select("*").execute()
    jogadores_mercado = res_mercado.data if res_mercado.data else []
except Exception as e:
    st.error(f"Erro ao carregar mercado: {e}")
    jogadores_mercado = []

# 📋 Filtro aplicado
jogadores_filtrados = []
for j in jogadores_mercado:
    if filtro_nome and filtro_nome.lower() not in j["nome"].lower():
        continue
    if filtro_posicao != "Todos" and j["posição"] != filtro_posicao:
        continue
    if j["overall"] < filtro_overall:
        continue
    jogadores_filtrados.append(j)

# 🔁 Nome dos times
res_times = supabase.table("times").select("id", "nome").execute()
mapa_times = {t["id"]: t["nome"] for t in res_times.data}

# 📰 Título
st.markdown("### 📋 Jogadores Disponíveis no Mercado")

# 📊 Exibição dos jogadores estilo planilha
if not jogadores_filtrados:
    st.info("Nenhum jogador disponível no mercado com os filtros aplicados.")
else:
    for jogador in jogadores_filtrados:
        col1, col2, col3, col4, col5 = st.columns([2, 3, 2, 2, 2])
        with col1:
            st.markdown(f"**{jogador['posição']}**")
        with col2:
            st.markdown(f"**{jogador['nome']}**")
        with col3:
            st.markdown(f"Overall: **{jogador['overall']}**")
        with col4:
            st.markdown(f"Valor: **R$ {jogador['valor']:,.0f}**".replace(",", "."))
        with col5:
            if mercado_aberto:
                if st.button("Comprar", key=f"comprar_{jogador['id']}"):
                    if jogador["valor"] > saldo_time:
                        st.error("❌ Saldo insuficiente para esta compra.")
                    else:
                        # 💸 Atualiza saldo do comprador
                        novo_saldo = saldo_time - jogador["valor"]
                        supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

                        # 👤 Adiciona jogador ao elenco
                        novo_jogador = {
                            "nome": jogador["nome"],
                            "posição": jogador["posição"],
                            "overall": jogador["overall"],
                            "valor": jogador["valor"],
                            "link_sofifa": jogador.get("link_sofifa", "")
                        }
                        supabase.table("elenco").insert({**novo_jogador, "id_time": id_time}).execute()

                        # 🔄 Remove do mercado
                        supabase.table("mercado_transferencias").delete().eq("id", jogador["id"]).execute()

                        # 💰 Registra movimentação
                        registrar_movimentacao(id_time, -jogador["valor"], "compra", "mercado", jogador["nome"])

                        st.success(f"✅ Jogador {jogador['nome']} contratado com sucesso!")
                        st.rerun()
# 📰 Painel informativo de últimas transferências concluídas
st.markdown("---")
st.markdown("## 🔄 Últimas Transferências Concluídas")

try:
    ultimas_movs = (
        supabase.table("movimentacoes")
        .select("*")
        .order("data", desc=True)
        .limit(10)
        .execute()
        .data
    )
except Exception as e:
    st.error(f"Erro ao buscar últimas transferências: {e}")
    ultimas_movs = []

if not ultimas_movs:
    st.info("Nenhuma transferência recente.")
else:
    for mov in ultimas_movs:
        jogador = mov.get("jogador", "Desconhecido")
        tipo = mov.get("tipo", "")
        categoria = mov.get("categoria", "")
        valor = mov.get("valor", 0)
        origem = mov.get("origem", "")
        destino = mov.get("destino", "")
        data = mov.get("data", "")

        try:
            data_formatada = datetime.fromisoformat(data).strftime('%d/%m/%Y %H:%M')
        except:
            data_formatada = "Data inválida"

        valor_str = f"R$ {abs(valor):,.0f}".replace(",", ".")

        mensagem = f"**{data_formatada}** — {jogador} "
        if tipo == "compra":
            if categoria == "mercado":
                mensagem += f"foi comprado no mercado por **{valor_str}**"
            elif categoria == "proposta":
                mensagem += f"foi comprado via proposta por **{valor_str}** de **{origem}** para **{destino}**"
            elif categoria == "leilao":
                mensagem += f"foi arrematado em leilão por **{valor_str}** para **{destino}**"
        elif tipo == "venda":
            mensagem += f"foi vendido por **{valor_str}**"
        else:
            mensagem += f"movimentação de **{valor_str}**"

        st.markdown(f"🟢 {mensagem}")
