"""
Pipeline Completo de Validação - Code Sandwich
Inclui: Simulações + Knowledge Tracing + Análise Pedagógica
"""

import analise_pedagogica
import analyze_results
import os
import subprocess
import sys
import asyncio
from utils import configure_gemini
from config import DEFAULT_GAME_CONFIG

# Importar módulos avançados
try:
    from advanced_metrics import AdvancedMetrics
    from gerar_relatorio import ReportGenerator
    ADVANCED_METRICS_AVAILABLE = True
except ImportError:
    ADVANCED_METRICS_AVAILABLE = False
    print("AVISO: Módulos de métricas avançadas não encontrados.")

# Importar Knowledge Tracing
try:
    from knowledge_tracing.data_preprocessing import load_logs, preprocess_logs, create_sequences, split_data
    from knowledge_tracing.training import train_model, evaluate_model
    KT_AVAILABLE = True
except ImportError as e:
    KT_AVAILABLE = False
    print(f"AVISO: Módulo de Knowledge Tracing não disponível: {e}")


async def main_async():
    print("="*70)
    print("PIPELINE COMPLETO DE VALIDAÇÃO - CODE SANDWICH")
    print("Simulações + Knowledge Tracing + Análise Pedagógica")
    print("="*70)

    # --- Etapa 1: Configuração da API Gemini ---
    print("\n--- Etapa 1: Configurando API Gemini ---")
    gemini_model = configure_gemini(DEFAULT_GAME_CONFIG.get('gemini_model_name', "gemini-2.5-flash"))
    if not gemini_model:
        print("AVISO: API Gemini não configurada. Análises de IA serão puladas.")

    # --- Etapa 2: Simulações Pedagógicas ---
    print("\n--- Etapa 2: Executando Simulações Pedagógicas ---")
    num_jogos = 500
    log_file_pedagogical = 'logs/pedagogical_simulation_logs.csv'
    
    os.makedirs('logs', exist_ok=True)
    
    if KT_AVAILABLE:
        print(f"Rodando {num_jogos} simulações com agentes pedagógicos...")
        args = [
            sys.executable,
            'run_pedagogical_simulations.py',
            '--log_file', log_file_pedagogical,
            '--num_games', str(num_jogos),
            '--personas', 'Novice,Intermediate,Expert'
        ]
        
        try:
            result = subprocess.run(args, check=True, text=True, capture_output=True, encoding='utf-8', errors='ignore')
            print("[OK] Simulacoes pedagogicas concluidas.")
            
            # --- Etapa 3: Knowledge Tracing ---
            if os.path.exists(log_file_pedagogical):
                print("\n--- Etapa 3: Treinamento de Knowledge Tracing ---")
                try:
                    analise_dir = DEFAULT_GAME_CONFIG.get('analysis_directory', 'analises')
                    os.makedirs(analise_dir, exist_ok=True)
                    
                    # Carrega dados
                    print("[3.1] Carregando e pré-processando logs...")
                    df = load_logs(log_file_pedagogical)
                    
                    if not df.empty:
                        df = preprocess_logs(df)
                        
                        # Cria sequências
                        print("[3.2] Criando sequências...")
                        X, y, feature_names = create_sequences(df, window_size=15)
                        
                        if len(X) > 0:
                            # Divide dados
                            print("[3.3] Dividindo dados...")
                            X_train, X_val, X_test, y_train, y_val, y_test = split_data(X, y)
                            
                            # Treina modelo CNN
                            print("[3.4] Treinando modelo CNN...")
                            model = train_model(
                                X_train, y_train,
                                X_val, y_val,
                                model_type='cnn',
                                epochs=20,
                                batch_size=32
                            )
                            
                            # Avalia
                            print("[3.5] Avaliando modelo...")
                            metrics = evaluate_model(model, X_test, y_test, analise_dir)
                            
                            # Salva modelo
                            model_path = os.path.join(analise_dir, 'gamedkt_cnn_model.keras')
                            model.save(model_path)
                            
                            # Salva métricas em JSON
                            import json
                            metrics_path = os.path.join(analise_dir, 'metrics.json')
                            with open(metrics_path, 'w', encoding='utf-8') as f:
                                json.dump(metrics, f, indent=2, ensure_ascii=False)
                            
                            print(f"[OK] Knowledge Tracing concluido!")
                            print(f"  Acurácia: {metrics['accuracy']*100:.2f}%")
                            print(f"  AUC: {metrics['auc']:.3f}")
                            print(f"  Métricas salvas em: {metrics_path}")
                        else:
                            print("AVISO: Nenhuma sequência criada. Pulando Knowledge Tracing.")
                    else:
                        print("AVISO: Logs vazios. Pulando Knowledge Tracing.")
                        
                except Exception as e:
                    print(f"ERRO ao executar Knowledge Tracing: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("\n--- Etapa 3: Knowledge Tracing (PULADA) ---")
                print(f"Logs não encontrados: {log_file_pedagogical}")
                
        except subprocess.CalledProcessError as e:
            print(f"ERRO ao rodar simulações pedagógicas:\n{e.stderr or e.stdout}")
        except FileNotFoundError:
            print("ERRO: 'run_pedagogical_simulations.py' não encontrado.")
    else:
        print("Knowledge Tracing não disponível. Pulando simulações pedagógicas.")

    # --- Etapa 4: Simulações Básicas (para análise tradicional) ---
    print("\n--- Etapa 4: Executando Simulações Básicas ---")
    log_file_original = DEFAULT_GAME_CONFIG.get('full_simulation_log_path', 'logs/simulation_logs_original.csv')
    
    if os.path.exists(log_file_original):
        try:
            os.remove(log_file_original)
        except OSError:
            pass
    
    print(f"Rodando 1000 simulações básicas...")
    args = [
        sys.executable,
        'run_simulations.py',
        '--log_file', log_file_original,
        '--num_games', '1000'
    ]
    
    try:
        result = subprocess.run(args, check=True, text=True, capture_output=True, encoding='utf-8', errors='ignore')
        print("[OK] Simulacoes basicas concluidas.")
    except subprocess.CalledProcessError as e:
        print(f"ERRO ao rodar simulações básicas:\n{e.stderr or e.stdout}")
        return
    except FileNotFoundError:
        print("ERRO: 'run_simulations.py' não encontrado.")
        return

    # --- Etapa 5: Análise de Coerência Pedagógica (ACP) ---
    print("\n--- Etapa 5: Análise de Coerência Pedagógica (ACP) ---")
    try:
        if hasattr(analise_pedagogica, 'run_analysis') and asyncio.iscoroutinefunction(analise_pedagogica.run_analysis):
            await analise_pedagogica.run_analysis(gemini_model, DEFAULT_GAME_CONFIG)
            print("[OK] Analise Pedagogica concluida.")
        else:
            print("ERRO: Função 'run_analysis' não encontrada.")
    except Exception as e:
        print(f"ERRO ao executar análise pedagógica: {e}")

    # --- Etapa 6: Análise de Resultados (Gráficos + IA) ---
    print("\n--- Etapa 6: Análise de Resultados (Gráficos + IA) ---")
    analise_dir = DEFAULT_GAME_CONFIG.get('analysis_directory', 'analises')
    
    try:
        if hasattr(analyze_results, 'main') and asyncio.iscoroutinefunction(analyze_results.main):
            await analyze_results.main(gemini_model, DEFAULT_GAME_CONFIG)
            print("[OK] Analise de resultados concluida.")
        else:
            print("ERRO: Função 'main' não encontrada.")
    except Exception as e:
        print(f"ERRO ao executar análise de resultados: {e}")

    # --- Etapa 7: Análise de Eficácia Pedagógica ---
    if KT_AVAILABLE and os.path.exists(log_file_pedagogical):
        print("\n--- Etapa 7: Análise de Eficácia Pedagógica ---")
        try:
            from analise_eficacia_pedagogica import analisar_eficacia_pedagogica
            relatorio_eficacia = analisar_eficacia_pedagogica(log_file_pedagogical, analise_dir)
            print("[OK] Analise de eficacia concluida.")
        except Exception as e:
            print(f"ERRO ao executar análise de eficácia: {e}")
    else:
        print("\n--- Etapa 7: Análise de Eficácia Pedagógica (PULADA) ---")
        print("Logs pedagógicos não disponíveis.")

    # --- Etapa 8: Métricas Avançadas ---
    if ADVANCED_METRICS_AVAILABLE:
        print("\n--- Etapa 8: Calculando Métricas Avançadas ---")
        try:
            cards_file = DEFAULT_GAME_CONFIG.get('cards_file', 'cartas.json')
            kcs_file = DEFAULT_GAME_CONFIG.get('kcs_file', 'kcs.json')
            
            metrics = AdvancedMetrics(log_file_original, cards_file, kcs_file)
            metrics_report_path = metrics.generate_full_report(analise_dir)
            metrics.generate_visualizations(analise_dir)
            
            print("[OK] Metricas avancadas calculadas.")
            
            # Gera relatório consolidado
            print("\n--- Etapa 8: Gerando Relatório Consolidado ---")
            generator = ReportGenerator(metrics_report_path, analise_dir)
            report_path = generator.generate_report()
            print("[OK] Relatorio gerado.")
            
        except Exception as e:
            print(f"ERRO ao calcular métricas avançadas: {e}")

    # --- Conclusão ---
    print("\n" + "="*70)
    print("PIPELINE CONCLUÍDO COM SUCESSO!")
    print("="*70)
    
    print("\n📊 RELATÓRIOS GERADOS:")
    print(f"  1. Análise Pedagógica (ACP): analises/RELATORIO_ACP.md")
    print(f"  2. Balanceamento (IA): analises/RELATORIO_BALANCEAMENTO_IA.md")
    
    if KT_AVAILABLE and os.path.exists(os.path.join(analise_dir, 'metrics.json')):
        print(f"  3. Knowledge Tracing: analises/gamedkt_*.png")
        print(f"  4. Modelo treinado: analises/gamedkt_cnn_model.keras")
    
    if KT_AVAILABLE and os.path.exists(os.path.join(analise_dir, 'eficacia_pedagogica.json')):
        print(f"  5. Eficácia Pedagógica: analises/eficacia_pedagogica.json")
        print(f"  6. Gráficos de eficácia: analises/curva_aprendizado.png, etc.")
    
    if ADVANCED_METRICS_AVAILABLE:
        print(f"  7. Relatório de validação: analises/RELATORIO_VALIDACAO.md")
    
    print(f"\n📈 VISUALIZAÇÕES: analises/")
    print(f"\n💡 Para visualizar dashboard: streamlit run dashboard.py")
    print("="*70)


# --- Ponto de Entrada ---
if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main_async())
