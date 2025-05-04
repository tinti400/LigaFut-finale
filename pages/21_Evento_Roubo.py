import streamlit as st
from supabase import create_client
from datetime import datetime
import random
from utils import verificar_login, registrar_movimentacao

st.set_page_config(page_title="Evento de Roubo - LigaFut", layout="wide")

# 🔐 Conexão com Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

# ✅ Verifica login
verificar_login()

# Dados do usuário logado
id_usuario = st.session_state["usuario_id"]
id_time = st.session_state["id_time"]
nome_time = st.session_state["nome_time"]
email_usuario = st.session_state["usuario"]

st.title("🚨 Evento de Roubo - LigaFut")

# ID fixo da configuração do evento
ID_CONFIG = "56f3af29-a4ac-4a76-aeb3-35400aa2a773"

# Verifica se é admin usando o campo 'administrador' da tabela 'usuarios'
admin_ref = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = admin_ref.data and len(admin_ref.data) > 0 and admin_ref.data[0]["administrador"] == True

# 🔄 Busca configuração do evento
res = supabase.table("configuracoes").select("*").eq("id", ID_CONFIG).execute()
evento = res.data[0] if res.data else {}

ativo = evento.get("ativo", False)
fase = evento.get("fase", "acao")
ordem = evento.get("ordem", [])
vez = evento.get("vez", 0)

# ✅ Conversão segura do campo 'vez'
try:
    vez = int(vez)
except:
    vez = 0

concluidos = evento.get("concluidos", [])
bloqueios = evento.get("bloqueios", {})
ja_perderam = evento.get("ja_perderam", {})
roubos = evento.get("roubos", {})

# ---------------------- ADMIN ----------------------
if eh_admin:
    st.markdown("### 👑 Painel do Administrador")
    if not ativo:
        if st.button("🚀 Iniciar Evento de Roubo"):
            try:
                times_ref = supabase.table("times").select("id").execute()
                ordem = [doc["id"] for doc in times_ref.data]
                random.shuffle(ordem)
                supabase.table("configuracoes").update({
                    "ativo": True,
                    "inicio": str(datetime.utcnow()),
                    "fase": "acao",
                    "ordem": ordem,
                    "vez": 0,
                    "concluidos": [],
                    "bloqueios": {},
                    "ja_perderam": {},
                    "roubos": {},
                    "finalizado": False
                }).eq("id", ID_CONFIG).execute()
                st.success("Evento iniciado com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao iniciar evento: {e}")
    else:
        if st.button("🛑 Encerrar Evento"):
            supabase.table("configuracoes").update({
                "ativo": False,
                "finalizado": True
            }).eq("id", ID_CONFIG).execute()
            st.success("Evento encerrado.")
            st.rerun()

