import fastf1
import pandas as pd
import os
if not os.path.exists('fastf1_cache'):
    os.makedirs('fastf1_cache')
# Abilita cache
fastf1.Cache.enable_cache('fastf1_cache')

def get_austin_2024_start_conditions():
    """
    Scarica la griglia di partenza reale e le gomme usate
    al GP USA 2024 per i Top 5 piloti.
    """
    print("⬇️ Scaricamento dati Austin 2024 (potrebbe richiedere un minuto)...")
    session = fastf1.get_session(2024, 'Austin', 'R')
    session.load(telemetry=False, weather=False)
    
    drivers_data = []
    # Prendiamo i primi 5 classificati per il test
    top_drivers = ['LEC', 'SAI', 'VER', 'NOR', 'PIA'] 
    
    for drv in top_drivers:
        # Info Pilota
        d_info = session.get_driver(drv)
        
        # Info Primo Stint (Gomma di partenza)
        # Prendiamo il primo giro per vedere la gomma
        laps = session.laps.pick_driver(drv)
        start_compound = laps.iloc[0]['Compound']
        
        # Tyre Age reale alla partenza (es. usata in Q2?)
        # FastF1 non dà l'età esatta alla partenza facilmente, 
        # assumiamo 0 per nuove, 3 per usate (stime)
        start_age = 0 
        
        drivers_data.append({
            'Driver': drv,
            'GridPosition': d_info['GridPosition'],
            'StartCompound': start_compound,
            'StartTyreAge': start_age
        })
        
    return pd.DataFrame(drivers_data)