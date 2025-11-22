"""
Métricas Avançadas para Validação Robusta do Code Sandwich
Foco: Validação mecânica, pedagógica e estatística
"""
import pandas as pd
import numpy as np
import json
import os
from collections import defaultdict, Counter
from scipy import stats
from typing import Dict, List, Tuple, Any
import matplotlib.pyplot as plt
import seaborn as sns

class AdvancedMetrics:
    """Classe para calcular métricas avançadas de validação."""
    
    def __init__(self, log_file: str, cards_file: str, kcs_file: str):
        """
        Inicializa com arquivos de dados.
        
        Args:
            log_file: Caminho para o CSV de logs de simulação
            cards_file: Caminho para o JSON de cartas
            kcs_file: Caminho para o JSON de KCs
        """
        self.log_file = log_file
        self.cards_file = cards_file
        self.kcs_file = kcs_file
        
        # Carregar dados
        self.df = self._load_log()
        self.cards = self._load_json(cards_file)
        self.kcs = self._load_json(kcs_file)
        
        # Preparar estruturas
        self.recipes = [c for c in self.cards if c.get('tipo') == 'Receita Final']
        self.ingredients = [c for c in self.cards if c.get('tipo') in ['Pão', 'Proteína', 'Vegetal', 'Condimento']]
        self.action_cards = [c for c in self.cards if c.get('tipo') == 'Ação']
        self.wildcard_cards = [c for c in self.cards if c.get('tipo') == 'Coringa']
        
    def _load_log(self) -> pd.DataFrame:
        """Carrega log de simulação."""
        if not os.path.exists(self.log_file):
            print(f"AVISO: Ficheiro de log não encontrado: {self.log_file}")
            return pd.DataFrame()
        try:
            return pd.read_csv(self.log_file)
        except pd.errors.EmptyDataError:
            print(f"AVISO: Ficheiro de log está vazio: {self.log_file}")
            return pd.DataFrame()
        except pd.errors.ParserError as e:
            print(f"ERRO ao fazer parse do CSV {self.log_file}: {e}")
            return pd.DataFrame()
        except FileNotFoundError:
             print(f"ERRO: Ficheiro de log não encontrado (FileNotFoundError): {self.log_file}")
             return pd.DataFrame()
        except Exception as e:
            print(f"ERRO inesperado ao carregar log {self.log_file}: {e}")
            return pd.DataFrame()
    
    def _load_json(self, filepath: str) -> List[Dict] | Dict:
        """Carrega arquivo JSON."""
        default_return = {} if 'kcs.json' in filepath else []
        if not os.path.exists(filepath):
            print(f"AVISO: Ficheiro JSON não encontrado: {filepath}")
            return default_return
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
                return data if isinstance(data, list) else default_return
        except json.JSONDecodeError as e:
             print(f"ERRO ao decodificar JSON {filepath}: {e}")
             return default_return
        except Exception as e:
            print(f"ERRO inesperado ao carregar JSON {filepath}: {e}")
            return default_return
    
    # ============================================================
    # MÉTRICAS DE VALIDAÇÃO MECÂNICA (Jogo não está quebrado)
    # ============================================================
    
    def mechanical_validation_report(self) -> Dict[str, Any]:
        """
        Gera relatório completo de validação mecânica.
        Prova que o jogo funciona corretamente.
        """
        report = {
            "timestamp": pd.Timestamp.now().isoformat(),
            "total_games": len(self.df),
            "metrics": {}
        }
        
        if self.df.empty:
            report["status"] = "NO_DATA"
            return report
        
        # 1. Taxa de Conclusão de Jogos
        completed_games = len(self.df[self.df['winner'] != 'Draw'])
        completion_rate = (completed_games / len(self.df)) * 100 if len(self.df) > 0 else 0
        
        report["metrics"]["game_completion"] = {
            "completed_games": int(completed_games),
            "total_games": int(len(self.df)),
            "completion_rate": float(completion_rate),
            "status": "PASS" if completion_rate > 80 else "WARNING" if completion_rate > 50 else "FAIL"
        }
        
        # 2. Duração dos Jogos (Detectar loops infinitos ou jogos muito curtos)
        if 'turns' in self.df.columns:
            turns_stats = {
                "mean": float(self.df['turns'].mean()),
                "median": float(self.df['turns'].median()),
                "std": float(self.df['turns'].std()),
                "min": int(self.df['turns'].min()),
                "max": int(self.df['turns'].max()),
                "q25": float(self.df['turns'].quantile(0.25)),
                "q75": float(self.df['turns'].quantile(0.75))
            }
            
            # Detectar anomalias
            too_short = len(self.df[self.df['turns'] < 5])
            too_long = len(self.df[self.df['turns'] > 100])
            
            report["metrics"]["game_duration"] = {
                "statistics": turns_stats,
                "anomalies": {
                    "too_short_games": int(too_short),
                    "too_long_games": int(too_long),
                    "anomaly_rate": float((too_short + too_long) / len(self.df) * 100)
                },
                "status": "PASS" if (too_short + too_long) / len(self.df) < 0.1 else "WARNING"
            }
        
        # 3. Distribuição de Vencedores (Detectar viés de jogador)
        if 'winner' in self.df.columns:
            winner_counts = self.df[self.df['winner'] != 'Draw']['winner'].value_counts()
            total_wins = winner_counts.sum()
            
            winner_distribution = {}
            for player, count in winner_counts.items():
                winner_distribution[str(player)] = {
                    "wins": int(count),
                    "win_rate": float(count / total_wins * 100) if total_wins > 0 else 0
                }
            
            # Chi-square test para uniformidade
            expected_freq = total_wins / len(winner_counts) if len(winner_counts) > 0 else 0
            chi2_stat, chi2_pvalue = stats.chisquare(winner_counts) if len(winner_counts) > 1 else (0, 1)
            
            # Calcular Gini coefficient (desigualdade)
            win_rates = [d["wins"] for d in winner_distribution.values()]
            gini = self._calculate_gini(win_rates)
            
            report["metrics"]["winner_distribution"] = {
                "distribution": winner_distribution,
                "balance_tests": {
                    "chi_square_statistic": float(chi2_stat),
                    "chi_square_pvalue": float(chi2_pvalue),
                    "is_balanced": bool(chi2_pvalue > 0.05),
                    "gini_coefficient": float(gini),
                    "gini_interpretation": "Balanced" if gini < 0.2 else "Moderate" if gini < 0.4 else "Imbalanced"
                },
                "status": "PASS" if chi2_pvalue > 0.05 and gini < 0.3 else "WARNING"
            }
        
        # 4. Diversidade de Receitas Vencedoras
        if 'winning_recipe' in self.df.columns:
            recipe_counts = self.df[self.df['winning_recipe'].notna()]['winning_recipe'].value_counts()
            total_recipes_in_game = len(self.recipes)
            unique_recipes_won = len(recipe_counts)
            
            recipe_diversity = (unique_recipes_won / total_recipes_in_game * 100) if total_recipes_in_game > 0 else 0
            
            # Shannon entropy (diversidade)
            entropy = stats.entropy(recipe_counts) if len(recipe_counts) > 0 else 0
            max_entropy = np.log(len(recipe_counts)) if len(recipe_counts) > 0 else 1
            normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
            
            report["metrics"]["recipe_diversity"] = {
                "unique_recipes_won": int(unique_recipes_won),
                "total_recipes_available": int(total_recipes_in_game),
                "diversity_rate": float(recipe_diversity),
                "shannon_entropy": float(entropy),
                "normalized_entropy": float(normalized_entropy),
                "most_common_recipe": str(recipe_counts.index[0]) if len(recipe_counts) > 0 else "N/A",
                "most_common_count": int(recipe_counts.iloc[0]) if len(recipe_counts) > 0 else 0,
                "status": "PASS" if recipe_diversity > 70 else "WARNING" if recipe_diversity > 50 else "FAIL"
            }
        
        # 5. Consistência de Resultados (Reprodutibilidade)
        if len(self.df) >= 10:
            # Dividir em blocos e comparar estatísticas
            block_size = len(self.df) // 5
            blocks = [self.df.iloc[i*block_size:(i+1)*block_size] for i in range(5)]
            
            block_means = [block['turns'].mean() for block in blocks if 'turns' in block.columns and not block.empty]
            
            if len(block_means) > 1:
                # ANOVA para verificar se blocos são estatisticamente similares
                f_stat, anova_pvalue = stats.f_oneway(*[block['turns'].dropna() for block in blocks if 'turns' in block.columns and not block.empty])
                
                report["metrics"]["consistency"] = {
                    "block_means": [float(m) for m in block_means],
                    "coefficient_of_variation": float(np.std(block_means) / np.mean(block_means) * 100) if np.mean(block_means) > 0 else 0,
                    "anova_f_statistic": float(f_stat),
                    "anova_pvalue": float(anova_pvalue),
                    "is_consistent": bool(anova_pvalue > 0.05),
                    "status": "PASS" if anova_pvalue > 0.05 else "WARNING"
                }
        
        # Status geral
        statuses = [m.get("status", "UNKNOWN") for m in report["metrics"].values() if isinstance(m, dict)]
        if all(s == "PASS" for s in statuses):
            report["overall_status"] = "PASS - Jogo mecanicamente sólido"
        elif any(s == "FAIL" for s in statuses):
            report["overall_status"] = "FAIL - Problemas mecânicos detectados"
        else:
            report["overall_status"] = "WARNING - Requer atenção"
        
        return report
    
    # ============================================================
    # MÉTRICAS PEDAGÓGICAS AVANÇADAS
    # ============================================================
    
    def pedagogical_metrics_report(self) -> Dict[str, Any]:
        """
        Gera relatório de métricas pedagógicas avançadas.
        Valida cobertura, progressão e exposição de conceitos.
        """
        report = {
            "timestamp": pd.Timestamp.now().isoformat(),
            "metrics": {}
        }
        
        # 1. Cobertura de Knowledge Components
        all_kcs = set(self.kcs.keys()) if isinstance(self.kcs, dict) else set()
        used_kcs = set()
        
        for card in self.cards:
            kc_list = card.get('kc_associado', [])
            if isinstance(kc_list, list):
                used_kcs.update(kc_list)
        
        coverage_rate = (len(used_kcs) / len(all_kcs) * 100) if len(all_kcs) > 0 else 0
        
        report["metrics"]["kc_coverage"] = {
            "total_kcs_defined": len(all_kcs),
            "kcs_used_in_cards": len(used_kcs),
            "coverage_rate": float(coverage_rate),
            "unused_kcs": list(all_kcs - used_kcs),
            "status": "PASS" if coverage_rate >= 95 else "WARNING"
        }
        
        # 2. Distribuição de Dificuldade dos KCs
        if isinstance(self.kcs, dict):
            difficulty_dist = defaultdict(int)
            for kc_id, kc_data in self.kcs.items():
                diff = kc_data.get('dificuldade', 0)
                difficulty_dist[diff] += 1
            
            total_kcs = sum(difficulty_dist.values())
            
            # Distribuição ideal (aproximadamente normal)
            ideal_dist = {1: 0.15, 2: 0.25, 3: 0.30, 4: 0.20, 5: 0.10}
            
            difficulty_analysis = {}
            deviation_score = 0
            
            for level in range(1, 6):
                actual_count = difficulty_dist.get(level, 0)
                actual_pct = (actual_count / total_kcs * 100) if total_kcs > 0 else 0
                ideal_pct = ideal_dist.get(level, 0) * 100
                deviation = abs(actual_pct - ideal_pct)
                deviation_score += deviation
                
                difficulty_analysis[f"level_{level}"] = {
                    "count": int(actual_count),
                    "percentage": float(actual_pct),
                    "ideal_percentage": float(ideal_pct),
                    "deviation": float(deviation)
                }
            
            avg_deviation = deviation_score / 5
            
            report["metrics"]["difficulty_distribution"] = {
                "distribution": difficulty_analysis,
                "average_deviation": float(avg_deviation),
                "balance_score": float(100 - avg_deviation),
                "status": "PASS" if avg_deviation < 10 else "WARNING"
            }
        
        # 3. Mapeamento KC → Cartas (Redundância)
        kc_to_cards = defaultdict(list)
        for card in self.cards:
            card_id = card.get('id', 'unknown')
            for kc in card.get('kc_associado', []):
                kc_to_cards[kc].append(card_id)
        
        redundancy_stats = {
            "min_cards_per_kc": min(len(cards) for cards in kc_to_cards.values()) if kc_to_cards else 0,
            "max_cards_per_kc": max(len(cards) for cards in kc_to_cards.values()) if kc_to_cards else 0,
            "mean_cards_per_kc": float(np.mean([len(cards) for cards in kc_to_cards.values()])) if kc_to_cards else 0,
            "median_cards_per_kc": float(np.median([len(cards) for cards in kc_to_cards.values()])) if kc_to_cards else 0
        }
        
        # KCs com baixa redundância (risco de não exposição)
        low_redundancy_kcs = {kc: len(cards) for kc, cards in kc_to_cards.items() if len(cards) < 2}
        
        report["metrics"]["kc_redundancy"] = {
            "statistics": redundancy_stats,
            "low_redundancy_kcs": low_redundancy_kcs,
            "low_redundancy_count": len(low_redundancy_kcs),
            "status": "PASS" if len(low_redundancy_kcs) < len(all_kcs) * 0.1 else "WARNING"
        }
        
        # 4. Progressão de Dificuldade nas Receitas
        recipe_difficulties = []
        for recipe in self.recipes:
            kcs_in_recipe = recipe.get('kc_associado', [])
            if kcs_in_recipe and isinstance(self.kcs, dict):
                difficulties = [self.kcs.get(kc, {}).get('dificuldade', 0) for kc in kcs_in_recipe if kc in self.kcs]
                if difficulties:
                    avg_diff = np.mean(difficulties)
                    recipe_difficulties.append({
                        "recipe_id": recipe.get('id'),
                        "recipe_name": recipe.get('nome'),
                        "average_difficulty": float(avg_diff),
                        "kc_count": len(kcs_in_recipe)
                    })
        
        recipe_difficulties.sort(key=lambda x: x['average_difficulty'])
        
        # Calcular "suavidade" da progressão (diferenças entre receitas consecutivas)
        if len(recipe_difficulties) > 1:
            diffs_between_recipes = [
                recipe_difficulties[i+1]['average_difficulty'] - recipe_difficulties[i]['average_difficulty']
                for i in range(len(recipe_difficulties) - 1)
            ]
            
            progression_smoothness = {
                "mean_step": float(np.mean(diffs_between_recipes)),
                "max_jump": float(max(diffs_between_recipes)),
                "std_step": float(np.std(diffs_between_recipes)),
                "large_jumps_count": sum(1 for d in diffs_between_recipes if d > 1.0)
            }
            
            report["metrics"]["difficulty_progression"] = {
                "recipe_progression": recipe_difficulties,
                "smoothness_analysis": progression_smoothness,
                "status": "PASS" if progression_smoothness["max_jump"] < 1.5 else "WARNING"
            }
        
        # 5. Exposição de KCs em Simulações
        if not self.df.empty and 'winning_recipe' in self.df.columns:
            exposed_kcs = set()
            kc_exposure_count = defaultdict(int)
            
            for recipe_name in self.df['winning_recipe'].dropna():
                recipe = next((r for r in self.recipes if r.get('nome') == recipe_name), None)
                if recipe:
                    for kc in recipe.get('kc_associado', []):
                        exposed_kcs.add(kc)
                        kc_exposure_count[kc] += 1
            
            exposure_rate = (len(exposed_kcs) / len(all_kcs) * 100) if len(all_kcs) > 0 else 0
            
            # KCs nunca expostos
            never_exposed = list(all_kcs - exposed_kcs)
            
            # KCs raramente expostos (< 5% dos jogos)
            threshold = len(self.df) * 0.05
            rarely_exposed = {kc: count for kc, count in kc_exposure_count.items() if count < threshold}
            
            report["metrics"]["kc_exposure_in_games"] = {
                "total_games_analyzed": len(self.df),
                "kcs_exposed": len(exposed_kcs),
                "exposure_rate": float(exposure_rate),
                "never_exposed_kcs": never_exposed,
                "rarely_exposed_kcs": rarely_exposed,
                "mean_exposures_per_kc": float(np.mean(list(kc_exposure_count.values()))) if kc_exposure_count else 0,
                "status": "PASS" if exposure_rate > 90 else "WARNING"
            }
        
        # Status geral
        statuses = [m.get("status", "UNKNOWN") for m in report["metrics"].values() if isinstance(m, dict)]
        if all(s == "PASS" for s in statuses):
            report["overall_status"] = "PASS - Pedagogicamente robusto"
        else:
            report["overall_status"] = "WARNING - Requer ajustes pedagógicos"
        
        return report
    
    # ============================================================
    # MÉTRICAS ESTATÍSTICAS (Robustez e Confiabilidade)
    # ============================================================
    
    def statistical_robustness_report(self) -> Dict[str, Any]:
        """
        Análise estatística de robustez e confiabilidade dos resultados.
        """
        report = {
            "timestamp": pd.Timestamp.now().isoformat(),
            "sample_size": len(self.df),
            "metrics": {}
        }
        
        if self.df.empty or len(self.df) < 30:
            report["status"] = "INSUFFICIENT_DATA"
            report["message"] = f"Amostra muito pequena ({len(self.df)} jogos). Mínimo recomendado: 30 jogos."
            return report
        
        # 1. Intervalos de Confiança (95%) para métricas principais
        if 'turns' in self.df.columns:
            turns_mean = self.df['turns'].mean()
            turns_sem = stats.sem(self.df['turns'])
            turns_ci = stats.t.interval(0.95, len(self.df)-1, loc=turns_mean, scale=turns_sem)
            
            report["metrics"]["turns_confidence_interval"] = {
                "mean": float(turns_mean),
                "confidence_level": 0.95,
                "lower_bound": float(turns_ci[0]),
                "upper_bound": float(turns_ci[1]),
                "margin_of_error": float(turns_ci[1] - turns_mean)
            }
        
        # 2. Teste de Normalidade (Shapiro-Wilk)
        if 'turns' in self.df.columns and len(self.df) >= 3:
            shapiro_stat, shapiro_p = stats.shapiro(self.df['turns'].dropna())
            
            report["metrics"]["normality_test"] = {
                "test": "Shapiro-Wilk",
                "statistic": float(shapiro_stat),
                "pvalue": float(shapiro_p),
                "is_normal": bool(shapiro_p > 0.05),
                "interpretation": "Distribuição normal" if shapiro_p > 0.05 else "Distribuição não-normal"
            }
        
        # 3. Poder Estatístico (Estimativa)
        effect_size = 0.5  # Efeito médio esperado
        alpha = 0.05
        
        # Estimativa simples de poder
        from scipy.stats import norm
        z_alpha = norm.ppf(1 - alpha/2)
        z_beta = np.sqrt(len(self.df)) * effect_size - z_alpha
        power = norm.cdf(z_beta)
        
        report["metrics"]["statistical_power"] = {
            "sample_size": len(self.df),
            "assumed_effect_size": effect_size,
            "alpha": alpha,
            "estimated_power": float(power),
            "power_interpretation": "Adequado" if power > 0.8 else "Baixo" if power > 0.5 else "Insuficiente",
            "recommended_sample_size": int(((z_alpha + norm.ppf(0.8)) / effect_size) ** 2) if power < 0.8 else len(self.df)
        }
        
        # 4. Análise de Outliers
        if 'turns' in self.df.columns:
            Q1 = self.df['turns'].quantile(0.25)
            Q3 = self.df['turns'].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = self.df[(self.df['turns'] < lower_bound) | (self.df['turns'] > upper_bound)]
            outlier_rate = (len(outliers) / len(self.df) * 100)
            
            report["metrics"]["outlier_analysis"] = {
                "method": "IQR (Interquartile Range)",
                "lower_bound": float(lower_bound),
                "upper_bound": float(upper_bound),
                "outlier_count": int(len(outliers)),
                "outlier_rate": float(outlier_rate),
                "status": "PASS" if outlier_rate < 5 else "WARNING"
            }
        
        # Status geral
        if report["metrics"].get("statistical_power", {}).get("estimated_power", 0) > 0.8:
            report["overall_status"] = "ROBUST - Resultados estatisticamente confiáveis"
        elif report["metrics"].get("statistical_power", {}).get("estimated_power", 0) > 0.5:
            report["overall_status"] = "MODERATE - Aumentar amostra recomendado"
        else:
            report["overall_status"] = "WEAK - Amostra insuficiente para conclusões robustas"
        
        return report
    
    # ============================================================
    # FUNÇÕES AUXILIARES
    # ============================================================
    
    def _calculate_gini(self, values: List[float]) -> float:
        """Calcula coeficiente de Gini (desigualdade)."""
        if not values or len(values) == 0:
            return 0.0
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        cumsum = np.cumsum(sorted_values)
        
        return (2 * np.sum((np.arange(1, n+1)) * sorted_values)) / (n * cumsum[-1]) - (n + 1) / n if cumsum[-1] > 0 else 0.0
    
    # ============================================================
    # GERAÇÃO DE RELATÓRIO CONSOLIDADO
    # ============================================================
    
    def generate_full_report(self, output_dir: str = 'analises') -> str:
        """
        Gera relatório JSON consolidado com todas as métricas.
        
        Returns:
            Caminho do arquivo gerado
        """
        os.makedirs(output_dir, exist_ok=True)
        
        full_report = {
            "metadata": {
                "timestamp": pd.Timestamp.now().isoformat(),
                "log_file": self.log_file,
                "cards_file": self.cards_file,
                "kcs_file": self.kcs_file,
                "total_games_analyzed": len(self.df)
            },
            "mechanical_validation": self.mechanical_validation_report(),
            "pedagogical_metrics": self.pedagogical_metrics_report(),
            "statistical_robustness": self.statistical_robustness_report()
        }
        
        # Salvar JSON
        output_path = os.path.join(output_dir, 'advanced_metrics_report.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(full_report, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Relatório avançado salvo: {output_path}")
        
        return output_path
    
    def generate_visualizations(self, output_dir: str = 'analises'):
        """Gera visualizações das métricas."""
        os.makedirs(output_dir, exist_ok=True)
        
        if self.df.empty:
            print("Sem dados para visualização")
            return
        
        sns.set_theme(style="whitegrid", palette="muted")
        
        # 1. Distribuição de duração com estatísticas
        if 'turns' in self.df.columns:
            fig, ax = plt.subplots(figsize=(12, 6))
            
            sns.histplot(self.df['turns'], kde=True, bins=30, ax=ax)
            
            mean_turns = self.df['turns'].mean()
            median_turns = self.df['turns'].median()
            
            ax.axvline(mean_turns, color='red', linestyle='--', linewidth=2, label=f'Média: {mean_turns:.1f}')
            ax.axvline(median_turns, color='green', linestyle='--', linewidth=2, label=f'Mediana: {median_turns:.1f}')
            
            ax.set_title('Distribuição de Duração dos Jogos (Turnos)', fontsize=16, fontweight='bold')
            ax.set_xlabel('Número de Turnos', fontsize=12)
            ax.set_ylabel('Frequência', fontsize=12)
            ax.legend(fontsize=10)
            
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'game_duration_detailed.png'), dpi=300)
            plt.close()
            
            print(f"✓ Visualização salva: game_duration_detailed.png")
        
        # 2. Balanceamento de vencedores
        if 'winner' in self.df.columns:
            winner_data = self.df[self.df['winner'] != 'Draw']['winner'].value_counts()
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            colors = sns.color_palette("husl", len(winner_data))
            winner_data.plot(kind='bar', ax=ax, color=colors)
            
            # Adicionar linha de referência (distribuição uniforme)
            expected_wins = len(self.df[self.df['winner'] != 'Draw']) / len(winner_data)
            ax.axhline(expected_wins, color='red', linestyle='--', linewidth=2, label=f'Distribuição Uniforme: {expected_wins:.1f}')
            
            ax.set_title('Distribuição de Vitórias por Jogador', fontsize=16, fontweight='bold')
            ax.set_xlabel('Jogador', fontsize=12)
            ax.set_ylabel('Número de Vitórias', fontsize=12)
            ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
            ax.legend(fontsize=10)
            
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'winner_balance.png'), dpi=300)
            plt.close()
            
            print(f"✓ Visualização salva: winner_balance.png")
        
        # 3. Diversidade de receitas
        if 'winning_recipe' in self.df.columns:
            recipe_data = self.df[self.df['winning_recipe'].notna()]['winning_recipe'].value_counts().head(15)
            
            fig, ax = plt.subplots(figsize=(14, 8))
            
            colors = sns.color_palette("viridis", len(recipe_data))
            recipe_data.plot(kind='barh', ax=ax, color=colors)
            
            ax.set_title('Top 15 Receitas Mais Completadas', fontsize=16, fontweight='bold')
            ax.set_xlabel('Número de Vitórias', fontsize=12)
            ax.set_ylabel('Receita', fontsize=12)
            
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'recipe_diversity.png'), dpi=300)
            plt.close()
            
            print(f"✓ Visualização salva: recipe_diversity.png")


