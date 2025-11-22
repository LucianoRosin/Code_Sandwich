# ... (imports como antes, EXCETO configure_gemini) ...
import matplotlib
matplotlib.use('Agg')
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json
import asyncio
# Importa APENAS load_json_data e call_gemini_api
from utils import load_json_data, call_gemini_api
import numpy as np

# --- Constantes ---
LOG_DIR = 'logs'
ANALYSIS_DIR = 'analises'
ORIGINAL_LOG = os.path.join(LOG_DIR, 'simulation_logs_original.csv')
AI_ANALYSIS_FILE = os.path.join(ANALYSIS_DIR, 'RELATORIO_BALANCEAMENTO_IA.md')

# --- Funções Auxiliares, Plotagem, Conversão ---
# (load_simulation_log, set_plot_style, plot_game_duration, plot_recipe_completion, convert_to_native_types SEM ALTERAÇÕES)
# ... (código dessas funções) ...
def load_simulation_log(log_file):
    """Carrega o log de simulação CSV com tratamento de erro."""
    if not os.path.exists(log_file):
        print(f"DEBUG (analyze_results): Log de simulação não encontrado: {log_file}")
        return None
    try:
        df = pd.read_csv(log_file)
        if df.empty:
            print(f"DEBUG (analyze_results): Log de simulação está vazio: {log_file}")
            return None
        return df
    except pd.errors.EmptyDataError:
        print(f"DEBUG (analyze_results): Log de simulação está vazio (EmptyDataError): {log_file}")
        return None
    except Exception as e:
        print(f"ERRO (analyze_results): Erro ao ler CSV {log_file}: {e}")
        return None

def set_plot_style():
    """Define o estilo visual para os gráficos."""
    sns.set_theme(style="whitegrid", palette="muted")
    plt.rcParams.update({
        'figure.figsize': (10, 6),
        'axes.titlesize': 16,
        'axes.labelsize': 12,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10
    })

def plot_game_duration(df, log_file, suffix):
    """Plota a distribuição da duração dos jogos a partir de um DataFrame."""
    if df is None or 'turns' not in df.columns:
        print(f"DEBUG (analyze_results): Dados insuficientes para gráfico de duração ({suffix}).")
        return
    if df['turns'].isnull().all():
        print(f"DEBUG (analyze_results): Coluna 'turns' sem dados válidos ({suffix}). Pulando gráfico.")
        return

    plt.figure()
    try:
        sns.histplot(df['turns'], kde=True, bins=20)
        plt.title(f'Distribuição da Duração do Jogo (em Turnos) - {suffix}')
        plt.xlabel('Número de Turnos')
        plt.ylabel('Frequência')
        plt.tight_layout()
        filepath = os.path.join(ANALYSIS_DIR, f'game_duration_distribution_{suffix}.png')
        plt.savefig(filepath)
        plt.close()
        print(f"Gráfico '{os.path.basename(filepath)}' salvo.")
    except Exception as e:
        print(f"ERRO (analyze_results): Erro ao gerar gráfico de duração para {log_file}: {e}")
        plt.close()

def plot_recipe_completion(df, log_file, suffix):
    """Plota a frequência de conclusão de receitas a partir de um DataFrame."""
    if df is None or 'winner' not in df.columns or 'winning_recipe' not in df.columns:
        print(f"DEBUG (analyze_results): Dados insuficientes para gráfico de receitas ({suffix}).")
        return

    df_winners = df[df['winner'] != 'Draw'].copy()
    if df_winners.empty:
        print(f"DEBUG (analyze_results): Nenhum vencedor encontrado para análise de receitas ({suffix}).")
        return
    if df_winners['winning_recipe'].isnull().all():
        print(f"DEBUG (analyze_results): Coluna 'winning_recipe' sem dados válidos ({suffix}). Pulando gráfico.")
        return

    plt.figure(figsize=(12, max(8, len(df_winners['winning_recipe'].unique()) * 0.5)))
    try:
        order = df_winners['winning_recipe'].value_counts().index
        sns.countplot(y=df_winners['winning_recipe'], order=order)
        plt.title(f'Frequência de Conclusão de Receitas - {suffix}')
        plt.xlabel('Número de Conclusões')
        plt.ylabel('Receita Final')
        plt.tight_layout()
        filepath = os.path.join(ANALYSIS_DIR, f'recipe_completion_frequency_{suffix}.png')
        plt.savefig(filepath)
        plt.close()
        print(f"Gráfico '{os.path.basename(filepath)}' salvo.")
    except Exception as e:
        print(f"ERRO (analyze_results): Erro ao gerar gráfico de receitas para {log_file}: {e}")
        plt.close()

