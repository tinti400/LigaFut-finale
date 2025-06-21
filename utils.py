# 🔒 Verificação de login
def verificar_login():
    if "usuario_id" not in st.session_state or not st.session_state["usuario_id"]:
        st.warning("Você precisa estar logado para acessar esta página.")
        st.stop()

# 🔒 Verificação de sessão única
def verificar_sessao():
    if "usuario_id" not in st.session_state or "session_id" not in st.session_state:
        st.warning("Você precisa estar logado.")
        st.stop()

    try:
        res = supabase.table("usuarios").select("session_id").eq("id", st.session_state["usuario_id"]).execute()
        if res.data and res.data[0]["session_id"] != st.session_state["session_id"]:
            st.error("⚠️ Sua sessão foi encerrada em outro dispositivo.")
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.stop()
    except Exception as e:
        st.error(f"Erro ao verificar sessão: {e}")
        st.stop()

# 💰 Registrar compra ou venda de jogador
def registrar_movimentacao(id_time, jogador, tipo, categoria, valor, origem=None, destino=None):
    try:
        categoria = categoria.strip().lower()
        tipo = tipo.strip().lower()

        if categoria not in ["compra", "venda"]:
            st.warning("⚠️ Categoria inválida. Use 'compra' ou 'venda'.")
            return

        res = supabase.table("times").select("saldo").eq("id", id_time).execute()
        if not res.data:
            st.error(f"❌ Time com ID '{id_time}' não encontrado.")
            return

        saldo_atual = res.data[0].get("saldo")
        if saldo_atual is None:
            st.error("❌ Saldo atual não encontrado para este time.")
            return

        valor = int(valor)
        novo_saldo = saldo_atual - valor if categoria == "compra" else saldo_atual + valor
        novo_saldo = int(novo_saldo)

        supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

        agora = datetime.now(pytz.timezone("America/Sao_Paulo")).isoformat()

        registro = {
            "id_time": id_time,
            "jogador": jogador,
            "tipo": tipo,
            "categoria": categoria,
            "valor": valor,
            "data": agora,
            "origem": origem,
            "destino": destino
        }

        supabase.table("movimentacoes").insert(registro).execute()
        st.success(f"✅ Movimentação registrada com sucesso. Novo saldo: R$ {novo_saldo:,.0f}".replace(",", "."))

    except Exception as e:
        st.error(f"❌ Erro ao registrar movimentação: {e}")

# 💰 Registrar movimentação simples (ajustes, salários, prêmios, multas)
def registrar_movimentacao_simples(id_time, valor, descricao):
    try:
        res = supabase.table("times").select("saldo").eq("id", id_time).execute()
        if not res.data:
            st.error("❌ Time não encontrado.")
            return

        saldo_atual = res.data[0].get("saldo", 0)
        valor = int(valor)
        novo_saldo = int(saldo_atual + valor)

        supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

        agora = datetime.now(pytz.timezone("America/Sao_Paulo")).isoformat()

        registro = {
            "id_time": id_time,
            "jogador": None,
            "tipo": "sistema",
            "categoria": "ajuste",
            "valor": abs(valor),
            "data": agora,
            "origem": None,
            "destino": None,
            "descricao": descricao
        }

        supabase.table("movimentacoes").insert(registro).execute()
        st.success(f"✅ {descricao} registrada. Novo saldo: R$ {novo_saldo:,.0f}".replace(",", "."))

    except Exception as e:
        st.error(f"Erro ao registrar movimentação simples: {e}")

# 📉 Pagar salários (1% do valor de cada jogador)
def pagar_salarios(id_time):
    try:
        elenco = supabase.table("elenco").select("valor").eq("id_time", id_time).execute()
        if not elenco.data:
            st.warning("🔍 Elenco não encontrado para este time.")
            return

        total_salarios = sum(int(j.get("valor", 0) * 0.01) for j in elenco.data)

        if total_salarios > 0:
            registrar_movimentacao_simples(id_time, -total_salarios, "Pagamento de salários")
        else:
            st.info("💡 Nenhum salário a pagar (valores zerados).")

    except Exception as e:
        st.error(f"Erro ao pagar salários: {e}")

# 🏆 Premiação por resultado (escala divisional + gols)
def pagar_salario_e_premiacao_resultado(id_time_m, id_time_v, gols_m, gols_v, divisao):
    try:
        divisao = str(divisao)
        tabela_premios = {
            "1": {"vitoria": 12_000_000, "empate": 9_000_000, "derrota": 4_500_000},
            "2": {"vitoria": 9_000_000,  "empate": 6_000_000, "derrota": 3_000_000},
            "3": {"vitoria": 6_000_000,  "empate": 4_500_000, "derrota": 2_000_000}
        }

        def premiar_time(id_time, resultado, gols_feitos, gols_sofridos):
            base = tabela_premios.get(divisao, {}).get(resultado, 0)
            bonus = gols_feitos * 200_000
            desconto = gols_sofridos * 25_000
            total = base + bonus - desconto
            registrar_movimentacao_simples(id_time, total, f"Premiação por {resultado}")
            pagar_salarios(id_time)

        if gols_m > gols_v:
            premiar_time(id_time_m, "vitoria", gols_m, gols_v)
            premiar_time(id_time_v, "derrota", gols_v, gols_m)
        elif gols_v > gols_m:
            premiar_time(id_time_v, "vitoria", gols_v, gols_m)
            premiar_time(id_time_m, "derrota", gols_m, gols_v)
        else:
            premiar_time(id_time_m, "empate", gols_m, gols_v)
            premiar_time(id_time_v, "empate", gols_v, gols_m)

    except Exception as e:
        st.error(f"Erro ao aplicar premiação e salários: {e}")
