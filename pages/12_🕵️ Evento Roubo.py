# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
import uuid
import random

st.set_page_config(page_title="Evento de Roubo - LigaFut", layout="wide")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verificar login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_usuario = st.session_state["usuario_id"]
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]
email_usuario = st.session_state["usuario"]

# ✅ Verifica se é admin
res_admin = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = res_admin.data and res_admin.data[0].get("administrador", False)

# 📦 Buscar configuração do evento
ID_CONFIG = "evento_roubo"
evento = supabase.table("configuracoes").select("*").eq("id", ID_CONFIG).execute().data
evento = evento[0] if evento else {}

ativo = evento.get("ativo", False)
fase = evento.get("fase", "inicio")
ordem = evento.get("ordem", [])
vez = int(evento.get("vez", 0))
tempo_por_time = evento.get("tempo_por_time", 3)
inicio_vez = evento.get("inicio_vez")

# ✅ Fase 1: Configuração inicial (Admin)
if eh_admin and not ativo:
    st.subheader("🟢 Iniciar Evento de Roubo")

    tempo_definido = st.number_input("⏱️ Tempo por time (em minutos)", min_value=1, max_value=10, value=3)
    if st.button("🚀 Iniciar Evento"):
        todos_times = supabase.table("times").select("id", "nome").execute().data
        ordem_sorteada = [t["id"] for t in todos_times]
        random.shuffle(ordem_sorteada)

        supabase.table("configuracoes").upsert({
            "id": ID_CONFIG,
            "ativo": True,
            "fase": "bloqueio",
            "ordem": ordem_sorteada,
            "vez": 0,
            "concluidos": [],
            "roubos": {},
            "bloqueios": {},
            "ja_perderam": {},
            "finalizado": False,
            "tempo_por_time": int(tempo_definido),
            "inicio_vez": datetime.utcnow().isoformat()
        }).execute()

        st.success("🚀 Evento iniciado com sucesso! Fase de bloqueio liberada.")
        st.experimental_rerun()

# ✅ Botão para encerrar evento manualmente em qualquer fase
if eh_admin and ativo and fase != "finalizado":
    if st.button("🛑 Finalizar Evento Agora"):
        supabase.table("configuracoes").update({
            "ativo": False,
            "fase": "finalizado",
            "finalizado": True
        }).eq("id", ID_CONFIG).execute()
        st.success("Evento finalizado manualmente.")
        st.experimental_rerun()
# ✅ Fase 2: Bloqueio (proteção dos jogadores)
if fase == "bloqueio":
    st.subheader("🛡️ Fase de Proteção de Jogadores")

    # Buscar config atualizada
    evento = supabase.table("configuracoes").select("*").eq("id", ID_CONFIG).execute().data[0]
    bloqueios = evento.get("bloqueios", {})
    limite = evento.get("limite_bloqueios", 3)

    bloqueios_time = bloqueios.get(id_time, [])

    # Buscar elenco do time
    elenco = supabase.table("elenco").select("nome", "posicao").eq("id_time", id_time).execute().data

    # Jogadores ainda não protegidos
    nomes_livres = [j for j in elenco if j["nome"] not in [b["nome"] for b in bloqueios_time]]
    nomes_disponiveis = [j["nome"] for j in nomes_livres]

    if len(bloqueios_time) < limite:
        st.markdown(f"🔐 Jogadores já protegidos: **{len(bloqueios_time)} / {limite}**")
        selecionados = st.multiselect("Selecione jogadores para proteger:", nomes_disponiveis)

        if selecionados and st.button("🔒 Proteger Selecionados"):
            novos = bloqueios_time + [
                {"nome": j["nome"], "posicao": j["posicao"]}
                for j in elenco if j["nome"] in selecionados
            ]
            bloqueios[id_time] = novos
            supabase.table("configuracoes").update({"bloqueios": bloqueios}).eq("id", ID_CONFIG).execute()
            st.success("Jogadores protegidos com sucesso!")
            st.experimental_rerun()
    else:
        st.success("✅ Você já atingiu o número máximo de jogadores protegidos.")

    # Admin pode avançar para a fase de ação
    if eh_admin:
        if st.button("➡️ Avançar para Fase de Ação (Roubo)"):
            supabase.table("configuracoes").update({
                "fase": "acao",
                "inicio_vez": datetime.utcnow().isoformat()
            }).eq("id", ID_CONFIG).execute()
            st.success("Fase de Ação iniciada!")
            st.experimental_rerun()
