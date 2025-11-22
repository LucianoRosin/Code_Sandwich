# knowledge_tracing/training.py
"""
Pipeline de treinamento e avaliação para GameDKT
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Backend sem interface gráfica
import matplotlib.pyplot as plt
import os
from typing import Dict, Any, Optional
from sklearn.metrics import roc_curve, auc, classification_report, confusion_matrix

from .gamedkt_model import GameDKTModel


def train_model(X_train: np.ndarray,
               y_train: np.ndarray,
               X_val: np.ndarray,
               y_val: np.ndarray,
               model_type: str = 'cnn',
               epochs: int = 20,
               batch_size: int = 32) -> GameDKTModel:
    """
    Treina um modelo GameDKT.
    
    Args:
        X_train: Dados de treino
        y_train: Labels de treino
        X_val: Dados de validação
        y_val: Labels de validação
        model_type: Tipo de modelo ('cnn', 'lstm', 'rnn', 'mlp')
        epochs: Número de épocas
        batch_size: Tamanho do batch
        
    Returns:
        Modelo treinado
    """
    sequence_length = X_train.shape[1]
    feature_dim = X_train.shape[2]
    
    print(f"\n{'='*60}")
    print(f"Treinando modelo {model_type.upper()}")
    print(f"{'='*60}")
    print(f"Sequência: {sequence_length} timesteps")
    print(f"Features: {feature_dim}")
    print(f"Amostras treino: {len(X_train)}")
    print(f"Amostras validação: {len(X_val)}")
    
    # Cria e treina o modelo
    model = GameDKTModel(
        sequence_length=sequence_length,
        feature_dim=feature_dim,
        model_type=model_type
    )
    
    model.build()
    model.summary()
    
    history = model.train(
        X_train, y_train,
        X_val, y_val,
        epochs=epochs,
        batch_size=batch_size,
        verbose=1
    )
    
    return model


def evaluate_model(model: GameDKTModel,
                  X_test: np.ndarray,
                  y_test: np.ndarray,
                  output_dir: str = 'analises') -> Dict[str, Any]:
    """
    Avalia o modelo e gera relatório detalhado.
    
    Args:
        model: Modelo treinado
        X_test: Dados de teste
        y_test: Labels de teste
        output_dir: Diretório para salvar resultados
        
    Returns:
        Dicionário com métricas
    """
    print(f"\n{'='*60}")
    print("Avaliando modelo")
    print(f"{'='*60}")
    
    # Predições
    y_pred_proba = model.predict(X_test)
    y_pred = (y_pred_proba > 0.5).astype(int).flatten()
    y_pred_proba = y_pred_proba.flatten()
    
    # Métricas básicas
    loss, accuracy, auc_score = model.evaluate(X_test, y_test)
    
    print(f"\nMétricas de Teste:")
    print(f"  Loss: {loss:.4f}")
    print(f"  Acurácia: {accuracy:.4f} ({accuracy*100:.2f}%)")
    print(f"  AUC: {auc_score:.4f}")
    
    # Relatório de classificação
    print(f"\nRelatório de Classificação:")
    print(classification_report(y_test, y_pred, target_names=['Falha', 'Sucesso']))
    
    # Matriz de confusão
    cm = confusion_matrix(y_test, y_pred)
    print(f"\nMatriz de Confusão:")
    print(cm)
    
    # Calcula ROC curve
    fpr, tpr, thresholds = roc_curve(y_test, y_pred_proba)
    roc_auc = auc(fpr, tpr)
    
    # Salva gráficos
    os.makedirs(output_dir, exist_ok=True)
    
    # Gráfico ROC
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {roc_auc:.3f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('Taxa de Falsos Positivos')
    plt.ylabel('Taxa de Verdadeiros Positivos')
    plt.title('Curva ROC - GameDKT')
    plt.legend(loc="lower right")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'gamedkt_roc_curve.png'), dpi=300)
    plt.close()
    
    # Gráfico de matriz de confusão
    plt.figure(figsize=(6, 5))
    plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    plt.title('Matriz de Confusão')
    plt.colorbar()
    tick_marks = np.arange(2)
    plt.xticks(tick_marks, ['Falha', 'Sucesso'])
    plt.yticks(tick_marks, ['Falha', 'Sucesso'])
    
    # Adiciona valores na matriz
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(j, i, format(cm[i, j], 'd'),
                    ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black")
    
    plt.ylabel('Verdadeiro')
    plt.xlabel('Predito')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'gamedkt_confusion_matrix.png'), dpi=300)
    plt.close()
    
    # Histórico de treinamento
    if model.history is not None:
        plot_training_history(model.history, output_dir)
    
    # Retorna métricas
    metrics = {
        'loss': float(loss),
        'accuracy': float(accuracy),
        'auc': float(auc_score),
        'roc_auc': float(roc_auc),
        'confusion_matrix': cm.tolist(),
        'classification_report': classification_report(y_test, y_pred, target_names=['Falha', 'Sucesso'], output_dict=True)
    }
    
    return metrics


def plot_training_history(history, output_dir: str = 'analises'):
    """
    Plota o histórico de treinamento.
    
    Args:
        history: Histórico do Keras
        output_dir: Diretório para salvar gráficos
    """
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    # Loss
    axes[0].plot(history.history['loss'], label='Treino', linewidth=2)
    if 'val_loss' in history.history:
        axes[0].plot(history.history['val_loss'], label='Validação', linewidth=2)
    axes[0].set_title('Loss ao Longo do Treinamento', fontsize=12, fontweight='bold')
    axes[0].set_xlabel('Época')
    axes[0].set_ylabel('Loss')
    axes[0].legend()
    axes[0].grid(alpha=0.3)
    
    # Accuracy
    axes[1].plot(history.history['accuracy'], label='Treino', linewidth=2)
    if 'val_accuracy' in history.history:
        axes[1].plot(history.history['val_accuracy'], label='Validação', linewidth=2)
    axes[1].set_title('Acurácia ao Longo do Treinamento', fontsize=12, fontweight='bold')
    axes[1].set_xlabel('Época')
    axes[1].set_ylabel('Acurácia')
    axes[1].legend()
    axes[1].grid(alpha=0.3)
    
    # AUC
    axes[2].plot(history.history['auc'], label='Treino', linewidth=2)
    if 'val_auc' in history.history:
        axes[2].plot(history.history['val_auc'], label='Validação', linewidth=2)
    axes[2].set_title('AUC ao Longo do Treinamento', fontsize=12, fontweight='bold')
    axes[2].set_xlabel('Época')
    axes[2].set_ylabel('AUC')
    axes[2].legend()
    axes[2].grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'gamedkt_training_history.png'), dpi=300)
    plt.close()


def compare_models(X_train: np.ndarray,
                  y_train: np.ndarray,
                  X_val: np.ndarray,
                  y_val: np.ndarray,
                  X_test: np.ndarray,
                  y_test: np.ndarray,
                  model_types: list = ['cnn', 'lstm', 'mlp'],
                  output_dir: str = 'analises') -> Dict[str, Dict[str, Any]]:
    """
    Compara diferentes tipos de modelos.
    
    Args:
        X_train, y_train: Dados de treino
        X_val, y_val: Dados de validação
        X_test, y_test: Dados de teste
        model_types: Lista de tipos de modelos a comparar
        output_dir: Diretório para salvar resultados
        
    Returns:
        Dicionário com resultados de cada modelo
    """
    results = {}
    
    for model_type in model_types:
        print(f"\n{'#'*60}")
        print(f"# Modelo: {model_type.upper()}")
        print(f"{'#'*60}")
        
        try:
            # Treina
            model = train_model(
                X_train, y_train,
                X_val, y_val,
                model_type=model_type,
                epochs=20,
                batch_size=32
            )
            
            # Avalia
            metrics = evaluate_model(model, X_test, y_test, output_dir)
            
            # Salva modelo
            model_path = os.path.join(output_dir, f'gamedkt_{model_type}_model.keras')
            model.save(model_path)
            
            results[model_type] = {
                'model': model,
                'metrics': metrics,
                'model_path': model_path
            }
            
        except Exception as e:
            print(f"ERRO ao treinar modelo {model_type}: {e}")
            results[model_type] = {
                'error': str(e)
            }
    
    # Gráfico comparativo
    plot_model_comparison(results, output_dir)
    
    return results


def plot_model_comparison(results: Dict[str, Dict[str, Any]], output_dir: str):
    """
    Plota comparação entre modelos.
    
    Args:
        results: Resultados dos modelos
        output_dir: Diretório para salvar gráfico
    """
    model_names = []
    accuracies = []
    aucs = []
    
    for model_type, result in results.items():
        if 'metrics' in result:
            model_names.append(model_type.upper())
            accuracies.append(result['metrics']['accuracy'] * 100)
            aucs.append(result['metrics']['auc'])
    
    if not model_names:
        return
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Acurácia
    axes[0].bar(model_names, accuracies, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'][:len(model_names)])
    axes[0].set_title('Comparação de Acurácia', fontsize=12, fontweight='bold')
    axes[0].set_ylabel('Acurácia (%)')
    axes[0].set_ylim([0, 100])
    axes[0].grid(axis='y', alpha=0.3)
    
    for i, v in enumerate(accuracies):
        axes[0].text(i, v + 2, f'{v:.2f}%', ha='center', fontweight='bold')
    
    # AUC
    axes[1].bar(model_names, aucs, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'][:len(model_names)])
    axes[1].set_title('Comparação de AUC', fontsize=12, fontweight='bold')
    axes[1].set_ylabel('AUC')
    axes[1].set_ylim([0, 1])
    axes[1].grid(axis='y', alpha=0.3)
    
    for i, v in enumerate(aucs):
        axes[1].text(i, v + 0.02, f'{v:.3f}', ha='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'gamedkt_model_comparison.png'), dpi=300)
    plt.close()
    
    print(f"\nGráfico de comparação salvo em: {os.path.join(output_dir, 'gamedkt_model_comparison.png')}")
