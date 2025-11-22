"""
Script principal para treinar e avaliar modelos de Knowledge Tracing
"""

import os
import sys
import argparse
import json
import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from knowledge_tracing.data_preprocessing import (
    load_logs, preprocess_logs, create_sequences, split_data
)
from knowledge_tracing.training import train_model, evaluate_model, compare_models
from config import DEFAULT_GAME_CONFIG


def main(log_file, output_dir, window_size, model_type, compare_all):
    """
    Pipeline principal de Knowledge Tracing.
    
    Args:
        log_file: Arquivo de logs
        output_dir: Diretório de saída
        window_size: Tamanho da janela de sequência
        model_type: Tipo de modelo
        compare_all: Se deve comparar todos os modelos
    """
    print("\n" + "="*60)
    print("KNOWLEDGE TRACING - Code Sandwich")
    print("Baseado em: Hooshyar et al. (2022) - GameDKT")
    print("="*60 + "\n")
    
    # Cria diretório de saída
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Carrega e pré-processa logs
    print("="*60)
    print("ETAPA 1: Carregamento e Pré-processamento")
    print("="*60)
    
    df = load_logs(log_file)
    
    if df.empty:
        print(f"ERRO: Não foi possível carregar logs de {log_file}")
        print("Execute primeiro: python run_pedagogical_simulations.py")
        return
    
    print(f"Logs carregados: {len(df)} registros")
    print(f"Jogadores únicos: {df['player_id'].nunique()}")
    print(f"Jogos únicos: {df['game_id'].nunique()}")
    
    df = preprocess_logs(df)
    print(f"Pré-processamento concluído")
    
    # 2. Cria sequências
    print("\n" + "="*60)
    print("ETAPA 2: Criação de Sequências")
    print("="*60)
    
    X, y, feature_names = create_sequences(df, window_size=window_size)
    
    if len(X) == 0:
        print("ERRO: Nenhuma sequência foi criada")
        print("Verifique se os logs contêm dados suficientes")
        return
    
    print(f"Features utilizadas: {feature_names}")
    print(f"Shape de X: {X.shape}")
    print(f"Shape de y: {y.shape}")
    print(f"Distribuição de labels: Sucesso={np.sum(y)}, Falha={len(y)-np.sum(y)}")
    
    # 3. Divide dados
    print("\n" + "="*60)
    print("ETAPA 3: Divisão de Dados")
    print("="*60)
    
    X_train, X_val, X_test, y_train, y_val, y_test = split_data(X, y)
    
    # 4. Treina modelo(s)
    print("\n" + "="*60)
    print("ETAPA 4: Treinamento de Modelo(s)")
    print("="*60)
    
    if compare_all:
        # Compara múltiplos modelos
        results = compare_models(
            X_train, y_train,
            X_val, y_val,
            X_test, y_test,
            model_types=['cnn', 'lstm', 'mlp'],
            output_dir=output_dir
        )
        
        # Salva resultados
        results_summary = {}
        for model_type, result in results.items():
            if 'metrics' in result:
                results_summary[model_type] = result['metrics']
        
        with open(os.path.join(output_dir, 'comparison_results.json'), 'w') as f:
            json.dump(results_summary, f, indent=2)
        
        print(f"\nResultados salvos em: {os.path.join(output_dir, 'comparison_results.json')}")
        
    else:
        # Treina um único modelo
        model = train_model(
            X_train, y_train,
            X_val, y_val,
            model_type=model_type,
            epochs=20,
            batch_size=32
        )
        
        # Avalia
        print("\n" + "="*60)
        print("ETAPA 5: Avaliação")
        print("="*60)
        
        metrics = evaluate_model(model, X_test, y_test, output_dir)
        
        # Salva modelo
        model_path = os.path.join(output_dir, f'gamedkt_{model_type}_model.keras')
        model.save(model_path)
        print(f"\nModelo salvo em: {model_path}")
        
        # Salva métricas
        with open(os.path.join(output_dir, 'metrics.json'), 'w') as f:
            json.dump(metrics, f, indent=2)
        
        print(f"Métricas salvas em: {os.path.join(output_dir, 'metrics.json')}")
    
    print("\n" + "="*60)
    print("PIPELINE CONCLUÍDO COM SUCESSO!")
    print("="*60 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Treina modelos de Knowledge Tracing para Code Sandwich"
    )
    
    parser.add_argument('--log_file', type=str,
                       default='logs/pedagogical_simulation_logs.csv',
                       help='Arquivo de logs pedagógicos')
    
    parser.add_argument('--output_dir', type=str,
                       default=DEFAULT_GAME_CONFIG.get('analysis_directory', 'analises'),
                       help='Diretório para salvar resultados')
    
    parser.add_argument('--window_size', type=int,
                       default=15,
                       help='Tamanho da janela de sequência')
    
    parser.add_argument('--model_type', type=str,
                       default='cnn',
                       choices=['cnn', 'lstm', 'rnn', 'mlp'],
                       help='Tipo de modelo a treinar')
    
    parser.add_argument('--compare_all', action='store_true',
                       help='Compara todos os tipos de modelos')
    
    args = parser.parse_args()
    
    main(
        log_file=args.log_file,
        output_dir=args.output_dir,
        window_size=args.window_size,
        model_type=args.model_type,
        compare_all=args.compare_all
    )
