# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import itertools
import random
from datetime import datetime

st.set_page_config(page_title="♻️ Gerar Rodadas", layout="wide")
st.title("♻️ Gerar Rodadas - LigaFut")

# 🔐 Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# 🔽 Temporada
temporada = st.selectbox("Selecione a temporada", ["Temporada 1", "Temporada 2", "Temporada 3"])
temporada_id = temporada.lower().replace(" ", "")[-1]  # pega '1', '2', etc

# 🔁 Buscar divisões existentes
res = supabase.table("times").select("id, nome, divisao").execute()
times_data = res.data

divisoes = sorted(list(set(t.get("divisao", "") for t in times_data if t.get("divisao"))))
if not divisoes:
    st.warning("Nenhuma divisão encontrada.")
    st.stop()

# 🔘 Botão para gerar rodadas
if st.button("🚀 Gerar Rodadas para todas as divisões"):
    try:
        for divisao in divisoes:
            # Filtrar times da divisão
            times_divisao = [t for t in times_data if t.get("divisao") == divisao]
            time_ids = [t["id"] for t in times_divisao]
            random.shuffle(time_ids)  # embaralha

            if len(time_ids) % 2 != 0:
                time_ids.append("folga")  # time fictício para número par

            n = len(time_ids)
            rodadas_turno = []
            for i in range(n - 1):
                rodada = []
                for j in range(n // 2):
                    mandante = time_ids[j]
                    visitante = time_ids[n - 1 - j]
                    if mandante != "folga" and visitante != "folga":
                        rodada.append({"mandante": mandante, "visitante": visitante})
                rodadas_turno.append(rodada)
                time_ids = [time_ids[0]] + [time_ids[-1]] + time_ids[1:-1]

            # Gera returno invertendo mando
            rodadas_returno = []
            for rodada in rodadas_turno:
                invertida = [{"mandante": jogo["visitante"], "visitante": jogo["mandante"]} for jogo in rodada]
                rodadas_returno.append(invertida)

            todas_rodadas = rodadas_turno + rodadas_returno

            # 🔄 Nome da tabela por divisão e temporada
            nome_tabela = f"rodadas_divisao_{divisao[-1]}_temp{temporada_id}"

            # ❌ Limpa rodadas anteriores
            try:
                supabase.table(nome_tabela).delete().neq("numero", -1).execute()
            except:
                pass  # ignora erro se tabela não existir

            # ✅ Salva novas rodadas
            for i, rodada in enumerate(todas_rodadas, start=1):
                supabase.table(nome_tabela).insert({
                    "numero": i,
                    "jogos": rodada,
                    "data_criacao": datetime.now().isoformat()
                }).execute()

        # ❌ Limpa punições da temporada anterior
        supabase.table("punicoes").delete().neq("id_time", "").execute()

        st.success("✅ Rodadas e punições atualizadas com sucesso!")

    except Exception as e:
        st.error(f"Erro ao gerar rodadas: {e}")


