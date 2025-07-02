# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
from utils import registrar_movimentacao

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="Classificação", page_icon="📊", layout="centered")
st.markdown("## 🏆 Tabela de Classificação")
st.markdown(f"🗓️ Atualizada em: `{datetime.now().strftime('%d/%m/%Y %H:%M')}`")

if "usuario" not in st.session_state:
    st.warning("Você precisa estar logado.")
    st.stop()

email_usuario = st.session_state.get("usuario", "")
res_admin = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = res_admin.data and res_admin.data[0].get("administrador", False)

col1, col2 = st.columns(2)
divisao = col1.selectbox("Selecione a divisão", ["Divisão 1", "Divisão 2", "Divisão 3"])
temporada = col2.selectbox("Selecione a temporada", ["Temporada 1", "Temporada 2", "Temporada 3"])
numero_divisao = int(divisao.split()[-1])
numero_temporada = int(temporada.split()[-1])

def calcular_renda_jogo(estadio):
    try:
        preco = float(estadio.get("preco_ingresso") or 20.0)
        nivel = int(estadio.get("nivel") or 1)
        capacidade = int(estadio.get("capacidade") or 10000)
    except:
        preco = 20.0
        nivel = 1
        capacidade = 10000
    demanda_base = capacidade * (0.9 + nivel * 0.02)
    fator_preco = max(0.3, 1 - (preco - 20) * 0.03)
    publico = int(min(capacidade, demanda_base * fator_preco))
    renda = publico * preco
    return renda, publico

@st.cache(ttl=60)
def buscar_resultados(temporada, divisao):
    try:
        res = supabase.table("rodadas").select("*").eq("temporada", temporada).eq("divisao", divisao).order("numero").execute()
        return res.data
    except:
        return []

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

def calcular_classificacao(rodadas, times_map):
    tabela = {}
    for rodada in rodadas:
        for jogo in rodada.get("jogos", []):
            m, v = jogo.get("mandante"), jogo.get("visitante")
            gm, gv = jogo.get("gols_mandante"), jogo.get("gols_visitante")
            if None in [m, v, gm, gv]: continue
            try: gm, gv = int(gm), int(gv)
            except: continue
            for t in (m, v):
                if t not in tabela:
                    tabela[t] = {
                        "nome": times_map.get(t, {}).get("nome", "Desconhecido"),
                        "logo": times_map.get(t, {}).get("logo", ""),
                        "tecnico": times_map.get(t, {}).get("tecnico", ""),
                        "pontos": 0, "v": 0, "e": 0, "d": 0, "gp": 0, "gc": 0, "sg": 0
                    }
            tabela[m]["gp"] += gm; tabela[m]["gc"] += gv; tabela[m]["sg"] += gm - gv
            tabela[v]["gp"] += gv; tabela[v]["gc"] += gm; tabela[v]["sg"] += gv - gm
            if gm > gv:
                tabela[m]["pontos"] += 3; tabela[m]["v"] += 1; tabela[v]["d"] += 1
            elif gv > gm:
                tabela[v]["pontos"] += 3; tabela[v]["v"] += 1; tabela[m]["d"] += 1
            else:
                tabela[m]["pontos"] += 1; tabela[v]["pontos"] += 1
                tabela[m]["e"] += 1; tabela[v]["e"] += 1

    return sorted(tabela.items(), key=lambda x: (x[1]["pontos"], x[1]["sg"], x[1]["gp"]), reverse=True)

# Execução
times_map = obter_nomes_times(numero_divisao)
rodadas = buscar_resultados(numero_temporada, numero_divisao)
classificacao = calcular_classificacao(rodadas, times_map)

if classificacao:
    df = pd.DataFrame([{
        "Posição": i + 1,
        "Time": f"<img src='{t['logo']}' width='25'> <b>{t['nome']}</b><br><small>{t['tecnico']}</small>",
        "Pontos": t["pontos"],
        "Jogos": t["v"] + t["e"] + t["d"],
        "Vitórias": t["v"],
        "Empates": t["e"],
        "Derrotas": t["d"],
        "Gols Pró": t["gp"],
        "Gols Contra": t["gc"],
        "Saldo de Gols": t["sg"]
    } for i, (tid, t) in enumerate(classificacao)])
    st.markdown("""<style>thead tr th {text-align: center;} td {text-align: center;}</style>""", unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True, hide_index=True)

# Rodadas
st.markdown("---")
st.subheader("🔕 Rodadas da Temporada")
rodadas_disponiveis = sorted(set(r["numero"] for r in rodadas))
rodada_selecionada = st.selectbox("Escolha a rodada", rodadas_disponiveis)

for rodada in rodadas:
    if rodada["numero"] != rodada_selecionada:
        continue
    st.markdown(f"### 📈 Rodada {rodada_selecionada}")
    for jogo in rodada.get("jogos", []):
        m_id, v_id = jogo.get("mandante"), jogo.get("visitante")
        gm, gv = jogo.get("gols_mandante", ""), jogo.get("gols_visitante", "")
        m = times_map.get(m_id, {}); v = times_map.get(v_id, {})
        m_nome = m.get("nome", "Desconhecido"); v_nome = v.get("nome", "Desconhecido")

        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 3])
        col1.markdown(f"**{m_nome}**")
        col2.markdown(f"**{gm}**")
        col3.markdown("x")
        col4.markdown(f"**{gv}**")
        col5.markdown(f"**{v_nome}**")

        if gm != "" and gv != "":
            if st.button("💸 Pagar Renda", key=f"renda_{m_id}_{v_id}_{rodada_selecionada}"):
                try:
                    estadio = supabase.table("estadios").select("*").eq("id_time", m_id).execute().data[0]
                    renda, publico = calcular_renda_jogo(estadio)
                    renda_mandante = int(renda * 0.95)
                    renda_visitante = renda - renda_mandante

                    saldo_m = supabase.table("times").select("saldo").eq("id", m_id).execute().data[0]["saldo"]
                    saldo_v = supabase.table("times").select("saldo").eq("id", v_id).execute().data[0]["saldo"]
                    supabase.table("times").update({"saldo": saldo_m + renda_mandante}).eq("id", m_id).execute()
                    supabase.table("times").update({"saldo": saldo_v + renda_visitante}).eq("id", v_id).execute()

                    registrar_movimentacao(m_id, "entrada", renda_mandante, f"Renda mandante - rodada {rodada_selecionada} (público: {publico:,})")
                    registrar_movimentacao(v_id, "entrada", renda_visitante, f"Renda visitante - rodada {rodada_selecionada}")

                    st.success(f"Renda total R${renda:,.2f} registrada com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao registrar renda: {e}")
