import streamlit as st
from supabase import create_client
from datetime import datetime
import random

st.set_page_config(page_title="Evento de Multa - LigaFut", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

id_usuario = st.session_state["usuario_id"]
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]
st.title("🚨 Evento de Multa - LigaFut")

# Verifica se é admin
email_usuario = st.session_state["usuario"]
try:
    # Verifica o campo 'administrador' na tabela 'usuarios'
    admin_ref = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
    eh_admin = admin_ref.data and len(admin_ref.data) > 0 and admin_ref.data[0]["administrador"] == True
except Exception as e:
    st.error(f"Erro ao verificar administrador: {e}")
    st.stop()

# ID fixo da configuração de multa
id_config = "evento_multa"

# 🔄 Busca configuração
conf_data = supabase.table("configuracoes").select("*").eq("id", id_config).execute().data
conf = conf_data[0] if conf_data else {}

ativo = conf.get("ativo", False)
fase = conf.get("fase", "bloqueio")
ordem = conf.get("ordem", [])
vez = conf.get("vez", 0)

# ✅ Conversão segura do campo 'vez' para inteiro
try:
    vez = int(vez)
except:
    vez = 0

concluidos = conf.get("concluidos", [])
bloqueios = conf.get("bloqueios", {})
roubos = conf.get("roubos", {})
ja_perderam = conf.get("ja_perderam", {})
finalizado = conf.get("finalizado", False)

# ---------------------- ADMIN ----------------------
if eh_admin:
    st.markdown("### 👑 Painel do Administrador")
    if not ativo:
        if st.button("🚀 Iniciar Evento de Multa"):
            try:
                times_ref = supabase.table("times").select("id").execute()
                ordem = [doc["id"] for doc in times_ref.data]
                random.shuffle(ordem)
                supabase.table("configuracoes").upsert({
                    "id": id_config,
                    "ativo": True,
                    "inicio": datetime.utcnow().isoformat(),
                    "fase": "bloqueio",
                    "ordem": ordem,
                    "bloqueios": {},
                    "roubos": {},
                    "vez": 0,
                    "concluidos": [],
                    "ja_perderam": {},
                    "finalizado": False
                }).execute()
                st.success("Evento iniciado com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao iniciar evento: {e}")
    else:
        if st.button("🛑 Encerrar Evento"):
            supabase.table("configuracoes").upsert({
                "id": id_config,
                "ativo": False,
                "finalizado": True
            }).execute()
            st.success("Evento encerrado.")
            st.rerun()

# ---------------------- STATUS ----------------------
st.markdown("---")
if ativo:
    st.success(f"Evento ativo - Fase: {fase.upper()}")

    if fase == "bloqueio":
        st.subheader("⛔ Bloqueie até 4 jogadores do seu elenco")

        elenco_ref = supabase.table("elenco").select("*").eq("id_time", id_time).execute()
        elenco = elenco_ref.data if elenco_ref.data else []

        if not elenco:
            st.info("Seu time não possui jogadores cadastrados no elenco.")
        else:
            bloqueados = bloqueios.get(id_time, [])
            nomes_bloqueados = [f"{j['nome']} - {j['posicao']}" for j in bloqueados]
            opcoes = [f"{j['nome']} - {j['posicao']}" for j in elenco if f"{j['nome']} - {j['posicao']}" not in nomes_bloqueados]

            escolhidos = st.multiselect("Jogadores para bloquear:", opcoes, default=nomes_bloqueados, max_selections=4)

            if st.button("🔐 Salvar bloqueios"):
                novos = [j for j in elenco if f"{j['nome']} - {j['posicao']}" in escolhidos]
                bloqueios[id_time] = novos
                supabase.table("configuracoes").upsert({"id": id_config, "bloqueios": bloqueios}).execute()
                st.success("Bloqueios salvos.")
                st.rerun()

        if eh_admin:
            if st.button("➡️ Avançar para Ação"):
                supabase.table("configuracoes").upsert({"id": id_config, "fase": "acao"}).execute()
                st.success("Avançou para fase de ação.")
                st.rerun()

    elif fase == "acao":
        st.subheader("🎯 Ordem e Vez Atual")
        for i, tid in enumerate(ordem):
            nome = supabase.table("times").select("nome").eq("id", tid).execute().data[0]["nome"]
            if tid in concluidos:
                st.markdown(f"🟢 {nome}")
            elif i == vez:
                st.markdown(f"🔹 {nome} (vez atual)")
            else:
                st.markdown(f"⚪ {nome}")

        if vez < len(ordem):
            id_vez = ordem[vez]
            if id_time == id_vez:
                st.success("🏸 É sua vez! Escolha jogadores para pagar a multa.")

                times_ref = supabase.table("times").select("id", "nome").execute().data

                for tdoc in times_ref:
                    tid = tdoc["id"]
                    if tid == id_time or ja_perderam.get(tid, 0) >= 4:
                        continue

                    elenco_ref = supabase.table("elenco").select("*").eq("id_time", tid).execute()
                    elenco_adversario = elenco_ref.data

                    if not elenco_adversario:
                        continue

                    with st.expander(f"📂 {tdoc['nome']}"):
                        for jogador in elenco_adversario:
                            nome_jogador = jogador.get("nome")
                            posicao = jogador.get("posicao")
                            valor = jogador.get("valor")

                            if not nome_jogador:
                                continue

                            bloqueado = any(j["nome"] == nome_jogador for j in bloqueios.get(tid, []))
                            ja_roubado = any(
                                nome_jogador == r.get("nome") and r.get("de") == tid
                                for rlist in roubos.values() for r in rlist
                            )
                            if ja_roubado:
                                continue

                            if bloqueado:
                                st.markdown(f"🔐 {nome_jogador} - {posicao} (R$ {valor:,.0f})")
                            else:
                                if st.button(f"Multar {nome_jogador} (R$ {valor:,.0f})", key=f"{tid}_{nome_jogador}"):
                                    novo = roubos.get(id_time, [])
                                    novo.append({"nome": nome_jogador, "posicao": posicao, "valor": valor, "de": tid})
                                    roubos[id_time] = novo
                                    ja_perderam[tid] = ja_perderam.get(tid, 0) + 1
                                    supabase.table("configuracoes").upsert({
                                        "id": id_config,
                                        "roubos": roubos,
                                        "ja_perderam": ja_perderam
                                    }).execute()
                                    st.success(f"{nome_jogador} multado!")
                                    st.rerun()

                if len(roubos.get(id_time, [])) >= 5:
                    st.info("Você já fez as 5 multas permitidas.")

                if st.button("✅ Finalizar minha vez"):
                    concluidos.append(id_time)
                    supabase.table("configuracoes").upsert({
                        "id": id_config,
                        "concluidos": concluidos,
                        "vez": vez + 1
                    }).execute()
                    st.rerun()

            elif eh_admin:
                if st.button("⏩ Pular vez do time atual"):
                    supabase.table("configuracoes").upsert({"id": id_config, "vez": vez + 1}).execute()
                    st.rerun()

    elif finalizado:
        st.success("✅ Evento finalizado. Veja o resumo:")
        for tid, acoes in roubos.items():
            nome_t = supabase.table("times").select("nome").eq("id", tid).execute().data[0]["nome"]
            st.markdown(f"### 🔵 {nome_t} comprou por multa:")
            for j in acoes:
                nome_vendido = supabase.table("times").select("nome").eq("id", j['de']).execute().data[0]["nome"]
                st.markdown(f"- {j['nome']} ({j['posicao']}) do time {nome_vendido}")
else:
    st.warning("🔐 Evento de multa não está ativo.")
