# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid
from utils import verificar_sessao

st.set_page_config(page_title="📤 Propostas Enviadas - LigaFut", layout="wide")
verificar_sessao()

url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

id_time_origem = st.session_state["id_time"]
nome_time_origem = st.session_state["nome_time"]

# 🔴 Contador de propostas enviadas pendentes
count_enviadas = supabase.table("propostas").select("*").eq("id_time_origem", id_time_origem).eq("status", "pendente").execute()
notificacoes_enviadas = len(count_enviadas.data) if count_enviadas.data else 0

st.markdown(f"""
<h3>📤 Propostas Enviadas
<span style='color:white;background:red;padding:2px 8px;border-radius:50%;margin-left:10px;'>{notificacoes_enviadas}</span>
</h3>
""", unsafe_allow_html=True)

# 🔎 Selecionar time alvo
times_ref = supabase.table("times").select("id", "nome").neq("id", id_time_origem).execute()
times_disponiveis = times_ref.data or []
nomes_times = {t["nome"]: t["id"] for t in times_disponiveis}
nome_time_alvo = st.selectbox("Escolha o time para enviar proposta:", list(nomes_times.keys()))
id_time_alvo = nomes_times[nome_time_alvo]

# 🔎 Selecionar jogador alvo
elenco_ref = supabase.table("elenco").select("*").eq("id_time", id_time_alvo).execute()
elenco_disponivel = elenco_ref.data or []
jogadores_alvo = [f'{j["nome"]} ({j["posicao"]})' for j in elenco_disponivel]
jogador_escolhido = st.selectbox("Escolha o jogador desejado:", jogadores_alvo)
jogador_data = next((j for j in elenco_disponivel if f'{j["nome"]} ({j["posicao"]})' == jogador_escolhido), None)

valor_oferecido = st.number_input("Valor oferecido (R$):", min_value=0, step=100000)

# 🏨 Enviar nova proposta
if st.button("📩 Enviar proposta"):
    if jogador_data:
        try:
            nova_proposta = {
                "id": str(uuid.uuid4()),
                "id_time_origem": id_time_origem,
                "nome_time_origem": nome_time_origem,
                "id_time_alvo": id_time_alvo,
                "destino_id": id_time_alvo,
                "nome_time_alvo": nome_time_alvo,
                "jogador_nome": jogador_data["nome"],
                "jogador_posicao": jogador_data["posicao"],
                "jogador_overall": jogador_data["overall"],
                "jogador_valor": jogador_data["valor"],
                "valor_oferecido": valor_oferecido,
                "status": "pendente",
                "created_at": datetime.now().isoformat(),
                "jogadores_oferecidos": [],
                "nacionalidade": jogador_data.get("nacionalidade", "Desconhecida"),
                "imagem_url": jogador_data.get("imagem_url", ""),
                "origem": jogador_data.get("origem", nome_time_alvo)
            }
            supabase.table("propostas").insert(nova_proposta).execute()
            st.success("✅ Proposta enviada com sucesso!")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Erro ao enviar proposta: {e}")
    else:
        st.warning("Jogador não encontrado!")

# 📜 Exibir propostas enviadas
st.subheader("📜 Suas propostas enviadas")
try:
    propostas_ref = supabase.table("propostas") \
        .select("*") \
        .eq("id_time_origem", id_time_origem) \
        .order("created_at", desc=True) \
        .execute()

    propostas = propostas_ref.data or []
    if not propostas:
        st.info("Você ainda não enviou nenhuma proposta.")
    else:
        for p in propostas:
            with st.container():
                st.markdown("---")
                col1, col2 = st.columns([1, 3])

                with col1:
                    imagem = p.get("imagem_url") or "https://cdn-icons-png.flaticon.com/512/147/147144.png"
                    try:
                        st.image(imagem, width=80)
                    except:
                        st.image("https://cdn-icons-png.flaticon.com/512/147/147144.png", width=80)

                with col2:
                    st.markdown(f"### {p['jogador_nome']} ({p['jogador_posicao']})")
                    st.write(f"🌍 **Nacionalidade:** {p.get('nacionalidade', 'Desconhecida')}")
                    st.write(f"📌 **Posição:** {p['jogador_posicao']}")
                    st.write(f"⭐ **Overall:** {p['jogador_overall']}")
                    st.write(f"💰 **Valor:** R$ {p['jogador_valor']:,.0f}".replace(",", "."))
                    st.write(f"🏟️ **Origem:** {p.get('origem', 'Desconhecida')}")
                    st.write(f"🌿 **Time Alvo:** {p['nome_time_alvo']}")
                    st.write(f"🛆 **Valor Oferecido:** R$ {p['valor_oferecido']:,.0f}".replace(",", "."))
                    st.write(f"🗓️ **Enviada em:** {datetime.fromisoformat(p['created_at']).strftime('%d/%m/%Y %H:%M')}")
                    st.write(f"📌 **Status:** {p['status'].capitalize()}")

                if p["status"] == "pendente":
                    col1, col2 = st.columns(2)

                    with col1:
                        novo_valor = st.number_input(
                            f"Editar valor (R$) - {p['jogador_nome']}",
                            min_value=0,
                            step=100000,
                            value=p["valor_oferecido"],
                            key=f"editar_valor_{p['id']}"
                        )
                        if st.button("✏️ Salvar Alteração", key=f"salvar_{p['id']}"):
                            try:
                                supabase.table("propostas").update({
                                    "valor_oferecido": novo_valor
                                }).eq("id", p["id"]).execute()
                                st.success("✏️ Valor da proposta atualizado!")
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Erro ao editar proposta: {e}")

                    with col2:
                        if st.button("❌ Cancelar proposta", key=f"cancelar_{p['id']}"):
                            try:
                                supabase.table("propostas").update({"status": "cancelada"}).eq("id", p["id"]).execute()
                                st.warning("❌ Proposta cancelada.")
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Erro ao cancelar proposta: {e}")

except Exception as e:
    st.error(f"Erro ao buscar propostas enviadas: {e}")


	