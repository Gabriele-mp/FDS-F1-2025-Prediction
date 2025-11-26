import pandas as pd

def get_pre_race_data():
    """
    Restituisce SOLO i dati noti il Sabato sera (Pre-Gara).
    Fonti: Qualifiche + Analisi FP2.
    """
    # PaceFactor: negativo = più veloce (es. -0.3s al giro).
    # Dati presi dall'analisi di ScuderiaFans
    drivers = [
        # NORRIS (Pole): Veloce sul giro secco, ma passo gara peggiore di Ferrari
        {'Driver': 'NOR', 'GridPosition': 1, 'StartCompound': 'MEDIUM', 'PaceFactor': -0.10},
        
        # VERSTAPPEN (2°): Red Bull faticava con il bilanciamento
        {'Driver': 'VER', 'GridPosition': 2, 'StartCompound': 'MEDIUM', 'PaceFactor': 0.00},
        
        # SAINZ (3°): Ferrari aveva un passo mostruoso venerdì
        {'Driver': 'SAI', 'GridPosition': 3, 'StartCompound': 'MEDIUM', 'PaceFactor': -0.25},
        
        # LECLERC (4°): Il passo migliore di tutti nelle libere
        {'Driver': 'LEC', 'GridPosition': 4, 'StartCompound': 'MEDIUM', 'PaceFactor': -0.30},
        
        # HAMILTON (17°): Mercedes disastrosa, parte dal fondo
        {'Driver': 'HAM', 'GridPosition': 17, 'StartCompound': 'HARD', 'PaceFactor': 0.10}
    ]
    return pd.DataFrame(drivers)