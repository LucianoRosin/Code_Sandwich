"""
Configurações globais para o ambiente Code Sandwich e scripts relacionados.
ATUALIZADO: Configuração padrão para 1000 simulações (robustez estatística)
"""
import os

DEFAULT_GAME_CONFIG = {
    # Configurações do Jogo/Ambiente
    'num_players': 2,              # Número padrão de jogadores (usado em env, simulations, train_ai, example)
    'cards_file': 'cartas.json',   # Arquivo de cartas padrão (usado em env, simulations, train_ai, example, pcg)
    'max_hand_size': 5,            # Tamanho máximo da mão (usado em game)
    'max_turns': 200,              # Limite máximo de turnos por jogo (usado em game, example)

    # Configurações de Simulação/Análise
    'num_simulations': 1000,       # ATUALIZADO: 1000 simulações para robustez estatística
    'log_directory': 'logs',       # Diretório para salvar logs de simulação
    'analysis_directory': 'analises', # Diretório para salvar relatórios e gráficos
    'simulation_log_file': 'simulation_logs_original.csv', # Nome base do arquivo de log

    # Configurações da API Gemini (pode ser deixado como None se usar variável de ambiente)
    'gemini_model_name': "gemini-2.5-flash", # Modelo Gemini a ser usado
    # 'gemini_api_key': None, # Opcional: Colocar a chave aqui diretamente (NÃO RECOMENDADO)

    # Configurações de Análise Pedagógica
    'kcs_file': 'kcs.json',        # Arquivo com definições dos KCs
    'num_cartas_pilar1': 10,       # ATUALIZADO: Mais cartas para análise no Pilar 1 (era 5)
    'acp_report_file': 'RELATORIO_ACP.md', # Nome do arquivo de relatório ACP
    'balance_report_file': 'RELATORIO_BALANCEAMENTO_IA.md' # Nome do arquivo de relatório de Balanceamento IA
}

# Constrói caminhos completos para diretórios e arquivos de log/análise
DEFAULT_GAME_CONFIG['full_simulation_log_path'] = os.path.join(
    DEFAULT_GAME_CONFIG['log_directory'],
    DEFAULT_GAME_CONFIG['simulation_log_file']
)
DEFAULT_GAME_CONFIG['full_acp_report_path'] = os.path.join(
    DEFAULT_GAME_CONFIG['analysis_directory'],
    DEFAULT_GAME_CONFIG['acp_report_file']
)
DEFAULT_GAME_CONFIG['full_balance_report_path'] = os.path.join(
    DEFAULT_GAME_CONFIG['analysis_directory'],
    DEFAULT_GAME_CONFIG['balance_report_file']
)

