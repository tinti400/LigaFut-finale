import streamlit as st
from supabase import create_client
import random
from itertools import combinations

# 🔐 Conexão Supabase
url = "https://hceqyuvryhtihhbvacyo.supabase.co"  # URL do seu Supabase
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhjZXF5dXZyeWh0aWhoYnZhY3lvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NTQ0NDgwNCwiZXhwIjoyMDYxMDIwODA0fQ.zzQs8YobpxZeFdWJhSyh34I_tzW_tUciEAsTat8setg"  # Sua chave do Supabase
supabase = create_client(url, key)

st.set_page_config(page_title="Gerar Rodadas", page_icon="📅", layout="centered")
st.title("📅 Gerar Rodadas Automáticas")

# 🔒 Verifica login
if "usuario" not in st.session_state:
    st.warning("Você precisa estar logado.")
    st.stop()

# 🎯 Dados da sessão
divisao = st.session_state.get("divisao", "Divisão 1")
numero_divisao = divisao.split()[-1]
nome_tabela_rodadas = f"rodadas_divisao_{numero_divisao}"

# 📥 Buscar times da divisão (usuários associados a times dessa divisão)
res_times = supabase.table("usuarios").select("time_id").eq("divisao", divisao).execute()
time_ids = [u["time_id"] for u in res_times.data]

# 📌 Buscar nomes dos times
res_nomes = supabase.table("Times").select("id", "nome").execute()
times_map = {t["id"]: t["nome"] for t in res_nomes.data if t["id"] in time_ids}

# 🧠 Função para gerar confrontos
def gerar_confrontos(times):
    confrontos = list(combinations(times, 2))
    random.shuffle(confrontos)

    rodadas = []
    max_por_rodada = len(times) // 2

    while confrontos:
        rodada = []
        usados = set()
        for c in confrontos[:]:
            t1, t2 = c
            if t1 not in usados and t2 not in usados:
                rodada.append({"mandante": t1, "visitante": t2})
                usados.update([t1, t2])
                confrontos.remove(c)
                if len(rodada) == max_por_rodada:
                    break
        rodadas.append(rodada)

    return rodadas

# 🚨 Botão para gerar
if st.button("⚙️ Gerar Rodadas da Divisão"):
    if len(time_ids) < 2:
        st.warning("Mínimo de 2 times para gerar confrontos.")
        st.stop()

    # Limpa rodadas antigas
    st.info("⏳ Apagando rodadas antigas...")
    supabase.table(nome_tabela_rodadas).delete().execute()

    # Gera confrontos
    rodadas = gerar_confrontos(time_ids)

    # Insere rodadas
    for i, jogos in enumerate(rodadas, 1):
        supabase.table(nome_tabela_rodadas).insert({
            "numero": i,
            "jogos": jogos
        }).execute()

    st.success(f"✅ {len(rodadas)} rodadas geradas com sucesso para {divisao}!")

