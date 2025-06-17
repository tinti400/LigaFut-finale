# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from collections import defaultdict

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="📥 Salvar Fase da Copa", layout="centered")
st.title("📥 Salvar Fase Alcançada na Copa da LigaFut")

# 🧩 Ordem das fases para ranqueamento
ordem_fases = ["grupo", "classificado", "oitavas", "quartas", "semi", "vice", "campeao"]

# 🔄 Mapear o maior avanço de cada time
fase_por_time = defaultdict(lambda: "grupo")

# 🔍 Buscar todos os jogos da Copa
res = supabase.table("copa_ligafut").select("*").execute()
jogos = res.data if res.data else []

for jogo in jogos:
    fase = jogo.get("fase", "").lower()
    mandante = jogo.get("mandante")
    visitante = jogo.get("visitante")
    gols_mandante = jogo.get("gols_mandante")
    gols_visitante = jogo.get("gols_visitante")

    # Ignora jogos não disputados
    if gols_mandante is None or gols_visitante is None:
        continue

    # 🧠 Atualiza a fase alcançada de cada time
    for time_id in [mandante, visitante]:
        if ordem_fases.index(fase) > ordem_fases.index(fase_por_time[time_id]):
            fase_por_time[time_id] = fase

    # 🏆 Detecta quem venceu a final
    if fase == "final":
        if gols_mandante > gols_visitante:
            fase_por_time[mandante] = "campeao"
            fase_por_time[visitante] = "vice"
        else:
            fase_por_time[visitante] = "campeao"
            fase_por_time[mandante] = "vice"

# 💾 Atualiza a tabela 'copa' com os resultados
for id_time, fase in fase_por_time.items():
    supabase.table("copa").upsert({
        "id_time": id_time,
        "fase_alcancada": fase
    }).execute()

st.success("✅ Fase da Copa salva com sucesso para todos os times!")
