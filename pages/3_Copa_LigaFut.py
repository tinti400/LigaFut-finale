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
        else:
            st.warning(f"⚠️ O time **{times[i]}** ficou sem adversário e foi ignorado.")
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
    try:
        res_info = supabase.table("times").select("id", "nome", "logo").execute()
        times_map = {
            t["id"]: {"nome": t["nome"], "logo": t.get("logo", "")}
            for t in res_info.data
            if t.get("nome") and is_valid_uuid(t["id"])
        }

        time_ids = []
        for tid, info in times_map.items():
            nome = info.get("nome", "")
            if is_valid_uuid(tid) and nome.strip() != "":
                time_ids.append(tid)
            else:
                st.warning(f"🚫 Time ignorado: nome inválido ou ID corrompido → nome='{nome}', id='{tid}'")

        st.write("📋 Times válidos para a Copa:", [times_map[tid]["nome"] for tid in time_ids])

        if len(time_ids) < 2:
            st.warning("⚠️ É preciso ao menos 2 times válidos para iniciar a copa.")
            st.stop()

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
