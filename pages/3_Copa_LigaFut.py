# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import random
import uuid

# 🔐 Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="🏆 Copa LigaFut", layout="wide")
st.title("🏆 Copa LigaFut - Mata-mata")

# 🔐 Login
if "usuario_id" not in st.session_state:
    st.warning("Você precisa estar logado.")
    st.stop()

email_usuario = st.session_state.get("usuario", "")
res_admin = supabase.table("usuarios").select("administrador").eq("usuario", email_usuario).execute()
eh_admin = res_admin.data and res_admin.data[0].get("administrador", False)

if not eh_admin:
    st.warning("Apenas administradores podem acessar esta página.")
    st.stop()

# ✅ Validar UUID
def is_valid_uuid(u):
    try:
        uuid.UUID(u)
        return True
    except:
        return False

# 📊 Buscar times válidos
res_info = supabase.table("times").select("id", "nome", "logo").execute()
times_map = {
    t["id"]: {"nome": t["nome"], "logo": t.get("logo", "")}
    for t in res_info.data
    if t.get("nome") and is_valid_uuid(t["id"])
}
time_ids = list(times_map.keys())

# ⚖️ Gerar confrontos
def gerar_confrontos(times, fase):
    random.shuffle(times)
    jogos = []
    for i in range(0, len(times), 2):
        if i + 1 < len(times):
            jogos.append({
                "id": str(uuid.uuid4()),
                "fase": fase,
                "numero": len(jogos) + 1,
                "id_mandante": times[i],
                "id_visitante": times[i + 1],
                "gols_mandante": None,
                "gols_visitante": None
            })
    return jogos

# ▶️ Avançar fase
def avancar_fase(jogos_fase_atual, fase_atual):
    proxima_fase_map = {
        "Preliminar": "Oitavas",
        "Oitavas": "Quartas",
        "Quartas": "Semifinal",
        "Semifinal": "Final"
    }
    proxima_fase = proxima_fase_map.get(fase_atual)
    if not proxima_fase:
        return None, None

    vencedores = []
    for jogo in jogos_fase_atual:
        if jogo["gols_mandante"] is None or jogo["gols_visitante"] is None:
            return None, None
        if jogo["gols_mandante"] > jogo["gols_visitante"]:
            vencedores.append(jogo["id_mandante"])
        elif jogo["gols_visitante"] > jogo["gols_mandante"]:
            vencedores.append(jogo["id_visitante"])
        else:
            vencedores.append(random.choice([jogo["id_mandante"], jogo["id_visitante"]]))

    proxima_rodada = gerar_confrontos(vencedores, proxima_fase)
    return proxima_fase, proxima_rodada

# 🔄 Botão para iniciar copa
if st.button("⚙️ Gerar Nova Copa LigaFut"):
    if len(time_ids) < 2:
        st.warning("⚠️ É preciso ao menos 2 times para iniciar a copa.")
        st.stop()
    try:
        supabase.table("copa_ligafut").delete().neq("id", "").execute()
        fase = "Preliminar" if len(time_ids) > 16 else "Oitavas"
        jogos = gerar_confrontos(time_ids, fase)
        supabase.table("copa_ligafut").insert({
            "numero": 1,
            "fase": fase,
            "jogos": jogos
        }).execute()
        st.success("✅ Primeira fase criada com sucesso!")
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao gerar a copa: {e}")

# 📅 Exibir rodadas
st.markdown("---")
st.subheader("📅 Fases da Copa")

try:
    res_jogos = supabase.table("copa_ligafut").select("*").order("numero").execute()
    rodadas = res_jogos.data

    if not rodadas:
        st.info("Nenhum jogo cadastrado ainda.")
    else:
        fases_ordem = ["Preliminar", "Oitavas", "Quartas", "Semifinal", "Final"]
        fases = sorted(set(r["fase"] for r in rodadas), key=lambda x: fases_ordem.index(x))

        for rodada in rodadas:
            fase = rodada["fase"]
            jogos_fase = rodada["jogos"]
            st.markdown(f"### 🎯 {fase}")
            for jogo in jogos_fase:
                m_id = jogo["id_mandante"]
                v_id = jogo["id_visitante"]
                m_nome = times_map.get(m_id, {}).get("nome", m_id)
                v_nome = times_map.get(v_id, {}).get("nome", v_id)

                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 2])
                with col1:
                    st.markdown(f"**{m_nome}**")
                with col2:
                    gm = st.number_input("", key=f"gm_{jogo['id']}", min_value=0, value=jogo.get("gols_mandante") or 0)
                with col3:
                    st.markdown("**x**")
                with col4:
                    gv = st.number_input("", key=f"gv_{jogo['id']}", min_value=0, value=jogo.get("gols_visitante") or 0)
                with col5:
                    st.markdown(f"**{v_nome}**")

                if st.button("Salvar", key=f"btn_{jogo['id']}"):
                    try:
                        # Atualiza placar do jogo
                        for j in jogos_fase:
                            if j["id"] == jogo["id"]:
                                j["gols_mandante"] = gm
                                j["gols_visitante"] = gv
                        supabase.table("copa_ligafut").update({
                            "jogos": jogos_fase
                        }).eq("id", rodada["id"]).execute()
                        st.success("✅ Resultado salvo!")

                        # Verifica se pode avançar
                        if all(j["gols_mandante"] is not None and j["gols_visitante"] is not None for j in jogos_fase):
                            proxima_fase, nova_rodada = avancar_fase(jogos_fase, fase)
                            if proxima_fase and nova_rodada:
                                supabase.table("copa_ligafut").insert({
                                    "numero": len(fases) + 1,
                                    "fase": proxima_fase,
                                    "jogos": nova_rodada
                                }).execute()
                                st.success(f"🚀 {proxima_fase} criada automaticamente!")
                            elif fase == "Final":
                                vencedor = None
                                for j in jogos_fase:
                                    if j["gols_mandante"] > j["gols_visitante"]:
                                        vencedor = times_map.get(j["id_mandante"], {}).get("nome", "Desconhecido")
                                    elif j["gols_visitante"] > j["gols_mandante"]:
                                        vencedor = times_map.get(j["id_visitante"], {}).get("nome", "Desconhecido")
                                    else:
                                        vencedor = times_map.get(random.choice([j["id_mandante"], j["id_visitante"]]), {}).get("nome", "Desconhecido")
                                st.balloons()
                                st.success(f"🏆 **{vencedor} é o campeão da Copa LigaFut!**")

                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")
except Exception as e:
    st.error(f"Erro ao carregar dados da copa: {e}")
