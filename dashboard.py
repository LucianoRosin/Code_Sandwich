"""
Dashboard Interativo - Code Sandwich
Inclui: Knowledge Tracing + Eficácia Pedagógica + Análise Pedagógica + Balanceamento
"""

import streamlit as st
import os
import json
from pathlib import Path
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import DEFAULT_GAME_CONFIG

# --- Constantes do Dashboard ---
ANALYSIS_DIR = "analises"
ACP_RELATORIO = os.path.join(ANALYSIS_DIR, "RELATORIO_ACP.md")
BALANCE_IA_RELATORIO = os.path.join(ANALYSIS_DIR, "RELATORIO_BALANCEAMENTO_IA.md")
RELATORIO = os.path.join(ANALYSIS_DIR, "RELATORIO_VALIDACAO.md")
ADVANCED_METRICS_JSON = os.path.join(ANALYSIS_DIR, "advanced_metrics_report.json")
KT_METRICS_JSON = os.path.join(ANALYSIS_DIR, "metrics.json")
EFICACIA_JSON = os.path.join(ANALYSIS_DIR, "eficacia_pedagogica.json")

# Imagens - Básicas
IMG_DURACAO_JOGO = os.path.join(ANALYSIS_DIR, "game_duration_distribution_original.png")
IMG_FREQUENCIA_RECEITAS = os.path.join(ANALYSIS_DIR, "recipe_completion_frequency_original.png")
IMG_DURACAO_DETALHADA = os.path.join(ANALYSIS_DIR, "game_duration_detailed.png")
IMG_BALANCEAMENTO = os.path.join(ANALYSIS_DIR, "winner_balance.png")
IMG_DIVERSIDADE = os.path.join(ANALYSIS_DIR, "recipe_diversity.png")

# Imagens - Knowledge Tracing
IMG_KT_ROC = os.path.join(ANALYSIS_DIR, "gamedkt_roc_curve.png")
IMG_KT_CONFUSION = os.path.join(ANALYSIS_DIR, "gamedkt_confusion_matrix.png")
IMG_KT_HISTORY = os.path.join(ANALYSIS_DIR, "gamedkt_training_history.png")
IMG_KT_COMPARISON = os.path.join(ANALYSIS_DIR, "gamedkt_model_comparison.png")

# Imagens - Eficácia Pedagógica
IMG_CURVA_APRENDIZADO = os.path.join(ANALYSIS_DIR, "curva_aprendizado.png")
IMG_COMPARACAO_PERSONAS = os.path.join(ANALYSIS_DIR, "comparacao_personas.png")
IMG_MAESTRIA_KC = os.path.join(ANALYSIS_DIR, "maestria_por_kc.png")
IMG_PROGRESSAO_TEMPORAL = os.path.join(ANALYSIS_DIR, "progressao_temporal.png")
IMG_EFICACIA_RECEITAS = os.path.join(ANALYSIS_DIR, "eficacia_receitas.png")

# --- Funções Auxiliares ---
def carregar_markdown(caminho_arquivo, erro_msg="Relatório não encontrado!"):
    """Carrega o conteúdo de um arquivo markdown."""
    if os.path.exists(caminho_arquivo):
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            st.error(f"Erro ao ler o arquivo '{caminho_arquivo}': {e}")
            return f"**Erro ao ler o arquivo:** {e}"
    st.warning(f"{erro_msg}\n\nVerifique se o arquivo existe em `{caminho_arquivo}`. Execute `python main.py` para gerar.")
    return None

def carregar_json(caminho_arquivo):
    """Carrega arquivo JSON."""
    if os.path.exists(caminho_arquivo):
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Erro ao ler JSON '{caminho_arquivo}': {e}")
            return None
    return None

