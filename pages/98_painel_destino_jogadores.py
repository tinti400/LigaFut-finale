# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import pandas as pd

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="🎯 Definir Destino dos Jogadores", layout="wide")
st.title("🎯 Painel de Destino dos Jogadores")

# 🎯 Legenda
st.markdown("### 🟢 Disponível  |  🟡 Leilão  |  🔵 Mercado  |  🔴 Atribuído a Time")

# 🧩 Buscar times
res_times = supabase.table("times").select("id", "nome").execute()
mapa_times = {t["nome"]: t["id"] for t in res_times.data}

# 🔎 Buscar todos os jogadores
res = supabase.table("jogadores_base").select("*").execute()
jogadores = res.data

if not jogadores:
    st.info("✅ Nenhum jogador cadastrado.")
    st.stop()

# Função para cor do status
def cor_destino(destino):
    if destino == "nenhum":
        return "🟢"
    elif destino == "leilao":
        return "🟡"
    elif destino == "mercado":
        return "🔵"
    else:
        return "🔴"

# 🔁 Mostrar jogadores
for jogador in jogadores:
    with st.container():
        col1, col2, col3, col4, col5 = st.columns([1, 2.5, 2, 2, 2])

        # 📸 Imagem + status
        with col1:
            if jogador.get("imagem_url"):
                st.image(jogador["imagem_url"], width=60)
            st.markdown(cor_destino(jogador.get("destino", "nenhum")))

        # ℹ️ Info jogador
        with col2:
            st.markdown(f"**{jogador['nome']}**")
            st.caption(f"📍 {jogador['posicao']} | ⭐ Overall: {jogador['overall']}")
            valor_editado = st.number_input("💰 Valor (editável)", value=int(jogador["valor"]), step=1_000_000, key=f"val_{jogador['id']}")

        # 🛒 Mercado
        with col3:
            if st.button("🛒 Mandar p/ Mercado", key=f"mercado_{jogador['id']}"):
                ja_no_mercado = supabase.table("mercado_transferencias").select("id").eq("id_jogador_base", jogador["id"]).execute()
                if ja_no_mercado.data:
                    st.warning("⚠️ Já está no mercado.")
                else:
                    supabase.table("mercado_transferencias").insert({
                        "id_jogador_base": jogador["id"],
                        "nome": jogador["nome"],
                        "posicao": jogador["posicao"],
                        "overall": jogador["overall"],
                        "valor": valor_editado,
                        "imagem_url": jogador["imagem_url"],
                        "nacionalidade": jogador.get("nacionalidade", ""),
                        "clube_original": jogador.get("clube_original", "")
                    }).execute()
                    supabase.table("jogadores_base").update({"destino": "mercado", "valor": valor_editado}).eq("id", jogador["id"]).execute()
                    st.success("✅ Enviado ao mercado.")
                    st.experimental_rerun()

        # 📢 Leilão
        with col4:
            if st.button("📢 Mandar p/ Leilão", key=f"leilao_{jogador['id']}"):
                ja_na_fila = supabase.table("fila_leilao").select("id").eq("id_jogador_base", jogador["id"]).execute()
                if ja_na_fila.data:
                    st.warning("⚠️ Já está na fila.")
                else:
                    supabase.table("fila_leilao").insert({
                        "id_jogador_base": jogador["id"],
                        "nome": jogador["nome"],
                        "posicao": jogador["posicao"],
                        "overall": jogador["overall"],
                        "valor": valor_editado,
                        "imagem_url": jogador["imagem_url"],
                        "status": "aguardando"
                    }).execute()
                    supabase.table("jogadores_base").update({"destino": "leilao", "valor": valor_editado}).eq("id", jogador["id"]).execute()
                    st.success("✅ Enviado para o leilão.")
                    st.experimental_rerun()

        # ✅ Atribuir a time
        with col5:
            nome_time = st.selectbox("👔 Time", options=list(mapa_times.keys()), key=f"time_{jogador['id']}")
            if st.button("✅ Atribuir a Time", key=f"atribuir_{jogador['id']}"):
                id_time = mapa_times[nome_time]
                supabase.table("elenco").insert({
                    "id_time": id_time,
                    "nome": jogador["nome"],
                    "posicao": jogador["posicao"],
                    "overall": jogador["overall"],
                    "valor": valor_editado,
                    "imagem_url": jogador["imagem_url"]
                }).execute()
                supabase.table("jogadores_base").update({"destino": nome_time, "valor": valor_editado}).eq("id", jogador["id"]).execute()
                st.success(f"✅ Atribuído ao time {nome_time}")
                st.experimental_rerun()
# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime

# ⚙️ Configuração da Página (deve ser a primeira coisa do Streamlit)
st.set_page_config(page_title="🔧 Admin - Leilão e Mercado", layout="wide")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.title("🔧 Painel de Administração - Jogadores Base")

# ✅ Verifica login
if "usuario_id" not in st.session_state:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 📦 Buscar jogadores base
res = supabase.table("jogadores_base").select("*").execute()
jogadores = res.data if res.data else []

# 📦 Buscar times
res_times = supabase.table("times").select("id", "nome").execute()
times = res_times.data if res_times.data else []
mapa_times = {t['nome']: t['id'] for t in times}

