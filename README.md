# Code Sandwich - Validação Pedagógica

Projeto de validação pedagógica e funcional do jogo educacional **Code Sandwich**, que ensina conceitos de programação através de mecânicas de jogo de cartas.

---

## 🎯 Objetivo do Projeto

Validar a **eficácia pedagógica** e **funcionalidade** do Code Sandwich usando:

1. **Agentes Pedagógicos** - Simulam jogadores de diferentes níveis (Novato, Intermediário, Expert)
2. **Knowledge Tracing** - Modelo de IA que rastreia aprendizado ao longo do tempo
3. **Análise de Eficácia** - Prova que o jogo ensina conceitos de programação
4. **Validação Mecânica** - Garante que o jogo funciona corretamente

---

## 🚀 Como Executar

### **1. Instalar Dependências**

```bash
pip install -r requirements.txt
```

### **2. Executar Pipeline Completo**

```bash
python main.py
```

**O que acontece:**
- Executa 500 simulações com agentes pedagógicos
- Treina modelo de Knowledge Tracing (CNN)
- Executa 1000 simulações básicas
- Gera análises pedagógicas
- Cria relatórios e gráficos

**Tempo estimado:** 20-30 minutos

### **3. Visualizar Dashboard**

```bash
streamlit run dashboard.py
```

Abre dashboard interativo com:
- 📈 Eficácia Pedagógica
- 🧠 Knowledge Tracing
- ⭐ Relatório de Validação
- 🎓 Análise Pedagógica
- 📊 Balanceamento

---

## 📊 Resultados Gerados

Após executar `python main.py`, você terá:

### **Logs**
- `logs/pedagogical_simulation_logs.csv` - Simulações com agentes pedagógicos
- `logs/simulation_logs_original.csv` - Simulações básicas

### **Modelo de Knowledge Tracing**
- `analises/gamedkt_cnn_model.keras` - Modelo treinado
- `analises/metrics.json` - Métricas do modelo
- `analises/gamedkt_roc_curve.png` - Curva ROC
- `analises/gamedkt_confusion_matrix.png` - Matriz de confusão
- `analises/gamedkt_training_history.png` - Histórico de treinamento

### **Análise de Eficácia Pedagógica**
- `analises/eficacia_pedagogica.json` - Relatório completo
- `analises/curva_aprendizado.png` - Curva de aprendizado por persona
- `analises/comparacao_personas.png` - Comparação entre níveis
- `analises/maestria_por_kc.png` - Heatmap de maestria por KC
- `analises/progressao_temporal.png` - Progressão ao longo do tempo
- `analises/eficacia_receitas.png` - Eficácia de cada receita

### **Relatórios**
- `analises/RELATORIO_ACP.md` - Análise de Coerência Pedagógica
- `analises/RELATORIO_BALANCEAMENTO_IA.md` - Análise de Balanceamento
- `analises/RELATORIO_VALIDACAO.md` - Relatório de Validação Completo

---

## 🎮 Executar Simulações Manualmente

### **Simulações com Agentes Pedagógicos**

```bash
# Simular com diferentes personas
python run_pedagogical_simulations.py --num_games 500 --personas "Novice,Intermediate,Expert"
```

### **Simulações Básicas**

```bash
# Agentes heurísticos
python run_simulations.py --num_games 1000 --agent_type heuristic

# Agentes pedagógicos
python run_simulations.py --num_games 1000 --agent_type pedagogical --personas "Novice,Expert"
```

### **Treinar Knowledge Tracing**

```bash
# Treinar modelo CNN
python run_knowledge_tracing.py --model_type cnn

# Comparar todos os modelos
python run_knowledge_tracing.py --compare_all
```

### **Análise de Eficácia Pedagógica**

```bash
python analise_eficacia_pedagogica.py logs/pedagogical_simulation_logs.csv
```

---

## 📈 Métricas Esperadas

### **Knowledge Tracing**
- **Acurácia:** ~85-90%
- **AUC:** ~0.85-0.91
- **Loss:** ~0.30-0.35

### **Eficácia Pedagógica**
- **Novatos:** Taxa inicial ~40%, melhoria de 30-50%
- **Intermediários:** Taxa inicial ~60%, melhoria de 15-25%
- **Experts:** Taxa inicial ~80%, melhoria de 5-10%

---

## 🧪 Estrutura do Projeto

```
code_sandwich_rlcard/
├── main.py                           # Pipeline completo
├── dashboard.py                      # Dashboard interativo
│
├── code_sandwich/                    # Módulo do jogo
│   ├── env.py                        # Ambiente RLCard
│   ├── game.py                       # Lógica do jogo
│   ├── heuristic_agent.py            # Agente heurístico
│   └── pedagogical_agents.py         # Agentes pedagógicos
│
├── knowledge_tracing/                # Módulo de Knowledge Tracing
│   ├── data_preprocessing.py         # Pré-processamento
│   ├── gamedkt_model.py              # Modelos (CNN, LSTM, RNN)
│   └── training.py                   # Treinamento e avaliação
│
├── run_simulations.py                # Simulações básicas
├── run_pedagogical_simulations.py   # Simulações pedagógicas
├── run_knowledge_tracing.py         # Treinar modelos
├── analise_eficacia_pedagogica.py   # Análise de eficácia
│
├── analise_pedagogica.py            # Análise de Coerência Pedagógica
├── analyze_results.py               # Análise de balanceamento
├── advanced_metrics.py              # Métricas avançadas
├── gerar_relatorio.py               # Gerador de relatórios
│
├── cartas.json                      # Definição das cartas
├── kcs.json                         # Knowledge Components
├── config.py                        # Configurações
└── requirements.txt                 # Dependências
```

---

## 🛠️ Tecnologias Utilizadas

- **Python 3.8+**
- **TensorFlow/Keras** - Deep Learning para Knowledge Tracing
- **RLCard** - Framework de ambientes de jogo
- **Streamlit** - Dashboard interativo
- **Pandas/NumPy** - Análise de dados
- **Matplotlib/Seaborn** - Visualizações
- **Google Gemini API** - Análises com IA

---

## 📝 Notas

- **Primeira execução:** Pode demorar 20-30 minutos
- **Teste rápido:** Use `--num_games 100` nas simulações
- **GPU:** TensorFlow usará GPU automaticamente se disponível
- **API Gemini:** Configure `GEMINI_API_KEY` no ambiente para análises de IA

---

## 🎓 Para Que Serve Este Projeto

Este projeto **prova cientificamente** que o Code Sandwich:

1. ✅ **Ensina conceitos de programação** - Curvas de aprendizado ascendentes
2. ✅ **Funciona corretamente** - Validação mecânica completa
3. ✅ **É pedagogicamente coerente** - Análise de design educacional
4. ✅ **Tem progressão adequada** - Diferentes níveis de dificuldade
5. ✅ **Cobre KCs importantes** - Sequência, loops, condicionais, etc.

---
