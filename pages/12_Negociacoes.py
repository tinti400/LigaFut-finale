import streamlit as st
from supabase import create_client
from datetime import datetime

st.set_page_config(page_title="Negociações entre Clubes", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state.usuario_id:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]

st.markdown(f"### Seu Time: {nome_time}")

# Buscar todos os times (exceto o logado)
times_ref = supabase.table("times").select("id", "nome").neq("id", id_time).execute()
times = {t["id"]: t["nome"] for t in times_ref.data}

# Carregar elenco do time logado
elenco_usuario_ref = supabase.table("elenco").select("*").eq("id_time", id_time).execute()
meu_elenco = elenco_usuario_ref.data

# Verifica se o usuário é admin
admin_ref = supabase.table("usuarios").select("administrador").eq("usuario", st.session_state["usuario"]).execute()
eh_admin = admin_ref.data and admin_ref.data[0]["administrador"] is True  # Corrigindo para verificar 'True'

# Listar times adversários
for time_id, time_nome in times.items():
    with st.expander(f"⚽ Time: {time_nome}"):

        # Somente administradores podem adicionar jogadores
        if eh_admin:
            st.subheader("📥 Adicionar Jogador ao Elenco")

            # Campos para adicionar jogador
            nome_jogador = st.text_input(f"Nome do Jogador para o time {time_nome}")
            posicao_jogador = st.selectbox(f"Posição do Jogador no time {time_nome}", [
                "Goleiro (GL)", "Lateral direito (LD)", "Zagueiro (ZAG)", "Lateral esquerdo (LE)",
                "Volante (VOL)", "Meio campo (MC)", "Meia direita (MD)", "Meia esquerda (ME)",
                "Ponta direita (PD)", "Ponta esquerda (PE)", "Segundo atacante (SA)", "Centroavante (CA)"
            ])
            overall_jogador = st.number_input(f"Overall do Jogador para o time {time_nome}", min_value=1, max_value=99, step=1)
            nacionalidade_jogador = st.text_input(f"Nacionalidade do Jogador para o time {time_nome}")
            valor_jogador = st.number_input(f"Valor do Jogador para o time {time_nome}", min_value=0, step=100_000)
            time_origem_jogador = st.text_input(f"Time de Origem do Jogador para o time {time_nome}")

            if st.button(f"Adicionar {nome_jogador} ao Elenco de {time_nome}", key=f"adicionar_{time_id}"):

                if nome_jogador and posicao_jogador and overall_jogador and nacionalidade_jogador and valor_jogador > 0 and time_origem_jogador:
                    try:
                        jogador_data = {
                            "id_time": time_id,
                            "nome": nome_jogador,
                            "posicao": posicao_jogador,
                            "overall": overall_jogador,
                            "nacionalidade": nacionalidade_jogador,
                            "valor": valor_jogador,
                            "time_origem": time_origem_jogador
                        }

                        # Inserindo o jogador no elenco
                        supabase.table("elenco").insert(jogador_data).execute()

                        st.success(f"✅ Jogador {nome_jogador} adicionado ao elenco de {time_nome} com sucesso!")
                        st.experimental_rerun()  # Atualiza a página para refletir as mudanças
                    except Exception as e:
                        st.error(f"Erro ao adicionar jogador: {e}")
                else:
                    st.warning("Por favor, preencha todos os campos corretamente.")
        
        # Exibindo o elenco do time adversário
        elenco_ref = supabase.table("elenco").select("*").eq("id_time", time_id).execute()
        elenco_adversario = elenco_ref.data

        if not elenco_adversario:
            st.write("Nenhum jogador disponível neste time.")
        else:
            for jogador in elenco_adversario:
                nome = jogador.get("nome", "Sem nome")
                valor = jogador.get("valor", 0)
                overall = jogador.get("overall", "N/A")
                nacionalidade = jogador.get("nacionalidade", "N/A")
                time_origem = jogador.get("time_origem", "N/A")

                st.markdown("---")
                col1, col2 = st.columns([3, 2])
                with col1:
                    st.markdown(f"**🎯 Jogador alvo:** {nome}")
                with col2:
                    st.markdown(f"**Valor:** R$ {valor:,.0f}")

                # Informações complementares
                st.markdown(f"**Overall:** {overall}")
                st.markdown(f"**Nacionalidade:** {nacionalidade}")
                st.markdown(f"**Time de Origem:** {time_origem}")

                # Somente Dinheiro
                valor_adicional = st.number_input(
                    "💰 Valor em dinheiro (R$)",
                    step=500_000,
                    value=valor,
                    key=f"valor_dinheiro_{jogador.get('id')}"
                )

                col_confirmar = st.columns(5)[2]
                with col_confirmar:
                    if st.button(f"🛒 Comprar {nome}", key=f"confirmar_{jogador.get('id')}"):

                        # Verifica se o valor é maior ou igual ao valor do jogador
                        if valor_adicional >= valor:
                            # Definindo os dados da proposta
                            proposta_data = {
                                "id_time_origem": id_time,
                                "id_time_destino": time_id,
                                "jogador_desejado": nome,
                                "id_jogador": jogador.get("id"),  # ID do jogador desejado
                                "jogador_oferecido": [],  # Não há jogadores oferecidos, pois é "Somente Dinheiro"
                                "valor_oferecido": valor_adicional,
                                "tipo_negociacao": "Somente Dinheiro",
                                "status": "pendente",
                                "data": datetime.utcnow().isoformat()  # Data da proposta
                            }

                            try:
                                # Inserindo proposta na tabela de negociações
                                response = supabase.table("negociacoes").insert(proposta_data).execute()

                                # Verifica se a resposta tem dados
                                if response and response.data:
                                    st.success("Proposta enviada com sucesso!")
                                    st.rerun()
                                else:
                                    st.error("Erro ao enviar a proposta: Sem dados na resposta.")
                            except Exception as e:
                                st.error(f"Erro ao enviar a proposta: {e}")
                        else:
                            st.warning(f"❌ O valor da proposta deve ser maior ou igual ao valor do jogador (R$ {valor:,.0f}).")

