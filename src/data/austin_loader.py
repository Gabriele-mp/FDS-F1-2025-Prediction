"""
Data Loader per FastF1
Carica tutte le sessioni di un weekend F1
"""

import fastf1
import pandas as pd


class AustinDataLoader:
    def __init__(self, year=2024, gp_name='United States'):
        self.year = year
        self.gp_name = gp_name
        self.sessions = {}  # ✅ Inizializza subito
        fastf1.Cache.enable_cache('./fastf1_cache')
    
    def load_all_sessions(self):
        """
        Carica tutte le sessioni del weekend.
        ✅ Include FP2 per pace PRE-gara
        """
        sessions = {}
        
        # ✅ LISTA COMPLETA con FP2
        session_types = ['FP1', 'FP2', 'Sprint Qualifying', 'Sprint', 'Qualifying', 'Race']
        
        for session_type in session_types:
            print(f"  ⏳ {session_type}...", end='')
            try:
                session = fastf1.get_session(self.year, self.gp_name, session_type)
                session.load(telemetry=False, weather=False, messages=False)
                
                # Normalizza chiavi
                sessions[session_type] = session
                print(f" ✅")
                
            except Exception as e:
                print(f" ❌ Non disponibile")
                sessions[session_type] = None
        
        # ✅ SALVA per usare in altri metodi
        self.sessions = sessions
        
        return sessions
    
    def get_race_results(self):
        """
        Wrapper per estrarre risultati della gara.
        Usa la sessione Race già caricata.
        """
        race = self.sessions.get('Race')
        
        if race is None:
            print("⚠️ Devi prima chiamare load_all_sessions()")
            return None
        
        return self.extract_real_results(race)
    
    def get_pit_stops(self):
        """
        Wrapper per estrarre pit stops dalla gara.
        Usa la sessione Race già caricata.
        """
        race = self.sessions.get('Race')
        
        if race is None:
            print("⚠️ Devi prima chiamare load_all_sessions()")
            return None
        
        return self.extract_real_pitstops(race)
    
    def extract_real_results(self, race_session):
        """Estrae risultati reali dalla gara"""
        if race_session is None:
            return None
        
        results = race_session.results[['Abbreviation', 'Position', 'GridPosition', 'Time', 'Points']]
        return results
    
    def extract_real_pitstops(self, race_session):
        """Estrae i pit stop reali"""
        if race_session is None:
            return None
        
        laps = race_session.laps
        pit_laps = laps[laps['PitInTime'].notna()].copy()
        
        pit_data = []
        for _, lap in pit_laps.iterrows():
            pit_data.append({
                'Driver': lap['Driver'],
                'PitLap': lap['LapNumber'],
                'Compound': lap['Compound'],
                'TyreAge': lap['TyreLife']
            })
        
        return pd.DataFrame(pit_data)