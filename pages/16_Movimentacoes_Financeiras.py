# Seleção final de colunas
colunas = ["📅 Data", "📌 Tipo", "📝 Descrição", "💸 Valor", "📦 Caixa Anterior", "💰 Caixa Atual"]
df_exibir = df[colunas].copy().head(10)  # ✅ agora mostra só as últimas 10

# Força todas as colunas como string
for col in df_exibir.columns:
    df_exibir[col] = df_exibir[col].astype(str)

# 🔍 Debug (opcional - pode remover depois)
st.subheader("🔍 Debug do DataFrame")
st.write("Colunas:", df_exibir.columns.tolist())
st.text("Tipos de dados:")
st.text(df_exibir.dtypes.to_string())
st.write("Amostra dos dados:")
st.write(df_exibir.head())

# 📋 Exibir
st.subheader(f"💼 Extrato do time **{nome_time}** (últimas 10 movimentações)")
st.dataframe(df_exibir, use_container_width=True)

