import fastf1
import pandas as pd
import os
import warnings
from datetime import datetime

# Ignoriamo i warning di Pandas per pulizia
warnings.simplefilter(action='ignore', category=FutureWarning)

def setup_cache():
    """Crea la cartella per la cache di FastF1 se non esiste."""
    cache_dir = 'fastf1_cache'
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    fastf1.Cache.enable_cache(cache_dir)

def download_data_for_module_b():
    """
    Scarica i dati per il Modulo B (Analisi Stile di Guida).
    Target: Previsione Abu Dhabi 2025.
    Anni: 2023, 2024, 2025.
    """
    setup_cache()
    
    # Anni da scaricare
    years = [2023, 2024, 2025]
    
    output_dir = "data/raw"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"--- INIZIO DOWNLOAD DATASET ---")
    print(f"Anni target: {years}")
    print(f"Salvataggio in: {output_dir}\n")

    for year in years:
        try:
            # Scarica il calendario
            schedule = fastf1.get_event_schedule(year)
            # Prendiamo solo gare convenzionali
            races = schedule[schedule['EventFormat'] == 'conventional']
            
        except Exception as e:
            print(f"Errore nel scaricare calendario {year}: {e}")
            continue

        for _, race in races.iterrows():
            race_name = race['EventName']
            round_number = race['RoundNumber']
            race_date = race['Session5Date'] # Data della gara (Domenica)

            # --- CORREZIONE 1: GESTIONE FUSO ORARIO ---
            # Se la data ha un fuso orario (è "aware"), lo rimuoviamo per confrontarla col PC
            if race_date.tzinfo is not None:
                race_date = race_date.tz_localize(None)

            # Se la gara è nel futuro (es. Abu Dhabi 2025), ci fermiamo
            if race_date >= datetime.now():
                continue

            file_path = os.path.join(output_dir, f"{year}_{race_name}_laps.parquet")
            
            if os.path.exists(file_path):
                print(f"[{year}] {race_name} -> Già presente, salto.")
                continue

            print(f"[{year}] Scaricando {race_name}...")
            
            try:
                processed_laps = []

                # --- 1. SESSIONE PUSH (Qualifiche) ---
                try:
                    session_q = fastf1.get_session(year, round_number, 'Q')
                    session_q.load(telemetry=True, weather=False, messages=False)
                    push_laps = session_q.laps.pick_quicklaps()
                    push_laps['Label'] = 1  
                    push_laps['Session'] = 'Q'
                    processed_laps.append(push_laps)
                except ValueError as ve:
                    # CATTURA L'ERRORE SPECIFICO DI MONACO/AUSTRALIA
                    if "no driver number" in str(ve):
                        print(f"  ⚠️ Dati corrotti (Missing Driver ID) in Q per {race_name}. Salto la sessione.")
                    else:
                        print(f"  - Errore Q: {ve}")
                except Exception as e:
                    print(f"  - Errore generico Q: {e}")

                # --- 2. SESSIONE SAVE (FP2) ---
                try:
                    session_fp2 = fastf1.get_session(year, round_number, 'FP2')
                    session_fp2.load(telemetry=True, weather=False, messages=False)
                    
                    save_laps = session_fp2.laps.pick_wo_box()
                    if not save_laps.empty:
                        fastest_time = session_fp2.laps.pick_fastest()['LapTime']
                        threshold = fastest_time * 1.15  
                        save_laps = save_laps[save_laps['LapTime'] < threshold]
                        save_laps['Label'] = 0 
                        save_laps['Session'] = 'FP2'
                        processed_laps.append(save_laps)
                except ValueError as ve:
                    # CATTURA L'ERRORE SPECIFICO ANCHE QUI
                    if "no driver number" in str(ve):
                        print(f"  ⚠️ Dati corrotti (Missing Driver ID) in FP2 per {race_name}. Salto la sessione.")
                    else:
                        print(f"  - Errore FP2: {ve}")
                except Exception as e:
                    # print(f"  - Nessun dato FP2 valido: {e}") 
                    pass

                # --- SALVATAGGIO ---
                if processed_laps:
                    all_laps = pd.concat(processed_laps)
                    cols_to_keep = ['Driver', 'LapTime', 'LapNumber', 'Compound', 'TyreLife', 'Label', 'Session', 'Team']
                    # Salviamo e filtriamo colonne se esistono
                    all_laps = all_laps[all_laps.columns.intersection(cols_to_keep)]
                    
                    all_laps.to_parquet(file_path)
                    print(f"  -> Salvato: {len(all_laps)} giri.")
                else:
                    print("  -> Nessun dato utile trovato o errore API.")

            except Exception as e:
                print(f"  -> Errore generico su {race_name}: {e}")

if __name__ == "__main__":
    download_data_for_module_b()