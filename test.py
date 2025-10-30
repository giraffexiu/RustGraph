from solana_fcg_tool import SolanaAnalyzer
analyzer = SolanaAnalyzer('./2025-01-pump-science')
result = analyzer.find_symbols('CreateEvent')
if result:
    print(result)
else:
    print("wrong")