def exibir_status_badge(status):
    """Retorna emoji de badge baseado no status."""
    status_upper = status.upper() if status else ""
    if 'PASS' in status_upper or 'ROBUST' in status_upper:
        return "🟢"
    elif 'FAIL' in status_upper:
        return "🔴"
    elif 'WARNING' in status_upper or 'MODERATE' in status_upper:
        return "🟡"
    else:
        return "⚪"

# --- Configuração da Página ---
st.set_page_config(layout="wide", page_title="Dashboard Code Sandwich")
st.title("🎮 Dashboard - Code Sandwich")
st.subheader("Validação Pedagógica e Funcional Completa")

# --- Abas ---
tab_eficacia, tab_kt, tab_validacao, tab_pedagogico, tab_balanceamento, tab_metricas = st.tabs([
    "📈 Eficácia Pedagógica",
    "🧠 Knowledge Tracing",
    "⭐ Relatório de Validação",
    "🎓 Análise Pedagógica",
    "📊 Balanceamento",
    "📈 Métricas Avançadas"
])

# === ABA 1: EFICÁCIA PEDAGÓGICA (NOVA) ===
with tab_eficacia:
    st.header("📈 Eficácia Pedagógica")
    st.info("📊 Análise que prova se o jogo ensina conceitos de programação.")
    
    eficacia_data = carregar_json(EFICACIA_JSON)
    
    if eficacia_data:
        st.success("✅ Análise de eficácia pedagógica disponível!")
        
        # Resumo Executivo
        st.subheader("📊 Resumo Executivo")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_jogos = eficacia_data.get('metadata', {}).get('total_jogos', 0)
            st.metric("🎲 Jogos Analisados", f"{total_jogos}")
        
        with col2:
            total_acoes = eficacia_data.get('metadata', {}).get('total_acoes', 0)
            st.metric("🎯 Ações Registradas", f"{total_acoes}")
        
        with col3:
            total_jogadores = eficacia_data.get('metadata', {}).get('total_jogadores', 0)
            st.metric("👥 Jogadores", f"{total_jogadores}")
        
        st.divider()
        
        # Curva de Aprendizado
        st.subheader("📈 Curva de Aprendizado")
        
        curva = eficacia_data.get('curva_aprendizado', {})
        
        if curva:
            col1, col2, col3 = st.columns(3)
            
            for i, (persona, dados) in enumerate(curva.items()):
                col = [col1, col2, col3][i]
                with col:
                    st.markdown(f"**{persona}**")
                    melhoria = dados.get('melhoria_percentual', 0)
                    delta_color = "normal" if melhoria > 5 else "off"
                    st.metric(
                        "Taxa Inicial",
                        f"{dados.get('taxa_inicial', 0)*100:.1f}%"
                    )
                    st.metric(
                        "Taxa Final",
                        f"{dados.get('taxa_final', 0)*100:.1f}%",
                        delta=f"{melhoria:+.1f}%",
                        delta_color=delta_color
                    )
        
        if os.path.exists(IMG_CURVA_APRENDIZADO):
            st.image(IMG_CURVA_APRENDIZADO, use_container_width=True, caption="Curva de Aprendizado por Persona")
        
        st.divider()
        
        # Comparação entre Personas
        st.subheader("🎯 Comparação entre Personas")
        
        if os.path.exists(IMG_COMPARACAO_PERSONAS):
            st.image(IMG_COMPARACAO_PERSONAS, use_container_width=True)
        
        personas_data = eficacia_data.get('analise_personas', {})
        
        if personas_data:
            cols = st.columns(len(personas_data))
            for i, (persona, dados) in enumerate(personas_data.items()):
                with cols[i]:
                    st.markdown(f"**{persona}**")
                    st.write(f"Taxa de Sucesso: {dados.get('taxa_sucesso', 0)*100:.1f}%")
                    st.write(f"Taxa de Otimalidade: {dados.get('taxa_otimalidade', 0)*100:.1f}%")
                    st.write(f"Turnos Médios: {dados.get('turnos_medio_por_jogo', 0):.1f}")
        
        st.divider()
        
        # Maestria por KC
        st.subheader("📚 Maestria por Knowledge Component")
        
        if os.path.exists(IMG_MAESTRIA_KC):
            st.image(IMG_MAESTRIA_KC, use_container_width=True)
        
        st.divider()
        
        # Progressão Temporal
        st.subheader("⏱️ Progressão Temporal")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if os.path.exists(IMG_PROGRESSAO_TEMPORAL):
                st.image(IMG_PROGRESSAO_TEMPORAL, use_container_width=True)
        
        with col2:
            progressao = eficacia_data.get('progressao_temporal', {})
            if progressao:
                st.markdown("**Evolução ao Longo do Tempo:**")
                for quartil, dados in progressao.items():
                    st.write(f"**{quartil}**")
                    st.write(f"  - Taxa de Sucesso: {dados.get('taxa_sucesso', 0)*100:.1f}%")
                    st.write(f"  - Taxa de Otimalidade: {dados.get('taxa_otimalidade', 0)*100:.1f}%")
        
        st.divider()
        
        # Eficácia de Receitas
        st.subheader("🍔 Eficácia de Receitas")
        
        if os.path.exists(IMG_EFICACIA_RECEITAS):
            st.image(IMG_EFICACIA_RECEITAS, use_container_width=True)
        
        # Download
        st.download_button(
            label="⬇️ Baixar Relatório de Eficácia (JSON)",
            data=json.dumps(eficacia_data, indent=2, ensure_ascii=False),
            file_name="eficacia_pedagogica.json",
            mime="application/json"
        )
        
    else:
        st.error("❌ Análise de eficácia pedagógica não encontrada.")
        st.info("Execute `python main.py` para gerar a análise completa.")

