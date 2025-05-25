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

# 🔒 Verifica login
if "usuario" not in st.session_state:
    st.warning("Você precisa estar logado.")
    st.stop()

# 📧 Verifica se é admin
email_usuario = st.session_state.get("usuario", "")
res_admin = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = res_admin.data and res_admin.data[0].get("administrador", False)

# 🔹 Seletor de divisão
divisao = st.selectbox("Selecione a divisão", ["Divisão 1", "Divisão 2"])
numero_divisao = divisao.split()[-1]
nome_tabela_rodadas = f"rodadas_divisao_{numero_divisao}"

# 📅 Buscar resultados
def buscar_resultados():
    try:
        res = supabase.table(nome_tabela_rodadas).select("*").execute()
        return res.data if res.data else []
    except Exception as e:
        st.error(f"Erro ao buscar rodadas: {e}")
        return []

# 👥 Buscar nomes e logos
def obter_nomes_times():
    try:
        usuarios = supabase.table("usuarios").select("time_id").eq("Divisão", divisao).execute().data
        time_ids = list({u["time_id"] for u in usuarios if u.get("time_id")})
        if not time_ids:
            return {}
        res = supabase.table("times").select("id", "nome", "logo").in_("id", time_ids).execute()
        return {t["id"]: {"nome": t["nome"], "logo": t.get("logo", "")} for t in res.data}
    except Exception as e:
        st.error(f"Erro ao buscar nomes dos times: {e}")
        return {}

# 🧠 Calcular classificação
def calcular_classificacao(rodadas, times_map):
    tabela = {
        tid: {
            "nome": times_map[tid]["nome"],
            "logo": times_map[tid]["logo"],
            "pontos": 0, "v": 0, "e": 0, "d": 0, "gp": 0, "gc": 0, "sg": 0
        }
        for tid in times_map
    }

    for rodada in rodadas:
        for jogo in rodada.get("jogos", []):
            m = jogo.get("mandante")
            v = jogo.get("visitante")
            gm = jogo.get("gols_mandante")
            gv = jogo.get("gols_visitante")
            if None in [m, v, gm, gv]:
                continue
            try:
                gm, gv = int(gm), int(gv)
            except:
                continue

            for t in (m, v):
                if t not in tabela:
                    tabela[t] = {
                        "nome": times_map.get(t, {}).get("nome", "Desconhecido"),
                        "logo": times_map.get(t, {}).get("logo", ""),
                        "pontos": 0, "v": 0, "e": 0, "d": 0, "gp": 0, "gc": 0, "sg": 0
                    }

            tabela[m]["gp"] += gm
            tabela[m]["gc"] += gv
            tabela[m]["sg"] += gm - gv
            tabela[v]["gp"] += gv
            tabela[v]["gc"] += gm
            tabela[v]["sg"] += gv - gm

            if gm > gv:
                tabela[m]["pontos"] += 3
                tabela[m]["v"] += 1
                tabela[v]["d"] += 1
            elif gm < gv:
                tabela[v]["pontos"] += 3
                tabela[v]["v"] += 1
                tabela[m]["d"] += 1
            else:
                tabela[m]["pontos"] += 1
                tabela[v]["pontos"] += 1
                tabela[m]["e"] += 1
                tabela[v]["e"] += 1

    return sorted(tabela.items(), key=lambda x: (x[1]["pontos"], x[1]["sg"], x[1]["gp"]), reverse=True)

# 🔄 Carregar dados
rodadas = buscar_resultados()
times_map = obter_nomes_times()
classificacao = calcular_classificacao(rodadas, times_map)

# 📊 Montar tabela
dados = []
for i, (tid, t) in enumerate(classificacao, start=1):
    nome_formatado = t["nome"].strip().capitalize()
    escudo_html = f"<img src='{t['logo']}' width='25' style='margin-right:6px; vertical-align:middle;'>"
    time_com_escudo = f"{escudo_html}{nome_formatado}"

    dados.append({
        "Posição": i,
        "Time": time_com_escudo,
        "Pontos": t["pontos"],
        "Jogos": t["v"] + t["e"] + t["d"],
        "Vitórias": t["v"],
        "Empates": t["e"],
        "Derrotas": t["d"],
        "Gols Pró": t["gp"],
        "Gols Contra": t["gc"],
        "Saldo de Gols": t["sg"]
    })

# 📋 Estilização HTML
def aplicar_estilo_linha(df):
    html = "<style>td, th { text-align: center; vertical-align: middle; }</style><table border='1' class='dataframe' style='width: 100%; border-collapse: collapse;'>"
    html += "<thead><tr>"
    for col in df.columns:
        html += f"<th>{col}</th>"
    html += "</tr></thead><tbody>"

    total_linhas = len(df)
    for i, row in df.iterrows():
        if i < 4:
            html += "<tr style='background-color: #d4edda;'>"
        elif i >= total_linhas - 2:
            html += "<tr style='background-color: #f8d7da;'>"
        else:
            html += "<tr>"

        for val in row:
            html += f"<td>{val}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    return html

# ✅ Exibir tabela
if dados:
    df_classificacao = pd.DataFrame(dados)
    st.markdown(aplicar_estilo_linha(df_classificacao), unsafe_allow_html=True)
else:
    st.info("Sem dados suficientes para exibir a tabela de classificação.")

# 🔧 Ações admin
if eh_admin:
    st.markdown("---")
    st.subheader("🔧 Ações administrativas")
    if st.button("🧹 Resetar Tabela de Classificação (apagar rodadas)"):
        try:
            res = supabase.table(nome_tabela_rodadas).select("id").execute()
            for doc in res.data:
                supabase.table(nome_tabela_rodadas).delete().eq("id", doc["id"]).execute()
            st.success("✅ Rodadas da divisão apagadas com sucesso.")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao resetar rodadas: {e}")
