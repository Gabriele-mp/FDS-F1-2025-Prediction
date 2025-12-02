import torch
import torch.nn as nn

class DriverStyleCNN(nn.Module):
    """
    1D-CNN per analisi telemetria F1.
    Input: (Batch, 4, 1000) -> Speed, RPM, Throttle, Brake
    Output: (Batch, 1) -> Push Probability (0-1)
    """
    def __init__(self, input_channels=4, sequence_length=1000):
        super(DriverStyleCNN, self).__init__()
        
        # --- Feature Extractor (Convoluzioni) ---
        self.features = nn.Sequential(
            # Layer 1: Cerca forme grezze (es. picchi)
            nn.Conv1d(input_channels, 32, kernel_size=7, padding=3),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.MaxPool1d(2), # Output: 32 x 500
            
            # Layer 2: Cerca combinazioni (es. accelerazione + alti rpm)
            nn.Conv1d(32, 64, kernel_size=5, padding=2),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.MaxPool1d(2), # Output: 64 x 250
            
            # Layer 3: Cerca pattern complessi (es. Lift and Coast)
            nn.Conv1d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.MaxPool1d(2)  # Output: 128 x 125
        )
        
        # --- Regressor (Decisione) ---
        # Calcolo dimensione appiattita: 128 canali * 125 punti
        flat_size = 128 * 125
        
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(flat_size, 256),
            nn.ReLU(),
            nn.Dropout(0.5), # Evita che impari a memoria i giri
            nn.Linear(256, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid() # Output tra 0 e 1
        )

    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x