# === ABA 2: KNOWLEDGE TRACING ===
with tab_kt:
    st.header("🧠 Knowledge Tracing")
    st.info("📊 Modelo de IA que rastreia o conhecimento dos jogadores ao longo do tempo.")
    
    kt_metrics = carregar_json(KT_METRICS_JSON)
    
    if kt_metrics:
        st.success("✅ Modelo de Knowledge Tracing treinado!")
        
        # Métricas principais
        st.subheader("📊 Performance do Modelo")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            accuracy = kt_metrics.get('accuracy', 0) * 100
            st.metric("🎯 Acurácia", f"{accuracy:.2f}%", 
                     delta="Excelente" if accuracy > 80 else "Bom" if accuracy > 70 else "Regular")
        
        with col2:
            auc = kt_metrics.get('auc', 0)
            st.metric("📈 AUC", f"{auc:.3f}",
                     delta="Excelente" if auc > 0.85 else "Bom" if auc > 0.75 else "Regular")
        
        with col3:
            loss = kt_metrics.get('loss', 0)
            st.metric("📉 Loss", f"{loss:.4f}")
        
        st.divider()
        
        # Visualizações
        st.subheader("📊 Visualizações")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if os.path.exists(IMG_KT_ROC):
                st.image(IMG_KT_ROC, use_container_width=True, caption="Curva ROC")
            else:
                st.warning("Curva ROC não encontrada")
        
        with col2:
            if os.path.exists(IMG_KT_CONFUSION):
                st.image(IMG_KT_CONFUSION, use_container_width=True, caption="Matriz de Confusão")
            else:
                st.warning("Matriz de Confusão não encontrada")
        
        if os.path.exists(IMG_KT_HISTORY):
            st.image(IMG_KT_HISTORY, use_container_width=True, caption="Histórico de Treinamento")
        
        if os.path.exists(IMG_KT_COMPARISON):
            st.image(IMG_KT_COMPARISON, use_container_width=True, caption="Comparação entre Modelos")
        
        st.divider()
        
        # Relatório de classificação
        st.subheader("📋 Relatório de Classificação")
        
        class_report = kt_metrics.get('classification_report', {})
        if class_report:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Classe: Falha**")
                falha = class_report.get('Falha', {})
                st.write(f"- Precisão: {falha.get('precision', 0):.2%}")
                st.write(f"- Recall: {falha.get('recall', 0):.2%}")
                st.write(f"- F1-Score: {falha.get('f1-score', 0):.2%}")
            
            with col2:
                st.markdown("**Classe: Sucesso**")
                sucesso = class_report.get('Sucesso', {})
                st.write(f"- Precisão: {sucesso.get('precision', 0):.2%}")
                st.write(f"- Recall: {sucesso.get('recall', 0):.2%}")
                st.write(f"- F1-Score: {sucesso.get('f1-score', 0):.2%}")
        
        st.divider()
        
        # Download
        st.download_button(
            label="⬇️ Baixar Métricas (JSON)",
            data=json.dumps(kt_metrics, indent=2, ensure_ascii=False),
            file_name="knowledge_tracing_metrics.json",
            mime="application/json"
        )
        
    else:
        st.error("❌ Modelo de Knowledge Tracing não encontrado.")
        st.info("Execute `python main.py` para treinar o modelo.")