# ---------------------- STATUS ----------------------
st.markdown("---")
if ativo:
    st.success(f"Evento ativo - Fase: {fase.upper()}")

    if fase == "acao":
        st.subheader("🎯 Ordem e Vez Atual")
        for i, tid in enumerate(ordem):
            nome = supabase.table("times").select("nome").eq("id", tid).execute().data[0]["nome"]
            if tid in concluidos:
                st.markdown(f"🟢 {nome}")
            elif i == vez:
                st.markdown(f"🟡 {nome} (vez atual)")
            else:
                st.markdown(f"⚪ {nome}")

        if vez < len(ordem):
            id_vez = ordem[vez]
            if id_time == id_vez:
                st.success("É sua vez! Escolha jogadores para roubar (pagando 50% do valor).")

                times = supabase.table("times").select("id", "nome").execute().data

                for adversario in times:
                    tid = adversario["id"]
                    if tid == id_time or ja_perderam.get(tid, 0) >= 4:
                        continue

                    nome_adversario = adversario["nome"]

                    # Busca elenco diretamente da tabela de elenco
                    elenco_ref = supabase.table("elenco").select("*").eq("id_time", tid).execute()
                    elenco = elenco_ref.data if elenco_ref.data else []

                    if not elenco:
                        continue

                    with st.expander(f"📂 {nome_adversario}"):
                        for jogador in elenco:
                            nome_j = jogador.get("nome")
                            posicao = jogador.get("posicao")
                            valor = jogador.get("valor", 0)

                            if not nome_j:
                                continue

                            bloqueado = any(nome_j == b.get("nome") for b in bloqueios.get(tid, []))
                            ja_roubado = any(
                                nome_j == r.get("nome") and r.get("de") == tid
                                for acoes in roubos.values()
                                for r in acoes
                            )

                            if bloqueado:
                                st.markdown(f"🔒 {nome_j} - {posicao} (R$ {valor:,.0f})")
                            elif ja_roubado:
                                st.markdown(f"❌ {nome_j} - já roubado")
                            else:
                                if st.button(f"Roubar {nome_j} (R$ {valor/2:,.0f})", key=f"{tid}_{nome_j}"):
                                    novo = roubos.get(id_time, [])
                                    novo.append({
                                        "nome": nome_j,
                                        "posicao": posicao,
                                        "valor": valor,
                                        "de": tid
                                    })
                                    roubos[id_time] = novo
                                    ja_perderam[tid] = ja_perderam.get(tid, 0) + 1

                                    supabase.table("configuracoes").update({
                                        "roubos": roubos,
                                        "ja_perderam": ja_perderam
                                    }).eq("id", ID_CONFIG).execute()

                                    st.success(f"{nome_j} selecionado para roubo!")
                                    st.rerun()

                if len(roubos.get(id_time, [])) >= 5:
                    st.info("Você já selecionou os 5 jogadores permitidos.")

                if st.button("✅ Finalizar minha vez"):
                    concluidos.append(id_time)
                    supabase.table("configuracoes").update({
                        "concluidos": concluidos,
                        "vez": vez + 1
                    }).eq("id", ID_CONFIG).execute()
                    st.rerun()

            elif eh_admin:
                if st.button("⏭️ Pular vez atual"):
                    supabase.table("configuracoes").update({
                        "vez": vez + 1
                    }).eq("id", ID_CONFIG).execute()
                    st.rerun()

    if evento.get("finalizado"):
        st.success("✅ Evento finalizado. Veja o resumo:")
        for tid, acoes in roubos.items():
            nome_t = supabase.table("times").select("nome").eq("id", tid).execute().data[0]["nome"]
            st.markdown(f"### 🗭 {nome_t} roubou:")
            for j in acoes:
                nome_vendido = supabase.table("times").select("nome").eq("id", j['de']).execute().data[0]["nome"]
                st.markdown(f"- {j['nome']} ({j['posicao']}) do time {nome_vendido}")
                try:
                    # 🔄 Remover do time original
                    elenco_antigo = supabase.table("elenco").select("*").eq("id_time", j['de']).execute().data
                    novo_elenco_v = [e for e in elenco_antigo if e['nome'] != j['nome']]
                    supabase.table("elenco").delete().eq("id_time", j['de']).eq("nome", j['nome']).execute()

                    # Atualiza saldo do time que perdeu
                    vendedor_data = supabase.table("times").select("saldo").eq("id", j['de']).execute().data[0]
                    novo_saldo_v = vendedor_data['saldo'] + j['valor'] / 2
                    supabase.table("times").update({"saldo": novo_saldo_v}).eq("id", j['de']).execute()

                    # 🔄 Adicionar ao novo time
                    j['id_time'] = tid
                    supabase.table("elenco").insert(j).execute()

                    comprador_data = supabase.table("times").select("saldo").eq("id", tid).execute().data[0]
                    novo_saldo_c = comprador_data['saldo'] - j['valor'] / 2
                    supabase.table("times").update({"saldo": novo_saldo_c}).eq("id", tid).execute()

                    # 📌 Registro da movimentação
                    registrar_movimentacao(tid, j['nome'], "Roubo", "Compra", j['valor'] / 2)

                except Exception as e:
                    st.error(f"Erro ao transferir {j['nome']}: {e}")
else:
    st.warning("🔐 Evento de roubo não está ativo.")