# 🔍 Filtros
with st.sidebar:
    st.header("🎯 Filtros")
    filtro_nome = st.text_input("🔎 Nome do jogador")
    filtro_nacionalidade = st.text_input("🌍 Nacionalidade")
    filtro_overall = st.slider("⭐ Overall mínimo", min_value=0, max_value=99, value=0)

# Aplicar filtros
jogadores_filtrados = []
for j in jogadores:
    if filtro_nome.lower() not in j["nome"].lower():
        continue
    if filtro_nacionalidade and filtro_nacionalidade.lower() not in j.get("nacionalidade", "").lower():
        continue
    if int(j["overall"]) < filtro_overall:
        continue
    jogadores_filtrados.append(j)

# 🔃 Mostrar jogadores filtrados
if not jogadores_filtrados:
    st.info("Nenhum jogador encontrado com os filtros aplicados.")
    st.stop()

for jogador in jogadores_filtrados:
    with st.container():
        col1, col2 = st.columns([1, 5])

        # 📷 Imagem do jogador
        with col1:
            st.image(jogador.get("imagem_url", ""), width=80)

            # 🟢🔴🟡🔵 Status visual
            destino = jogador.get("destino", "disponivel")
            if destino == "leilao":
                st.markdown("🟡 **Leilão**")
            elif destino == "mercado":
                st.markdown("🔵 **Mercado**")
            elif destino in mapa_times:
                st.markdown("🔴 **Atribuído**")
            else:
                st.markdown("🟢 **Disponível**")

        with col2:
            st.markdown(f"### {jogador['nome']}")
            st.markdown(f"- 📌 Posição: `{jogador.get('posicao', 'N/A')}`")
            st.markdown(f"- 🇧🇷 Nacionalidade: `{jogador.get('nacionalidade', 'Desconhecida')}`")
            st.markdown(f"- ⭐ Overall: `{jogador.get('overall', '-')}`")

            # 🔗 Link SoFIFA
            if jogador.get("sofifa_id"):
                st.markdown(f"[📄 Ficha Técnica (SoFIFA)](https://sofifa.com/player/{jogador['sofifa_id']}/)", unsafe_allow_html=True)

            # 💰 Valor editável
            novo_valor = st.number_input(
                f"💰 Valor - {jogador['nome']}",
                value=int(jogador["valor"]),
                step=500_000,
                key=f"valor_{jogador['uuid']}"
            )

            # 👔 Atribuir a time
            col_a, col_b, col_c = st.columns([3, 3, 2])
            time_escolhido = col_a.selectbox("👔 Atribuir a um time:", list(mapa_times.keys()), key=f"time_{jogador['uuid']}")
            if col_b.button("✅ Atribuir", key=f"atr_{jogador['uuid']}"):
                id_time = mapa_times[time_escolhido]
                supabase.table("elenco").insert({
                    "id_time": id_time,
                    "nome": jogador["nome"],
                    "posicao": jogador["posicao"],
                    "overall": jogador["overall"],
                    "valor": novo_valor,
                    "imagem_url": jogador["imagem_url"]
                }).execute()
                supabase.table("jogadores_base").update({"destino": time_escolhido, "valor": novo_valor}).eq("uuid", jogador["uuid"]).execute()
                st.success(f"{jogador['nome']} atribuído ao {time_escolhido}.")
                st.experimental_rerun()

            # 🛒 Enviar para o mercado
            if col_c.button("🛒 Mercado", key=f"mercado_{jogador['uuid']}"):
                supabase.table("mercado_transferencias").insert({
                    "uuid": jogador["uuid"],
                    "nome": jogador["nome"],
                    "posicao": jogador["posicao"],
                    "overall": jogador["overall"],
                    "valor": novo_valor,
                    "imagem_url": jogador["imagem_url"]
                }).execute()
                supabase.table("jogadores_base").update({"destino": "mercado", "valor": novo_valor}).eq("uuid", jogador["uuid"]).execute()
                st.success(f"{jogador['nome']} enviado ao mercado.")
                st.experimental_rerun()

            # 📢 Enviar para o leilão
            if st.button("📢 Leilão", key=f"leilao_{jogador['uuid']}"):
                supabase.table("leiloes").insert({
                    "nome_jogador": jogador["nome"],
                    "posicao_jogador": jogador["posicao"],
                    "overall_jogador": jogador["overall"],
                    "valor_inicial": novo_valor,
                    "valor_atual": novo_valor,
                    "imagem_url": jogador.get("imagem_url", ""),
                    "link_sofifa": f"https://sofifa.com/player/{jogador.get('sofifa_id')}" if jogador.get("sofifa_id") else "",
                    "nacionalidade": jogador.get("nacionalidade", ""),
                    "origem": "Jogadores Base",
                    "incremento_minimo": 3_000_000,
                    "inicio": None,
                    "fim": None,
                    "ativo": False,
                    "finalizado": False,
                    "enviado_bid": False,
                    "aguardando_validacao": False,
                    "validado": False,
                    "tempo_minutos": 2
                }).execute()
                supabase.table("jogadores_base").update({"destino": "leilao", "valor": novo_valor}).eq("uuid", jogador["uuid"]).execute()
                st.success(f"{jogador['nome']} enviado para o leilão.")
                st.experimental_rerun()