# === ABA 3: VALIDAÇÃO ===
with tab_validacao:
    st.header("⭐ Relatório de Validação")
    st.info("📄 Relatório com validação mecânica, pedagógica e estatística.")
    
    relatorio = carregar_markdown(RELATORIO, "Relatório de Validação não encontrado!")
    
    if relatorio:
        metrics_data = carregar_json(ADVANCED_METRICS_JSON)
        
        if metrics_data:
            st.success("✅ Relatório de validação completo disponível!")
            
            st.subheader("📊 Resumo Executivo")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                mech_status = metrics_data.get('mechanical_validation', {}).get('overall_status', 'N/A')
                badge = exibir_status_badge(mech_status)
                st.metric(f"{badge} Validação Mecânica", "Funcionalidade", delta=mech_status)
                
            with col2:
                ped_status = metrics_data.get('pedagogical_metrics', {}).get('overall_status', 'N/A')
                badge = exibir_status_badge(ped_status)
                st.metric(f"{badge} Validação Pedagógica", "Estrutura Curricular", delta=ped_status)
                
            with col3:
                stat_status = metrics_data.get('statistical_robustness', {}).get('overall_status', 'N/A')
                badge = exibir_status_badge(stat_status)
                st.metric(f"{badge} Robustez Estatística", "Confiabilidade", delta=stat_status)
            
            st.divider()
        
        with st.expander("📖 Clique para expandir o relatório completo", expanded=False):
            st.markdown(relatorio, unsafe_allow_html=True)
        
        st.download_button(
            label="⬇️ Baixar Relatório (Markdown)",
            data=relatorio,
            file_name="RELATORIO_VALIDACAO.md",
            mime="text/markdown"
        )
        
    else:
        st.error("❌ Relatório de Validação não encontrado.")
        st.info("Execute `python main.py` para gerar o relatório.")

# === ABA 4: ANÁLISE PEDAGÓGICA ===
with tab_pedagogico:
    st.header("🎓 Análise de Coerência Pedagógica (ACP)")
    st.info("Auditoria do design educacional do jogo com auxílio de IA.")
    
    relatorio_acp_md = carregar_markdown(ACP_RELATORIO, "Relatório ACP não encontrado!")
    
    if relatorio_acp_md:
        st.markdown(relatorio_acp_md, unsafe_allow_html=True)
        
        st.download_button(
            label="⬇️ Baixar Relatório ACP (Markdown)",
            data=relatorio_acp_md,
            file_name="RELATORIO_ACP.md",
            mime="text/markdown"
        )

