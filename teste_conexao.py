from supabase import create_client, Client

# 🔐 Dados do seu projeto Supabase
url = "https://hceqyuvryhtihhbvacyo.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhjZXF5dXZyeWh0aWhoYnZhY3lvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU0NDQ4MDQsImV4cCI6MjA2MTAyMDgwNH0.XW5I3uXrgfOFaw2hGxtbFQO6up9orhGeswZ-u8cYENs"

# 🔗 Cria cliente Supabase
supabase: Client = create_client(url, key)

# 🔍 Teste com a tabela "Times"
try:
    dados = supabase.table("Times").select("*").execute()
    print("✅ Conectado e dados obtidos com sucesso:")
    print(dados.data)
except Exception as e:
    print("❌ Erro ao buscar dados:", e)