# ✅ Fase 3: Ação
elif fase == "acao":
    st.subheader("🎯 Fase de Roubo")

    evento = supabase.table("configuracoes").select("*").eq("id", ID_CONFIG).execute().data[0]
    ordem = evento["ordem"]
    vez = int(evento.get("vez", 0))
    inicio_vez = datetime.fromisoformat(evento.get("inicio_vez"))
    tempo_fase = evento.get("tempo_fase", 180)
    tempo_restante = max(0, int(tempo_fase - (datetime.utcnow() - inicio_vez).total_seconds()))

    # Finaliza evento se acabou
    if vez >= len(ordem):
        st.success("✅ Evento encerrado com sucesso!")
        supabase.table("configuracoes").update({"ativo": False, "fase": "finalizado"}).eq("id", ID_CONFIG).execute()
        st.stop()

    id_vez = ordem[vez]
    dados_time = supabase.table("times").select("nome").eq("id", id_vez).execute().data
    nome_time_vez = dados_time[0]["nome"] if dados_time else "Time desconhecido"

    st.info(f"🎲 Vez do time: **{nome_time_vez}**")
    st.warning(f"⏳ Tempo restante: **{tempo_restante} segundos**")

    # Caso não seja a vez do time logado e não seja admin
    if id_time != id_vez and not eh_admin:
        st.info("⏱️ Aguarde sua vez...")
        st.stop()

    # Visualização de outros elencos
    times = supabase.table("times").select("id", "nome").neq("id", id_time).execute().data
    time_alvo_nome = st.selectbox("👀 Selecione um time para ver o elenco:", [t["nome"] for t in times])
    id_alvo = next(t["id"] for t in times if t["nome"] == time_alvo_nome)

    bloqueios = evento.get("bloqueios", {})
    bloqueados = [j["nome"] for j in bloqueios.get(id_alvo, [])]

    elenco_alvo = supabase.table("elenco").select("*").eq("id_time", id_alvo).execute().data
    saldo_info = supabase.table("times").select("saldo").eq("id", id_time).execute().data
    saldo_atual = saldo_info[0]["saldo"] if saldo_info else 0

    for jogador in elenco_alvo:
        nome, posicao, valor, id_original = jogador["nome"], jogador["posicao"], jogador["valor"], jogador["id"]

        if nome in bloqueados:
            st.markdown(f"🔒 **{nome}** ({posicao}) - Protegido")
        else:
            valor_roubo = int(valor * 0.5)
            col1, col2 = st.columns([4, 1])
            col1.markdown(f"**{nome}** ({posicao}) - Valor do roubo: `R$ {valor_roubo:,.0f}`")
            if col2.button("⚡ Roubar", key=f"{id_original}"):
                if saldo_atual < valor_roubo:
                    st.error("❌ Saldo insuficiente para roubar esse jogador.")
                else:
                    # Atualiza saldo e move jogador
                    supabase.table("times").update({"saldo": saldo_atual - valor_roubo}).eq("id", id_time).execute()
                    jogador["id_time"] = id_time
                    jogador["id"] = str(uuid.uuid4())
                    supabase.table("elenco").insert(jogador).execute()
                    supabase.table("elenco").delete().eq("id", id_original).execute()
                    st.success(f"✅ Você roubou {nome} com sucesso!")
                    st.experimental_rerun()

    # Admin pode pular a vez
    if eh_admin and st.button("⏭️ Pular Vez"):
        supabase.table("configuracoes").update({
            "vez": vez + 1,
            "inicio_vez": datetime.utcnow().isoformat()
        }).eq("id", ID_CONFIG).execute()
        st.success("Vez pulada com sucesso.")
        st.experimental_rerun()

    # Qualquer usuário da vez pode finalizar
    if st.button("✅ Finalizar Minha Vez"):
        supabase.table("configuracoes").update({
            "vez": vez + 1,
            "inicio_vez": datetime.utcnow().isoformat()
        }).eq("id", ID_CONFIG).execute()
        st.success("Vez finalizada!")
        st.experimental_rerun()
# ✅ Fase 4: Finalizado
elif fase == "finalizado":
    st.title("🏁 Evento Finalizado")
    st.success("✅ O Evento de Roubo foi concluído com sucesso!")

    # Exibe a ordem dos times e os jogadores roubados
    evento = supabase.table("configuracoes").select("*").eq("id", ID_CONFIG).execute().data[0]
    ordem = evento.get("ordem", [])
    bloqueios = evento.get("bloqueios", {})
    roubos = evento.get("roubos", {})

    st.markdown("### 🔄 Ordem dos Times na Fase de Roubo")
    for i, id_t in enumerate(ordem):
        nome = supabase.table("times").select("nome").eq("id", id_t).execute().data[0]["nome"]
        st.markdown(f"{i+1}️⃣ {nome}")

    st.markdown("### 🛡️ Jogadores Protegidos")
    for id_t, bloqueados in bloqueios.items():
        nome_time = supabase.table("times").select("nome").eq("id", id_t).execute().data[0]["nome"]
        nomes = [j["nome"] for j in bloqueados]
        st.markdown(f"**{nome_time}**: {', '.join(nomes) if nomes else 'Nenhum'}")

    # Histórico de roubos pode ser exibido aqui futuramente (se for salvo em evento["roubos"])
