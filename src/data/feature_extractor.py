"""
Feature Extractor per Austin GP 2024
✅ VERSIONE PRE-GARA: Usa solo FP1, FP2, Qualifying, Sprint
❌ NON usa dati dalla Race che stiamo predicendo
"""

import fastf1
import pandas as pd
import numpy as np


class FeatureExtractor:
    def __init__(self, sessions):
        """
        sessions: dict con chiavi 'FP1', 'FP2', 'Sprint', 'Qualifying', 'Race'
        """
        self.sessions = sessions
    
    def extract_long_run_pace(self):
        """
        Estrae il pace factor dai long run.
        ✅ PRE-GARA: Priorità FP2 > Sprint
        """
        # PRIORITÀ: FP2 prima!
        if 'FP2' in self.sessions and self.sessions['FP2'] is not None:
            session = self.sessions['FP2']
            print("📊 Usando FP2 per pace (long runs)")
        elif 'Sprint' in self.sessions and self.sessions['Sprint'] is not None:
            session = self.sessions['Sprint']
            print("📊 Usando Sprint per pace (fallback)")
        else:
            raise ValueError("Nessuna sessione disponibile per pace!")
        
        laps = session.laps[session.laps['LapTime'].notna()]
        
        # Usa i 5 giri migliori di ogni pilota
        pace_dict = {}
        
        for driver in laps['Driver'].unique():
            driver_laps = laps[laps['Driver'] == driver]
            
            # Prendi i 5 giri più veloci
            best_5 = driver_laps.nsmallest(5, 'LapTime')['LapTime']
            
            if len(best_5) > 0:
                pace_dict[driver] = best_5.mean().total_seconds()
        
        return pace_dict
    
    def extract_quali_positions(self):
        """
        Estrae le posizioni di qualifica.
        ✅ PRE-GARA: Usa Qualifying o Sprint Qualifying
        """
        # Prova tutte le varianti di chiave
        quali = None
        
        # Prova chiavi esatte
        for key in ['Qualifying', 'Sprint Qualifying', 'Sprint']:
            if key in self.sessions and self.sessions[key] is not None:
                quali = self.sessions[key]
                print(f"✅ Usando {key} per griglia")
                break
        
        if quali is None:
            print(f"⚠️ ERRORE: Nessuna qualifying trovata!")
            print(f"   Chiavi disponibili: {list(self.sessions.keys())}")
            raise ValueError("Nessuna qualifica disponibile!")
        
        results = quali.results
        
        grid_dict = {}
        for idx, row in results.iterrows():
            driver = row['Abbreviation']
            position = row['Position']
            grid_dict[driver] = int(position)
        
        return grid_dict
    
    def extract_start_compounds(self):
        """
        Stima il compound di partenza dalla Qualifying.
        ✅ PRE-GARA: Usa gomma più veloce in Q2/Q3
        """
        # Prova tutte le varianti
        quali = None
        
        for key in ['Qualifying', 'Sprint Qualifying']:
            if key in self.sessions and self.sessions[key] is not None:
                quali = self.sessions[key]
                print(f"✅ Compound stimati da {key}")
                break
        
        if quali is None:
            print("⚠️ Nessuna quali, uso MEDIUM per tutti")
            return {}
        
        laps = quali.laps[quali.laps['LapTime'].notna()]
        compounds = {}
        
        for driver in laps['Driver'].unique():
            driver_laps = laps[laps['Driver'] == driver]
            
            # Prendi il giro più veloce
            if len(driver_laps) > 0:
                fastest = driver_laps.nsmallest(1, 'LapTime').iloc[0]
                if pd.notna(fastest.get('Compound')):
                    compounds[driver] = fastest['Compound']
                else:
                    compounds[driver] = 'MEDIUM'
            else:
                compounds[driver] = 'MEDIUM'
        
        return compounds
    
    def extract_actual_results(self):
        """
        Estrae i risultati effettivi della gara.
        ⚠️ SOLO PER VALIDAZIONE POST-GARA
        """
        race = self.sessions.get('Race')
        if race is None:
            print("⚠️ Nessuna gara disponibile per risultati reali")
            return {}
        
        results = race.results
        actual_dict = {}
        
        for idx, row in results.iterrows():
            driver = row['Abbreviation']
            position = row['Position']
            actual_dict[driver] = int(position)
        
        return actual_dict
    
    def create_grid_dataframe(self):
        """
        Crea DataFrame completo per simulatore.
        ✅ PRE-GARA: Usa solo FP2, Qualifying, Sprint
        
        Colonne: Driver, GridPosition, PaceFactor, StartCompound
        """
        pace_factor = self.extract_long_run_pace()
        grid_pos = self.extract_quali_positions()
        start_compounds = self.extract_start_compounds()
        
        # Usa la GARA solo per lista piloti (non per dati prestazionali)
        race = self.sessions.get('Race')
        if race is None:
            raise ValueError("Serve la Race per avere la lista completa piloti!")
        
        all_drivers = race.results['Abbreviation'].tolist()
        
        rows = []
        for driver in all_drivers:
            # Se manca il pace, usa media degli altri
            if driver not in pace_factor:
                avg_pace = np.mean(list(pace_factor.values()))
                print(f"⚠️ {driver}: pace mancante, uso media={avg_pace:.3f}s")
                pace = avg_pace
            else:
                pace = pace_factor[driver]
            
            rows.append({
                'Driver': driver,
                'GridPosition': grid_pos.get(driver, 20),
                'PaceFactor': pace,
                'StartCompound': start_compounds.get(driver, 'MEDIUM')
            })
        
        df = pd.DataFrame(rows)
        df = df.sort_values('GridPosition').reset_index(drop=True)
        
        print(f"\n✅ Grid creato: {len(df)} piloti")
        return df
    
    def tyre_degrade_rate(self, compound='MEDIUM'):
        """
        Calcola il tasso di degrado gomme da FP2 long runs.
        ✅ PRE-GARA: Usa solo Practice sessions
        """
        fp2 = self.sessions.get('FP2')
        
        if fp2 is None:
            print("⚠️ Nessuna FP2, uso degrado default Austin = 0.08s/giro")
            return 0.08
        
        laps = fp2.laps
        laps = laps[laps['Compound'] == compound]
        laps = laps[laps['LapTime'].notna()]
        
        if len(laps) < 10:
            print(f"⚠️ Pochi dati FP2 per {compound}, uso default")
            return 0.08
        
        # Trova stint lunghi (8+ giri continui)
        laps = laps.sort_values(['Driver', 'LapNumber'])
        laps['StintLap'] = laps.groupby(['Driver', 'Stint']).cumcount() + 1
        long_stints = laps[laps['StintLap'] >= 8]
        
        if len(long_stints) == 0:
            return 0.08
        
        # Calcola pendenza media tempo vs giro
        degrade_rates = []
        for driver in long_stints['Driver'].unique():
            driver_laps = long_stints[long_stints['Driver'] == driver]
            if len(driver_laps) >= 8:
                times = driver_laps['LapTime'].dt.total_seconds().values
                laps_num = driver_laps['StintLap'].values
                
                # Fit lineare
                coef = np.polyfit(laps_num, times, 1)
                degrade_rates.append(coef[0])
        
        if degrade_rates:
            avg_degrade = np.median(degrade_rates)
            print(f"📉 Degrado {compound} da FP2: {avg_degrade:.4f}s/giro")
            return max(0.02, avg_degrade)
        
        return 0.08
    
    def optimal_pit_window(self):
        """
        Ritorna finestra pit storica per Austin.
        ✅ PRE-GARA: Valore fisso da analisi storica circuito
        """
        print("🔧 Finestra pit storica Austin: giro 23 ± 5")
        return (23, 5)
# --- FINE FILE ---

