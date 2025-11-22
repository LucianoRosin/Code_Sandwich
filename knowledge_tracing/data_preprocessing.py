# knowledge_tracing/data_preprocessing.py
"""
Pré-processamento de logs para Knowledge Tracing
Baseado em: Hooshyar et al. (2022) - GameDKT
"""

import pandas as pd
import numpy as np
from typing import Tuple, List, Dict
from sklearn.preprocessing import LabelEncoder


def load_logs(log_file: str) -> pd.DataFrame:
    """
    Carrega os logs de simulação.
    
    Args:
        log_file: Caminho para o arquivo CSV de logs
        
    Returns:
        DataFrame com os logs
    """
    try:
        df = pd.read_csv(log_file)
        return df
    except Exception as e:
        print(f"Erro ao carregar logs: {e}")
        return pd.DataFrame()


def preprocess_logs(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pré-processa os logs para preparar para o modelo.
    
    Args:
        df: DataFrame com logs brutos
        
    Returns:
        DataFrame pré-processado
    """
    if df.empty:
        return df
    
    # Remove linhas com valores faltantes críticos
    df = df.dropna(subset=['game_id', 'player_id', 'turn'])
    
    # Ordena por jogo, jogador e turno
    df = df.sort_values(['game_id', 'player_id', 'turn'])
    
    # Codifica variáveis categóricas
    label_encoders = {}
    categorical_cols = ['action_type', 'thinking_strategy']
    
    for col in categorical_cols:
        if col in df.columns:
            le = LabelEncoder()
            df[f'{col}_encoded'] = le.fit_transform(df[col].fillna('unknown'))
            label_encoders[col] = le
    
    # Normaliza valores numéricos
    if 'recipe_progress' in df.columns:
        df['recipe_progress'] = df['recipe_progress'].fillna(0).clip(0, 1)
    
    if 'hand_size' in df.columns:
        df['hand_size_norm'] = df['hand_size'] / df['hand_size'].max()
    
    # Converte booleanos para int
    bool_cols = ['has_bugs', 'optimal_action', 'success']
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].astype(int)
    
    return df


def create_sequences(df: pd.DataFrame, 
                    window_size: int = 15,
                    stride: int = 1) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Cria sequências de ações para treinamento do modelo.
    
    Args:
        df: DataFrame pré-processado
        window_size: Tamanho da janela de histórico
        stride: Passo entre janelas consecutivas
        
    Returns:
        Tupla (X, y, feature_names) onde:
        - X: Array de sequências de features (shape: [n_samples, window_size, n_features])
        - y: Array de labels (shape: [n_samples,])
        - feature_names: Lista com nomes das features
    """
    sequences = []
    labels = []
    
    # Define as features a usar
    feature_cols = [
        'action_type_encoded',
        'recipe_progress',
        'has_bugs',
        'hand_size_norm',
        'optimal_action'
    ]
    
    # Adiciona thinking_strategy se disponível
    if 'thinking_strategy_encoded' in df.columns:
        feature_cols.append('thinking_strategy_encoded')
    
    # Filtra apenas colunas que existem
    available_features = [col for col in feature_cols if col in df.columns]
    
    if not available_features:
        print("AVISO: Nenhuma feature disponível para criar sequências")
        return np.array([]), np.array([]), []
    
    # Agrupa por jogador
    for player_id in df['player_id'].unique():
        player_df = df[df['player_id'] == player_id].sort_values('turn')
        
        # Pula se não houver dados suficientes
        if len(player_df) <= window_size:
            continue
        
        # Cria janelas deslizantes
        for i in range(0, len(player_df) - window_size, stride):
            window = player_df.iloc[i:i+window_size]
            next_action = player_df.iloc[i+window_size]
            
            # Extrai features da janela
            X_window = window[available_features].values
            
            # Label: sucesso da próxima ação
            y_label = next_action['success'] if 'success' in next_action else 0
            
            sequences.append(X_window)
            labels.append(y_label)
    
    if not sequences:
        print("AVISO: Nenhuma sequência criada")
        return np.array([]), np.array([]), available_features
    
    X = np.array(sequences)
    y = np.array(labels)
    
    print(f"Criadas {len(X)} sequências com shape {X.shape}")
    
    return X, y, available_features


def apply_padding(sequences: np.ndarray, 
                 max_length: int,
                 padding_value: float = 0.0) -> np.ndarray:
    """
    Aplica padding às sequências para garantir tamanho uniforme.
    
    Args:
        sequences: Array de sequências
        max_length: Comprimento máximo desejado
        padding_value: Valor para preencher
        
    Returns:
        Array com sequências padronizadas
    """
    padded = []
    
    for seq in sequences:
        if len(seq) < max_length:
            # Padding no início
            padding = np.full((max_length - len(seq), seq.shape[1]), padding_value)
            padded_seq = np.vstack([padding, seq])
        else:
            # Trunca se necessário
            padded_seq = seq[-max_length:]
        
        padded.append(padded_seq)
    
    return np.array(padded)


def split_data(X: np.ndarray, 
              y: np.ndarray,
              train_ratio: float = 0.7,
              val_ratio: float = 0.15) -> Tuple:
    """
    Divide os dados em treino, validação e teste.
    Usa divisão temporal (não aleatória) para respeitar a ordem das sequências.
    
    Args:
        X: Features
        y: Labels
        train_ratio: Proporção de dados para treino
        val_ratio: Proporção de dados para validação
        
    Returns:
        Tupla (X_train, X_val, X_test, y_train, y_val, y_test)
    """
    n_samples = len(X)
    
    train_end = int(n_samples * train_ratio)
    val_end = int(n_samples * (train_ratio + val_ratio))
    
    X_train = X[:train_end]
    y_train = y[:train_end]
    
    X_val = X[train_end:val_end]
    y_val = y[train_end:val_end]
    
    X_test = X[val_end:]
    y_test = y[val_end:]
    
    print(f"Divisão dos dados:")
    print(f"  Treino: {len(X_train)} amostras")
    print(f"  Validação: {len(X_val)} amostras")
    print(f"  Teste: {len(X_test)} amostras")
    
    return X_train, X_val, X_test, y_train, y_val, y_test
