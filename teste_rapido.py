"""
Script de Teste Rápido para Validar Implementação
Executa 10 simulações para testar se tudo está funcionando
"""
import subprocess
import sys
import os
import json

def test_quick_run():
    """Executa teste rápido com 10 simulações."""
    
    print("="*70)
    print("TESTE RÁPIDO DE VALIDAÇÃO - CODE SANDWICH")
    print("Executando 10 simulações para verificar se tudo funciona...")
    print("="*70)
    
    # 1. Executar simulações rápidas
    print("\n[1/3] Executando 10 simulações de teste...")
    result = subprocess.run([
        sys.executable,
        'run_simulations.py',
        '--log_file', 'logs/test_quick.csv',
        '--num_games', '10'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print("❌ ERRO ao executar simulações:")
        print(result.stderr)
        return False
    
    print("✓ Simulações concluídas")
    
    # 2. Testar métricas avançadas
    print("\n[2/3] Testando cálculo de métricas avançadas...")
    
    try:
        from advanced_metrics import AdvancedMetrics
        
        metrics = AdvancedMetrics(
            'logs/test_quick.csv',
            'cartas.json',
            'kcs.json'
        )
        
        # Testar cada relatório
        print("  - Testando validação mecânica...")
        mech_report = metrics.mechanical_validation_report()
        assert 'overall_status' in mech_report
        
        print("  - Testando validação pedagógica...")
        ped_report = metrics.pedagogical_metrics_report()
        assert 'overall_status' in ped_report
        
        print("  - Testando robustez estatística...")
        stat_report = metrics.statistical_robustness_report()
        # Pode retornar INSUFFICIENT_DATA com apenas 10 jogos
        
        print("  - Gerando relatório completo...")
        report_path = metrics.generate_full_report('test_output')
        assert os.path.exists(report_path)
        
        print("✓ Métricas avançadas funcionando")
        
    except Exception as e:
        print(f"❌ ERRO ao calcular métricas: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. Testar geração de relatório 
    print("\n[3/3] Testando geração de relatório...")
    
    try:
        from gerar_relatorio import ReportGenerator
        
        generator = ReportGenerator(
            'test_output/advanced_metrics_report.json',
            'test_output'
        )
        
        report_path = generator.generate_report()
        assert os.path.exists(report_path)
        
        print("✓ Relatório gerado")
        
    except Exception as e:
        print(f"❌ ERRO ao gerar relatório: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. Verificar arquivos gerados
    print("\n[4/4] Verificando arquivos gerados...")
    
    expected_files = [
        'test_output/advanced_metrics_report.json',
        'test_output/RELATORIO_VALIDACAO.md'
    ]
    
    all_exist = True
    for filepath in expected_files:
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"  ✓ {filepath} ({size} bytes)")
        else:
            print(f"  ❌ {filepath} NÃO ENCONTRADO")
            all_exist = False
    
    if not all_exist:
        return False
    
    # 5. Validar estrutura do JSON
    print("\n[5/5] Validando estrutura do relatório JSON...")
    
    try:
        with open('test_output/advanced_metrics_report.json', 'r') as f:
            data = json.load(f)
        
        required_keys = ['metadata', 'mechanical_validation', 'pedagogical_metrics', 'statistical_robustness']
        for key in required_keys:
            if key in data:
                print(f"  ✓ {key}")
            else:
                print(f"  ❌ {key} ausente")
                return False
        
    except Exception as e:
        print(f"❌ ERRO ao validar JSON: {e}")
        return False
    
    print("\n" + "="*70)
    print("✅ TESTE RÁPIDO CONCLUÍDO COM SUCESSO!")
    print("="*70)
    print("\n📝 Arquivos de teste gerados em: test_output/")
    print("🚀 Você pode agora executar com 1000 simulações:")
    print("   python main_enhanced.py")
    print("="*70)
    
    return True


if __name__ == "__main__":
    # Criar diretórios necessários
    os.makedirs('logs', exist_ok=True)
    os.makedirs('test_output', exist_ok=True)
    
    success = test_quick_run()
    
    if success:
        sys.exit(0)
    else:
        print("\n❌ TESTE FALHOU - Verifique os erros acima")
        sys.exit(1)

