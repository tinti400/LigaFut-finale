# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid
import pandas as pd
import random

# ✅ Configuração da Página (ESSA LINHA DEVE SER A PRIMEIRA)
st.set_page_config(page_title="Evento de Roubo - LigaFut", layout="wide")

# ✅ Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica sessão ativa
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("⚠️ Você precisa estar logado para acessar esta página.")
    st.stop()

# ✅ Dados do usuário logado
id_usuario = st.session_state["usuario_id"]
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]
email_usuario = st.session_state["usuario"]

# ✅ Verifica se o usuário é administrador
res_admin = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = res_admin.data and res_admin.data[0].get("administrador", False)

# ✅ ID da configuração do evento de roubo
ID_CONFIG = "56f3af29-a4ac-4a76-aeb3-35400aa2a773"

# ✅ Recupera configurações do evento
res_config = supabase.table("configuracoes").select("*").eq("id", ID_CONFIG).execute()
evento = res_config.data[0] if res_config.data else {}

ativo = evento.get("ativo", False)
fase = evento.get("fase", "sorteio")
ordem = evento.get("ordem", [])
vez = int(evento.get("vez", 0))
bloqueios = evento.get("bloqueios", {})
ultimos_bloqueios = evento.get("ultimos_bloqueios", {})
roubos = evento.get("roubos", {})
ja_perderam = evento.get("ja_perderam", {})
concluidos = evento.get("concluidos", [])
limite_bloqueios = evento.get("limite_bloqueios", 3)
limite_roubo = evento.get("limite_roubo", 5)
limite_perder = evento.get("limite_perder", 4)

# 🔁 Botão de recarregar manual
st.button("🔄 Atualizar Página", on_click=st.rerun)
# ✅ FASE 2 – Configuração inicial do evento (ADM)
if eh_admin and not ativo:
    st.subheader("⚙️ Configurações Iniciais do Evento de Roubo")

    col1, col2, col3 = st.columns(3)
    with col1:
        novo_bloqueios = st.number_input("🔐 Quantos jogadores cada time pode bloquear?", 1, 5, 3)
    with col2:
        novo_perdas = st.number_input("🔴 Quantos jogadores cada time pode perder?", 1, 6, 4)
    with col3:
        novo_roubos = st.number_input("🕵️‍♂️ Quantos jogadores cada time pode roubar?", 1, 6, 5)

    st.markdown("---")
    st.markdown("🎲 A ordem dos times será sorteada aleatoriamente.")
    
    if st.button("✅ Iniciar Evento de Roubo"):
        # Busca todos os times
        times_data = supabase.table("times").select("id", "nome").execute().data
        random.shuffle(times_data)
        ordem_aleatoria = [t["id"] for t in times_data]

        config = {
            "ativo": True,
            "fase": "bloqueio",
            "ordem": ordem_aleatoria,
            "vez": 0,
            "roubos": {},
            "bloqueios": {},
            "ultimos_bloqueios": {},
            "ja_perderam": {},
            "concluidos": [],
            "inicio": str(datetime.utcnow()),
            "limite_bloqueios": novo_bloqueios,
            "limite_roubo": novo_roubos,
            "limite_perder": novo_perdas,
            "finalizado": False
        }

        supabase.table("configuracoes").update(config).eq("id", ID_CONFIG).execute()
        st.success("✅ Evento iniciado com sucesso!")
        st.rerun()
