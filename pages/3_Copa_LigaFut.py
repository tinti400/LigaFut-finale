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
            m_id = times[i]
            v_id = times[i + 1]
            if is_valid_uuid(m_id) and is_valid_uuid(v_id):
                jogo_id = str(uuid.uuid4())
                jogos.append({
                    "id": jogo_id,
                    "fase": fase,
                    "numero": len(jogos) + 1,
                    "id_mandante": m_id,
                    "id_visitante": v_id,
                    "gols_mandante": None,
                    "gols_visitante": None
                })
            else:
                st.warning(f"🚫 Jogo ignorado: mandante='{m_id}', visitante='{v_id}'")
        else:
            st.warning(f"⚠️ Time sem adversário: {times[i]}")
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
            nome = info.get("nome", "").strip()
            if is_valid_uuid(tid) and nome != "":
                time_ids.append(tid)
            else:
                st.warning(f"🚫 Time ignorado: nome='{nome}', id='{tid}' (inválido)")

        st.write("📋 Times válidos para a Copa:")
        for tid in time_ids:
            nome = times_map.get(tid, {}).get("nome", "Desconhecido")
            st.write(f"🟩 {nome} — ID: '{tid}'")

        for i, tid in enumerate(time_ids):
            if not is_valid_uuid(tid):
                st.error(f"❌ time_ids[{i}] contém UUID inválido: '{tid}'")

        if len(time_ids) < 2:
            st.warning("⚠️ É preciso ao menos 2 times válidos para iniciar a copa.")
            st.stop()

        supabase.table("copa_ligafut").delete().neq("id", "").execute()
        fase = "Preliminar" if len(time_ids) > 16 else "Oitavas"

        st.write("🎯 Lista de IDs para gerar confrontos:", time_ids)
        jogos = gerar_confrontos(time_ids, fase)

        for j in jogos:
            m = j.get("id_mandante", "")
            v = j.get("id_visitante", "")
            if not is_valid_uuid(m):
                st.error(f"❌ ID do mandante inválido: '{m}' no jogo: {j}")
            if not is_valid_uuid(v):
                st.error(f"❌ ID do visitante inválido: '{v}' no jogo: {j}")
        st.write("🧪 Jogos preparados:", jogos)

        jogos_filtrados = []
        for jogo in jogos:
            if (
                is_valid_uuid(jogo.get("id_mandante", ""))
                and is_valid_uuid(jogo.get("id_visitante", ""))
            ):
                jogos_filtrados.append(jogo)
            else:
                st.warning(f"🚫 Jogo removido antes de salvar: {jogo}")

        import json

# 🔒 Reforço: garantir que todos jogos tenham IDs válidos
jogos_filtrados = [
    j for j in jogos_filtrados
    if is_valid_uuid(j.get("id", ""))
    and is_valid_uuid(j.get("id_mandante", ""))
    and is_valid_uuid(j.get("id_visitante", ""))
]

# 💾 Inserção segura
supabase.table("copa_ligafut").insert({
    "numero": 1,
    "fase": fase,
    "jogos": json.loads(json.dumps(jogos_filtrados))
}).execute()

        st.success("✅ Primeira fase criada com sucesso!")
        st.rerun()

    except Exception as e:
        st.error(f"Erro ao gerar a copa: {e}")




