# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid

st.set_page_config(page_title="Negociações entre Clubes", layout="wide")

# 🔐 Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Login
if "usuario_id" not in st.session_state or not st.session_state.usuario_id:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]
email_usuario = st.session_state["usuario"]

# 🚫 Verificar status do mercado
try:
    status_ref = supabase.table("configuracoes").select("mercado_aberto").eq("id", "estado_mercado").execute()
    mercado_aberto = status_ref.data[0]["mercado_aberto"] if status_ref.data else False
except Exception as e:
    st.error(f"Erro ao verificar status do mercado: {e}")
    mercado_aberto = False

st.title("🤝 Negociações entre Clubes")
st.markdown(f"### Seu Time: **{nome_time}**")

if not mercado_aberto:
    st.warning("🚫 O mercado está fechado no momento. Você pode visualizar os elencos, mas não pode enviar propostas.")

# 🔍 Buscar outros times
res_times = supabase.table("times").select("id", "nome").neq("id", id_time).execute()
times = {t["id"]: t["nome"] for t in res_times.data}

# 📋 Buscar elenco do time logado
res_elenco = supabase.table("elenco").select("*").eq("id_time", id_time).execute()
meu_elenco = res_elenco.data or []

# 🟡 Filtro para selecionar time adversário
time_selecionado = st.selectbox("🔍 Escolha um time para negociar:", list(times.values()))
id_time_selecionado = next((tid for tid, nome in times.items() if nome == time_selecionado), None)

if id_time_selecionado:
    elenco_adv = supabase.table("elenco").select("*").eq("id_time", id_time_selecionado).execute().data or []

    st.subheader(f"🎯 Elenco de {time_selecionado}")

    with st.expander("🔎 Filtros para busca no elenco adversário"):
        filtro_nome = st.text_input("🔤 Buscar por nome")
        posicoes = sorted(set(j.get("posicao", "") for j in elenco_adv if j.get("posicao")))
        filtro_posicao = st.selectbox("📌 Filtrar por posição", ["Todas"] + posicoes)
        filtro_overall = st.slider("⭐ Overall mínimo", min_value=0, max_value=99, value=0)

    elenco_adv = [j for j in elenco_adv if filtro_nome.lower() in j.get("nome", "").lower()
                  and (filtro_posicao == "Todas" or j.get("posicao") == filtro_posicao)
                  and j.get("overall", 0) >= filtro_overall]

    if not elenco_adv:
        st.info("Nenhum jogador disponível neste time com os filtros aplicados.")
    else:
        overalls = [j["overall"] for j in elenco_adv if isinstance(j.get("overall"), int)]
        media_overall = sum(overalls) / len(overalls) if overalls else 0
        st.markdown(f"📊 **Overall médio do time:** `{media_overall:.1f}`")

        for jogador in elenco_adv:
            st.markdown("---")
            col1, col2 = st.columns([1, 5])
            with col1:
                img = jogador.get("imagem_url") or "https://cdn-icons-png.flaticon.com/512/147/147144.png"
                st.image(img, width=60)
            with col2:
                st.markdown(f"**👤 Nome:** {jogador.get('nome', '-')}") 
                st.markdown(f"📌 **Posição:** {jogador.get('posicao', '-')}") 
                st.markdown(f"⭐ **Overall:** {jogador.get('overall', '-')}") 
                st.markdown(f"🌍 **Nacionalidade:** {jogador.get('nacionalidade', '-')}") 
                st.markdown(f"🏟️ **Origem:** {jogador.get('origem', '-')}") 
                st.markdown(f"🧩 **Classificação:** {jogador.get('classificacao', 'Não definida')}") 
                valor_jogador = jogador.get("valor", 0)
                st.markdown(f"💰 **Valor:** R$ {valor_jogador:,.0f}".replace(",", "."))

            tipo = st.radio(
                f"Tipo de negociação para {jogador['nome']}",
                ["Somente Dinheiro", "Troca Simples", "Troca Composta"],
                horizontal=True,
                key=f"tipo_{jogador['id']}"
            )

            jogadores_oferecidos = []
            valor_proposta = 0

            posicoes_meu_elenco = sorted(set(j.get("posicao", "") for j in meu_elenco if j.get("posicao")))
            filtro_posicao_meu = st.selectbox("📌 Filtrar seu elenco por posição", ["Todas"] + posicoes_meu_elenco, key=f"filtro_pos_{jogador['id']}")
            elenco_filtrado_meu = [j for j in meu_elenco if filtro_posicao_meu == "Todas" or j.get("posicao") == filtro_posicao_meu]
            opcoes = [f"{j['nome']} (OVR {j['overall']})" for j in elenco_filtrado_meu]

            if tipo == "Somente Dinheiro":
                valor_proposta = st.number_input(
                    "💵 Valor da Proposta (R$)",
                    step=500_000,
                    value=valor_jogador,
                    key=f"valor_dinheiro_{jogador['id']}"
                )

            elif tipo == "Troca Simples":
                if opcoes:
                    selecao = st.selectbox(
                        "🔁 Escolha um jogador do seu elenco",
                        opcoes,
                        key=f"troca_simples_{jogador['id']}"
                    )
                    jogadores_oferecidos = [elenco_filtrado_meu[opcoes.index(selecao)]]

            elif tipo == "Troca Composta":
                selecao = st.multiselect(
                    "🔁 Escolha um ou mais jogadores do seu elenco",
                    opcoes,
                    key=f"troca_composta_{jogador['id']}"
                )
                jogadores_oferecidos = [elenco_filtrado_meu[opcoes.index(s)] for s in selecao]
                valor_proposta = st.number_input(
                    "💰 Valor adicional em dinheiro (R$)",
                    step=500_000,
                    key=f"valor_composta_{jogador['id']}"
                )

            btn = st.button("📩 Enviar Proposta", key=f"btn_proposta_{jogador['id']}", disabled=not mercado_aberto)
            if btn:
                if tipo != "Somente Dinheiro" and not jogadores_oferecidos:
                    st.warning("Selecione ao menos um jogador do seu elenco para a troca.")
                else:
                    proposta = {
                        "id": str(uuid.uuid4()),
                        "destino_id": id_time_selecionado,
                        "id_time_origem": id_time,
                        "id_time_alvo": id_time_selecionado,
                        "nome_time_origem": nome_time,
                        "nome_time_alvo": time_selecionado,
                        "jogador_nome": jogador["nome"],
                        "jogador_posicao": jogador["posicao"],
                        "jogador_overall": jogador["overall"],
                        "jogador_valor": jogador["valor"],
                        "imagem_url": jogador.get("imagem_url", ""),
                        "nacionalidade": jogador.get("nacionalidade", "-"),
                        "origem": jogador.get("origem", "-"),
                        "classificacao": jogador.get("classificacao", ""),
                        "valor_oferecido": int(valor_proposta),
                        "jogadores_oferecidos": jogadores_oferecidos,
                        "status": "pendente",
                        "created_at": datetime.utcnow().isoformat()
                    }

                    try:
                        resp = supabase.table("propostas").insert(proposta).execute()
                        if resp and resp.data:
                            st.success("✅ Proposta enviada com sucesso!")
                            st.experimental_rerun()
                        else:
                            st.error("Erro ao enviar proposta: resposta vazia.")
                    except Exception as e:
                        st.error(f"Erro: {e}")
