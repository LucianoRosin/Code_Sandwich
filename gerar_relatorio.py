"""
Gerador de Relatório
Consolida todas as métricas em um documento Markdown formatado
"""

import json
import os
from datetime import datetime

class ReportGenerator:
    """Gera relatório formatado."""
    
    def __init__(self, metrics_file: str, output_dir: str = 'analises'):
        """
        Inicializa o gerador.
        
        Args:
            metrics_file: Caminho para o JSON de métricas avançadas
            output_dir: Diretório de saída
        """
        self.metrics_file = metrics_file
        self.output_dir = output_dir
        
        with open(metrics_file, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
    
    def generate_report(self) -> str:
        """
        Gera relatório completo em Markdown.
        
        Returns:
            Caminho do arquivo gerado
        """
        os.makedirs(self.output_dir, exist_ok=True)
        
        report_lines = []
        
        # Cabeçalho
        report_lines.extend(self._generate_header())
        
        # Sumário Executivo
        report_lines.extend(self._generate_executive_summary())
        
        # Validação Mecânica
        report_lines.extend(self._generate_mechanical_section())
        
        # Validação Pedagógica
        report_lines.extend(self._generate_pedagogical_section())
        
        # Robustez Estatística
        report_lines.extend(self._generate_statistical_section())
        
        # Conclusões
        report_lines.extend(self._generate_conclusions())
        
        # Salvar
        output_path = os.path.join(self.output_dir, 'RELATORIO_VALIDACAO.md')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        print(f"✓ Relatório gerado: {output_path}")
        
        return output_path
    
    def _generate_header(self) -> list:
        """Gera cabeçalho do relatório."""
        metadata = self.data.get('metadata', {})
        
        return [
            "# Relatório de Validação Computacional",
            "## Code Sandwich",
            "",
            "---",
            "",
            f"**Data de Geração**: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}  ",
            f"**Jogos Analisados**: {metadata.get('total_games_analyzed', 'N/A')}  ",
            f"**Versão do Relatório**: 2.0 (Métricas Avançadas)  ",
            "",
            "---",
            ""
        ]
    
    def _generate_executive_summary(self) -> list:
        """Gera sumário executivo."""
        mech = self.data.get('mechanical_validation', {})
        ped = self.data.get('pedagogical_metrics', {})
        stat = self.data.get('statistical_robustness', {})
        
        mech_status = mech.get('overall_status', 'N/A')
        ped_status = ped.get('overall_status', 'N/A')
        stat_status = stat.get('overall_status', 'N/A')
        
        # Determinar status geral
        if all('PASS' in s or 'ROBUST' in s for s in [mech_status, ped_status, stat_status]):
            overall_badge = "🟢 **APROVADO**"
            overall_text = "O jogo Code Sandwich foi validado com sucesso em todas as dimensões analisadas. As mecânicas estão funcionais, a estrutura pedagógica é robusta e os resultados são estatisticamente confiáveis."
        elif any('FAIL' in s for s in [mech_status, ped_status, stat_status]):
            overall_badge = "🔴 **REPROVADO**"
            overall_text = "Foram identificados problemas críticos que requerem correção antes da publicação."
        else:
            overall_badge = "🟡 **APROVADO COM RESSALVAS**"
            overall_text = "O jogo está funcional e pedagogicamente adequado, mas alguns aspectos podem ser aprimorados para maior robustez."
        
        return [
            "## 1. Sumário Executivo",
            "",
            f"### Status Geral: {overall_badge}",
            "",
            overall_text,
            "",
            "### Resultados por Dimensão",
            "",
            "| Dimensão | Status | Descrição |",
            "|----------|--------|-----------|",
            f"| **Validação Mecânica** | {self._status_badge(mech_status)} | {mech_status} |",
            f"| **Validação Pedagógica** | {self._status_badge(ped_status)} | {ped_status} |",
            f"| **Robustez Estatística** | {self._status_badge(stat_status)} | {stat_status} |",
            "",
            "---",
            ""
        ]
    
    def _generate_mechanical_section(self) -> list:
        """Gera seção de validação mecânica."""
        mech = self.data.get('mechanical_validation', {})
        metrics = mech.get('metrics', {})
        
        lines = [
            "## 2. Validação Mecânica",
            "",
            "Esta seção comprova que o jogo **não está quebrado** e funciona corretamente em todas as suas mecânicas fundamentais.",
            ""
        ]
        
        # 2.1 Conclusão de Jogos
        if 'game_completion' in metrics:
            gc = metrics['game_completion']
            lines.extend([
                "### 2.1 Taxa de Conclusão de Jogos",
                "",
                f"**Resultado**: {self._status_badge(gc.get('status', 'UNKNOWN'))} {gc.get('status', 'N/A')}",
                "",
                f"- **Jogos Completados**: {gc.get('completed_games', 0)}/{gc.get('total_games', 0)}",
                f"- **Taxa de Conclusão**: {gc.get('completion_rate', 0):.2f}%",
                "",
                "**Interpretação**: " + (
                    "Excelente taxa de conclusão. O jogo raramente termina em empate ou deadlock."
                    if gc.get('completion_rate', 0) > 90 else
                    "Taxa de conclusão adequada. Alguns jogos podem terminar em empate."
                    if gc.get('completion_rate', 0) > 70 else
                    "Taxa de conclusão baixa. Investigar possíveis deadlocks ou condições de empate excessivas."
                ),
                ""
            ])
        
        # 2.2 Duração dos Jogos
        if 'game_duration' in metrics:
            gd = metrics['game_duration']
            stats_data = gd.get('statistics', {})
            anomalies = gd.get('anomalies', {})
            
            lines.extend([
                "### 2.2 Duração dos Jogos",
                "",
                f"**Resultado**: {self._status_badge(gd.get('status', 'UNKNOWN'))} {gd.get('status', 'N/A')}",
                "",
                "#### Estatísticas Descritivas",
                "",
                "| Métrica | Valor |",
                "|---------|-------|",
                f"| Média | {stats_data.get('mean', 0):.2f} turnos |",
                f"| Mediana | {stats_data.get('median', 0):.2f} turnos |",
                f"| Desvio Padrão | {stats_data.get('std', 0):.2f} |",
                f"| Mínimo | {stats_data.get('min', 0)} turnos |",
                f"| Máximo | {stats_data.get('max', 0)} turnos |",
                f"| Q1 (25%) | {stats_data.get('q25', 0):.2f} turnos |",
                f"| Q3 (75%) | {stats_data.get('q75', 0):.2f} turnos |",
                "",
                "#### Detecção de Anomalias",
                "",
                f"- **Jogos Muito Curtos** (< 5 turnos): {anomalies.get('too_short_games', 0)}",
                f"- **Jogos Muito Longos** (> 100 turnos): {anomalies.get('too_long_games', 0)}",
                f"- **Taxa de Anomalias**: {anomalies.get('anomaly_rate', 0):.2f}%",
                "",
                "**Interpretação**: " + (
                    "Duração consistente e sem anomalias significativas. O jogo tem ritmo adequado."
                    if anomalies.get('anomaly_rate', 0) < 5 else
                    "Algumas anomalias detectadas. Investigar jogos extremamente curtos ou longos."
                ),
                ""
            ])
        
        # 2.3 Balanceamento de Vencedores
        if 'winner_distribution' in metrics:
            wd = metrics['winner_distribution']
            distribution = wd.get('distribution', {})
            balance_tests = wd.get('balance_tests', {})
            
            lines.extend([
                "### 2.3 Balanceamento de Vencedores",
                "",
                f"**Resultado**: {self._status_badge(wd.get('status', 'UNKNOWN'))} {wd.get('status', 'N/A')}",
                "",
                "#### Distribuição de Vitórias",
                "",
                "| Jogador | Vitórias | Taxa de Vitória |",
                "|---------|----------|-----------------|"
            ])
            
            for player, data in distribution.items():
                lines.append(f"| Jogador {player} | {data['wins']} | {data['win_rate']:.2f}% |")
            
            lines.extend([
                "",
                "#### Testes Estatísticos de Balanceamento",
                "",
                f"- **Teste Chi-Quadrado**: χ² = {balance_tests.get('chi_square_statistic', 0):.4f}, p = {balance_tests.get('chi_square_pvalue', 0):.4f}",
                f"- **Balanceado?**: {'✓ Sim' if balance_tests.get('is_balanced', False) else '✗ Não'} (p > 0.05 indica distribuição uniforme)",
                f"- **Coeficiente de Gini**: {balance_tests.get('gini_coefficient', 0):.4f} ({balance_tests.get('gini_interpretation', 'N/A')})",
                "",
                "**Interpretação**: " + (
                    "Distribuição balanceada. Nenhum jogador tem vantagem significativa pela posição."
                    if balance_tests.get('is_balanced', False) and balance_tests.get('gini_coefficient', 1) < 0.3 else
                    "Leve desbalanceamento detectado. Pode ser devido à variação aleatória ou vantagem posicional."
                ),
                "",
                "> **Nota Metodológica**: O teste Chi-Quadrado verifica se a distribuição de vitórias é estatisticamente diferente de uma distribuição uniforme. O coeficiente de Gini mede desigualdade (0 = perfeitamente igual, 1 = totalmente desigual).",
                ""
            ])
        
        # 2.4 Diversidade de Receitas
        if 'recipe_diversity' in metrics:
            rd = metrics['recipe_diversity']
            
            lines.extend([
                "### 2.4 Diversidade de Receitas Vencedoras",
                "",
                f"**Resultado**: {self._status_badge(rd.get('status', 'UNKNOWN'))} {rd.get('status', 'N/A')}",
                "",
                f"- **Receitas Únicas Vencedoras**: {rd.get('unique_recipes_won', 0)}/{rd.get('total_recipes_available', 0)}",
                f"- **Taxa de Diversidade**: {rd.get('diversity_rate', 0):.2f}%",
                f"- **Entropia de Shannon**: {rd.get('shannon_entropy', 0):.4f}",
                f"- **Entropia Normalizada**: {rd.get('normalized_entropy', 0):.4f}",
                "",
                f"**Receita Mais Comum**: {rd.get('most_common_recipe', 'N/A')} ({rd.get('most_common_count', 0)} vitórias)",
                "",
                "**Interpretação**: " + (
                    "Alta diversidade de receitas. O jogo não tem estratégia dominante única."
                    if rd.get('diversity_rate', 0) > 70 else
                    "Diversidade moderada. Algumas receitas são mais comuns, mas não dominantes."
                    if rd.get('diversity_rate', 0) > 50 else
                    "Baixa diversidade. Poucas receitas são viáveis, indicando possível desbalanceamento."
                ),
                "",
                "> **Nota Metodológica**: A entropia de Shannon mede a diversidade da distribuição. Valores mais altos indicam maior variedade de receitas vencedoras.",
                ""
            ])
        
        # 2.5 Consistência
        if 'consistency' in metrics:
            cons = metrics['consistency']
            
            lines.extend([
                "### 2.5 Consistência e Reprodutibilidade",
                "",
                f"**Resultado**: {self._status_badge(cons.get('status', 'UNKNOWN'))} {cons.get('status', 'N/A')}",
                "",
                "#### Análise de Blocos Temporais",
                "",
                "Os jogos foram divididos em 5 blocos para verificar consistência ao longo da simulação.",
                "",
                f"- **Coeficiente de Variação**: {cons.get('coefficient_of_variation', 0):.2f}%",
                f"- **Teste ANOVA**: F = {cons.get('anova_f_statistic', 0):.4f}, p = {cons.get('anova_pvalue', 0):.4f}",
                f"- **Consistente?**: {'✓ Sim' if cons.get('is_consistent', False) else '✗ Não'}",
                "",
                "**Interpretação**: " + (
                    "Resultados consistentes ao longo da simulação. O jogo é reprodutível."
                    if cons.get('is_consistent', False) else
                    "Variação significativa entre blocos. Pode indicar efeitos de aprendizado ou aleatoriedade excessiva."
                ),
                ""
            ])
        
        lines.extend([
            "---",
            ""
        ])
        
        return lines
    
    def _generate_pedagogical_section(self) -> list:
        """Gera seção de validação pedagógica."""
        ped = self.data.get('pedagogical_metrics', {})
        metrics = ped.get('metrics', {})
        
        lines = [
            "## 3. Validação Pedagógica",
            "",
            "Esta seção valida a **estrutura pedagógica** do jogo, incluindo cobertura de conceitos, progressão de dificuldade e exposição em simulações.",
            ""
        ]
        
        # 3.1 Cobertura de KCs
        if 'kc_coverage' in metrics:
            kc_cov = metrics['kc_coverage']
            
            lines.extend([
                "### 3.1 Cobertura de Knowledge Components (KCs)",
                "",
                f"**Resultado**: {self._status_badge(kc_cov.get('status', 'UNKNOWN'))} {kc_cov.get('status', 'N/A')}",
                "",
                f"- **KCs Definidos**: {kc_cov.get('total_kcs_defined', 0)}",
                f"- **KCs Utilizados em Cartas**: {kc_cov.get('kcs_used_in_cards', 0)}",
                f"- **Taxa de Cobertura**: {kc_cov.get('coverage_rate', 0):.2f}%",
                ""
            ])
            
            unused = kc_cov.get('unused_kcs', [])
            if unused:
                lines.extend([
                    f"**KCs Não Utilizados** ({len(unused)}): {', '.join(unused)}",
                    ""
                ])
            else:
                lines.extend([
                    "**KCs Não Utilizados**: Nenhum (cobertura completa)",
                    ""
                ])
            
            lines.extend([
                "**Interpretação**: " + (
                    "Cobertura completa ou quase completa de conceitos. Todos os KCs definidos estão representados no jogo."
                    if kc_cov.get('coverage_rate', 0) >= 95 else
                    "Boa cobertura, mas alguns KCs não estão representados. Considerar adicionar cartas ou remover KCs não utilizados."
                ),
                ""
            ])
        
        # 3.2 Distribuição de Dificuldade
        if 'difficulty_distribution' in metrics:
            diff_dist = metrics['difficulty_distribution']
            distribution = diff_dist.get('distribution', {})
            
            lines.extend([
                "### 3.2 Distribuição de Dificuldade dos KCs",
                "",
                f"**Resultado**: {self._status_badge(diff_dist.get('status', 'UNKNOWN'))} {diff_dist.get('status', 'N/A')}",
                "",
                "#### Distribuição Atual vs. Ideal",
                "",
                "| Nível | Quantidade | % Atual | % Ideal | Desvio |",
                "|-------|------------|---------|---------|--------|"
            ])
            
            for level in range(1, 6):
                level_key = f"level_{level}"
                if level_key in distribution:
                    data = distribution[level_key]
                    lines.append(
                        f"| Nível {level} | {data['count']} | {data['percentage']:.1f}% | "
                        f"{data['ideal_percentage']:.1f}% | {data['deviation']:.1f}% |"
                    )
            
            lines.extend([
                "",
                f"- **Desvio Médio**: {diff_dist.get('average_deviation', 0):.2f}%",
                f"- **Score de Balanceamento**: {diff_dist.get('balance_score', 0):.2f}/100",
                "",
                "**Interpretação**: " + (
                    "Distribuição bem balanceada, próxima do ideal. Boa progressão de dificuldade."
                    if diff_dist.get('average_deviation', 100) < 10 else
                    "Distribuição razoável, mas com desvios. Considerar rebalancear KCs entre níveis."
                ),
                "",
                "> **Nota Metodológica**: A distribuição ideal segue aproximadamente uma curva normal: mais conceitos intermediários (níveis 2-3) e menos nos extremos (níveis 1 e 5).",
                ""
            ])
        
        # 3.3 Redundância de KCs
        if 'kc_redundancy' in metrics:
            kc_red = metrics['kc_redundancy']
            stats_data = kc_red.get('statistics', {})
            low_red = kc_red.get('low_redundancy_kcs', {})
            
            lines.extend([
                "### 3.3 Redundância de KCs (Mapeamento KC → Cartas)",
                "",
                f"**Resultado**: {self._status_badge(kc_red.get('status', 'UNKNOWN'))} {kc_red.get('status', 'N/A')}",
                "",
                "#### Estatísticas de Redundância",
                "",
                f"- **Mínimo de Cartas por KC**: {stats_data.get('min_cards_per_kc', 0)}",
                f"- **Máximo de Cartas por KC**: {stats_data.get('max_cards_per_kc', 0)}",
                f"- **Média de Cartas por KC**: {stats_data.get('mean_cards_per_kc', 0):.2f}",
                f"- **Mediana de Cartas por KC**: {stats_data.get('median_cards_per_kc', 0):.2f}",
                "",
                f"**KCs com Baixa Redundância** (< 2 cartas): {kc_red.get('low_redundancy_count', 0)}",
                ""
            ])
            
            if low_red:
                lines.append("| KC | Número de Cartas |")
                lines.append("|----|------------------|")
                for kc, count in list(low_red.items())[:10]:  # Limitar a 10
                    lines.append(f"| {kc} | {count} |")
                lines.append("")
            
            lines.extend([
                "**Interpretação**: " + (
                    "Boa redundância. A maioria dos KCs aparece em múltiplas cartas, aumentando a probabilidade de exposição."
                    if kc_red.get('low_redundancy_count', 100) < 10 else
                    "Alguns KCs têm baixa redundância. Considerar adicionar mais cartas para esses conceitos."
                ),
                "",
                "> **Nota Metodológica**: Redundância é importante para garantir que os jogadores encontrem os conceitos durante o jogo. KCs com apenas 1 carta podem não ser expostos em todas as partidas.",
                ""
            ])
        
        # 3.4 Progressão de Dificuldade nas Receitas
        if 'difficulty_progression' in metrics:
            diff_prog = metrics['difficulty_progression']
            smoothness = diff_prog.get('smoothness_analysis', {})
            
            lines.extend([
                "### 3.4 Progressão de Dificuldade nas Receitas",
                "",
                f"**Resultado**: {self._status_badge(diff_prog.get('status', 'UNKNOWN'))} {diff_prog.get('status', 'N/A')}",
                "",
                "#### Análise de Suavidade da Progressão",
                "",
                f"- **Incremento Médio entre Receitas**: {smoothness.get('mean_step', 0):.3f}",
                f"- **Maior Salto de Dificuldade**: {smoothness.get('max_jump', 0):.3f}",
                f"- **Desvio Padrão dos Incrementos**: {smoothness.get('std_step', 0):.3f}",
                f"- **Saltos Grandes** (> 1.0): {smoothness.get('large_jumps_count', 0)}",
                "",
                "**Interpretação**: " + (
                    "Progressão suave e gradual. As receitas aumentam de dificuldade de forma consistente."
                    if smoothness.get('max_jump', 10) < 1.5 else
                    "Alguns saltos grandes de dificuldade detectados. Considerar adicionar receitas intermediárias."
                ),
                ""
            ])
        
        # 3.5 Exposição de KCs em Simulações
        if 'kc_exposure_in_games' in metrics:
            kc_exp = metrics['kc_exposure_in_games']
            never_exp = kc_exp.get('never_exposed_kcs', [])
            rarely_exp = kc_exp.get('rarely_exposed_kcs', {})
            
            lines.extend([
                "### 3.5 Exposição de KCs nas Simulações",
                "",
                f"**Resultado**: {self._status_badge(kc_exp.get('status', 'UNKNOWN'))} {kc_exp.get('status', 'N/A')}",
                "",
                f"- **Jogos Analisados**: {kc_exp.get('total_games_analyzed', 0)}",
                f"- **KCs Expostos**: {kc_exp.get('kcs_exposed', 0)}",
                f"- **Taxa de Exposição**: {kc_exp.get('exposure_rate', 0):.2f}%",
                f"- **Média de Exposições por KC**: {kc_exp.get('mean_exposures_per_kc', 0):.2f}",
                ""
            ])
            
            if never_exp:
                lines.extend([
                    f"**KCs Nunca Expostos** ({len(never_exp)}): {', '.join(never_exp)}",
                    ""
                ])
            
            if rarely_exp:
                lines.extend([
                    f"**KCs Raramente Expostos** (< 5% dos jogos): {len(rarely_exp)}",
                    ""
                ])
            
            lines.extend([
                "**Interpretação**: " + (
                    "Excelente exposição. Quase todos os KCs aparecem nas simulações."
                    if kc_exp.get('exposure_rate', 0) > 90 else
                    "Boa exposição, mas alguns KCs raramente aparecem. Considerar aumentar redundância ou ajustar receitas."
                ),
                ""
            ])
        
        lines.extend([
            "---",
            ""
        ])
        
        return lines
    
    def _generate_statistical_section(self) -> list:
        """Gera seção de robustez estatística."""
        stat = self.data.get('statistical_robustness', {})
        
        if stat.get('status') == 'INSUFFICIENT_DATA':
            return [
                "## 4. Robustez Estatística",
                "",
                f"⚠️ **{stat.get('message', 'Dados insuficientes')}**",
                "",
                "---",
                ""
            ]
        
        metrics = stat.get('metrics', {})
        
        lines = [
            "## 4. Robustez Estatística",
            "",
            "Esta seção analisa a **confiabilidade estatística** dos resultados obtidos nas simulações.",
            ""
        ]
        
        # 4.1 Intervalos de Confiança
        if 'turns_confidence_interval' in metrics:
            ci = metrics['turns_confidence_interval']
            
            lines.extend([
                "### 4.1 Intervalos de Confiança (95%)",
                "",
                f"- **Média de Turnos**: {ci.get('mean', 0):.2f}",
                f"- **Intervalo de Confiança (95%)**: [{ci.get('lower_bound', 0):.2f}, {ci.get('upper_bound', 0):.2f}]",
                f"- **Margem de Erro**: ±{ci.get('margin_of_error', 0):.2f} turnos",
                "",
                "**Interpretação**: Com 95% de confiança, a duração média real dos jogos está dentro deste intervalo.",
                ""
            ])
        
        # 4.2 Teste de Normalidade
        if 'normality_test' in metrics:
            norm = metrics['normality_test']
            
            lines.extend([
                "### 4.2 Teste de Normalidade",
                "",
                f"- **Teste**: {norm.get('test', 'N/A')}",
                f"- **Estatística**: W = {norm.get('statistic', 0):.4f}",
                f"- **p-valor**: {norm.get('pvalue', 0):.4f}",
                f"- **Distribuição Normal?**: {'✓ Sim' if norm.get('is_normal', False) else '✗ Não'}",
                "",
                f"**Interpretação**: {norm.get('interpretation', 'N/A')}",
                "",
                "> **Nota Metodológica**: O teste de Shapiro-Wilk verifica se os dados seguem uma distribuição normal. Isso é importante para aplicar testes paramétricos.",
                ""
            ])
        
        # 4.3 Poder Estatístico
        if 'statistical_power' in metrics:
            power = metrics['statistical_power']
            
            lines.extend([
                "### 4.3 Poder Estatístico",
                "",
                f"- **Tamanho da Amostra**: {power.get('sample_size', 0)} jogos",
                f"- **Tamanho de Efeito Assumido**: {power.get('assumed_effect_size', 0)}",
                f"- **Nível de Significância (α)**: {power.get('alpha', 0)}",
                f"- **Poder Estimado**: {power.get('estimated_power', 0):.4f} ({power.get('estimated_power', 0)*100:.2f}%)",
                f"- **Interpretação**: {power.get('power_interpretation', 'N/A')}",
                ""
            ])
            
            if power.get('estimated_power', 1) < 0.8:
                lines.extend([
                    f"⚠️ **Recomendação**: Aumentar o tamanho da amostra para pelo menos **{power.get('recommended_sample_size', 0)} jogos** para atingir poder de 80%.",
                    ""
                ])
            else:
                lines.extend([
                    "✓ **Poder adequado**: A amostra é suficiente para detectar efeitos médios com confiança.",
                    ""
                ])
            
            lines.extend([
                "> **Nota Metodológica**: O poder estatístico é a probabilidade de detectar um efeito real quando ele existe. Valores acima de 0.8 (80%) são considerados adequados.",
                ""
            ])
        
        # 4.4 Análise de Outliers
        if 'outlier_analysis' in metrics:
            outlier = metrics['outlier_analysis']
            
            lines.extend([
                "### 4.4 Análise de Outliers",
                "",
                f"- **Método**: {outlier.get('method', 'N/A')}",
                f"- **Limite Inferior**: {outlier.get('lower_bound', 0):.2f}",
                f"- **Limite Superior**: {outlier.get('upper_bound', 0):.2f}",
                f"- **Outliers Detectados**: {outlier.get('outlier_count', 0)}",
                f"- **Taxa de Outliers**: {outlier.get('outlier_rate', 0):.2f}%",
                "",
                f"**Status**: {self._status_badge(outlier.get('status', 'UNKNOWN'))} {outlier.get('status', 'N/A')}",
                "",
                "**Interpretação**: " + (
                    "Poucos outliers detectados. Os dados são consistentes."
                    if outlier.get('outlier_rate', 100) < 5 else
                    "Taxa elevada de outliers. Investigar jogos anômalos."
                ),
                ""
            ])
        
        lines.extend([
            "---",
            ""
        ])
        
        return lines
    
    def _generate_conclusions(self) -> list:
        """Gera seção de conclusões."""
        mech = self.data.get('mechanical_validation', {})
        ped = self.data.get('pedagogical_metrics', {})
        stat = self.data.get('statistical_robustness', {})
        
        mech_status = mech.get('overall_status', '')
        ped_status = ped.get('overall_status', '')
        stat_status = stat.get('overall_status', '')
        
        # Determinar conclusão geral
        all_pass = all('PASS' in s or 'ROBUST' in s for s in [mech_status, ped_status, stat_status])
        any_fail = any('FAIL' in s for s in [mech_status, ped_status, stat_status])
        
        if all_pass:
            conclusion_text = """
O jogo **Code Sandwich** foi validado com sucesso através de simulações computacionais com agentes de IA. Os resultados demonstram que:

1. **O jogo não está quebrado**: Todas as mecânicas funcionam corretamente, com alta taxa de conclusão e sem deadlocks ou loops infinitos detectados.

2. **A estrutura pedagógica é robusta**: Há cobertura completa dos Knowledge Components definidos, com distribuição adequada de dificuldade e progressão suave nas receitas.

3. **Os resultados são estatisticamente confiáveis**: O tamanho da amostra é suficiente para conclusões robustas, com intervalos de confiança estreitos e poder estatístico adequado.

4. **O jogo é balanceado**: Não há vantagem significativa por posição de jogador, e há alta diversidade de estratégias vencedoras (receitas).

Esta validação computacional fornece **evidência sólida** de que o jogo está pronto para testes com humanos e pode ser utilizado como ferramenta educacional para ensino de conceitos de programação.
"""
        elif any_fail:
            conclusion_text = """
A validação identificou **problemas críticos** que requerem correção antes de prosseguir com testes humanos:

- Revisar mecânicas que falharam nos testes
- Ajustar balanceamento de cartas e receitas
- Corrigir possíveis deadlocks ou condições de empate excessivas

Recomenda-se executar nova rodada de validação após as correções.
"""
        else:
            conclusion_text = """
O jogo **Code Sandwich** foi validado com **aprovação condicional**. Os resultados indicam que:

1. As mecânicas fundamentais funcionam corretamente.
2. A estrutura pedagógica é adequada, mas pode ser aprimorada.
3. Alguns aspectos requerem atenção antes de testes com humanos.

**Recomendações**:
- Aumentar o número de simulações para maior robustez estatística (idealmente 1000+ jogos)
- Ajustar cartas ou receitas com baixa exposição
- Revisar KCs com baixa redundância
- Considerar rebalancear receitas com saltos grandes de dificuldade

Com esses ajustes, o jogo estará pronto para validação com humanos.
"""
        
        return [
            "## 5. Conclusões e Recomendações",
            "",
            conclusion_text.strip(),
            "",
            "### 5.1 Limitações da Validação Computacional",
            "",
            "É importante reconhecer que esta validação com IA, embora robusta, possui limitações:",
            "",
            "- **Não valida aprendizado real**: Agentes de IA não aprendem conceitos de programação como humanos.",
            "- **Não mede engajamento**: Aspectos emocionais e motivacionais não são capturados.",
            "- **Não avalia intuitividade**: A clareza das metáforas para humanos requer validação qualitativa.",
            "- **Racionalidade perfeita**: Agentes não cometem erros conceituais como iniciantes reais.",
            "",
            "### 5.2 Próximos Passos Recomendados",
            "",
            "1. **Playtest Qualitativo**: Testar com 5-10 pessoas para avaliar usabilidade e clareza.",
            "2. **Estudo Piloto**: Aplicar pré-teste e pós-teste de conhecimento com pequeno grupo.",
            "3. **Ajustes Iterativos**: Refinar com base no feedback humano.",
            "4. **Estudo Experimental**: Validação pedagógica completa com grupo controle.",
            "",
            "---",
            ""
        ]
    
    def _generate_methodology(self) -> list:
        """Gera seção de metodologia."""
        metadata = self.data.get('metadata', {})
        
        return [
            "## 6. Metodologia de Validação",
            "",
            "### 6.1 Abordagem",
            "",
            "A validação foi realizada através de **simulações computacionais** utilizando agentes de IA com diferentes níveis de sofisticação:",
            "",
            "- **Heuristic Agent**: As simulações principais foram executadas utilizando um agente com regras heurísticas pré-definidas para garantir consistência na análise do design do jogo.",
            "",
            "### 6.2 Dados Analisados",
            "",
            f"- **Arquivo de Log**: `{metadata.get('log_file', 'N/A')}`",
            f"- **Arquivo de Cartas**: `{metadata.get('cards_file', 'N/A')}`",
            f"- **Arquivo de KCs**: `{metadata.get('kcs_file', 'N/A')}`",
            f"- **Total de Jogos**: {metadata.get('total_games_analyzed', 'N/A')}",
            "",
            "### 6.3 Métricas Calculadas",
            "",
            "**Validação Mecânica**:",
            "- Taxa de conclusão de jogos",
            "- Distribuição de duração (média, mediana, desvio padrão)",
            "- Balanceamento de vencedores (Chi-Quadrado, Coeficiente de Gini)",
            "- Diversidade de receitas (Entropia de Shannon)",
            "- Consistência temporal (ANOVA)",
            "",
            "**Validação Pedagógica**:",
            "- Cobertura de Knowledge Components",
            "- Distribuição de dificuldade dos KCs",
            "- Redundância de KCs (mapeamento KC → Cartas)",
            "- Progressão de dificuldade nas receitas",
            "- Exposição de KCs nas simulações",
            "",
            "**Robustez Estatística**:",
            "- Intervalos de confiança (95%)",
            "- Teste de normalidade (Shapiro-Wilk)",
            "- Poder estatístico",
            "- Análise de outliers (IQR)",
            "",
            "### 6.4 Ferramentas Utilizadas",
            "",
            "- **Python 3.11**: Linguagem de programação",
            "- **Pandas**: Manipulação de dados",
            "- **NumPy**: Computação numérica",
            "- **SciPy**: Testes estatísticos",
            "- **Matplotlib/Seaborn**: Visualização de dados",
            "- **RLCard**: Framework para ambientes de jogo",
            "",
            "---",
            "",
            f"*Relatório gerado automaticamente em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}*"
        ]
    
    def _status_badge(self, status: str) -> str:
        """Retorna emoji de badge baseado no status."""
        status_upper = status.upper()
        if 'PASS' in status_upper or 'ROBUST' in status_upper:
            return "🟢"
        elif 'FAIL' in status_upper:
            return "🔴"
        elif 'WARNING' in status_upper or 'MODERATE' in status_upper:
            return "🟡"
        else:
            return "⚪"


def main():
    """Execução standalone."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Gerador de Relatório')
    parser.add_argument('--metrics', default='analises/advanced_metrics_report.json', help='Arquivo JSON de métricas')
    parser.add_argument('--output', default='analises', help='Diretório de saída')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.metrics):
        print(f"❌ Arquivo de métricas não encontrado: {args.metrics}")
        print("Execute primeiro: python advanced_metrics.py")
        return
    
    print("="*60)
    print("GERADOR DE RELATÓRIO - CODE SANDWICH")
    print("="*60)
    
    generator = ReportGenerator(args.metrics, args.output)
    report_path = generator.generate_report()
    
    print("\n" + "="*60)
    print("RELATÓRIO GERADO COM SUCESSO!")
    print(f"Arquivo: {report_path}")
    print("="*60)


if __name__ == "__main__":
    main()

