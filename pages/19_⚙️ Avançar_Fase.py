# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import random

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="⚙️ Avançar Fase da Copa", layout="centered")
st.title("⚙️ Avançar Fase da Copa da LigaFut")

# ✅ Verifica se está logado
if "usuario" not in st.session_state:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# 🔒 Verifica se é admin
usuario = st.session_state["usuario"]
res_admin = supabase.table("usuarios").select("administrador").eq("usuario", usuario).execute()
if not res_admin.data or not res_admin.data[0].get("administrador", False):
    st.error("Acesso restrito a administradores.")
    st.stop()

# 🔄 Função para buscar dados da fase
def buscar_fase(fase):
    res = supabase.table("copa_ligafut").select("*").eq("fase", fase).order("data_criacao", desc=True).limit(1).execute()
    return res.data[0] if res.data else None

# 📦 Fases disponíveis para avanço
fases_disponiveis = {
    "oitavas": "quartas",
    "quartas": "semifinal",
    "semifinal": "final"
}

# 🔁 Processar cada fase
for fase_atual, proxima_fase in fases_disponiveis.items():
    dados_fase = buscar_fase(fase_atual)

    if dados_fase:
        st.subheader(f"🎯 Avançar de **{fase_atual.capitalize()}** para **{proxima_fase.capitalize()}**")
        if st.button(f"🔄 Avançar para {proxima_fase.capitalize()}"):
            jogos = dados_fase["jogos"]
            vencedores = []

            for i in range(0, len(jogos), 2 if proxima_fase != "final" else 1):
                if proxima_fase != "final":
                    jogo_ida = jogos[i]
                    jogo_volta = jogos[i + 1]

                    if None in [jogo_ida["gols_mandante"], jogo_ida["gols_visitante"],
                                jogo_volta["gols_mandante"], jogo_volta["gols_visitante"]]:
                        st.error("❌ Preencha todos os resultados antes de avançar.")
                        st.stop()

                    ida_m = jogo_ida["gols_mandante"]
                    ida_v = jogo_ida["gols_visitante"]
                    volta_m = jogo_volta["gols_mandante"]
                    volta_v = jogo_volta["gols_visitante"]

                    time_a = jogo_ida["mandante"]
                    time_b = jogo_ida["visitante"]

                    total_a = ida_m + volta_v
                    total_b = ida_v + volta_m

                    if total_a > total_b:
                        vencedores.append(time_a)
                    elif total_b > total_a:
                        vencedores.append(time_b)
                    else:
                        vencedor = random.choice([time_a, time_b])
                        vencedores.append(vencedor)
                else:
                    jogo_final = jogos[i]
                    if None in [jogo_final["gols_mandante"], jogo_final["gols_visitante"]]:
                        st.error("❌ Preencha o placar da final antes de encerrar o campeonato.")
                        st.stop()
                    vencedor = jogo_final["mandante"] if jogo_final["gols_mandante"] > jogo_final["gols_visitante"] else jogo_final["visitante"]
                    vencedores.append(vencedor)

            # Criar confrontos da próxima fase
            if proxima_fase != "final":
                if len(vencedores) % 2 != 0:
                    st.error("❌ Número de vencedores inválido.")
                    st.stop()

                random.shuffle(vencedores)
                novos_jogos = []
                for i in range(0, len(vencedores), 2):
                    ida = {
                        "mandante": vencedores[i],
                        "visitante": vencedores[i + 1],
                        "gols_mandante": None,
                        "gols_visitante": None
                    }
                    volta = {
                        "mandante": vencedores[i + 1],
                        "visitante": vencedores[i],
                        "gols_mandante": None,
                        "gols_visitante": None
                    }
                    novos_jogos.extend([ida, volta])
            else:
                novos_jogos = [{
                    "mandante": vencedores[0],
                    "visitante": vencedores[1],
                    "gols_mandante": None,
                    "gols_visitante": None
                }]

            nova_data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            supabase.table("copa_ligafut").insert({
                "fase": proxima_fase,
                "data_criacao": nova_data,
                "jogos": novos_jogos
            }).execute()

            st.success(f"✅ Fase '{proxima_fase}' criada com sucesso!")
            st.experimental_rerun()
