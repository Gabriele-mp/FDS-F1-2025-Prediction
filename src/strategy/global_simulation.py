import pandas as pd
import numpy as np
from src.models.physics_engine import TrackPhysics
from src.models.gnn_traffic import TrafficGNN

class GlobalRaceSimulator:
    def __init__(self, track_name='AUSTIN'):
        self.physics = TrackPhysics(track_name)
        self.gnn = TrafficGNN()
        self.TOTAL_LAPS = 56 
        
        self.drivers_state = {} 
        self.race_history = []

    def initialize_grid(self, grid_data):
        grid_data = grid_data.sort_values('GridPosition')
        for _, row in grid_data.iterrows():
            drv = row['Driver']
            self.drivers_state[drv] = {
                'position': row['GridPosition'],
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

    def get_gap_to_car_ahead(self, current_driver_time, leaderboard):
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
        teams = {'LEC': 'FER', 'SAI': 'FER', 'VER': 'RBR', 'PER': 'RBR', 
                 'NOR': 'MCL', 'PIA': 'MCL', 'HAM': 'MER', 'RUS': 'MER'}
        my_team = teams.get(driver_name)
        if not my_team: return None
        for d in self.drivers_state:
            if d != driver_name and teams.get(d) == my_team: return d
        return None

    def run_simulation(self):
        print("🏁 STARTING GLOBAL SIMULATION (Fixed Overtake Logic)...")
        
        SERVICE_TIME = 5.0 
        SC_START_LAP = 3
        
        for lap in range(1, self.TOTAL_LAPS + 1):
            
            # 1. SAFETY CAR
            if lap == SC_START_LAP:
                # print(f"🚨 SCATTATA SAFETY CAR (Giro {lap})")
                for drv_name, state in self.drivers_state.items():
                    if state['pit_stops'] == 0 and state['planned_pit_lap'] > lap + 5:
                        state['planned_pit_lap'] = lap 

            # 2. LEADERBOARD
            leaderboard = sorted(
                [(d, info['total_time']) for d, info in self.drivers_state.items()],
                key=lambda x: x[1]
            )
            
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
                                print(f"   ⚠️ CONFLITTO {drv_name}: Ritardo sosta (+1 giro)")
                                state['planned_pit_lap'] += 1
                                actual_pit_now = False
                            else: actual_pit_now = True
                        else: actual_pit_now = True
                    else: actual_pit_now = True
                
                # --- B. INFO RIVALE ---
                gap_ahead, rival_name = self.get_gap_to_car_ahead((drv_name, state['total_time']), leaderboard)
                
                # --- C. ESECUZIONE PIT ---
                pit_loss = 0.0
                if actual_pit_now:
                    state['compound'] = 'HARD'
                    state['tyre_age'] = 0
                    state['pit_stops'] += 1
                    is_sc = (3 <= lap <= 5)
                    pit_loss = 14.0 if is_sc else self.physics.PIT_LOSS

                # --- D. FISICA BASE ---
                lap_time_base = self.physics.calculate_lap_time(
                    state['compound'], state['tyre_age'], state['fuel'],
                    state['pace_factor'], state['position'], lap, traffic_gap=99.0
                )
                
                # --- E. TRAFFICO & SORPASSO (LOGICA CORRETTA) ---
                traffic_pen = 0.0
                
                if rival_name != "NONE" and gap_ahead < 1.5:
                    # Recupero passi base
                    rival_pace = self.drivers_state[rival_name].get('pace_factor', 0.0)
                    my_pace = state['pace_factor']
                    
                    # Esempio: LEC (-0.30) vs NOR (-0.10). 
                    # Diff = (-0.10) - (-0.30) = +0.20s (Sono più veloce di 0.2s)
                    pace_advantage = rival_pace - my_pace 
                    
                    # SOGLIA SORPASSO: Se sono più veloce di 0.15s, PASSO (penalità zero)
                    if pace_advantage > 0.15:
                        traffic_pen = 0.0 
                    else:
                        # Altrimenti resto bloccato nell'aria sporca
                        traffic_pen = 0.8 

                # --- SOMMA FINALE ---
                total_lap_time = lap_time_base + pit_loss + traffic_pen
                
                state['total_time'] += total_lap_time
                state['fuel'] -= self.physics.FUEL_BURN
                state['tyre_age'] += 1
                
                self.race_history.append({
                    'Lap': lap, 'Driver': drv_name, 'TotalTime': state['total_time'], 
                    'Tyre': state['compound'], 'GapAhead': gap_ahead
                })
                
        return pd.DataFrame(self.race_history)