# ============================================================
# FUNÇÃO PRINCIPAL PARA EXECUÇÃO STANDALONE
# ============================================================

def main():
    """Execução standalone do módulo."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Métricas Avançadas de Validação - Code Sandwich')
    parser.add_argument('--log', default='logs/simulation_logs_original.csv', help='Arquivo de log CSV')
    parser.add_argument('--cards', default='cartas.json', help='Arquivo de cartas JSON')
    parser.add_argument('--kcs', default='kcs.json', help='Arquivo de KCs JSON')
    parser.add_argument('--output', default='analises', help='Diretório de saída')
    
    args = parser.parse_args()
    
    print("="*60)
    print("MÉTRICAS AVANÇADAS DE VALIDAÇÃO - CODE SANDWICH")
    print("="*60)
    
    metrics = AdvancedMetrics(args.log, args.cards, args.kcs)
    
    print("\n[1/3] Gerando relatório consolidado...")
    report_path = metrics.generate_full_report(args.output)
    
    print("\n[2/3] Gerando visualizações...")
    metrics.generate_visualizations(args.output)
    
    print("\n[3/3] Resumo dos resultados:")
    
    # Carregar e exibir resumo
    with open(report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    print(f"\n✓ Validação Mecânica: {report['mechanical_validation'].get('overall_status', 'N/A')}")
    print(f"✓ Métricas Pedagógicas: {report['pedagogical_metrics'].get('overall_status', 'N/A')}")
    print(f"✓ Robustez Estatística: {report['statistical_robustness'].get('overall_status', 'N/A')}")
    
    print("\n" + "="*60)
    print("ANÁLISE CONCLUÍDA!")
    print("="*60)


if __name__ == "__main__":
    main()

