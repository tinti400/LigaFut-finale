# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from utils import verificar_sessao, registrar_movimentacao

st.set_page_config(page_title="📨 Propostas Recebidas", layout="wide")
verificar_sessao()

url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

# 🔴 Buscar propostas pendentes
res = supabase.table("propostas").select("*").eq("destino_id", id_time).eq("status", "pendente").execute()
propostas = res.data if res.data else []
notificacoes_recebidas = len(propostas)

# 🔔 Sidebar
with st.sidebar:
    if notificacoes_recebidas > 0:
        st.markdown(f"""
        <span style='color:white;background:red;padding:4px 10px;border-radius:50%;font-size:14px'>
        {notificacoes_recebidas}</span> 🔔 Propostas Recebidas
        """, unsafe_allow_html=True)

# 🔰 Título
st.markdown(f"""
<h3>📨 Propostas Recebidas - {nome_time}
<span style='color:white;background:red;padding:2px 8px;border-radius:50%;margin-left:10px;'>{notificacoes_recebidas}</span>
</h3>
""", unsafe_allow_html=True)

if not propostas:
    st.info("📭 Nenhuma proposta pendente no momento.")
else:
    for proposta in propostas:
        with st.container():
            st.markdown("---")
            col1, col2 = st.columns([1, 3])

            with col1:
                imagem = proposta.get("imagem_url") or "https://cdn-icons-png.flaticon.com/512/147/147144.png"
                st.image(imagem, width=80)

            with col2:
                st.markdown(f"### {proposta['jogador_nome']} ({proposta['jogador_posicao']})")
                st.write(f"🌍 **Nacionalidade:** {proposta.get('nacionalidade', 'Desconhecida')}")
                st.write(f"📌 **Posição:** {proposta['jogador_posicao']}")
                st.write(f"⭐ **Overall:** {proposta['jogador_overall']}")
                st.write(f"💰 **Valor:** R$ {proposta['jogador_valor']:,.0f}".replace(",", "."))
                st.write(f"🏟️ **Origem:** {proposta.get('origem', 'Desconhecida')}")
                st.write(f"📨 **Proposta de:** {proposta['nome_time_origem']}")
                st.write(f"📦 **Valor Oferecido:** R$ {proposta['valor_oferecido']:,.0f}".replace(",", "."))

            jogadores_oferecidos = proposta.get("jogadores_oferecidos", [])
            if jogadores_oferecidos:
                st.markdown("**🔁 Jogadores Oferecidos em Troca:**")
                for j in jogadores_oferecidos:
                    st.write(f"- {j['nome']} (OVR {j['overall']}) - {j['posicao']}")

            col1, col2 = st.columns(2)

            if col1.button("✅ Aceitar", key=f"aceitar_{proposta['id']}"):
                try:
                    valor = proposta["valor_oferecido"]
                    id_time_origem = proposta["id_time_origem"]
                    id_time_destino = proposta["id_time_alvo"]
                    jogador_nome = proposta["jogador_nome"]

                    # Remover jogador do time atual
                    supabase.table("elenco").delete().eq("id_time", id_time_destino).eq("nome", jogador_nome).execute()

                    # Adicionar jogador ao time comprador
                    novo_jogador = {
                        "nome": jogador_nome,
                        "posicao": proposta["jogador_posicao"],
                        "overall": proposta["jogador_overall"],
                        "valor": valor,
                        "id_time": id_time_origem,
                        "nacionalidade": proposta.get("nacionalidade"),
                        "imagem_url": proposta.get("imagem_url"),
                        "origem": proposta.get("origem", nome_time)
                    }
                    supabase.table("elenco").insert(novo_jogador).execute()

                    # Inserir jogadores oferecidos no time atual (se houver)
                    for jogador in jogadores_oferecidos:
                        supabase.table("elenco").delete().eq("id_time", id_time_origem).eq("nome", jogador["nome"]).execute()
                        jogador_trocado = {
                            "nome": jogador["nome"],
                            "posicao": jogador["posicao"],
                            "overall": jogador["overall"],
                            "valor": jogador["valor"],
                            "id_time": id_time_destino,
                            "nacionalidade": jogador.get("nacionalidade"),
                            "imagem_url": jogador.get("imagem_url"),
                            "origem": nome_time_origem
                        }
                        supabase.table("elenco").insert(jogador_trocado).execute()

                    # Registrar movimentações financeiras
                    if valor > 0:
                        registrar_movimentacao(id_time_origem, jogador_nome, "Transferência", "Compra", valor)
                        registrar_movimentacao(id_time_destino, jogador_nome, "Transferência", "Venda", valor)

                    # ❌ Apagar TODAS as propostas pendentes desse jogador (inclusive a aceita)
                    supabase.table("propostas").delete() \
                        .eq("jogador_nome", jogador_nome) \
                        .eq("destino_id", id_time) \
                        .eq("status", "pendente").execute()

                    st.success(f"✅ Proposta aceita! {jogador_nome} foi transferido para {proposta['nome_time_origem']}.")
                    st.experimental_rerun()

                except Exception as e:
                    st.error(f"Erro ao aceitar a proposta: {e}")

            if col2.button("❌ Recusar", key=f"recusar_{proposta['id']}"):
                try:
                    # ❌ Apagar a proposta recusada
                    supabase.table("propostas").delete().eq("id", proposta["id"]).execute()
                    st.warning("❌ Proposta recusada e removida do histórico.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Erro ao recusar a proposta: {e}")

