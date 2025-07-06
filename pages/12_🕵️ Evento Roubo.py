# 🔘 Botão para iniciar o evento (aparece apenas para admin se não estiver ativo)
if eh_admin and not ativo:
    st.subheader("🟢 Iniciar Evento de Roubo")

    # 🧮 Definir tempo e limite de bloqueios
    tempo_rodada = st.number_input("⏱️ Tempo por rodada (minutos)", min_value=1, max_value=10, value=3)
    limite_bloqueios = st.number_input("🛡️ Quantidade de jogadores que cada time pode proteger", min_value=1, max_value=6, value=4)

    if st.button("🚀 Iniciar Evento"):
        # Sorteia a ordem dos times participantes
        todos_times = supabase.table("times").select("id", "nome").execute().data
        ordem_sorteada = [t["id"] for t in todos_times]
        random.shuffle(ordem_sorteada)

        # Calcula o timestamp final da 1ª rodada
        agora = datetime.utcnow()
        fim_primeira_vez = (agora + pd.Timedelta(minutes=tempo_rodada)).isoformat()

        supabase.table("configuracoes").update({
            "ativo": True,
            "fase": "bloqueio",
            "ordem": ordem_sorteada,
            "vez": "0",
            "concluidos": [],
            "roubos": {},
            "bloqueios": {},
            "ja_perderam": {},
            "tempo_rodada": tempo_rodada,
            "limite_bloqueios": limite_bloqueios,
            "fim_vez": fim_primeira_vez,
            "finalizado": False
        }).eq("id", ID_CONFIG).execute()

        st.success("🚀 Evento iniciado com sucesso! Fase de bloqueio liberada.")
        st.experimental_rerun()
if fase == "bloqueio":
    st.header("🛡️ Fase de Proteção dos Jogadores")

    st.info(f"Cada time pode proteger até **{limite_bloqueios} jogadores**. Após essa fase, começa o roubo. Proteções salvas não podem ser alteradas.")

    # Verifica jogadores já protegidos pelo time
    jogadores_bloqueados = bloqueios.get(id_time, [])

    # Puxa o elenco do time logado
    elenco_resp = supabase.table("elencos").select("*").eq("id_time", id_time).execute()
    elenco = elenco_resp.data if elenco_resp.data else []

    if not elenco:
        st.warning("Seu elenco está vazio.")
        st.stop()

    # Interface de seleção dos jogadores protegidos
    nomes_jogadores = [j["nome"] for j in elenco]
    selecionados = st.multiselect("🔒 Selecione os jogadores a proteger", nomes_jogadores, default=jogadores_bloqueados)

    # Verifica se passou do limite
    if len(selecionados) > limite_bloqueios:
        st.error(f"Você só pode proteger até {limite_bloqueios} jogadores.")
        st.stop()

    # Botão para salvar bloqueios
    if st.button("✅ Confirmar Proteção"):
        bloqueios[id_time] = selecionados
        supabase.table("configuracoes").update({
            "bloqueios": bloqueios
        }).eq("id", ID_CONFIG).execute()
        st.success("Jogadores protegidos com sucesso!")

    # ADMIN pode avançar para próxima fase
    if eh_admin:
        st.divider()
        if st.button("➡️ Avançar para Fase de Roubo"):
            # Define fim da vez 0
            agora = datetime.utcnow()
            fim_primeira_vez = (agora + pd.Timedelta(minutes=tempo_rodada)).isoformat()

            supabase.table("configuracoes").update({
                "fase": "acao",
                "fim_vez": fim_primeira_vez
            }).eq("id", ID_CONFIG).execute()
            st.success("Fase de roubo iniciada.")
            st.experimental_rerun()
