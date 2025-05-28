# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import random

# Configuração da página
st.set_page_config(page_title="Copa LigaFut - Mata-Mata", layout="wide")

# Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# Verifica login
if "usuario_id" not in st.session_state or not st.session_state.usuario_id:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

st.markdown("""
    <h1 style='text-align: center;'>🏆 Copa LigaFut - Mata-mata</h1><hr>
""", unsafe_allow_html=True)

# Função para buscar times
@st.cache_data
def buscar_times():
    response = supabase.table("times").select("id, nome").execute()
    if response.data:
        return [t for t in response.data if t['id']]
    return []

# Função para gerar confrontos aleatórios
def gerar_confrontos(times_ids):
    random.shuffle(times_ids)
    jogos = []
    for i in range(0, len(times_ids), 2):
        jogos.append({
            "mandante": times_ids[i],
            "visitante": times_ids[i + 1],
            "gols_mandante": None,
            "gols_visitante": None
        })
    return jogos

# Função para salvar copa
def salvar_copa(jogos):
    try:
        dados = {
            "nome": "Copa LigaFut",
            "fase": "oitavas",
            "data_criacao": datetime.now().isoformat(),
            "jogos": jogos
        }
        supabase.table("copa_ligafut").insert(dados).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar a copa: {e}")
        return False

# FUNÇÃO para atualizar resultado
def atualizar_resultado(index, gols_mandante, gols_visitante):
    try:
        res = supabase.table("copa_ligafut").select("id, jogos").order("data_criacao", desc=True).limit(1).execute()
        if not res.data:
            st.error("Nenhuma copa encontrada.")
            return

        copa_id = res.data[0]["id"]
        jogos = res.data[0]["jogos"]
        jogos[index]["gols_mandante"] = gols_mandante
        jogos[index]["gols_visitante"] = gols_visitante

        supabase.table("copa_ligafut").update({"jogos": jogos}).eq("id", copa_id).execute()
        st.success("Resultado atualizado!")
    except Exception as e:
        st.error(f"Erro ao atualizar resultado: {e}")

# FUNÇÃO para exibir jogos
@st.cache_data
def mapear_times():
    times = buscar_times()
    return {t["id"]: t["nome"] for t in times}

# Formulário de seleção manual
with st.expander("⚙️ Selecionar manualmente os times para a Copa"):
    todos_times = buscar_times()
    opcoes = {f"{t['nome']} — ID: {t['id']}": t['id'] for t in todos_times}
    selecionados = st.multiselect("Selecione os times (quantidade par):", list(opcoes.keys()))

    if len(selecionados) % 2 != 0:
        st.warning("Selecione uma quantidade **par** de times.")
    elif st.button("🚀 Gerar Copa com Times Selecionados"):
        times_ids = [opcoes[t] for t in selecionados]
        jogos_gerados = gerar_confrontos(times_ids)
        sucesso = salvar_copa(jogos_gerados)
        if sucesso:
            st.success("✅ Copa criada com sucesso!")
            st.json(jogos_gerados)

# Mostrar última copa criada e editar resultados
res = supabase.table("copa_ligafut").select("*").order("data_criacao", desc=True).limit(1).execute()
if res.data:
    st.subheader("📊 Última Copa Criada")
    dados = res.data[0]
    jogos = dados["jogos"]
    mapa = mapear_times()

    for i, jogo in enumerate(jogos):
        col1, col2, col3 = st.columns([4, 4, 3])
        with col1:
            st.write(f"🔷 {mapa.get(jogo['mandante'], 'Desconhecido')}")
        with col2:
            st.write(f"🔶 {mapa.get(jogo['visitante'], 'Desconhecido')}")
        with col3:
            gm = st.number_input(f"Gols mandante [{i+1}]", min_value=0, key=f"gm_{i}", value=jogo['gols_mandante'] or 0)
            gv = st.number_input(f"Gols visitante [{i+1}]", min_value=0, key=f"gv_{i}", value=jogo['gols_visitante'] or 0)
            if st.button("💾 Salvar Resultado", key=f"save_{i}"):
                atualizar_resultado(i, gm, gv)
else:
    st.info("Nenhuma copa foi criada ainda.")




