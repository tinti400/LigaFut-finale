# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import random

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="Gerenciar Rodadas", page_icon="🏕️", layout="centered")
st.title("🏕️ Gerenciar Rodadas da Divisão")

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 👑 Verifica se é admin pela tabela "admins"
email_usuario = st.session_state.get("usuario", "")
try:
    admin_ref = supabase.table("admins").select("email").eq("email", email_usuario).execute()
    eh_admin = len(admin_ref.data) > 0
    if not eh_admin:
        st.error("🔒 Acesso restrito: somente administradores podem acessar esta página.")
        st.stop()
except Exception as e:
    st.error(f"Erro ao verificar administrador: {e}")
    st.stop()

# 🔹 Filtro de divisão
divisao = st.selectbox("Selecione a Divisão", ["Divisão 1", "Divisão 2"])
numero_divisao = divisao.split()[-1]
nome_tabela_rodadas = f"rodadas_divisao_{numero_divisao}"

# 🗓️ Obter times da divisão
def obter_times(divisao):
    res_times = supabase.table("usuarios").select("time_id").eq("Divisão", divisao).execute()
    return [u["time_id"] for u in res_times.data if u.get("time_id")]

# 📖 Obter nomes dos times
def obter_nomes_times():
    res_nomes = supabase.table("times").select("id", "nome").execute()
    return {t["id"]: t["nome"] for t in res_nomes.data}

# ⚽ Gerar confrontos estilo Brasileirão com FOLGA
def gerar_rodadas_brasileirao(times):
    random.shuffle(times)
    if len(times) % 2 != 0:
        times.append("FOLGA_PLACEHOLDER")

    n = len(times)
    metade = n // 2
    rodadas = []

    for turno in [0, 1]:  # 0 = ida, 1 = volta
        lista = times[:]
        for i in range(n - 1):
            rodada = []
            for j in range(metade):
                t1 = lista[j]
                t2 = lista[n - 1 - j]

                if "FOLGA_PLACEHOLDER" in [t1, t2]:
                    time_folgando = t2 if t1 == "FOLGA_PLACEHOLDER" else t1
                    rodada.append({
                        "mandante": time_folgando,
                        "visitante": "FOLGA",
                        "gols_mandante": None,
                        "gols_visitante": None
                    })
                else:
                    rodada.append({
                        "mandante": t1 if turno == 0 else t2,
                        "visitante": t2 if turno == 0 else t1,
                        "gols_mandante": None,
                        "gols_visitante": None
                    })
            rodadas.append(rodada)
            lista = [lista[0]] + [lista[-1]] + lista[1:-1]
    return rodadas

# 🔍 Buscar rodadas existentes
def buscar_rodadas():
    return supabase.table(nome_tabela_rodadas).select("*").order("numero").execute().data

# ⚙️ Botão para gerar rodadas
if st.button("⚙️ Gerar Rodadas da " + divisao):
    time_ids = obter_times(divisao)
    if len(time_ids) < 2:
        st.warning("🚨 Mínimo de 2 times para gerar confrontos.")
        st.stop()

    supabase.table(nome_tabela_rodadas).delete().neq("numero", -1).execute()
    rodadas = gerar_rodadas_brasileirao(time_ids)
    for i, jogos in enumerate(rodadas, 1):
        supabase.table(nome_tabela_rodadas).insert({"numero": i, "jogos": jogos}).execute()
    st.success(f"✅ {len(rodadas)} rodadas geradas com sucesso para {divisao}!")
    st.rerun()

# 🔍 Editor de resultados por rodada
rodadas_existentes = buscar_rodadas()
times_map = obter_nomes_times()

if rodadas_existentes:
    st.subheader("🗓️ Editar Resultados")
    lista_numeros = [r["numero"] for r in rodadas_existentes]
    rodada_escolhida = st.selectbox("Selecione a rodada para editar", lista_numeros)
    rodada = next(r for r in rodadas_existentes if r["numero"] == rodada_escolhida)

    for jogo in rodada["jogos"]:
        mandante = jogo["mandante"]
        visitante = jogo["visitante"]
        gols_mandante = jogo.get("gols_mandante") or 0
        gols_visitante = jogo.get("gols_visitante") or 0

        nome_m = times_map.get(mandante, "FOLGA" if mandante == "FOLGA" else "?")
        nome_v = times_map.get(visitante, "FOLGA" if visitante == "FOLGA" else "?")

        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 2])
        with col1:
            st.markdown(f"**{nome_m}**")
        with col3:
            st.markdown("**x**")
        with col5:
            st.markdown(f"**{nome_v}**")

        if "FOLGA" in [mandante, visitante]:
            st.markdown("🚫 Este time folgou nesta rodada.")
            continue

        with col2:
            gm = st.number_input(" ", min_value=0, value=gols_mandante, key=f"gm_{rodada_escolhida}_{mandante}")
        with col4:
            gv = st.number_input("  ", min_value=0, value=gols_visitante, key=f"gv_{rodada_escolhida}_{visitante}")

        if st.button("📂 Salvar", key=f"salvar_{rodada_escolhida}_{mandante}_{visitante}"):
            novos_jogos = []
            for j in rodada["jogos"]:
                if j["mandante"] == mandante and j["visitante"] == visitante:
                    j["gols_mandante"] = gm
                    j["gols_visitante"] = gv
                novos_jogos.append(j)

            supabase.table(nome_tabela_rodadas).update({"jogos": novos_jogos}).eq("numero", rodada_escolhida).execute()
            st.success(f"✅ Resultado salvo: {nome_m} {gm} x {gv} {nome_v}")
            st.rerun()
