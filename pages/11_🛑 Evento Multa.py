# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from datetime import datetime
from utils import registrar_movimentacao, verificar_login

st.set_page_config(page_title="Evento de Multa - LigaFut", layout="wide")

# 🔐 Conexão Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Login
verificar_login()
id_usuario = st.session_state["usuario_id"]
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]
email_usuario = st.session_state["usuario"]
st.title("🚨 Evento de Multa - LigaFut")

# 🔍 Verifica se é admin
admin_ref = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = admin_ref.data and admin_ref.data[0].get("administrador", False)

# ⚙️ Configuração
id_config = "evento_multa"
conf_data = supabase.table("configuracoes").select("*").eq("id", id_config).execute().data
conf = conf_data[0] if conf_data else {}

ativo = conf.get("ativo", False)
fase = conf.get("fase", "bloqueio")
ordem = conf.get("ordem", [])
vez = int(conf.get("vez", 0))
concluidos = conf.get("concluidos", [])
bloqueios = conf.get("bloqueios", {})
ja_perderam = conf.get("ja_perderam", {})
finalizado = conf.get("finalizado", False)

# ---------------------- ADMIN ----------------------
if eh_admin:
    st.markdown("### 👑 Painel do Administrador")
    if not ativo:
        if st.button("🚀 Iniciar Evento de Multa"):
            times_ref = supabase.table("times").select("id").execute()
            ordem = [doc["id"] for doc in times_ref.data]
            import random; random.shuffle(ordem)
            supabase.table("configuracoes").upsert({
                "id": id_config,
                "ativo": True,
                "inicio": datetime.utcnow().isoformat(),
                "fase": "bloqueio",
                "ordem": ordem,
                "bloqueios": {},
                "vez": 0,
                "concluidos": [],
                "ja_perderam": {},
                "finalizado": False
            }).execute()
            st.success("Evento iniciado com sucesso!")
            st.rerun()
    else:
        if st.button("🛑 Encerrar Evento"):
            supabase.table("configuracoes").upsert({
                "id": id_config,
                "ativo": False,
                "finalizado": True
            }).execute()
            st.success("Evento encerrado.")
            st.rerun()

# ---------------------- BLOQUEIO ----------------------
if ativo and fase == "bloqueio":
    st.subheader("⛔ Bloqueie até 4 jogadores")
    elenco_ref = supabase.table("elenco").select("*").eq("id_time", id_time).execute()
    elenco = elenco_ref.data if elenco_ref.data else []
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

    if eh_admin and st.button("➡️ Avançar para Ação"):
        supabase.table("configuracoes").upsert({"id": id_config, "fase": "acao"}).execute()
        st.rerun()

# ---------------------- AÇÃO ----------------------
if ativo and fase == "acao":
    st.subheader("🎯 Ordem Atual")
    for i, tid in enumerate(ordem):
        nome = supabase.table("times").select("nome").eq("id", tid).execute().data[0]["nome"]
        if tid in concluidos:
            st.markdown(f"🟢 {nome}")
        elif i == vez:
            st.markdown(f"🔷 {nome} (vez atual)")
        else:
            st.markdown(f"⚪ {nome}")

    if vez < len(ordem) and id_time == ordem[vez]:
        st.success("🎯 É sua vez! Compre até 5 jogadores de outros times pagando multa.")
        times_ref = supabase.table("times").select("id", "nome", "saldo").execute().data

        for t in times_ref:
            tid = t["id"]
            if tid == id_time or ja_perderam.get(tid, 0) >= 4:
                continue

            elenco_ref = supabase.table("elenco").select("*").eq("id_time", tid).execute()
            elenco_adv = elenco_ref.data
            if not elenco_adv: continue

            with st.expander(f"📂 {t['nome']}"):
                for j in elenco_adv:
                    nome_j = j["nome"]
                    posicao = j["posicao"]
                    valor = j["valor"]
                    bloqueado = any(b["nome"] == nome_j for b in bloqueios.get(tid, []))

                    if bloqueado:
                        st.markdown(f"🔐 {nome_j} - {posicao} (R$ {valor:,.0f})")
                    else:
                        if st.button(f"💸 Comprar {nome_j} (R$ {valor:,.0f})", key=f"{tid}_{nome_j}"):
                            comprador = [x for x in times_ref if x["id"] == id_time][0]
                            vendedor = [x for x in times_ref if x["id"] == tid][0]

                            if comprador["saldo"] < valor:
                                st.error("❌ Saldo insuficiente.")
                                st.stop()

                            # 🔁 Transferência
                            supabase.table("elenco").delete().eq("id_time", tid).eq("nome", nome_j).execute()
                            supabase.table("elenco").insert({
                                "id_time": id_time,
                                "nome": nome_j,
                                "posicao": posicao,
                                "overall": j["overall"],
                                "valor": valor
                            }).execute()

                            # 💰 Saldo
                            novo_saldo_comprador = comprador["saldo"] - valor
                            novo_saldo_vendedor = vendedor["saldo"] + valor
                            supabase.table("times").update({"saldo": novo_saldo_comprador}).eq("id", id_time).execute()
                            supabase.table("times").update({"saldo": novo_saldo_vendedor}).eq("id", tid).execute()

                            # 🧾 Registro
                            registrar_movimentacao(supabase, id_time, nome_j, "Multa", "compra", valor)
                            registrar_movimentacao(supabase, tid, nome_j, "Multa", "venda", valor)

                            ja_perderam[tid] = ja_perderam.get(tid, 0) + 1
                            supabase.table("configuracoes").upsert({
                                "id": id_config,
                                "ja_perderam": ja_perderam
                            }).execute()

                            st.success(f"{nome_j} comprado com sucesso!")
                            st.rerun()

        if st.button("✅ Finalizar minha vez"):
            supabase.table("configuracoes").upsert({
                "id": id_config,
                "vez": vez + 1,
                "concluidos": concluidos + [id_time]
            }).execute()
            st.success("Sua vez foi finalizada.")
            st.rerun()

# ---------------------- FINALIZADO ----------------------
if finalizado:
    st.success("✅ Evento finalizado.")
