# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
from utils import verificar_login, pagar_salario_e_premiacao_resultado

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="✏️ Editar Resultados", layout="wide")
st.title("✏️ Editar Resultados das Rodadas")

# ✅ Verifica login
verificar_login()

# Selecionar temporada e divisão
temporada = st.selectbox("Selecione a temporada", ["1", "2", "3"], index=0)
divisao = st.selectbox("Selecione a divisão", ["1", "2", "3"], index=0)
numero_divisao = int(divisao)

# 🔄 Buscar rodadas
rodadas = supabase.table(f"rodadas_temporada_{temporada}_divisao_{divisao}").select("*").order("numero").execute().data

if not rodadas:
    st.info("Nenhuma rodada encontrada.")
    st.stop()

rodada_numeros = [f"Rodada {r['numero']}" for r in rodadas]
rodada_selecionada = st.selectbox("Selecione a rodada", rodada_numeros)
indice_rodada = rodada_numeros.index(rodada_selecionada)
rodada = rodadas[indice_rodada]
jogos = rodada["jogos"]

# Buscar nomes dos times
times_res = supabase.table("times").select("id, nome").execute()
times_dict = {t["id"]: t["nome"] for t in times_res.data}

st.markdown("### 📝 Preencher Resultados")
for idx, jogo in enumerate(jogos):
    col1, col2, col3, col4, col5 = st.columns([4, 1, 1, 1, 4])

    with col1:
        mandante_nome = times_dict.get(jogo["mandante"], "Desconhecido")
        st.markdown(f"**{mandante_nome}**")

    with col2:
        gols_mandante = st.number_input("Gols", min_value=0, key=f"gols_mandante_{idx}", value=jogo.get("gols_mandante", 0))

    with col3:
        st.markdown("x")

    with col4:
        gols_visitante = st.number_input("Gols ", min_value=0, key=f"gols_visitante_{idx}", value=jogo.get("gols_visitante", 0))

    with col5:
        visitante_nome = times_dict.get(jogo["visitante"], "Desconhecido")
        st.markdown(f"**{visitante_nome}**")

if st.button("💾 Salvar Resultados e Atualizar"):
    novos_jogos = []
    for idx, jogo in enumerate(jogos):
        gols_mandante = st.session_state.get(f"gols_mandante_{idx}", 0)
        gols_visitante = st.session_state.get(f"gols_visitante_{idx}", 0)

        # Atualizar no array
        novo_jogo = {
            "mandante": jogo["mandante"],
            "visitante": jogo["visitante"],
            "gols_mandante": gols_mandante,
            "gols_visitante": gols_visitante,
        }
        novos_jogos.append(novo_jogo)

        # Pagar salário + premiação + bônus para os dois times
        try:
            pagar_salario_e_premiacao_resultado(
                jogo["mandante"],
                jogo["visitante"],
                gols_mandante,
                gols_visitante,
                numero_divisao
            )
        except Exception as e:
            st.error(f"Erro ao processar pagamento: {e}")

    # Atualizar rodada na tabela
    supabase.table(f"rodadas_temporada_{temporada}_divisao_{divisao}").update({
        "jogos": novos_jogos
    }).eq("id", rodada["id"]).execute()

    st.success("✅ Resultados salvos e pagamentos processados.")
    st.experimental_rerun()