# ✅ FASE 3 – BLOQUEIO DE JOGADORES (fase 'bloqueio')
if ativo and fase == "bloqueio":
    st.subheader("🛡️ Proteja seus jogadores")

    if id_time in bloqueios:
        st.success("✅ Você já bloqueou seus jogadores.")
    else:
        # 🔎 Carrega elenco do time
        elenco_data = supabase.table("elenco").select("*").eq("id_time", id_time).execute().data
        if not elenco_data:
            st.warning("⚠️ Seu elenco está vazio.")
        else:
            st.markdown(f"Selecione até **{limite_bloqueios}** jogadores para bloquear:")

            jogadores_escolhidos = []
            for jogador in elenco_data:
                nome = jogador.get("nome")
                posicao = jogador.get("posicao")
                overall = jogador.get("overall", "")
                col1, col2, col3 = st.columns([5, 3, 2])
                with col1:
                    st.markdown(f"**{nome}** ({posicao})")
                with col2:
                    st.markdown(f"OVR: {overall}")
                with col3:
                    bloquear = st.checkbox("🔐 Bloquear", key=f"block_{jogador['id']}")
                    if bloquear:
                        jogadores_escolhidos.append(jogador["id"])

            if st.button("✅ Confirmar Bloqueios"):
                if len(jogadores_escolhidos) != limite_bloqueios:
                    st.warning(f"Você deve selecionar exatamente {limite_bloqueios} jogadores.")
                else:
                    bloqueios[id_time] = jogadores_escolhidos
                    ultimos_bloqueios[id_time] = jogadores_escolhidos

                    supabase.table("configuracoes").update({
                        "bloqueios": bloqueios,
                        "ultimos_bloqueios": ultimos_bloqueios
                    }).eq("id", ID_CONFIG).execute()

                    st.success("✅ Bloqueios registrados com sucesso!")
                    st.rerun()

    # ✅ ADM pode avançar de fase quando todos tiverem bloqueado
    if eh_admin:
        times_data = supabase.table("times").select("id").execute().data
        total_times = len(times_data)
        bloqueios_realizados = len(bloqueios)

        st.info(f"{bloqueios_realizados} de {total_times} times já bloquearam jogadores.")
        if bloqueios_realizados == total_times:
            if st.button("➡️ Avançar para fase de ação (roubo)"):
                supabase.table("configuracoes").update({
                    "fase": "acao",
                    "vez": 0
                }).eq("id", ID_CONFIG).execute()
                st.success("Fase de bloqueios encerrada. Vamos para a ação!")
                st.rerun()
# ✅ FASE 4 – AÇÃO (fase "acao")
if ativo and fase == "acao":
    st.subheader("🕵️ Sua vez de roubar jogadores!")

    if vez >= len(ordem):
        st.info("✅ Todos os times já participaram.")
    else:
        time_da_vez = ordem[vez]

        # ⚠️ Só o time da vez pode agir
        if id_time != time_da_vez:
            st.warning("⏳ Aguarde sua vez. Outro time está agindo agora.")
        else:
            # 🔎 Mostrar quantos o time pode roubar ainda
            roubados_por_time = roubos.get(str(id_time), [])
            ja_roubou = len(roubados_por_time)
            faltam_roubar = limite_roubo - ja_roubou
            st.success(f"Você pode roubar até **{faltam_roubar}** jogadores.")

            # ➕ Escolher um time alvo
            todos_times = supabase.table("times").select("id", "nome").execute().data
            adversarios = [t for t in todos_times if t["id"] != id_time]

            nomes_times = {t["id"]: t["nome"] for t in adversarios}
            nome_selecionado = st.selectbox("👀 Escolha um time para visualizar o elenco:", list(nomes_times.values()))

            id_time_alvo = next((id_ for id_, nome in nomes_times.items() if nome == nome_selecionado), None)

            if id_time_alvo:
                elenco_alvo = supabase.table("elenco").select("*").eq("id_time", id_time_alvo).execute().data
                bloqueados_alvo = bloqueios.get(str(id_time_alvo), [])
                ja_perdeu = len(ja_perderam.get(str(id_time_alvo), []))
                pode_perder = limite_perder - ja_perdeu

                st.markdown(f"🔒 Jogadores protegidos: {len(bloqueados_alvo)}")
                st.markdown(f"❌ Esse time ainda pode perder **{pode_perder}** jogador(es)")

                if pode_perder == 0:
                    st.info("🚫 Esse time já perdeu o número máximo permitido.")
                else:
                    for jogador in elenco_alvo:
                        id_jogador = jogador["id"]
                        if id_jogador in bloqueados_alvo:
                            continue  # Está protegido
                        if str(id_jogador) in roubados_por_time:
                            continue  # Já roubou esse

                        nome = jogador["nome"]
                        pos = jogador["posicao"]
                        ovr = jogador.get("overall", "")
                        val = jogador.get("valor", 0)

                        col1, col2, col3, col4, col5 = st.columns([4, 2, 2, 2, 2])
                        col1.markdown(f"**{nome}**")
                        col2.markdown(pos)
                        col3.markdown(f"OVR: {ovr}")
                        col4.markdown(f"R$ {val:,.0f}".replace(",", "."))

                        if col5.button("💥 Roubar", key=f"roubar_{id_jogador}"):
                            # ➕ Adiciona ao elenco do time que roubou
                            novo = {
                                "id": str(uuid.uuid4()),
                                "id_time": id_time,
                                "nome": nome,
                                "posicao": pos,
                                "overall": ovr,
                                "valor": val
                            }
                            supabase.table("elenco").insert(novo).execute()

                            # ➖ Remove do time anterior
                            supabase.table("elenco").delete().eq("id", id_jogador).execute()

                            # 🧠 Atualiza contadores
                            roubos.setdefault(str(id_time), []).append(str(id_jogador))
                            ja_perderam.setdefault(str(id_time_alvo), []).append(str(id_jogador))

                            supabase.table("configuracoes").update({
                                "roubos": roubos,
                                "ja_perderam": ja_perderam
                            }).eq("id", ID_CONFIG).execute()

                            st.success(f"✅ Jogador {nome} roubado com sucesso!")
                            st.rerun()

            # ✅ Finalizar vez
            if st.button("➡️ Finalizar minha vez"):
                supabase.table("configuracoes").update({
                    "vez": vez + 1
                }).eq("id", ID_CONFIG).execute()
                st.success("🔄 Vez finalizada!")
                st.rerun()

    # ✅ Botão ADM para encerrar evento a qualquer momento
    if eh_admin:
        st.markdown("---")
        if st.button("🛑 Encerrar Evento de Roubo (ADM)"):
            supabase.table("configuracoes").update({
                "fase": "final",
                "ativo": False,
                "finalizado": True
            }).eq("id", ID_CONFIG).execute()
            st.success("✅ Evento encerrado.")
            st.rerun()
