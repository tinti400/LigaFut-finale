# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="Classificação", page_icon="📊", layout="centered")
st.markdown("## 🏆 Tabela de Classificação")
st.markdown(f"🗓️ Atualizada em: `{datetime.now().strftime('%d/%m/%Y %H:%M')}`")

# 🔒 Login
if "usuario" not in st.session_state:
    st.warning("Você precisa estar logado.")
    st.stop()

# 👤 Admin
email_usuario = st.session_state.get("usuario", "")
res_admin = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = res_admin.data and res_admin.data[0].get("administrador", False)

# 🔹 Seleção da divisão
divisao = st.selectbox("Selecione a divisão", ["Divisão 1", "Divisão 2"])
numero_divisao = divisao.split()[-1]
nome_tabela_rodadas = f"rodadas_divisao_{numero_divisao}"

# 📅 Buscar rodadas
def buscar_resultados():
    try:
        res = supabase.table(nome_tabela_rodadas).select("*").order("numero").execute()
        return res.data if res.data else []
    except Exception as e:
        st.error(f"Erro ao buscar rodadas: {e}")
        return []

# 👥 Buscar times
def obter_nomes_times():
    try:
        usuarios = supabase.table("usuarios").select("time_id").eq("Divisão", divisao).execute().data
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
    except Exception as e:
        st.error(f"Erro ao buscar nomes dos times: {e}")
        return {}

# 🧠 Classificação com punições
def calcular_classificacao(rodadas, times_map):
    tabela = {}

    for rodada in rodadas:
        for jogo in rodada.get("jogos", []):
            m = jogo.get("mandante")
            v = jogo.get("visitante")
            gm = jogo.get("gols_mandante")
            gv = jogo.get("gols_visitante")
            if None in [m, v, gm, gv]: continue
            try:
                gm, gv = int(gm), int(gv)
            except: continue

            for t in (m, v):
                if t not in tabela:
                    tabela[t] = {
                        "nome": times_map.get(t, {}).get("nome", "Desconhecido"),
                        "logo": times_map.get(t, {}).get("logo", ""),
                        "tecnico": times_map.get(t, {}).get("tecnico", ""),
                        "pontos": 0, "v": 0, "e": 0, "d": 0, "gp": 0, "gc": 0, "sg": 0
                    }

            tabela[m]["gp"] += gm
            tabela[m]["gc"] += gv
            tabela[m]["sg"] += gm - gv
            tabela[v]["gp"] += gv
            tabela[v]["gc"] += gm
            tabela[v]["sg"] += gv - gm

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

    try:
        res_punicoes = supabase.table("punicoes").select("id_time, pontos_retirados").execute()
        puni_map = {}
        for p in res_punicoes.data:
            tid = p["id_time"]
            puni_map[tid] = puni_map.get(tid, 0) + p["pontos_retirados"]
        for tid in tabela:
            if tid in puni_map:
                tabela[tid]["pontos"] -= puni_map[tid]
    except Exception as e:
        st.error(f"Erro ao aplicar punições: {e}")

    return sorted(tabela.items(), key=lambda x: (x[1]["pontos"], x[1]["sg"], x[1]["gp"]), reverse=True)

# 🔄 Dados
rodadas = buscar_resultados()
times_map = obter_nomes_times()
classificacao = calcular_classificacao(rodadas, times_map)

# 📅 Exibição das rodadas
st.markdown("---")
st.subheader("📅 Rodadas da Temporada")
if rodadas:
    rodadas_ordenadas = sorted(rodadas, key=lambda r: r.get("numero", 0))
    lista_rodadas = [f"Rodada {r.get('numero', '?')}" for r in rodadas_ordenadas]
    selecao = st.selectbox("🔁 Selecione a rodada para visualizar", lista_rodadas)
    rodada_escolhida = rodadas_ordenadas[lista_rodadas.index(selecao)]
    st.markdown(f"### 🕹️ {selecao}")

    for jogo in rodada_escolhida.get("jogos", []):
        m, v = jogo.get("mandante"), jogo.get("visitante")
        gm, gv = jogo.get("gols_mandante"), jogo.get("gols_visitante")
        m_info = times_map.get(m, {"nome": "?", "logo": "", "tecnico": ""})
        v_info = times_map.get(v, {"nome": "?", "logo": "", "tecnico": ""})
        escudo_m = f"<img src='{m_info['logo']}' width='25' style='margin-right: 5px;'>"
        escudo_v = f"<img src='{v_info['logo']}' width='25' style='margin-left: 5px;'>"
        nome_m = f"<div style='display: inline-block; text-align: left;'><b>{m_info['nome']}</b><br><span style='font-size: 10px; color: gray;'>{m_info.get('tecnico', '')}</span></div>"
        nome_v = f"<div style='display: inline-block; text-align: right;'><b>{v_info['nome']}</b><br><span style='font-size: 10px; color: gray;'>{v_info.get('tecnico', '')}</span></div>"
        placar = f"{gm} x {gv}" if gm is not None and gv is not None else "vs"

        st.markdown(f"""
        <div style='font-size: 16px; display: flex; justify-content: space-between; align-items: center;'>
            {escudo_m}{nome_m}
            <div style='margin: 0 10px; font-weight: bold;'>{placar}</div>
            {nome_v}{escudo_v}
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("Nenhuma rodada encontrada.")
