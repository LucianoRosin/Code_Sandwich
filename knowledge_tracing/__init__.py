# knowledge_tracing/__init__.py
"""
Módulo de Knowledge Tracing para Code Sandwich
Implementa GameDKT para rastreamento de conhecimento de jogadores
"""

from .gamedkt_model import GameDKTModel
from .data_preprocessing import preprocess_logs, create_sequences
from .training import train_model, evaluate_model

__all__ = [
    'GameDKTModel',
    'preprocess_logs',
    'create_sequences',
    'train_model',
    'evaluate_model'
]
