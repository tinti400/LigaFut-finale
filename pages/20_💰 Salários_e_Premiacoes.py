# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
from utils import registrar_movimentacao

st.set_page_config(page_title="💰 Salários e Premiações", layout="wide")
st.title("💰 Pagamento de Salários e Premiações")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login e admin
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado.")
    st.stop()

email_usuario = st.session_state.get("usuario", "")
res_admin = supabase.table("admins").select("email").eq("email", email_usuario).execute()
if not res_admin.data:
    st.error("Acesso restrito apenas para administradores.")
    st.stop()

# 🔽 Seleção de divisão e temporada
col1, col2 = st.columns(2)
divisao = col1.selectbox("Divisão", ["Divisão 1", "Divisão 2", "Divisão 3"])
temporada = col2.selectbox("Temporada", ["Temporada 1", "Temporada 2", "Temporada 3"])
numero_divisao = int(divisao.split()[-1])
numero_temporada = int(temporada.split()[-1])

# 🏷️ Parâmetros de premiação e salário por divisão
parametros = {
    1: {"vitoria": 12_000_000, "empate": 8_000_000, "derrota": 5_000_000, "gol_feito": 400_000, "gol_sofrido": -80_000},
    2: {"vitoria": 8_000_000, "empate": 5_000_000, "derrota": 3_000_000, "gol_feito": 300_000, "gol_sofrido": -60_000},
    3: {"vitoria": 5_000_000, "empate": 3_000_000, "derrota": 1_500_000, "gol_feito": 200_000, "gol_sofrido": -40_000}
}

# 🔄 Buscar todos os times
res_times = supabase.table("times").select("id", "nome", "logo", "saldo").execute()
times_info = {t["id"]: {"nome": t["nome"], "logo": t.get("logo", ""), "saldo": t["saldo"]} for t in res_times.data}

# 💰 Função para calcular salário total
def salario_total(id_time):
    try:
        res = supabase.table("elenco").select("salario").eq("id_time", id_time).execute()
        elenco = res.data or []
        return sum(j.get("salario", 0) for j in elenco if isinstance(j, dict))
    except Exception as e:
        st.error(f"Erro ao buscar salários do time {id_time}: {e}")
        return 0

# ✅ Função para pagar premiação e salário
def pagar_por_jogo(id_m, id_v, gm, gv, numero_divisao):
    if not all(isinstance(x, (int, float)) for x in [gm, gv]):
        return

    config = parametros[numero_divisao]

    # Time Mandante
    pontos_m = 3 if gm > gv else 1 if gm == gv else 0
    valor_premio_m = (
        config["vitoria"] if pontos_m == 3 else
        config["empate"] if pontos_m == 1 else
        config["derrota"]
    ) + (gm * config["gol_feito"]) + (gv * config["gol_sofrido"])
    sal_m = salario_total(id_m)
    valor_total_m = valor_premio_m + sal_m
    registrar_movimentacao(id_m, "saida", valor_total_m, f"Pagamento Jogo (Salário + Premiação)")

    # Time Visitante
    pontos_v = 3 if gv > gm else 1 if gv == gm else 0
    valor_premio_v = (
        config["vitoria"] if pontos_v == 3 else
        config["empate"] if pontos_v == 1 else
        config["derrota"]
    ) + (gv * config["gol_feito"]) + (gm * config["gol_sofrido"])
    sal_v = salario_total(id_v)
    valor_total_v = valor_premio_v + sal_v
    registrar_movimentacao(id_v, "saida", valor_total_v, f"Pagamento Jogo (Salário + Premiação)")

    st.success("💸 Pagamento realizado para ambos os times.")

# 📊 Rodadas com placar definido
res_rodadas = (
    supabase.table("rodadas")
    .select("*")
    .eq("temporada", numero_temporada)
    .eq("divisao", numero_divisao)
    .order("numero")
    .execute()
)

rodadas_data = res_rodadas.data or []
pagos = []

for rodada in rodadas_data:
    for jogo in rodada["jogos"]:
        id_m, id_v = jogo["mandante"], jogo["visitante"]
        gm, gv = jogo.get("gols_mandante"), jogo.get("gols_visitante")

        if not all(isinstance(x, (int, float)) for x in [gm, gv]):
            continue  # pula jogos sem placar

        nome_m = times_info.get(id_m, {}).get("nome", "Mandante")
        nome_v = times_info.get(id_v, {}).get("nome", "Visitante")
        logo_m = times_info.get(id_m, {}).get("logo", "")
        logo_v = times_info.get(id_v, {}).get("logo", "")

        st.markdown("---")
        st.markdown(f"### Rodada {rodada['numero']}")
        col1, col2, col3, col4, col5 = st.columns([1.5, 1, 1, 1, 1.5])

        with col1:
            st.image(logo_m or "https://cdn-icons-png.flaticon.com/512/147/147144.png", width=50)
            st.markdown(f"**{nome_m}**")

        with col2:
            st.markdown(f"<h3 style='text-align:center'>{gm}</h3>", unsafe_allow_html=True)

        with col3:
            st.markdown("<h3 style='text-align:center'>⚽</h3>", unsafe_allow_html=True)

        with col4:
            st.markdown(f"<h3 style='text-align:center'>{gv}</h3>", unsafe_allow_html=True)

        with col5:
            st.image(logo_v or "https://cdn-icons-png.flaticon.com/512/147/147144.png", width=50)
            st.markdown(f"**{nome_v}**")

        if st.button("💸 Pagar Jogo", key=f"pagar_{rodada['id']}_{id_m}_{id_v}"):
            pagar_por_jogo(id_m, id_v, gm, gv, numero_divisao)
            st.experimental_rerun()

