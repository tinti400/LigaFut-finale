# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import itertools

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="Gerar Rodadas", page_icon="⚙️", layout="centered")
st.title("⚙️ Gerar Rodadas da Temporada")

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 👑 Verifica se é admin
email_usuario = st.session_state.get("usuario", "")
try:
    admin_ref = supabase.table("admins").select("email").eq("email", email_usuario).execute()
    eh_admin = len(admin_ref.data) > 0
    if not eh_admin:
        st.warning("🔒 Acesso permitido apenas para administradores.")
        st.stop()
except Exception as e:
    st.error(f"Erro ao verificar administrador: {e}")
    st.stop()

# 🔽 Seleção da divisão e temporada
col1, col2 = st.columns(2)
opcao_divisao = col1.selectbox("Selecione a Divisão", ["Divisão 1", "Divisão 2", "Divisão 3"])
opcao_temporada = col2.selectbox("Selecione a Temporada", ["Temporada 1", "Temporada 2", "Temporada 3"])

numero_divisao = int(opcao_divisao.split()[-1])
numero_temporada = int(opcao_temporada.split()[-1])

# 📅 Buscar times pela divisão
try:
    usuarios = supabase.table("usuarios").select("time_id").eq("Divisão", opcao_divisao).execute().data
    time_ids = list({u["time_id"] for u in usuarios if u.get("time_id")})
except Exception as e:
    st.error(f"Erro ao buscar times: {e}")
    st.stop()

# ✅ Botão de gerar rodadas
if st.button(f"⚙️ Gerar Rodadas da {opcao_divisao} - {opcao_temporada}"):
    if len(time_ids) < 2:
        st.warning("🚨 É necessário no mínimo 2 times para gerar rodadas.")
        st.stop()

    # 🔄 Apagar rodadas anteriores da temporada e divisão
    try:
        supabase.table("rodadas")\
            .delete()\
            .eq("temporada", numero_temporada)\
            .eq("divisao", numero_divisao)\
            .execute()
    except Exception as e:
        st.error(f"Erro ao apagar rodadas antigas: {e}")
        st.stop()

    # ✅ Algoritmo Round-Robin (Turno e Returno)
    def gerar_rodadas_round_robin(time_ids):
        if len(time_ids) % 2 != 0:
            time_ids.append("folga")

        n = len(time_ids)
        metade = n // 2
        rodadas_turno = []
        lista = time_ids[:]

        for rodada in range(n - 1):
            jogos = []
            for i in range(metade):
                time_a = lista[i]
                time_b = lista[-(i + 1)]
                if "folga" not in (time_a, time_b):
                    jogos.append({
                        "mandante": time_a,
                        "visitante": time_b,
                        "gols_mandante": None,
                        "gols_visitante": None
                    })
            rodadas_turno.append(jogos)
            lista = [lista[0]] + [lista[-1]] + lista[1:-1]

        rodadas_returno = []
        for jogos in rodadas_turno:
            jogos_volta = []
            for jogo in jogos:
                jogos_volta.append({
                    "mandante": jogo["visitante"],
                    "visitante": jogo["mandante"],
                    "gols_mandante": None,
                    "gols_visitante": None
                })
            rodadas_returno.append(jogos_volta)

        return rodadas_turno + rodadas_returno

    # ⚽ Gera as rodadas completas
    rodadas = gerar_rodadas_round_robin(time_ids)

    # 💾 Salvar rodadas no Supabase
    try:
        for i, jogos in enumerate(rodadas, 1):
            supabase.table("rodadas").insert({
                "temporada": numero_temporada,
                "divisao": numero_divisao,
                "numero": i,
                "jogos": jogos
            }).execute()
        st.success(f"✅ {len(rodadas)} rodadas geradas com sucesso para {opcao_divisao} - {opcao_temporada}!")
    except Exception as e:
        st.error(f"Erro ao salvar rodadas: {e}")

    # 🧹 Limpa punições (exceto temporada 1)
    if numero_temporada != 1:
        try:
            for time_id in time_ids:
                supabase.table("times").update({
                    "restricoes": [],
                    "pontuacao_negativa": 0
                }).eq("id", time_id).execute()
            st.info("🧹 Restrições e punições zeradas para a nova temporada!")
        except Exception as e:
            st.error(f"Erro ao limpar punições: {e}")