# ✅ FASE 5 – RELATÓRIO FINAL
if not ativo and fase == "final":
    st.subheader("📊 Relatório Final do Evento de Roubo")

    # 🔁 Mostrar ordem de participação
    st.markdown("### 🎲 Ordem de Participação")
    for i, id_t in enumerate(ordem, 1):
        nome = supabase.table("times").select("nome").eq("id", id_t).execute().data[0]["nome"]
        st.markdown(f"{i}º - **{nome}**")

    st.markdown("---")
    st.markdown("### 🕵️‍♂️ Jogadores Roubados")
    dados_tabela = []

    for id_time_roubador, jogadores_ids in roubos.items():
        nome_roubador = supabase.table("times").select("nome").eq("id", id_time_roubador).execute().data[0]["nome"]
        for id_jogador in jogadores_ids:
            jogador_info = supabase.table("historico_elenco").select("*").eq("id", id_jogador).execute().data
            if not jogador_info:
                continue
            j = jogador_info[0]
            nome_jogador = j["nome"]
            pos = j["posicao"]
            ovr = j.get("overall", "")
            id_time_origem = j.get("id_time_antigo", "")
            nome_perdedor = supabase.table("times").select("nome").eq("id", id_time_origem).execute().data[0]["nome"]

            dados_tabela.append({
                "Time que Roubou": nome_roubador,
                "Jogador": nome_jogador,
                "Posição": pos,
                "OVR": ovr,
                "Time que Perdeu": nome_perdedor
            })

    df = pd.DataFrame(dados_tabela)
    if df.empty:
        st.info("Nenhum roubo foi registrado.")
    else:
        st.dataframe(df, use_container_width=True)

    st.markdown("---")
    st.success("✅ Evento encerrado com sucesso.")
    st.markdown("### 📋 Resumo por Time")

    for t in supabase.table("times").select("id", "nome").execute().data:
        t_id = str(t["id"])
        t_nome = t["nome"]

        # ✅ Jogadores roubados por este time
        jogadores_roubados_ids = roubos.get(t_id, [])
        jogadores_roubados = []
        for jid in jogadores_roubados_ids:
            j = supabase.table("historico_elenco").select("*").eq("id", jid).execute().data
            if j:
                jogador = j[0]
                jogadores_roubados.append(f"{jogador['nome']} ({jogador['posicao']}, OVR {jogador.get('overall', '-')})")

        # ❌ Jogadores que este time perdeu
        jogadores_perdidos_ids = ja_perderam.get(t_id, [])
        jogadores_perdidos = []
        for jid in jogadores_perdidos_ids:
            j = supabase.table("historico_elenco").select("*").eq("id", jid).execute().data
            if j:
                jogador = j[0]
                jogadores_perdidos.append(f"{jogador['nome']} ({jogador['posicao']}, OVR {jogador.get('overall', '-')})")

        with st.expander(f"📌 {t_nome} — 🟢 Roubou {len(jogadores_roubados)} | 🔴 Perdeu {len(jogadores_perdidos)}"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 🟢 Jogadores Roubados:")
                if jogadores_roubados:
                    for j in jogadores_roubados:
                        st.markdown(f"- {j}")
                else:
                    st.markdown("Nenhum.")

            with col2:
                st.markdown("#### 🔴 Jogadores Perdidos:")
                if jogadores_perdidos:
                    for j in jogadores_perdidos:
                        st.markdown(f"- {j}")
                else:
                    st.markdown("Nenhum.")


