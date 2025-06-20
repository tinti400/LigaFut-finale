# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="Classificação", page_icon="📊", layout="wide")
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

# 🔄 Buscar rodadas
@st.cache_data(ttl=60)
def buscar_resultados():
    try:
        res = supabase.table(nome_tabela_rodadas).select("*").order("numero").execute()
        return res.data if res.data else []
    except Exception as e:
        st.error(f"Erro ao buscar rodadas: {e}")
        return []

# 👥 Buscar times
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

# ▶️ Execução
rodadas = buscar_resultados()
times_map = obter_nomes_times()
classificacao = calcular_classificacao(rodadas, times_map)

# 📊 Exibir classificação
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

# 📅 Filtro por rodada ou time
st.markdown("---")
filtro = st.radio("Filtrar jogos por:", ["Rodada", "Time"])

if filtro == "Rodada":
    rodadas_numeros = [r["numero"] for r in rodadas]
    num = st.selectbox("Escolha a rodada", rodadas_numeros)
    rodada = next((r for r in rodadas if r["numero"] == num), None)
    if rodada:
        st.markdown(f"### 🗓 Rodada {num}")
        for jogo in rodada.get("jogos", []):
            m, v = jogo["mandante"], jogo["visitante"]
            gm, gv = jogo.get("gols_mandante", ""), jogo.get("gols_visitante", "")
            time_m = times_map.get(m, {"nome": "Desconhecido", "logo": ""})
            time_v = times_map.get(v, {"nome": "Desconhecido", "logo": ""})
            col1, col2, col3 = st.columns([5, 1, 5])
            with col1:
                st.markdown(f"<img src='{time_m['logo']}' width='30'> {time_m['nome']}", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<h5 style='text-align:center'>{gm} x {gv}</h5>", unsafe_allow_html=True)
            with col3:
                st.markdown(f"{time_v['nome']} <img src='{time_v['logo']}' width='30'>", unsafe_allow_html=True)
            st.markdown("---")
else:
    nomes_times = {v["nome"]: k for k, v in times_map.items()}
    nome_escolhido = st.selectbox("Selecione um time", sorted(nomes_times.keys()))
    id_escolhido = nomes_times[nome_escolhido]

    partidas = []
    for rodada in rodadas:
        for jogo in rodada.get("jogos", []):
            if jogo["mandante"] == id_escolhido or jogo["visitante"] == id_escolhido:
                partidas.append((rodada["numero"], jogo))

    for numero, jogo in partidas:
        m, v = jogo["mandante"], jogo["visitante"]
        gm, gv = jogo.get("gols_mandante", ""), jogo.get("gols_visitante", "")
        time_m = times_map.get(m, {"nome": "Desconhecido", "logo": ""})
        time_v = times_map.get(v, {"nome": "Desconhecido", "logo": ""})
        st.markdown(f"### Rodada {numero}")
        col1, col2, col3 = st.columns([5, 1, 5])
        with col1:
            st.markdown(f"<img src='{time_m['logo']}' width='30'> {time_m['nome']}", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<h5 style='text-align:center'>{gm} x {gv}</h5>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"{time_v['nome']} <img src='{time_v['logo']}' width='30'>", unsafe_allow_html=True)
        st.markdown("---")

# 🔧 Admin: resetar rodadas
if eh_admin:
    st.markdown("---")
    if st.button("🧹 Resetar Rodadas"):
        try:
            docs = supabase.table(nome_tabela_rodadas).select("id").execute().data
            for d in docs:
                supabase.table(nome_tabela_rodadas).delete().eq("id", d["id"]).execute()
            st.success("Rodadas apagadas com sucesso.")
            st.rerun()
        except Exception as e:
            st.error(f"Erro: {e}")


