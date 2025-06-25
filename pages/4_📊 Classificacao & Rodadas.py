# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
from utils import registrar_movimentacao

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="Classificação", page_icon="📊", layout="centered")
st.markdown("## 🏆 Tabela de Classificação")
st.markdown(f"🗓️ Atualizada em: `{datetime.now().strftime('%d/%m/%Y %H:%M')}`")

# 🔒 Verifica login
if "usuario" not in st.session_state:
    st.warning("Você precisa estar logado.")
    st.stop()

# 👤 Verifica admin
email_usuario = st.session_state.get("usuario", "")
res_admin = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = res_admin.data and res_admin.data[0].get("administrador", False)

# 🔹 Seleção da divisão e temporada
col1, col2 = st.columns(2)
divisao = col1.selectbox("Selecione a divisão", ["Divisão 1", "Divisão 2", "Divisão 3"])
temporada = col2.selectbox("Selecione a temporada", ["Temporada 1", "Temporada 2", "Temporada 3"])
numero_divisao = int(divisao.split()[-1])
numero_temporada = int(temporada.split()[-1])

# 🧠 Função de renda variável por jogo

def calcular_renda_jogo(estadio, fase=None, decisivo=False):
    preco = float(estadio.get("preco_ingresso", 20.0))
    nivel = estadio.get("nivel", 1)
    capacidade = estadio.get("capacidade", 10000)
    demanda_base = capacidade * (0.9 + nivel * 0.02)
    fator_preco = max(0.3, 1 - (preco - 20) * 0.03)
    bonus = 1.0
    if fase == "boa":
        bonus += 0.10
    elif fase == "ruim":
        bonus -= 0.10
    if decisivo:
        bonus += 0.20
    publico = int(min(capacidade, demanda_base * fator_preco * bonus))
    renda = publico * preco
    return renda, publico

# 🔄 Buscar rodadas
@st.cache(ttl=60)
def buscar_resultados(temporada, divisao):
    try:
        res = supabase.table("rodadas") \
            .select("*") \
            .eq("temporada", temporada) \
            .eq("divisao", divisao) \
            .order("numero") \
            .execute()
        return res.data
    except Exception as e:
        return []

# 👥 Buscar nomes e logos dos times
@st.cache(ttl=60)
def obter_nomes_times(divisao):
    try:
        usuarios = supabase.table("usuarios").select("time_id").eq("Divisão", f"Divisão {divisao}").execute().data
        time_ids = list({u["time_id"] for u in usuarios if u.get("time_id")})
        if not time_ids:
            return {}
        res = supabase.table("times").select("id", "nome", "logo", "tecnico").in_("id", time_ids).execute()
        return {
            t["id"]: {
                "nome": t["nome"],
                "logo": t.get("logo", ""),
                "tecnico": t.get("tecnico", "")
            } for t in res.data
        }
    except:
        return {}

# 📊 Calcular fase dos times com base nos últimos 3 jogos

def avaliar_fase_dos_times(rodadas, rodada_atual):
    fases = {}
    for rodada in rodadas:
        if rodada["numero"] >= rodada_atual:
            continue
        for jogo in rodada.get("jogos", []):
            m, v = jogo.get("mandante"), jogo.get("visitante")
            gm, gv = jogo.get("gols_mandante"), jogo.get("gols_visitante")
            if None in [m, v, gm, gv]:
                continue
            try:
                gm, gv = int(gm), int(gv)
            except:
                continue
            for time_id, resultado in [(m, gm - gv), (v, gv - gm)]:
                if time_id not in fases:
                    fases[time_id] = []
                if resultado > 0:
                    fases[time_id].append("v")
                elif resultado < 0:
                    fases[time_id].append("d")
                else:
                    fases[time_id].append("e")
    fases_finais = {}
    for tid, ultimos in fases.items():
        ultimos = ultimos[-3:]
        v = ultimos.count("v")
        d = ultimos.count("d")
        if v >= 2:
            fases_finais[tid] = "boa"
        elif d >= 2:
            fases_finais[tid] = "ruim"
        else:
            fases_finais[tid] = None
    return fases_finais

# 🔄 Dados e rodadas
rodadas = buscar_resultados(numero_temporada, numero_divisao)
times_map = obter_nomes_times(numero_divisao)
rodadas_disponiveis = sorted(set(r["numero"] for r in rodadas))
rodada_selecionada = st.selectbox("Escolha a rodada que deseja visualizar", rodadas_disponiveis)
fases_times = avaliar_fase_dos_times(rodadas, rodada_selecionada)

# 📅 Mostrar jogos da rodada com renda
for rodada in rodadas:
    if rodada["numero"] != rodada_selecionada:
        continue

    st.markdown(f"<h4 style='margin-top: 30px;'>🔢 Rodada {rodada_selecionada}</h4>", unsafe_allow_html=True)
    for jogo in rodada.get("jogos", []):
        m_id, v_id = jogo.get("mandante"), jogo.get("visitante")
        gm, gv = jogo.get("gols_mandante", ""), jogo.get("gols_visitante", "")
        m = times_map.get(m_id, {}); v = times_map.get(v_id, {})

        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 2])
        with col1:
            st.markdown(f"<div style='text-align: right;'><img src='{m.get('logo', '')}' width='30'> <b>{m.get('nome', 'Desconhecido')}</b></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<h5 style='text-align: center;'>{gm}</h5>", unsafe_allow_html=True)
        with col3:
            st.markdown("<h5 style='text-align: center;'>x</h5>", unsafe_allow_html=True)
        with col4:
            st.markdown(f"<h5 style='text-align: center;'>{gv}</h5>", unsafe_allow_html=True)
        with col5:
            st.markdown(f"<div style='text-align: left;'><img src='{v.get('logo', '')}' width='30'> <b>{v.get('nome', 'Desconhecido')}</b></div>", unsafe_allow_html=True)

        # 💰 Renda do mandante
        if gm != "" and gv != "":
            try:
                descricao = f"Renda da partida rodada {rodada_selecionada}"
                check = supabase.table("movimentacoes_financeiras").select("id").eq("id_time", m_id).eq("descricao", descricao).execute()
                if not check.data:
                    estadio = supabase.table("estadios").select("*").eq("id_time", m_id).execute().data[0]
                    fase = fases_times.get(m_id)
                    decisivo = rodada_selecionada == max(rodadas_disponiveis)
                    renda, publico = calcular_renda_jogo(estadio, fase=fase, decisivo=decisivo)
                    saldo = supabase.table("times").select("saldo").eq("id", m_id).execute().data[0]["saldo"]
                    supabase.table("times").update({"saldo": saldo + renda}).eq("id", m_id).execute()
                    registrar_movimentacao(m_id, "entrada", renda, f"{descricao} (público: {publico:,})")
                    st.success(f"💰 Renda registrada: R${renda:,.2f} para {m.get('nome')}")
            except Exception as e:
                st.warning(f"Erro ao calcular renda do jogo: {e}")
