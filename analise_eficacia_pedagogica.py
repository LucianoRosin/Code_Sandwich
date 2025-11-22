"""
Análise de Eficácia Pedagógica do Code Sandwich
Prova que o jogo ensina conceitos de programação
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json
from typing import Dict, List, Tuple

def analisar_eficacia_pedagogica(log_file: str, output_dir: str = 'analises') -> Dict:
    """
    Analisa a eficácia pedagógica do jogo baseado em logs de simulações.
    
    Args:
        log_file: Caminho para o arquivo de logs pedagógicos
        output_dir: Diretório para salvar resultados
        
    Returns:
        Dict com métricas de eficácia
    """
    
    print("\n" + "="*70)
    print("ANÁLISE DE EFICÁCIA PEDAGÓGICA")
    print("="*70)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Carregar dados
    print(f"\n[1/6] Carregando logs de {log_file}...")
    df = pd.read_csv(log_file)
    
    print(f"  Total de ações: {len(df)}")
    print(f"  Jogos únicos: {df['game_id'].nunique()}")
    print(f"  Jogadores únicos: {df['player_id'].nunique()}")
    
    # 1. Curva de Aprendizado
    print("\n[2/6] Gerando curva de aprendizado...")
    curva_aprendizado = gerar_curva_aprendizado(df, output_dir)
    
    # 2. Análise por Persona
    print("\n[3/6] Analisando performance por persona...")
    analise_personas = analisar_por_persona(df, output_dir)
    
    # 3. Análise por KC
    print("\n[4/6] Analisando maestria por KC...")
    analise_kcs = analisar_por_kc(df, output_dir)
    
    # 4. Progressão ao Longo do Tempo
    print("\n[5/6] Analisando progressão temporal...")
    progressao = analisar_progressao_temporal(df, output_dir)
    
    # 5. Análise de Receitas
    print("\n[6/6] Analisando eficácia de receitas...")
    analise_receitas = analisar_receitas(df, output_dir)
    
    # Compilar relatório
    relatorio = {
        'metadata': {
            'total_acoes': len(df),
            'total_jogos': int(df['game_id'].nunique()),
            'total_jogadores': int(df['player_id'].nunique())
        },
        'curva_aprendizado': curva_aprendizado,
        'analise_personas': analise_personas,
        'analise_kcs': analise_kcs,
        'progressao_temporal': progressao,
        'analise_receitas': analise_receitas
    }
    
    # Salvar relatório
    relatorio_path = os.path.join(output_dir, 'eficacia_pedagogica.json')
    with open(relatorio_path, 'w', encoding='utf-8') as f:
        json.dump(relatorio, f, indent=2, ensure_ascii=False)
    
    print(f"\n[OK] Relatorio salvo em: {relatorio_path}")
    
    # Imprimir resumo
    imprimir_resumo(relatorio)
    
    return relatorio


def gerar_curva_aprendizado(df: pd.DataFrame, output_dir: str) -> Dict:
    """Gera curva de aprendizado por persona."""
    
    plt.figure(figsize=(12, 6))
    
    resultados = {}
    
    for persona in ['Novice', 'Intermediate', 'Expert']:
        persona_df = df[df['persona'] == persona]
        
        if len(persona_df) == 0:
            continue
        
        # Taxa de sucesso por jogo
        success_by_game = persona_df.groupby('game_id')['success'].mean()
        
        # Suavizar com média móvel
        window = min(10, len(success_by_game) // 5)
        if window > 1:
            smoothed = success_by_game.rolling(window=window, center=True).mean()
        else:
            smoothed = success_by_game
        
        plt.plot(smoothed.index, smoothed.values, label=persona, linewidth=2, alpha=0.8)
        
        # Calcular melhoria
        inicio = success_by_game.iloc[:len(success_by_game)//4].mean()
        fim = success_by_game.iloc[-len(success_by_game)//4:].mean()
        melhoria = ((fim - inicio) / inicio * 100) if inicio > 0 else 0
        
        resultados[persona] = {
            'taxa_inicial': float(inicio),
            'taxa_final': float(fim),
            'melhoria_percentual': float(melhoria)
        }
    
    plt.xlabel('Jogo', fontsize=12)
    plt.ylabel('Taxa de Sucesso', fontsize=12)
    plt.title('Curva de Aprendizado por Persona', fontsize=14, fontweight='bold')
    plt.legend(fontsize=11)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'curva_aprendizado.png'), dpi=300)
    plt.close()
    
    return resultados


def analisar_por_persona(df: pd.DataFrame, output_dir: str) -> Dict:
    """Analisa performance por persona."""
    
    resultados = {}
    
    for persona in ['Novice', 'Intermediate', 'Expert']:
        persona_df = df[df['persona'] == persona]
        
        if len(persona_df) == 0:
            continue
        
        resultados[persona] = {
            'taxa_sucesso': float(persona_df['success'].mean()),
            'taxa_otimalidade': float(persona_df['optimal_action'].mean()),
            'turnos_medio_por_jogo': float(persona_df.groupby('game_id')['turn'].max().mean()),
            'total_acoes': int(len(persona_df))
        }
    
    # Gráfico de comparação
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    personas = list(resultados.keys())
    
    # Taxa de Sucesso
    axes[0].bar(personas, [resultados[p]['taxa_sucesso'] for p in personas], 
                color=['#e74c3c', '#f39c12', '#27ae60'])
    axes[0].set_ylabel('Taxa de Sucesso')
    axes[0].set_title('Taxa de Sucesso por Persona')
    axes[0].set_ylim([0, 1])
    
    # Taxa de Otimalidade
    axes[1].bar(personas, [resultados[p]['taxa_otimalidade'] for p in personas],
                color=['#e74c3c', '#f39c12', '#27ae60'])
    axes[1].set_ylabel('Taxa de Ações Ótimas')
    axes[1].set_title('Otimalidade por Persona')
    axes[1].set_ylim([0, 1])
    
    # Turnos Médios
    axes[2].bar(personas, [resultados[p]['turnos_medio_por_jogo'] for p in personas],
                color=['#e74c3c', '#f39c12', '#27ae60'])
    axes[2].set_ylabel('Turnos Médios')
    axes[2].set_title('Duração Média dos Jogos')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'comparacao_personas.png'), dpi=300)
    plt.close()
    
    return resultados


def analisar_por_kc(df: pd.DataFrame, output_dir: str) -> Dict:
    """Analisa maestria por Knowledge Component."""
    
    # Expandir KCs (podem estar em formato de lista)
    kc_data = []
    
    for _, row in df.iterrows():
        if pd.notna(row['kcs_involved']) and row['kcs_involved'] != '[]':
            kcs = eval(row['kcs_involved']) if isinstance(row['kcs_involved'], str) else row['kcs_involved']
            for kc in kcs:
                kc_data.append({
                    'kc': kc,
                    'persona': row['persona'],
                    'success': row['success']
                })
    
    if len(kc_data) == 0:
        return {}
    
    kc_df = pd.DataFrame(kc_data)
    
    # Taxa de sucesso por KC e persona
    resultados = {}
    
    for kc in kc_df['kc'].unique():
        kc_subset = kc_df[kc_df['kc'] == kc]
        resultados[kc] = {}
        
        for persona in ['Novice', 'Intermediate', 'Expert']:
            persona_subset = kc_subset[kc_subset['persona'] == persona]
            if len(persona_subset) > 0:
                resultados[kc][persona] = float(persona_subset['success'].mean())
    
    # Heatmap
    if resultados:
        kcs = list(resultados.keys())
        personas = ['Novice', 'Intermediate', 'Expert']
        
        matrix = np.zeros((len(kcs), len(personas)))
        
        for i, kc in enumerate(kcs):
            for j, persona in enumerate(personas):
                matrix[i, j] = resultados[kc].get(persona, 0)
        
        plt.figure(figsize=(10, max(6, len(kcs) * 0.5)))
        sns.heatmap(matrix, annot=True, fmt='.2f', cmap='RdYlGn', 
                    xticklabels=personas, yticklabels=kcs,
                    vmin=0, vmax=1, cbar_kws={'label': 'Taxa de Sucesso'})
        plt.title('Maestria por KC e Persona', fontsize=14, fontweight='bold')
        plt.xlabel('Persona')
        plt.ylabel('Knowledge Component')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'maestria_por_kc.png'), dpi=300)
        plt.close()
    
    return resultados


def analisar_progressao_temporal(df: pd.DataFrame, output_dir: str) -> Dict:
    """Analisa progressão ao longo do tempo."""
    
    resultados = {}
    
    # Dividir em quartis temporais
    df_sorted = df.sort_values('game_id')
    n = len(df_sorted)
    
    quartis = {
        'Q1 (Início)': df_sorted.iloc[:n//4],
        'Q2': df_sorted.iloc[n//4:n//2],
        'Q3': df_sorted.iloc[n//2:3*n//4],
        'Q4 (Fim)': df_sorted.iloc[3*n//4:]
    }
    
    for quartil, data in quartis.items():
        resultados[quartil] = {
            'taxa_sucesso': float(data['success'].mean()),
            'taxa_otimalidade': float(data['optimal_action'].mean())
        }
    
    # Gráfico de progressão
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    quartil_names = list(resultados.keys())
    
    # Taxa de Sucesso
    axes[0].plot(quartil_names, [resultados[q]['taxa_sucesso'] for q in quartil_names],
                 marker='o', linewidth=2, markersize=8, color='#3498db')
    axes[0].set_ylabel('Taxa de Sucesso')
    axes[0].set_title('Progressão da Taxa de Sucesso')
    axes[0].grid(alpha=0.3)
    axes[0].set_ylim([0, 1])
    
    # Taxa de Otimalidade
    axes[1].plot(quartil_names, [resultados[q]['taxa_otimalidade'] for q in quartil_names],
                 marker='s', linewidth=2, markersize=8, color='#2ecc71')
    axes[1].set_ylabel('Taxa de Ações Ótimas')
    axes[1].set_title('Progressão da Otimalidade')
    axes[1].grid(alpha=0.3)
    axes[1].set_ylim([0, 1])
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'progressao_temporal.png'), dpi=300)
    plt.close()
    
    return resultados


def analisar_receitas(df: pd.DataFrame, output_dir: str) -> Dict:
    """Analisa eficácia de cada receita."""
    
    resultados = {}
    
    for receita in df['recipe_id'].unique():
        if pd.isna(receita):
            continue
        
        receita_df = df[df['recipe_id'] == receita]
        
        resultados[str(receita)] = {
            'taxa_sucesso': float(receita_df['success'].mean()),
            'total_tentativas': int(len(receita_df)),
            'taxa_sucesso_por_persona': {}
        }
        
        for persona in ['Novice', 'Intermediate', 'Expert']:
            persona_receita = receita_df[receita_df['persona'] == persona]
            if len(persona_receita) > 0:
                resultados[str(receita)]['taxa_sucesso_por_persona'][persona] = float(persona_receita['success'].mean())
    
    # Gráfico de receitas
    if resultados:
        receitas = list(resultados.keys())
        taxas = [resultados[r]['taxa_sucesso'] for r in receitas]
        
        plt.figure(figsize=(12, 6))
        bars = plt.bar(receitas, taxas, color='#9b59b6')
        plt.xlabel('Receita')
        plt.ylabel('Taxa de Sucesso')
        plt.title('Taxa de Sucesso por Receita', fontsize=14, fontweight='bold')
        plt.xticks(rotation=45)
        plt.ylim([0, 1])
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'eficacia_receitas.png'), dpi=300)
        plt.close()
    
    return resultados


def imprimir_resumo(relatorio: Dict):
    """Imprime resumo executivo da análise."""
    
    print("\n" + "="*70)
    print("RESUMO EXECUTIVO - EFICÁCIA PEDAGÓGICA")
    print("="*70)
    
    print(f"\n📊 Dados Analisados:")
    print(f"  • Total de ações: {relatorio['metadata']['total_acoes']}")
    print(f"  • Total de jogos: {relatorio['metadata']['total_jogos']}")
    print(f"  • Total de jogadores: {relatorio['metadata']['total_jogadores']}")
    
    print(f"\n📈 Curva de Aprendizado:")
    for persona, dados in relatorio['curva_aprendizado'].items():
        print(f"  • {persona}:")
        print(f"    - Taxa inicial: {dados['taxa_inicial']*100:.1f}%")
        print(f"    - Taxa final: {dados['taxa_final']*100:.1f}%")
        print(f"    - Melhoria: {dados['melhoria_percentual']:+.1f}%")
    
    print(f"\n🎯 Performance por Persona:")
    for persona, dados in relatorio['analise_personas'].items():
        print(f"  • {persona}:")
        print(f"    - Taxa de sucesso: {dados['taxa_sucesso']*100:.1f}%")
        print(f"    - Taxa de otimalidade: {dados['taxa_otimalidade']*100:.1f}%")
    
    print(f"\n[CONCLUSAO]:")
    # Verificar se há evidência de aprendizado
    melhorias = [dados['melhoria_percentual'] for dados in relatorio['curva_aprendizado'].values()]
    melhoria_media = np.mean(melhorias) if melhorias else 0
    
    if melhoria_media > 5:
        print(f"  [OK] EFICACIA COMPROVADA: Melhoria media de {melhoria_media:.1f}%")
    elif melhoria_media > 0:
        print(f"  [PARCIAL] EFICACIA PARCIAL: Melhoria media de {melhoria_media:.1f}%")
    else:
        print(f"  [FALHA] EFICACIA NAO COMPROVADA: Sem melhoria significativa")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
    else:
        log_file = 'logs/pedagogical_simulation_logs.csv'
    
    if not os.path.exists(log_file):
        print(f"ERRO: Arquivo {log_file} não encontrado.")
        print("Execute primeiro: python run_pedagogical_simulations.py")
        sys.exit(1)
    
    analisar_eficacia_pedagogica(log_file)
