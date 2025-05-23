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

# 📧 Email do usuário e verificação de admin
email_usuario = st.session_state.get("usuario", "")
res_admin = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = res_admin.data and res_admin.data[0].get("administrador", False)

# 🔹 Seletor de divisão
divisao = st.selectbox("Selecione a divisão", ["Divisão 1", "Divisão 2"])
numero_divisao = divisao.split()[-1]
nome_tabela_rodadas = f"rodadas_divisao_{numero_divisao}"

# 📅 Buscar resultados das rodadas
def buscar_resultados():
    try:
        res = supabase.table(nome_tabela_rodadas).select("*").execute()
        return res.data if res.data else []
    except Exception as e:
        st.error(f"Erro ao buscar rodadas: {e}")
        return []

# 👥 Buscar nomes dos times
def obter_nomes_times():
    try:
        usuarios = supabase.table("usuarios").select("time_id").eq("Divisão", divisao).execute().data
        time_ids = list({u["time_id"] for u in usuarios if u.get("time_id")})
        if not time_ids:
            return {}
        res = supabase.table("times").select("id", "nome").in_("id", time_ids).execute()
        return {t["id"]: t["nome"] for t in res.data}
    except Exception as e:
        st.error(f"Erro ao buscar nomes dos times: {e}")
        return {}

# 🧠 Calcular classificação
def calcular_classificacao(rodadas, times_map):
    tabela = {tid: {"nome": nome, "pontos": 0, "v": 0, "e": 0, "d": 0, "gp": 0, "gc": 0, "sg": 0}
              for tid, nome in times_map.items()}

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
                    tabela[t] = {"nome": times_map.get(t, "Desconhecido"), "pontos": 0, "v": 0, "e": 0, "d": 0, "gp": 0, "gc": 0, "sg": 0}

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

# 📊 Montar DataFrame
dados = []
for i, (tid, t) in enumerate(classificacao, start=1):
    dados.append({
        "Posição": i,
        "Time": t["nome"],
        "Pontos": t["pontos"],
        "Jogos": t["v"] + t["e"] + t["d"],
        "Vitórias": t["v"],
        "Empates": t["e"],
        "Derrotas": t["d"],
        "Gols Pró": t["gp"],
        "Gols Contra": t["gc"],
        "Saldo de Gols": t["sg"]
    })

# 🖌️ Estilo visual por posição
def destacar_linha(row):
    total = len(df_classificacao)
    if row["Posição"] <= 4:
        return ['background-color: #d4edda'] * len(row)  # G4
    elif row["Posição"] > total - 2:
        return ['background-color: #f8d7da'] * len(row)  # Z2
    else:
        return [''] * len(row)

# 📋 Exibir tabela
if dados:
    df_classificacao = pd.DataFrame(dados)
    df_formatada = df_classificacao.style.apply(destacar_linha, axis=1)
    st.write(df_formatada)
else:
    st.info("Sem dados suficientes para exibir a tabela de classificação.")

# 🧹 Botão de reset para admin
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