# ✅ Fase: Ação
elif fase == "acao":
    st.title("🎯 Fase de Roubo")
    evento = supabase.table("configuracoes").select("*").eq("id", ID_CONFIG).execute().data[0]
    ordem = evento["ordem"]
    vez = int(evento["vez"])
    inicio_vez = datetime.fromisoformat(evento.get("inicio_vez"))
    tempo_fase = evento.get("tempo_fase", 180)
    tempo_restante = max(0, int(tempo_fase - (datetime.utcnow() - inicio_vez).total_seconds()))

    if vez >= len(ordem):
        st.success("✅ Evento concluído!")
        supabase.table("configuracoes").update({"ativo": False, "fase": "finalizado"}).eq("id", ID_CONFIG).execute()
        st.stop()

    id_vez = ordem[vez]
    nome_time_vez = supabase.table("times").select("nome").eq("id", id_vez).execute().data[0]["nome"]

    st.info(f"🎲 Vez do time: **{nome_time_vez}**")
    st.warning(f"⏳ Tempo restante: {tempo_restante} segundos")

    # Se não for o time da vez e não for admin, aguarda
    if id_vez != id_time and not eh_admin:
        st.info("⏳ Aguarde sua vez. Somente o time da vez pode interagir.")
        st.stop()

    # Exibir times disponíveis para roubo
    times = supabase.table("times").select("id", "nome").neq("id", id_time).execute().data
    time_alvo_nome = st.selectbox("Selecione o time para visualizar elenco:", [t["nome"] for t in times])
    id_alvo = next(t["id"] for t in times if t["nome"] == time_alvo_nome)

    # Carregar bloqueios
    bloqueios = evento.get("bloqueios", {})
    bloqueados = [j["nome"] for j in bloqueios.get(id_alvo, [])]

    # Buscar elenco do time alvo
    elenco = supabase.table("elenco").select("*").eq("id_time", id_alvo).execute().data

    for jogador in elenco:
        nome, posicao, valor = jogador["nome"], jogador["posicao"], jogador["valor"]
        val_roubo = int(valor * 0.5)

        if nome in bloqueados:
            st.markdown(f"🔒 **{nome}** ({posicao}) - Protegido")
        else:
            col1, col2 = st.columns([4, 1])
            col1.markdown(f"**{nome}** ({posicao}) - R$ {val_roubo:,.0f}")
            if col2.button("⚡ Roubar", key=nome):
                # Validar saldo
                saldo_data = supabase.table("times").select("saldo").eq("id", id_time).execute().data
                saldo = saldo_data[0]["saldo"] if saldo_data else 0

                if saldo < val_roubo:
                    st.error("❌ Saldo insuficiente.")
                else:
                    # Atualizar saldo do comprador
                    novo_saldo = saldo - val_roubo
                    supabase.table("times").update({"saldo": novo_saldo}).eq("id", id_time).execute()

                    # Inserir jogador no elenco do novo time
                    novo_jogador = jogador.copy()
                    novo_jogador["id"] = str(uuid.uuid4())
                    novo_jogador["id_time"] = id_time
                    supabase.table("elenco").insert(novo_jogador).execute()

                    # Remover do time antigo
                    supabase.table("elenco").delete().eq("id", jogador["id"]).execute()

                    # Registrar movimentação
                    descricao = f"Roubou {nome} ({posicao}) do time {time_alvo_nome} por R$ {val_roubo:,.0f}"
                    supabase.table("movimentacoes_financeiras").insert({
                        "id": str(uuid.uuid4()),
                        "id_time": id_time,
                        "tipo": "roubo",
                        "descricao": descricao,
                        "valor": val_roubo,
                        "data": datetime.now().isoformat()
                    }).execute()

                    st.success(f"✅ {nome} foi roubado com sucesso!")
                    st.rerun()

    # Ações do admin
    if eh_admin:
        if st.button("⏭️ Pular vez"):
            supabase.table("configuracoes").update({
                "vez": vez + 1,
                "inicio_vez": str(datetime.utcnow())
            }).eq("id", ID_CONFIG).execute()
            st.warning("🔁 Vez pulada pelo admin.")
            st.rerun()

    # Botão para finalizar vez
    if st.button("✅ Finalizar minha vez"):
        supabase.table("configuracoes").update({
            "vez": vez + 1,
            "inicio_vez": str(datetime.utcnow())
        }).eq("id", ID_CONFIG).execute()
        st.success("🚩 Vez finalizada.")
        st.rerun()
# ✅ Fase Finalizada
elif fase == "finalizado":
    st.title("🏁 Evento Finalizado")
    st.success("✅ O Evento de Roubo foi encerrado com sucesso!")

    # Exibe resumo final se desejar
    st.markdown("### 📋 Resumo dos Jogadores Roubados")

    dados_mov = supabase.table("movimentacoes_financeiras").select("*").eq("tipo", "roubo").order("data", desc=True).execute().data
    if dados_mov:
        df = pd.DataFrame(dados_mov)
        df["valor"] = df["valor"].apply(lambda v: f"R$ {v:,.0f}".replace(",", "."))
        df["data"] = pd.to_datetime(df["data"]).dt.strftime("%d/%m/%Y %H:%M")
        df = df[["data", "descricao", "valor"]]
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum roubo registrado.")


