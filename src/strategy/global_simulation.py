import pandas as pd
import numpy as np

class GlobalRaceSimulator:
    def __init__(self, track_name=None, total_laps=None, pit_loss_time=None):
        """
        Args:
            track_name: Nome circuito (es. 'AUSTIN') - usa config automatico
            total_laps: Numero giri totali (opzionale se track_name fornito)
            pit_loss_time: Tempo perso in pit (opzionale se track_name fornito)
        """
        from src.data.circuit_configs import CircuitConfig
        
        # Se track_name fornito, usa config
        if track_name:
            config = CircuitConfig.get(track_name)
            self.total_laps = config['total_laps']
            self.pit_loss_time = config['pit_loss_time']
        else:
            # Altrimenti usa parametri manuali
            self.total_laps = total_laps
            self.pit_loss_time = pit_loss_time
        
        # ✅ INIZIALIZZA VARIABILI
        self.drivers_state = {}
        self.race_history = []
        
        # ✅ PARAMETRI FISICI (invece di TrackPhysics)
        self.FUEL_BURN = 1.8  # kg/giro
        self.FUEL_EFFECT = 0.03  # s/kg

    def initialize_grid(self, grid_data):
        """Inizializza stato piloti dalla griglia"""
        self.drivers_state = {}
        
        grid_data = grid_data.sort_values('GridPosition')
        for _, row in grid_data.iterrows():
            drv = row['Driver']
            self.drivers_state[drv] = {
                'position': int(row['GridPosition']),
                'total_time': 0.0,
                'compound': row['StartCompound'],
                'tyre_age': row.get('StartTyreAge', 0),
                'fuel': 100.0,
                'pace_factor': row.get('PaceFactor', 0.0),
                'status': 'RUNNING',
                'pit_stops': 0,
                'planned_pit_lap': int(row.get('PitLap', 25)) 
            }
        print(f"🚦 Gara Inizializzata con {len(self.drivers_state)} piloti.")

    def calculate_lap_time(self, compound, tyre_age, fuel, pace_factor):
        """Calcola tempo sul giro con fisica semplificata"""
        # Baseline
        base_time = 95.0  # Austin baseline
        
        # Effetto compound
        compound_effect = {
            'SOFT': -0.5,
            'MEDIUM': 0.0,
            'HARD': 0.3
        }
        time = base_time + compound_effect.get(compound, 0.0)
        
        # Degrado gomme (s/giro)
        degradation_rate = {
            'SOFT': 0.08,
            'MEDIUM': 0.05,
            'HARD': 0.03
        }
        time += tyre_age * degradation_rate.get(compound, 0.05)
        
        # Effetto carburante
        fuel_effect = (100 - fuel) * self.FUEL_EFFECT
        time -= fuel_effect
        
        # Pace factor (differenziale pilota)
        time += pace_factor
        
        return time

    def get_gap_to_car_ahead(self, current_driver_time, leaderboard):
        """Calcola gap al pilota davanti"""
        my_idx = -1
        for i, (drv, time) in enumerate(leaderboard):
            if drv == current_driver_time[0]:
                my_idx = i
                break
        
        if my_idx > 0: 
            car_ahead_name = leaderboard[my_idx - 1][0]
            car_ahead_time = leaderboard[my_idx - 1][1]
            gap = current_driver_time[1] - car_ahead_time
            return gap, car_ahead_name
        return 999.0, "NONE"

    def _get_teammate(self, driver_name):
        """Trova il compagno di squadra"""
        teams = {
            'LEC': 'FER', 'SAI': 'FER', 
            'VER': 'RBR', 'PER': 'RBR', 
            'NOR': 'MCL', 'PIA': 'MCL', 
            'HAM': 'MER', 'RUS': 'MER',
            'ALO': 'AST', 'STR': 'AST',
            'GAS': 'ALP', 'OCO': 'ALP',
            'HUL': 'HAA', 'MAG': 'HAA',
            'TSU': 'RB', 'LAW': 'RB',
            'ALB': 'WIL', 'SAR': 'WIL',
            'BOT': 'SAU', 'ZHO': 'SAU'
        }
        my_team = teams.get(driver_name)
        if not my_team: 
            return None
        for d in self.drivers_state:
            if d != driver_name and teams.get(d) == my_team: 
                return d
        return None

    def run_simulation(self):
        """Esegue simulazione gara completa"""
        print("🏁 STARTING GLOBAL SIMULATION...")
        
        self.race_history = []
        
        SERVICE_TIME = 5.0 
        SC_START_LAP = 999  # Disabilitato per ora
        
        for lap in range(1, self.total_laps + 1):
            
            # 1. SAFETY CAR (opzionale)
            if lap == SC_START_LAP:
                for drv_name, state in self.drivers_state.items():
                    if state['pit_stops'] == 0 and state['planned_pit_lap'] > lap + 5:
                        state['planned_pit_lap'] = lap 

            # 2. LEADERBOARD
            leaderboard = sorted(
                [(d, info['total_time']) for d, info in self.drivers_state.items()],
                key=lambda x: x[1]
            )
            
            # Aggiorna posizioni
            for pos, (drv, _) in enumerate(leaderboard, 1):
                self.drivers_state[drv]['position'] = pos
            
            pitting_drivers = [d for d, s in self.drivers_state.items() if s['planned_pit_lap'] == lap]
            
            # 3. LOOP PILOTI
            for drv_name, state in self.drivers_state.items():
                
                # --- A. DOUBLE STACK CHECK ---
                actual_pit_now = False
                if state['planned_pit_lap'] == lap:
                    teammate = self._get_teammate(drv_name)
                    if teammate and teammate in pitting_drivers:
                        my_time = state['total_time']
                        team_time = self.drivers_state[teammate]['total_time']
                        if team_time < my_time:
                            if (my_time - team_time) < SERVICE_TIME:
                                # print(f"   ⚠️ CONFLITTO {drv_name}: Ritardo sosta (+1 giro)")
                                state['planned_pit_lap'] += 1
                                actual_pit_now = False
                            else: 
                                actual_pit_now = True
                        else: 
                            actual_pit_now = True
                    else: 
                        actual_pit_now = True
                
                # --- B. INFO RIVALE ---
                gap_ahead, rival_name = self.get_gap_to_car_ahead(
                    (drv_name, state['total_time']), 
                    leaderboard
                )
                
                # --- C. ESECUZIONE PIT ---
                pit_loss = 0.0
                if actual_pit_now:
                    state['compound'] = 'HARD'
                    state['tyre_age'] = 0
                    state['pit_stops'] += 1
                    is_sc = (SC_START_LAP <= lap <= SC_START_LAP + 2)
                    pit_loss = 14.0 if is_sc else self.pit_loss_time

                # --- D. FISICA BASE ---
                lap_time_base = self.calculate_lap_time(
                    state['compound'], 
                    state['tyre_age'], 
                    state['fuel'],
                    state['pace_factor']
                )
                
                # --- E. TRAFFICO & SORPASSO ---
                traffic_pen = 0.0
                
                if rival_name != "NONE" and gap_ahead < 1.5:
                    rival_pace = self.drivers_state[rival_name].get('pace_factor', 0.0)
                    my_pace = state['pace_factor']
                    
                    pace_advantage = rival_pace - my_pace 
                    
                    # SOGLIA SORPASSO: Se sono più veloce di 0.15s, PASSO
                    if pace_advantage > 0.15:
                        traffic_pen = 0.0 
                    else:
                        # Altrimenti resto bloccato
                        traffic_pen = 0.8 

                # --- SOMMA FINALE ---
                total_lap_time = lap_time_base + pit_loss + traffic_pen
                
                state['total_time'] += total_lap_time
                state['fuel'] -= self.FUEL_BURN
                state['tyre_age'] += 1
                
                self.race_history.append({
                    'Lap': lap, 
                    'Driver': drv_name, 
                    'TotalTime': state['total_time'], 
                    'Tyre': state['compound'], 
                    'GapAhead': gap_ahead
                })
        
        print(f"✅ Simulazione completata - {self.total_laps} giri")
        return pd.DataFrame(self.race_history)