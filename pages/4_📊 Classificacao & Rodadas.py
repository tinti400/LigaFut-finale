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
    punicoes_por_time = {}
    try:
        res_punicoes = supabase.table("punicoes").select("id_time, pontos_retirados").eq("tipo", "pontos").execute()
        for p in res_punicoes.data:
            tid = str(p["id_time"])
            punicoes_por_time[tid] = punicoes_por_time.get(tid, 0) + p.get("pontos_retirados", 0)
    except:
        pass

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

    for tid in times_map:
        if tid not in tabela:
            tabela[tid] = {
                "nome": times_map[tid]["nome"],
                "logo": times_map[tid]["logo"],
                "tecnico": times_map[tid].get("tecnico", ""),
                "pontos": 0, "v": 0, "e": 0, "d": 0, "gp": 0, "gc": 0, "sg": 0
            }
        penalidade = punicoes_por_time.get(str(tid), 0)
        tabela[tid]["pontos"] = tabela[tid]["pontos"] - penalidade

    return sorted(tabela.items(), key=lambda x: (x[1]["pontos"], x[1]["sg"], x[1]["gp"]), reverse=True)

# Execução
times_map = obter_nomes_times(numero_divisao)
rodadas = buscar_resultados(numero_temporada, numero_divisao)
classificacao = calcular_classificacao(rodadas, times_map)

if classificacao:
    df = pd.DataFrame([{...}])  # OMITIDO PARA FOCO NO PAGAMENTO

# Rodadas
df_rodadas = buscar_resultados(numero_temporada, numero_divisao)
rodadas_disponiveis = sorted(set(r["numero"] for r in df_rodadas))
rodada_selecionada = st.selectbox("Escolha a rodada que deseja visualizar", rodadas_disponiveis)

for rodada in df_rodadas:
    if rodada["numero"] != rodada_selecionada:
        continue

    st.subheader(f"Rodada {rodada_selecionada}")
    for jogo in rodada.get("jogos", []):
        m_id, v_id = jogo.get("mandante"), jogo.get("visitante")
        gm, gv = jogo.get("gols_mandante"), jogo.get("gols_visitante")

        if gm is None or gv is None:
            continue

        descricao = f"Renda da partida rodada {rodada_selecionada}"
        if st.button(f"💸 Pagar Renda Jogo {m_id[:4]} vs {v_id[:4]}", key=f"pagar_{m_id}_{v_id}_{rodada_selecionada}"):
            try:
                estadio = supabase.table("estadios").select("*").eq("id_time", m_id).execute().data[0]
                renda, publico = calcular_renda_jogo(estadio)
                renda_mandante = renda * 0.95
                renda_visitante = renda * 0.05

                saldo_m = supabase.table("times").select("saldo").eq("id", m_id).execute().data[0]["saldo"]
                saldo_v = supabase.table("times").select("saldo").eq("id", v_id).execute().data[0]["saldo"]

                supabase.table("times").update({"saldo": saldo_m + renda_mandante}).eq("id", m_id).execute()
                supabase.table("times").update({"saldo": saldo_v + renda_visitante}).eq("id", v_id).execute()

                registrar_movimentacao(m_id, "entrada", renda_mandante, f"{descricao} (público: {publico:,})")
                registrar_movimentacao(v_id, "entrada", renda_visitante, f"{descricao} (público: {publico:,})")

                st.success(f"Renda paga com sucesso. Público: {publico:,}")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao pagar renda: {e}")