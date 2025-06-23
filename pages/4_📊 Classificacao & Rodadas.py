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

# 🔄 Buscar rodadas da tabela unificada "rodadas"
def buscar_resultados():
    try:
        res = supabase.table("rodadas").select("*").eq("divisao", numero_divisao).eq("temporada", numero_temporada).order("numero").execute()
        return res.data if res.data else []
    except Exception as e:
        st.error(f"Erro ao buscar rodadas: {e}")
        return []

# 👥 Buscar nomes e logos dos times
@st.cache_data(ttl=60)
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

# 🧠 Calcular classificação
def calcular_classificacao(rodadas, times_map):
    tabela = {}

    for rodada in rodadas:
        for jogo in rodada.get("jogos", []):
            m, v = jogo.get("mandante"), jogo.get("visitante")
            gm, gv = jogo.get("gols_mandante"), jogo.get("gols_visitante")
            if None in [m, v, gm, gv]: continue
            try: gm, gv = int(gm), int(gv)
            except: continue

            # 💸 Descontar salários dos dois times (1x por jogo confirmado)
            for time_id in [m, v]:
                elenco = supabase.table("elenco").select("salario", "valor").eq("time_id", time_id).execute().data
                total_salario = sum(j.get("salario", int(j.get("valor", 0)*0.01)) for j in elenco)

                res_saldo = supabase.table("times").select("saldo").eq("id", time_id).execute()
                saldo_atual = res_saldo.data[0]["saldo"] if res_saldo.data else 0
                novo_saldo = saldo_atual - total_salario
                supabase.table("times").update({"saldo": novo_saldo}).eq("id", time_id).execute()
                registrar_movimentacao(supabase, time_id, -total_salario, "Pagamento de salários")

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

    try:
        res_punicoes = supabase.table("punicoes").select("id_time, pontos_retirados").execute()
        puni_map = {p["id_time"]: p["pontos_retirados"] for p in res_punicoes.data}
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

# 📊 Exibe classificação
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

    def aplicar_estilo(df):
        html = "<table style='width: 100%; border-collapse: collapse;'>"
        html += "<thead><tr>" + ''.join(f"<th>{col}</th>" for col in df.columns) + "</tr></thead><tbody>"
        for i, row in df.iterrows():
            cor = "#d4edda" if i < 4 else "#f8d7da" if i >= len(df) - 2 else "white"
            html += f"<tr style='background-color: {cor};'>" + ''.join(f"<td>{val}</td>" for val in row) + "</tr>"
        html += "</tbody></table>"
        return html

    st.markdown(aplicar_estilo(df), unsafe_allow_html=True)
else:
    st.info("Nenhum dado de classificação disponível.")

# 📅 Filtro de rodada
st.markdown("---")
st.subheader("📅 Rodadas da Temporada")

rodadas_disponiveis = sorted(set(r["numero"] for r in rodadas))
rodada_selecionada = st.selectbox("Escolha a rodada que deseja visualizar", rodadas_disponiveis)

for rodada in rodadas:
    if rodada["numero"] != rodada_selecionada:
        continue

    st.markdown(f"<h4 style='margin-top: 30px;'>🔢 Rodada {rodada_selecionada}</h4>", unsafe_allow_html=True)
    for jogo in rodada.get("jogos", []):
        m_id, v_id = jogo.get("mandante"), jogo.get("visitante")
        gm, gv = jogo.get("gols_mandante", ""), jogo.get("gols_visitante", "")
        m = times_map.get(m_id, {}); v = times_map.get(v_id, {})

        m_logo = m.get("logo", "https://cdn-icons-png.flaticon.com/512/147/147144.png")
        v_logo = v.get("logo", "https://cdn-icons-png.flaticon.com/512/147/147144.png")
        m_nome = m.get("nome", "Desconhecido")
        v_nome = v.get("nome", "Desconhecido")

        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 2])
        with col1:
            st.markdown(f"<div style='text-align: right;'><img src='{m_logo}' width='30'> <b>{m_nome}</b></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<h5 style='text-align: center;'>{gm}</h5>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<h5 style='text-align: center;'>x</h5>", unsafe_allow_html=True)
        with col4:
            st.markdown(f"<h5 style='text-align: center;'>{gv}</h5>", unsafe_allow_html=True)
        with col5:
            st.markdown(f"<div style='text-align: left;'><img src='{v_logo}' width='30'> <b>{v_nome}</b></div>", unsafe_allow_html=True)

# 🧹 Admin: resetar rodadas
if eh_admin:
    st.markdown("---")
    if st.button("🧹 Resetar Rodadas"):
        try:
            docs = supabase.table("rodadas").select("id").eq("divisao", numero_divisao).eq("temporada", numero_temporada).execute().data
            for d in docs:
                supabase.table("rodadas").delete().eq("id", d["id"]).execute()
            st.success("Rodadas apagadas com sucesso.")
            st.rerun()
        except Exception as e:
            st.error(f"Erro: {e}")

