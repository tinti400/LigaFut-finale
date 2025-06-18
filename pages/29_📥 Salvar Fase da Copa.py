# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from collections import defaultdict
import pandas as pd

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="📥 Salvar Fase da Copa", layout="wide")
st.title("📥 Atualizar Fase Alcançada na Copa da LigaFut")

# 📌 Ordem das fases
ordem_fases = ["grupo", "classificado", "oitavas", "quartas", "semi", "final"]

# 🗺️ Mapeia o maior avanço por time
fase_por_time = defaultdict(lambda: "grupo")

# 🧩 Buscar todos os times que jogaram a fase de grupos
res_grupos = supabase.table("grupos_copa").select("id_time").execute()
times_de_grupo = [row["id_time"] for row in res_grupos.data] if res_grupos.data else []

# 🔄 Buscar todos os jogos da copa
res_jogos = supabase.table("copa_ligafut").select("*").execute()
jogos = res_jogos.data if res_jogos.data else []

for jogo in jogos:
    fase = jogo.get("fase", "").lower()
    mandante = jogo.get("mandante")
    visitante = jogo.get("visitante")
    gols_mandante = jogo.get("gols_mandante")
    gols_visitante = jogo.get("gols_visitante")

    # Ignora jogos sem resultado
    if gols_mandante is None or gols_visitante is None:
        continue

    # Atualiza fase para mandante e visitante
    for time_id in [mandante, visitante]:
        if ordem_fases.index(fase) > ordem_fases.index(fase_por_time[time_id]):
            fase_por_time[time_id] = fase

    # 👑 Detectar campeão e vice na final
    if fase == "final":
        if gols_mandante > gols_visitante:
            fase_por_time[mandante] = "campeao"
            fase_por_time[visitante] = "vice"
        elif gols_visitante > gols_mandante:
            fase_por_time[visitante] = "campeao"
            fase_por_time[mandante] = "vice"

# ✅ Garantir que todos os que jogaram a fase de grupos tenham registro
for id_time in times_de_grupo:
    if id_time not in fase_por_time:
        fase_por_time[id_time] = "grupo"

# 💾 Atualizar a tabela `copa` com o resultado final
for id_time, fase in fase_por_time.items():
    supabase.table("copa").upsert({
        "id_time": id_time,
        "fase_alcancada": fase
    }).execute()

st.success("✅ Fase da Copa salva com sucesso para todos os times!")

# 👁️ Visualização com nomes dos times
mostrar = st.checkbox("👁️ Ver resumo com nomes dos times")
if mostrar:
    # Buscar nomes dos times
    res_times = supabase.table("times").select("id", "nome").execute()
    mapa_nomes = {t["id"]: t["nome"] for t in res_times.data} if res_times.data else {}

    dados_visual = []
    for id_time, fase in fase_por_time.items():
        nome = mapa_nomes.get(id_time, "❓ Desconhecido")
        dados_visual.append({
            "Time": nome,
            "Fase Alcançada": fase.capitalize()
        })

    df = pd.DataFrame(dados_visual).sort_values("Fase Alcançada", ascending=False)
    st.dataframe(df, use_container_width=True)

