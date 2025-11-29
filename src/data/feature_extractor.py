"""
Feature Extractor Generico
✅ VERSIONE PRE-GARA: Usa solo dati disponibili prima della gara
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
        ✅ PRE-GARA: Priorità FP2 > Sprint > FP1
        """
        # PRIORITÀ: FP2 prima (più rappresentativo)
        if 'FP2' in self.sessions and self.sessions['FP2'] is not None:
            session = self.sessions['FP2']
            print("📊 Usando FP2 per pace (long runs)")
        elif 'Sprint' in self.sessions and self.sessions['Sprint'] is not None:
            session = self.sessions['Sprint']
            print("📊 Usando Sprint per pace (fallback)")
        elif 'FP1' in self.sessions and self.sessions['FP1'] is not None:
            session = self.sessions['FP1']
            print("📊 Usando FP1 per pace (fallback)")
        else:
            raise ValueError("Nessuna sessione disponibile per pace!")
        
        laps = session.laps[session.laps['LapTime'].notna()]
        
        # Usa i 5 giri migliori di ogni pilota (più robusto)
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
        quali = None
        
        # Prova tutte le varianti di chiave
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
        
        Regola F1: Top 10 partono con gomma usata in Q2
        """
        quali = None
        
        # Prova tutte le varianti
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
            
            # Prendi il giro più veloce (rappresenta la gomma di partenza)
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
    
    def tyre_degrade_rate(self, compound='MEDIUM', circuit_config=None):
        """
        Calcola il tasso di degrado gomme da FP2 long runs.
        ✅ PRE-GARA: Usa Practice sessions o config circuito
        
        Args:
            circuit_config: Dict da CircuitConfig.get()
        """
        session = None
        
        # Prova FP2 poi FP1
        if 'FP2' in self.sessions and self.sessions['FP2'] is not None:
            session = self.sessions['FP2']
            session_name = 'FP2'
        elif 'FP1' in self.sessions and self.sessions['FP1'] is not None:
            session = self.sessions['FP1']
            session_name = 'FP1'
        
        if session is None:
            # Usa config storica circuito
            if circuit_config and compound in circuit_config['tyre_degradation']:
                degrade = circuit_config['tyre_degradation'][compound]
                print(f"📉 Degrado {compound}: {degrade:.4f}s/giro (da config circuito)")
                return degrade
            else:
                print(f"⚠️ Nessun dato, uso default 0.08")
                return 0.08
        
        # Calcola da sessione
        laps = session.laps
        laps = laps[laps['Compound'] == compound]
        laps = laps[laps['LapTime'].notna()]
        
        if len(laps) < 10:
            # Fallback a config
            if circuit_config and compound in circuit_config['tyre_degradation']:
                return circuit_config['tyre_degradation'][compound]
            return 0.08
        
        # Trova stint lunghi (8+ giri continui)
        laps = laps.sort_values(['Driver', 'LapNumber'])
        laps['StintLap'] = laps.groupby(['Driver', 'Stint']).cumcount() + 1
        long_stints = laps[laps['StintLap'] >= 8]
        
        if len(long_stints) == 0:
            if circuit_config:
                return circuit_config['tyre_degradation'].get(compound, 0.08)
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
            print(f"📉 Degrado {compound} da {session_name}: {avg_degrade:.4f}s/giro")
            return max(0.02, avg_degrade)
        
        # Ultima risorsa: config circuito
        if circuit_config:
            return circuit_config['tyre_degradation'].get(compound, 0.08)
        return 0.08
    
    def optimal_pit_window(self, circuit_config=None):
        """
        Ritorna finestra pit da config circuito.
        ✅ PRE-GARA: Valore storico fisso
        
        Args:
            circuit_config: Dict da CircuitConfig.get()
        """
        if circuit_config and 'pit_window' in circuit_config:
            window = circuit_config['pit_window']
            print(f"🔧 Finestra pit (config circuito): giro {window[0]} ± {window[1]}")
            return window
        else:
            print("🔧 Finestra pit default: giro 25 ± 5")
            return (25, 5)
