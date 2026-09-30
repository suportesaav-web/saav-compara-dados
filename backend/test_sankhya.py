import os
from dotenv import load_dotenv
from services.sankhya_service import SankhyaService

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

def test_sankhya_integration():
    CLIENT_ID = os.environ.get("SANKHYA_CLIENT_ID")
    CLIENT_SECRET = os.environ.get("SANKHYA_CLIENT_SECRET")
    X_TOKEN = os.environ.get("SANKHYA_X_TOKEN")
    ENV = os.environ.get("SANKHYA_ENV", "sandbox")

    if not all([CLIENT_ID, CLIENT_SECRET, X_TOKEN]):
        print("ERRO: Faltam variáveis de ambiente no arquivo .env!")
        print("Certifique-se de que SANKHYA_CLIENT_ID, SANKHYA_CLIENT_SECRET e SANKHYA_X_TOKEN estão definidos.")
        return

    print("=========================================")
    print(f"Iniciando testes na API Gateway do Sankhya ({ENV})...")
    print("=========================================\n")

    try:
        service = SankhyaService(
            client_id=CLIENT_ID, 
            client_secret=CLIENT_SECRET, 
            x_token=X_TOKEN, 
            env=ENV
        )
        
        # Teste 1: Autenticação
        print("1. Testando Autenticação (OAuth 2.0)...")
        bearer_token = service.login()
        print(f"SUCESSO: Login bem-sucedido! Bearer Token gerado: {bearer_token[:15]}...\n")
        
        # Teste 2: Buscando Vendas (Ajuste as datas conforme necessário)
        print("2. Testando Consulta de Vendas (DbExplorerSP.executeQuery)...")
        # Ajuste estas datas para um período que você tem certeza que tem dados
        start_date = "01/01/2024" 
        end_date = "31/12/2024"
        
        print(f"   Buscando dados entre {start_date} e {end_date}...")
        sales = service.get_sales(start_date=start_date, end_date=end_date)
        
        print(f"SUCESSO: Consulta bem-sucedida! Retornou {len(sales)} registros.")
        if sales:
            print("   Exibindo os 3 primeiros registros:")
            for s in sales[:3]:
                print(f"   - {s}")
                
    except Exception as e:
        print(f"\nERRO NA INTEGRAÇÃO:")
        print(e)

if __name__ == "__main__":
    test_sankhya_integration()
