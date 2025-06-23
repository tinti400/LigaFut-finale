# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from utils import registrar_movimentacao

st.set_page_config(page_title="💰 Salários e Premiações", layout="wide")
st.title("💰 Painel de Salários e Premiações por Jogo")

# 🔐 Conexão Supabase
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

# 📅 Seleção de divisão e temporada
col1, col2 = st.columns(2)
divisao = col1.selectbox("Divisão", ["Divisão 1", "Divisão 2", "Divisão 3"])
temporada = col2.selectbox("Temporada", ["Temporada 1", "Temporada 2", "Temporada 3"])
numero_divisao = int(divisao.split()[-1])
numero_temporada = int(temporada.split()[-1])

# 📦 Buscar nomes e logos dos times
res_times = supabase.table("times").select("id, nome, logo").execute()
times = {t["id"]: {"nome": t["nome"], "logo": t.get("logo", "")} for t in res_times.data}

# 📄 Buscar rodadas com placares definidos
res_rodadas = (
    supabase.table("rodadas")
    .select("*")
    .eq("temporada", numero_temporada)
    .eq("divisao", numero_divisao)
    .order("numero")
    .execute()
)

rodadas = res_rodadas.data if res_rodadas.data else []

# ⚙️ Função para pagar salários e premiações
def pagar_por_jogo(id_mandante, id_visitante, gols_m, gols_v, divisao):
    if divisao == 1:
        premio_vit = 12_000_000
        premio_emp = 8_000_000
        premio_der = 5_000_000
        gol_feito = 400_000
        gol_sofrido = 80_000
    elif divisao == 2:
        premio_vit = 9_000_000
        premio_emp = 6_000_000
        premio_der = 3_000_000
        gol_feito = 300_000
        gol_sofrido = 60_000
    else:
        premio_vit = 6_000_000
        premio_emp = 4_000_000
        premio_der = 2_000_000
        gol_feito = 200_000
        gol_sofrido = 40_000

    # 💸 Salários
    for id_time in [id_mandante, id_visitante]:
        elenco = supabase.table("elenco").select("salario").eq("id_time", id_time).execute().data
        total_salario = sum(j.get("salario", 0) for j in elenco)
        saldo = supabase.table("times").select("saldo").eq("id", id_time).execute().data[0]["saldo"]
        novo_saldo = saldo - total_salario
        supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()
        registrar_movimentacao(id_time, "saida", total_salario, "Pagamento de salários (jogo)")

    # 🏆 Resultado
    if gols_m > gols_v:
        premios = [(id_mandante, premio_vit), (id_visitante, premio_der)]
    elif gols_v > gols_m:
        premios = [(id_visitante, premio_vit), (id_mandante, premio_der)]
    else:
        premios = [(id_mandante, premio_emp), (id_visitante, premio_emp)]

    for id_time, valor in premios:
        saldo = supabase.table("times").select("saldo").eq("id", id_time).execute().data[0]["saldo"]
        novo_saldo = saldo + valor
        supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()
        registrar_movimentacao(id_time, "entrada", valor, "Premiação por resultado (jogo)")

    # ⚽ Gols
    bonus = [
        (id_mandante, gols_m * gol_feito - gols_v * gol_sofrido),
        (id_visitante, gols_v * gol_feito - gols_m * gol_sofrido)
    ]
    for id_time, valor in bonus:
        saldo = supabase.table("times").select("saldo").eq("id", id_time).execute().data[0]["saldo"]
        novo_saldo = saldo + valor
        supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()
        registrar_movimentacao(id_time, "entrada" if valor >= 0 else "saida", abs(valor), "Premiação por gols (jogo)")

# 📋 Mostrar jogos com placar definido
st.markdown("---")
pagamentos_exibidos = 0

for rodada in rodadas:
    numero = rodada["numero"]
    for idx, jogo in enumerate(rodada["jogos"]):
        gm = jogo.get("gols_mandante")
        gv = jogo.get("gols_visitante")
        id_m = jogo["mandante"]
        id_v = jogo["visitante"]

        if gm is None or gv is None or "FOLGA" in [id_m, id_v]:
            continue

        nome_m = times.get(id_m, {}).get("nome", "❓")
        nome_v = times.get(id_v, {}).get("nome", "❓")
        logo_m = times.get(id_m, {}).get("logo", "")
        logo_v = times.get(id_v, {}).get("logo", "")

        st.markdown(f"### 🏟️ Rodada {numero} — {nome_m} {gm} x {gv} {nome_v}")
        cols = st.columns([1, 1, 1])
        with cols[0]:
            if logo_m:
                st.image(logo_m, width=50)
            st.caption(nome_m)
        with cols[1]:
            st.markdown("<h4 style='text-align:center;'>⚔️</h4>", unsafe_allow_html=True)
        with cols[2]:
            if logo_v:
                st.image(logo_v, width=50)
            st.caption(nome_v)

        if st.button("💰 Pagar Premiação + Salários", key=f"pagar_{numero}_{idx}"):
            pagar_por_jogo(id_m, id_v, gm, gv, numero_divisao)
            st.success("✅ Pagamento realizado com sucesso.")
            st.experimental_rerun()

        st.markdown("---")
        pagamentos_exibidos += 1

if pagamentos_exibidos == 0:
    st.info("Nenhum jogo com placar definido encontrado.")
