# knowledge_tracing/gamedkt_model.py
"""
Implementação do modelo GameDKT usando CNN
Baseado em: Hooshyar et al. (2022) - GameDKT: Deep knowledge tracing in educational games
"""

import numpy as np
from typing import Tuple, Optional

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, models
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    print("AVISO: TensorFlow não está instalado. Funcionalidade de Knowledge Tracing limitada.")


class GameDKTModel:
    """
    Modelo CNN para Deep Knowledge Tracing em jogos educacionais.
    """
    
    def __init__(self, 
                 sequence_length: int = 15,
                 feature_dim: int = 5,
                 model_type: str = 'cnn'):
        """
        Inicializa o modelo GameDKT.
        
        Args:
            sequence_length: Tamanho da sequência de entrada
            feature_dim: Número de features por timestep
            model_type: Tipo de modelo ('cnn', 'lstm', 'rnn', 'mlp')
        """
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow é necessário para usar GameDKTModel")
        
        self.sequence_length = sequence_length
        self.feature_dim = feature_dim
        self.model_type = model_type
        self.model = None
        self.history = None
        
    def build_cnn_model(self) -> keras.Model:
        """
        Constrói modelo CNN (melhor performance segundo o artigo).
        
        Returns:
            Modelo Keras compilado
        """
        model = models.Sequential([
            # Camada de entrada
            layers.Input(shape=(self.sequence_length, self.feature_dim)),
            
            # Camada convolucional 1D
            layers.Conv1D(filters=64, kernel_size=3, activation='relu', padding='same'),
            layers.BatchNormalization(),
            
            # Max pooling
            layers.MaxPooling1D(pool_size=2),
            
            # Dropout para regularização
            layers.Dropout(0.3),
            
            # Segunda camada convolucional
            layers.Conv1D(filters=32, kernel_size=3, activation='relu', padding='same'),
            layers.BatchNormalization(),
            
            # Flatten
            layers.Flatten(),
            
            # Camadas densas
            layers.Dense(50, activation='relu'),
            layers.Dropout(0.3),
            
            # Camada de saída (classificação binária)
            layers.Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy', keras.metrics.AUC(name='auc')]
        )
        
        return model
    
    def build_lstm_model(self) -> keras.Model:
        """
        Constrói modelo LSTM.
        
        Returns:
            Modelo Keras compilado
        """
        model = models.Sequential([
            layers.Input(shape=(self.sequence_length, self.feature_dim)),
            
            layers.LSTM(64, return_sequences=True),
            layers.Dropout(0.3),
            
            layers.LSTM(32),
            layers.Dropout(0.3),
            
            layers.Dense(50, activation='relu'),
            layers.Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy', keras.metrics.AUC(name='auc')]
        )
        
        return model
    
    def build_rnn_model(self) -> keras.Model:
        """
        Constrói modelo RNN simples.
        
        Returns:
            Modelo Keras compilado
        """
        model = models.Sequential([
            layers.Input(shape=(self.sequence_length, self.feature_dim)),
            
            layers.SimpleRNN(64, return_sequences=True),
            layers.Dropout(0.3),
            
            layers.SimpleRNN(32),
            layers.Dropout(0.3),
            
            layers.Dense(50, activation='relu'),
            layers.Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy', keras.metrics.AUC(name='auc')]
        )
        
        return model
    
    def build_mlp_model(self) -> keras.Model:
        """
        Constrói modelo MLP (baseline).
        
        Returns:
            Modelo Keras compilado
        """
        model = models.Sequential([
            layers.Input(shape=(self.sequence_length, self.feature_dim)),
            
            layers.Flatten(),
            
            layers.Dense(128, activation='relu'),
            layers.Dropout(0.3),
            
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.3),
            
            layers.Dense(32, activation='relu'),
            layers.Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy', keras.metrics.AUC(name='auc')]
        )
        
        return model
    
    def build(self):
        """Constrói o modelo baseado no tipo especificado."""
        if self.model_type == 'cnn':
            self.model = self.build_cnn_model()
        elif self.model_type == 'lstm':
            self.model = self.build_lstm_model()
        elif self.model_type == 'rnn':
            self.model = self.build_rnn_model()
        elif self.model_type == 'mlp':
            self.model = self.build_mlp_model()
        else:
            raise ValueError(f"Tipo de modelo desconhecido: {self.model_type}")
        
        print(f"Modelo {self.model_type.upper()} construído com sucesso")
        return self.model
    
    def train(self,
             X_train: np.ndarray,
             y_train: np.ndarray,
             X_val: Optional[np.ndarray] = None,
             y_val: Optional[np.ndarray] = None,
             epochs: int = 20,
             batch_size: int = 32,
             verbose: int = 1) -> keras.callbacks.History:
        """
        Treina o modelo.
        
        Args:
            X_train: Dados de treino
            y_train: Labels de treino
            X_val: Dados de validação (opcional)
            y_val: Labels de validação (opcional)
            epochs: Número de épocas
            batch_size: Tamanho do batch
            verbose: Nível de verbosidade
            
        Returns:
            Histórico de treinamento
        """
        if self.model is None:
            self.build()
        
        # Callbacks
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_loss' if X_val is not None else 'loss',
                patience=5,
                restore_best_weights=True
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss' if X_val is not None else 'loss',
                factor=0.5,
                patience=3,
                min_lr=1e-6
            )
        ]
        
        # Validação
        validation_data = (X_val, y_val) if X_val is not None and y_val is not None else None
        
        # Treinamento
        self.history = self.model.fit(
            X_train, y_train,
            validation_data=validation_data,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=verbose
        )
        
        return self.history
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Faz predições.
        
        Args:
            X: Dados de entrada
            
        Returns:
            Predições (probabilidades)
        """
        if self.model is None:
            raise ValueError("Modelo não foi construído ou treinado")
        
        return self.model.predict(X)
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Tuple[float, float, float]:
        """
        Avalia o modelo.
        
        Args:
            X_test: Dados de teste
            y_test: Labels de teste
            
        Returns:
            Tupla (loss, accuracy, auc)
        """
        if self.model is None:
            raise ValueError("Modelo não foi construído ou treinado")
        
        results = self.model.evaluate(X_test, y_test, verbose=0)
        loss, accuracy, auc = results[0], results[1], results[2]
        
        return loss, accuracy, auc
    
    def save(self, filepath: str):
        """
        Salva o modelo.
        
        Args:
            filepath: Caminho para salvar o modelo
        """
        if self.model is None:
            raise ValueError("Modelo não foi construído")
        
        self.model.save(filepath)
        print(f"Modelo salvo em: {filepath}")
    
    def load(self, filepath: str):
        """
        Carrega um modelo salvo.
        
        Args:
            filepath: Caminho do modelo salvo
        """
        self.model = keras.models.load_model(filepath)
        print(f"Modelo carregado de: {filepath}")
    
    def summary(self):
        """Imprime o resumo do modelo."""
        if self.model is None:
            print("Modelo não foi construído")
        else:
            self.model.summary()
