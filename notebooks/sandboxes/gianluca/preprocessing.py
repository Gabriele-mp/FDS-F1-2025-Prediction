
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
import fastf1
from tqdm.notebook import tqdm
import os
import gc
import sys
import copy
from scipy.interpolate import interp1d

from CNN import DriverStyleCNN

# --- COSTANTI DI NORMALIZZAZIONE ---
PHYSICAL_LIMITS = {
    'Speed': 365.0,
    'RPM': 13500.0,
    'Throttle': 100.0,
    'Brake': 100.0,
    'nGear': 8.0
}

# --- 1. FUNZIONI DI PREPROCESSING ---
def process_telemetry(lap, target_length=1000):
    try:
        tel = lap.get_telemetry()
        required_cols = ['Distance', 'Speed', 'RPM', 'Throttle', 'Brake']
        
        if not all(col in tel.columns for col in required_cols): return None
        if len(tel) < 50: return None

        # Interpolazione NaN
        tel = tel[required_cols].interpolate(method='linear', limit_direction='both')
        tel = tel.ffill().bfill().fillna(0)

        # Resampling
        total_dist = tel['Distance'].max()
        x_original = tel['Distance'].values
        x_new = np.linspace(0, total_dist, target_length)

        processed_channels = []
        keys = ['Speed', 'RPM', 'Throttle', 'Brake']
        
        for key in keys:
            values = tel[key].values
            f = interp1d(x_original, values, kind='linear', fill_value="extrapolate")
            new_values = f(x_new)
            
            if key == 'Brake':
                max_val = np.max(new_values)
                norm_values = np.clip(new_values / 100.0, 0.0, 1.0) if max_val > 1.5 else np.clip(new_values, 0.0, 1.0)
            else:
                limit = PHYSICAL_LIMITS[key]
                norm_values = np.clip(new_values / limit, 0.0, 1.0)
            
            processed_channels.append(norm_values)

        return np.array(processed_channels, dtype=np.float32)
    except Exception:
        return None

# --- 2. FUNZIONE CARICAMENTO DATI ---
def load_dataset_from_files(file_list, data_dir, desc="Loading"):
    X_list = []
    y_list = []
    
    import warnings
    warnings.simplefilter(action='ignore', category=FutureWarning)
    
    if not os.path.exists(data_dir): return None, None

    pbar = tqdm(file_list, desc=desc)
    
    for file_name in pbar:
        try:
            path = os.path.join(data_dir, file_name)
            df = pd.read_parquet(path)
            if df.empty: continue
            
            parts = file_name.split('_')
            year, race_name = int(parts[0]), parts[1]
            
            for session_name, group in df.groupby('Session'):
                session = None
                try:
                    session = fastf1.get_session(year, race_name, session_name)
                    session.load(telemetry=True, weather=False, messages=False)
                    
                    for _, row in group.iterrows():
                        try:
                            drv_laps = session.laps[session.laps['Driver'] == row['Driver']]
                            lap_data = drv_laps[drv_laps['LapNumber'] == row['LapNumber']]
                            if lap_data.empty: continue
                            
                            matrix = process_telemetry(lap_data.iloc[0])
                            if matrix is not None:
                                X_list.append(matrix)
                                y_list.append(row['Label'])
                        except: continue
                except: continue
                finally:
                    if session: del session
                    gc.collect()
            del df
            gc.collect()
        except: continue

    if len(X_list) == 0: return None, None
        
    X_np = np.array(X_list, dtype=np.float32)
    y_np = np.array(y_list, dtype=np.float32)
    
    del X_list, y_list
    gc.collect()
    
    return torch.from_numpy(X_np), torch.from_numpy(y_np).unsqueeze(1)

# --- 3. FUNZIONE DI TRAINING ---
def train_one_model(config, X_train, y_train, X_val, y_val, device):
    
    train_loader = DataLoader(TensorDataset(X_train, y_train), batch_size=config['batch_size'], shuffle=True)
    val_loader = DataLoader(TensorDataset(X_val, y_val), batch_size=config['batch_size'])
    
    # Tentativo di inizializzare il modello (gestisce nomi diversi)
    from CNN import DriverStyleCNN

    model = DriverStyleCNN().to(device)
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=config['learning_rate'])
    
    best_loss = float('inf')
    patience_counter = 0
    best_model_state = None
    
    # History per i grafici
    history = {'train_loss': [], 'val_loss': [], 'val_acc': []}
    
    for epoch in range(config['epochs']):
        model.train()
        train_loss = 0.0
        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            
        model.eval()
        val_loss = 0.0
        correct = 0
        total = 0
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                val_loss += criterion(outputs, labels).item()
                predicted = (outputs > 0.5).float()
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
        
        avg_train_loss = train_loss / len(train_loader)
        avg_val_loss = val_loss / len(val_loader)
        val_acc = 100 * correct / total
        
        history['train_loss'].append(avg_train_loss)
        history['val_loss'].append(avg_val_loss)
        history['val_acc'].append(val_acc)
        
        if avg_val_loss < best_loss:
            best_loss = avg_val_loss
            best_model_state = copy.deepcopy(model.state_dict())
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= config['patience']:
                break
                
    return best_loss, best_model_state, history
