# src/data/data_loader.py
"""
Caricatore dati F1 generalizzato per qualsiasi GP
Gestisce weekend normali e Sprint, con fallback intelligenti
"""

import fastf1
from pathlib import Path
import os

class F1DataLoader:
    """Carica dati F1 per un GP specifico usando FastF1"""
    
    def __init__(self, year: int, gp_name: str, cache_dir: str = None):
        """
        Args:
            year: Anno del campionato (es. 2024)
            gp_name: Nome del GP (es. 'United States', 'Abu Dhabi')
            cache_dir: Cartella cache FastF1 (default: ./fastf1_cache)
        """
        self.year = year
        self.gp_name = gp_name
        
        # Setup cache
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent.parent / 'fastf1_cache'
        
        # ✅ CREA LA CARTELLA SE NON ESISTE
        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        fastf1.Cache.enable_cache(str(cache_dir))
        
        self.sessions = {}
    
    def load_all_sessions(self):
        """Carica tutte le sessioni disponibili per il GP"""
        sessions = {}
        
        session_types = ['FP1', 'FP2', 'FP3', 'Sprint Qualifying', 'Sprint', 'Qualifying', 'Race']
        
        for session_type in session_types:
            try:
                session = fastf1.get_session(self.year, self.gp_name, session_type)
                # Carica CON weather e messages per dati completi
                session.load(weather=True, messages=True)
                sessions[session_type] = session
                print(f"✅ Caricata sessione: {session_type}")
            except Exception as e:
                print(f"⚠️ Sessione {session_type} non disponibile")
                sessions[session_type] = None
        
        self.sessions = sessions
        return sessions
    
    def get_race_results(self):
        """Ottiene i risultati finali della gara (solo per validazione)"""
        if 'Race' not in self.sessions or self.sessions['Race'] is None:
            raise ValueError("Sessione Race non caricata")
        
        race = self.sessions['Race']
        results = race.results[['Position', 'Abbreviation', 'TeamName', 'Points', 'Status']].copy()
        return results
    
    def get_pit_stops(self):
        """Estrae tutti i pit stop della gara (solo per validazione)"""
        if 'Race' not in self.sessions or self.sessions['Race'] is None:
            raise ValueError("Sessione Race non caricata")
        
        race = self.sessions['Race']
        laps = race.laps
        
        # Trova tutti i giri con pit-in
        pit_laps = laps[laps['PitInTime'].notna()].copy()
        
        pit_stops = []
        for _, lap in pit_laps.iterrows():
            pit_stops.append({
                'Driver': lap['Driver'],
                'LapNumber': lap['LapNumber'],
                'Compound_Before': lap['Compound'],
                'PitInTime': lap['PitInTime'],
                'PitOutTime': lap['PitOutTime']
            })
        
        return pit_stops
    
    def get_session_for_pace(self):
        """
        Restituisce la sessione migliore per analizzare il passo gara
        Priorità: FP2 > Sprint > FP1
        """
        # Prova FP2 (migliore per long run)
        if self.sessions.get('FP2') is not None:
            return self.sessions['FP2'], 'FP2'
        
        # Fallback Sprint (se weekend Sprint)
        if self.sessions.get('Sprint') is not None:
            print("⚠️ FP2 non disponibile (Sprint weekend) - uso Sprint per analisi passo")
            return self.sessions['Sprint'], 'Sprint'
        
        # Ultimo fallback: FP1
        if self.sessions.get('FP1') is not None:
            print("⚠️ FP2 e Sprint non disponibili - uso FP1 per analisi passo")
            return self.sessions['FP1'], 'FP1'
        
        raise ValueError("Nessuna sessione disponibile per analisi passo gara")
    
    def get_session_for_grid(self):
        """
        Restituisce la sessione che determina la griglia di partenza
        Priorità: Qualifying > Sprint Qualifying
        """
        # Weekend normale: Qualifying
        if self.sessions.get('Qualifying') is not None:
            return self.sessions['Qualifying'], 'Qualifying'
        
        # Weekend Sprint: Sprint Qualifying determina griglia Sprint, 
        # ma la griglia GARA viene dalla classifica Sprint
        # Per semplicità usiamo Qualifying se esiste, altrimenti Sprint Quali
        if self.sessions.get('Sprint Qualifying') is not None:
            print("⚠️ Weekend Sprint - uso Sprint Qualifying per griglia")
            return self.sessions['Sprint Qualifying'], 'Sprint Qualifying'
        
        raise ValueError("Nessuna sessione qualifica disponibile")
    
    def is_sprint_weekend(self):
        """Verifica se è un weekend Sprint"""
        return self.sessions.get('Sprint') is not None