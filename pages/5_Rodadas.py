import streamlit as st
from supabase import create_client
import random
from itertools import combinations
from datetime import datetime

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="Gerenciar Rodadas", page_icon="📅", layout="centered")
st.title("📅 Gerenciar Rodadas da Divisão")

# 🔒 Verifica login
if "usuario" not in st.session_state:
    st.warning("Você precisa estar logado.")
    st.stop()

# 🎯 Dados da sessão
divisao = st.session_state.get("divisao", "Divisão 1")
numero_divisao = divisao.split()[-1]
nome_tabela_rodadas = f"rodadas_divisao_{numero_divisao}"

# 📥 Obter times da divisão
def obter_times(divisao):
    res_times = supabase.table("usuarios").select("time_id").eq("divisao", divisao).execute()
    return [u["time_id"] for u in res_times.data]

# 📥 Obter os nomes dos times
def obter_nomes_times():
    res_nomes = supabase.table("times").select("id", "nome").execute()
    return {t["id"]: t["nome"] for t in res_nomes.data}

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
                rodada.append({"mandante": t1, "visitante": t2, "gols_mandante": None, "gols_visitante": None})
                usados.update([t1, t2])
                confrontos.remove(c)
                if len(rodada) == max_por_rodada:
                    break
        rodadas.append(rodada)

    return rodadas

# 📥 Buscar os resultados já gerados
def buscar_rodadas():
    return supabase.table(nome_tabela_rodadas).select("*").execute().data

# 🚨 Botão para gerar rodadas
if st.button("⚙️ Gerar Rodadas da Divisão"):
    time_ids = obter_times(divisao)

    if len(time_ids) < 2:
        st.warning("Mínimo de 2 times para gerar confrontos.")
        st.stop()

    # Limpa rodadas antigas
    st.info("⏳ Apagando rodadas antigas...")
    supabase.table(nome_tabela_rodadas).delete().neq("numero", -1).execute()

    # Gera confrontos
    rodadas = gerar_confrontos(time_ids)

    # Insere rodadas
    for i, jogos in enumerate(rodadas, 1):
        supabase.table(nome_tabela_rodadas).insert({
            "numero": i,
            "jogos": jogos
        }).execute()

    st.success(f"✅ {len(rodadas)} rodadas geradas com sucesso para {divisao}!")

# 📊 Exibir rodadas existentes e permitir edição
rodadas_existentes = buscar_rodadas()

# Obter os nomes dos times
times_map = obter_nomes_times()

if rodadas_existentes:
    st.subheader("Resultados das Rodadas")
    
    for rodada in rodadas_existentes:
        st.write(f"**Rodada {rodada['numero']}**")
        
        for jogo in rodada["jogos"]:
            mandante = jogo["mandante"]
            visitante = jogo["visitante"]
            gols_mandante = jogo.get("gols_mandante", None)
            gols_visitante = jogo.get("gols_visitante", None)

            # Puxando os nomes dos times
            nome_mandante = times_map.get(mandante, mandante)
            nome_visitante = times_map.get(visitante, visitante)

            col1, col2, col3, col4 = st.columns([2, 1, 1, 2])

            # Exibindo os times e os campos para os gols
            with col1:
                st.write(f"**{nome_mandante}** vs **{nome_visitante}**")
            
            with col2:
                gols_mandante = st.number_input(f"Gols {nome_mandante}", min_value=0, value=gols_mandante or 0, key=f"{rodada['numero']}_{mandante}")
            
            with col3:
                gols_visitante = st.number_input(f"Gols {nome_visitante}", min_value=0, value=gols_visitante or 0, key=f"{rodada['numero']}_{visitante}")
            
            with col4:
                # Estilizando o botão de salvar com um ícone
                salvar_key = f"salvar_{rodada['numero']}_{mandante}_{visitante}"
                if st.button("💾 Salvar Resultado", key=salvar_key, help="Clique para salvar o resultado"):
                    # Atualiza o resultado no Supabase (somente os gols)
                    supabase.table(nome_tabela_rodadas).update({
                        "jogos": [
                            {
                                "mandante": mandante,
                                "visitante": visitante,
                                "gols_mandante": gols_mandante,
                                "gols_visitante": gols_visitante
                            }
                        ]
                    }).eq("numero", rodada["numero"]).execute()
                    st.success(f"Resultado atualizado para {nome_mandante} {gols_mandante} x {gols_visitante} {nome_visitante}")

        # 🚮 Botão para excluir os resultados da rodada
        if st.button(f"Excluir Resultados da Rodada {rodada['numero']}", key=f"excluir_resultados_{rodada['numero']}"):
            # Limpa os resultados (gols) da rodada
            jogos_atualizados = [
                {
                    "mandante": jogo["mandante"],
                    "visitante": jogo["visitante"],
                    "gols_mandante": None,
                    "gols_visitante": None
                }
                for jogo in rodada["jogos"]
            ]
            supabase.table(nome_tabela_rodadas).update({
                "jogos": jogos_atualizados
            }).eq("numero", rodada["numero"]).execute()
            st.success(f"Resultados da rodada {rodada['numero']} excluídos com sucesso!")