def convert_to_native_types(data):
    if isinstance(data, dict):
        return {k: convert_to_native_types(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_to_native_types(i) for i in data]
    elif isinstance(data, (np.int_, np.intc, np.intp, np.int8,
                           np.int16, np.int32, np.int64, np.uint8,
                           np.uint16, np.uint32, np.uint64)):
        return int(data)
    elif isinstance(data, (np.float64, np.float16, np.float32,
                           np.float64)):
        if np.isnan(data) or np.isinf(data):
             return None
        return float(data)
    elif isinstance(data, np.ndarray):
        return data.tolist()
    elif isinstance(data, pd.Timestamp):
        return data.isoformat()
    return data

# --- Função de Análise por IA ---
# (interpret_balance_data_with_ia sem alterações)
# ... (código da função) ...
async def interpret_balance_data_with_ia(model, df, suffix):
    """Gera prompts com estatísticas e chama a API Gemini para interpretação."""
    if df is None or df.empty:
        return f"## Análise IA ({suffix})\n\nDados insuficientes para análise.\n"

    interpretation = f"## Análise de Balanceamento por IA ({suffix})\n\n"
    duration_stats = {}
    recipe_stats = {}

    # --- Prepara Estatísticas de Duração ---
    if 'turns' in df.columns and not df['turns'].isnull().all():
        turns_data = df['turns']
        duration_stats = {
            "Média": float(turns_data.mean()) if not pd.isna(turns_data.mean()) else None,
            "Mediana": int(turns_data.median()) if not pd.isna(turns_data.median()) else None,
            "Mínimo": int(turns_data.min()) if not pd.isna(turns_data.min()) else None,
            "Máximo": int(turns_data.max()) if not pd.isna(turns_data.max()) else None,
            "Desvio Padrão": float(turns_data.std()) if not pd.isna(turns_data.std()) else None
        }
        interpretation += "### Duração das Partidas\n\n"
        for key, value in duration_stats.items():
            if value is not None:
                interpretation += f"- {key}: {value:.2f}\n" if isinstance(value, float) else f"- {key}: {value}\n"
            else:
                interpretation += f"- {key}: N/A\n"
        interpretation += "\n"
    else:
        interpretation += "### Duração das Partidas\n\nDados não disponíveis ou inválidos.\n"

    # --- Prepara Estatísticas de Receitas ---
    if 'winner' in df.columns and 'winning_recipe' in df.columns:
        df_winners = df[df['winner'] != 'Draw']
        if not df_winners.empty and not df_winners['winning_recipe'].isnull().all():
            recipe_counts = df_winners['winning_recipe'].value_counts()
            total_wins = len(df_winners)
            unique_recipes = len(recipe_counts)
            top_10_dict = convert_to_native_types(recipe_counts.head(10).to_dict())
            recipe_stats = {
                "Total Vitórias": int(total_wins),
                "Receitas Únicas Vencedoras": int(unique_recipes),
                "Top 10": top_10_dict
            }
            interpretation += "\n### Frequência das Receitas\n\n"
            interpretation += f"- Número total de vitórias (sem empates): {total_wins}\n"
            interpretation += f"- Número de receitas únicas concluídas: {unique_recipes}\n"
            interpretation += "- Top 3 Receitas mais concluídas:\n"
            for recipe, count in recipe_counts.head(3).items():
                interpretation += f"  - {recipe}: {count} ({count/total_wins:.1%})\n"
            interpretation += "\n"
        else:
             interpretation += "\n### Frequência das Receitas\n\nDados não disponíveis ou inválidos.\n"
    else:
        interpretation += "\n### Frequência das Receitas\n\nColunas necessárias não encontradas.\n"

    # --- Chama IA para Interpretação ---
    if model: # Verifica se o modelo foi passado corretamente
        print(f"DEBUG (analyze_results): Modelo Gemini VÁLIDO detectado para '{suffix}'. Chamando API...")
        tasks = []
        if duration_stats:
            duration_stats_native = convert_to_native_types(duration_stats)
            prompt_duration = f"""
            Analise os dados de duração das partidas do jogo 'Code Sandwich' (baralho: {suffix}):
            {json.dumps(duration_stats_native, indent=2, ensure_ascii=False)}
            Comente em um parágrafo sobre o ritmo do jogo. A duração parece razoável? Há muita variabilidade? A experiência do jogador parece consistente em termos de tempo? Responda em português do Brasil.
            """
            tasks.append(call_gemini_api(model, prompt_duration))

        if recipe_stats:
            prompt_recipes = f"""
            Analise os dados de frequência das receitas vencedoras no jogo 'Code Sandwich' (baralho: {suffix}):
            {json.dumps(recipe_stats, indent=2, ensure_ascii=False)}
            Comente em um parágrafo sobre a variedade de estratégias vencedoras e o balanceamento entre as receitas. Todas parecem viáveis? Existe alguma dominante ou muito difícil? Responda em português do Brasil.
            """
            tasks.append(call_gemini_api(model, prompt_recipes))

        if tasks:
             results_ia = await asyncio.gather(*tasks)
             if duration_stats:
                 interpretation += f"**Interpretação da IA (Duração):** {results_ia.pop(0)}\n"
             if recipe_stats:
                 interpretation += f"\n**Interpretação da IA (Receitas):** {results_ia.pop(0)}\n"
        else:
             interpretation += "**Interpretação da IA:** Nenhuma estatística válida encontrada para análise.\n"

    else: # Se model for None
        print(f"DEBUG (analyze_results): Modelo Gemini INVÁLIDO (None) detectado para '{suffix}'. Pulando chamada API.") # Mensagem ajustada
        interpretation += "**Interpretação da IA:** Pulada (Modelo não configurado).\n"

    return interpretation


# --- Função Principal Assíncrona (Reconfigura API) ---
async def main(gemini_model=None, config=None):
    """Função principal: carrega dados, gera gráficos e análises de IA."""
    # Se modelo for passado, usa ele; senão tenta configurar localmente
    print("Iniciando analyze_results.py (Foco: Balanceamento Mecânico + Análise IA)...")
    set_plot_style()
    os.makedirs(ANALYSIS_DIR, exist_ok=True)

    # Se modelo não foi passado, tenta configurar localmente
    if gemini_model is None:
        from utils import configure_gemini
        print("DEBUG (analyze_results): Configurando Gemini localmente...")
        gemini_model = configure_gemini()
        if gemini_model:
            print("DEBUG (analyze_results): Modelo configurado com sucesso.")
        else:
            print("DEBUG (analyze_results): Falha ao configurar modelo.")
    else:
        print("DEBUG (analyze_results): Usando modelo Gemini passado como parâmetro.")

    ai_analysis_content = "# Relatório de Análise de Balanceamento (IA)\n\n"

    # Processa APENAS o log original
    log_file = ORIGINAL_LOG
    suffix = 'original'

    print(f"\nAnalisando logs do baralho '{suffix}' ({os.path.basename(log_file)})...")
    df = load_simulation_log(log_file)
    interpretation = f"## Análise IA ({suffix})\n\n"

    if df is not None:
        plot_game_duration(df, log_file, suffix)
        plot_recipe_completion(df, log_file, suffix)

        print(f"DEBUG (analyze_results): Chamando interpret_balance_data_with_ia para '{suffix}'...")
        # Passa o modelo configurado LOCALMENTE
        interpretation += await interpret_balance_data_with_ia(gemini_model, df, suffix)

    else:
        interpretation += f"Pulada: Não foi possível carregar ou processar '{os.path.basename(log_file)}'.\n"
        print(f"Gráficos e análise IA para '{suffix}' pulados.")

    ai_analysis_content += interpretation

    try:
        with open(AI_ANALYSIS_FILE, 'w', encoding='utf-8') as f:
            f.write(ai_analysis_content)
        print(f"\nRelatório de análise da IA salvo em: {AI_ANALYSIS_FILE}")
    except IOError as e:
        print(f"ERRO (analyze_results): Não foi possível salvar o relatório da IA: {e}")

    print(f"\nGráficos de balanceamento salvos em: {ANALYSIS_DIR}")

if __name__ == "__main__":
    asyncio.run(main())