# === ABA 5: BALANCEAMENTO ===
with tab_balanceamento:
    st.header("📊 Análise de Balanceamento Mecânico")
    st.info("Validação da funcionalidade e equilíbrio do jogo.")
    
    st.subheader("Resultados da Simulação")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Distribuição da Duração do Jogo")
        if os.path.exists(IMG_DURACAO_JOGO):
            st.image(IMG_DURACAO_JOGO, use_container_width=True)
        else:
            st.warning("Imagem não encontrada")
            
    with col2:
        st.markdown("#### Frequência de Conclusão de Receitas")
        if os.path.exists(IMG_FREQUENCIA_RECEITAS):
            st.image(IMG_FREQUENCIA_RECEITAS, use_container_width=True)
        else:
            st.warning("Imagem não encontrada")
    
    st.divider()
    
    relatorio_balance_ia_md = carregar_markdown(BALANCE_IA_RELATORIO, "Relatório de Balanceamento não encontrado!")
    
    if relatorio_balance_ia_md:
        st.markdown(relatorio_balance_ia_md, unsafe_allow_html=True)
        
        st.download_button(
            label="⬇️ Baixar Relatório de Balanceamento (Markdown)",
            data=relatorio_balance_ia_md,
            file_name="RELATORIO_BALANCEAMENTO_IA.md",
            mime="text/markdown"
        )

# === ABA 6: MÉTRICAS AVANÇADAS ===
with tab_metricas:
    st.header("📈 Métricas Avançadas (JSON)")
    st.info("Dados brutos das métricas de validação.")
    
    metrics_data = carregar_json(ADVANCED_METRICS_JSON)
    
    if metrics_data:
        st.success("✅ Métricas avançadas carregadas!")
        
        metric_tab1, metric_tab2, metric_tab3 = st.tabs([
            "🔧 Validação Mecânica",
            "📚 Validação Pedagógica",
            "📊 Robustez Estatística"
        ])
        
        with metric_tab1:
            st.subheader("Validação Mecânica")
            mech_data = metrics_data.get('mechanical_validation', {})
            if mech_data:
                st.json(mech_data)
            else:
                st.warning("Dados não disponíveis")
                
        with metric_tab2:
            st.subheader("Validação Pedagógica")
            ped_data = metrics_data.get('pedagogical_metrics', {})
            if ped_data:
                st.json(ped_data)
            else:
                st.warning("Dados não disponíveis")
                
        with metric_tab3:
            st.subheader("Robustez Estatística")
            stat_data = metrics_data.get('statistical_robustness', {})
            if stat_data:
                st.json(stat_data)
            else:
                st.warning("Dados não disponíveis")
        
        st.download_button(
            label="⬇️ Baixar Métricas Avançadas (JSON)",
            data=json.dumps(metrics_data, indent=2, ensure_ascii=False),
            file_name="advanced_metrics_report.json",
            mime="application/json"
        )
        
    else:
        st.error("❌ Métricas avançadas não encontradas.")
        st.info("Execute `python main.py` para gerar.")

# --- Sidebar ---
st.sidebar.success("✅ Dashboard carregado!")
st.sidebar.divider()

st.sidebar.subheader("📋 Status dos Relatórios")

relatorios = {
    "📈 Eficácia Pedagógica": EFICACIA_JSON,
    "🧠 Knowledge Tracing": KT_METRICS_JSON,
    "⭐ Relatório de Validação": RELATORIO,
    "📈 Métricas Avançadas": ADVANCED_METRICS_JSON,
    "🎓 Análise Pedagógica": ACP_RELATORIO,
    "📊 Balanceamento": BALANCE_IA_RELATORIO
}

for nome, caminho in relatorios.items():
    if os.path.exists(caminho):
        st.sidebar.success(f"✅ {nome}")
    else:
        st.sidebar.warning(f"⚠️ {nome}")

st.sidebar.divider()

st.sidebar.subheader("🚀 Como Gerar")
st.sidebar.code("""
# Pipeline completo
python main.py
""", language="bash")

st.sidebar.divider()
st.sidebar.info("💡 **Dica**: Execute `python main.py` para gerar todos os relatórios!")
