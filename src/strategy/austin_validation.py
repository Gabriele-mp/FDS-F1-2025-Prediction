from src.models.physics_engine import TrackPhysics

class AustinSimulator:
    def __init__(self):
        self.physics = TrackPhysics('AUSTIN')
        self.LAPS = 56 
        
        # DATI DI PASSO GARA (Performance Factor)
        # Questi sono i valori che normalmente predirrebbe la tua Rete Neurale (Modulo B).
        # Per la validazione storica, usiamo i dati noti delle FP2 di Austin 2024.
        # (Negativo = Più veloce della media di 98.0s)
        self.TEAM_PACE = {
            'LEC': -0.45, # Ferrari dominante quel giorno
            'SAI': -0.40, # Sainz fortissimo
            'VER': -0.10, # Verstappen faticava
            'NOR': -0.15, # Norris veloce ma incostante
            'PIA': 0.00,  # Piastri media
            'HAM': -0.05, # Mercedes instabile
            'RUS': -0.05
        }

    def run_race(self, driver_data):
        driver = driver_data['Driver']
        compound = driver_data['StartCompound']
        tyre_age = driver_data['StartTyreAge']
        grid_pos = driver_data['GridPosition'] # Ora usiamo la Variabile 18!
        
        # Recupero il passo specifico di quel pilota
        pace_factor = self.TEAM_PACE.get(driver, 0.5) # Se non in lista, è lento (+0.5)
        
        fuel = 100.0
        total_time = 0.0
        history = []
        
        # Strategia: I primi si sono fermati intorno al giro 22-27
        pit_lap = 26 
        
        for lap in range(1, self.LAPS + 1):
            
            # PIT STOP
            loss = 0
            if lap == pit_lap:
                compound = 'HARD'
                tyre_age = 0
                loss = self.physics.PIT_LOSS
                
            # CALCOLO TEMPO (Ora passiamo grid_pos e pace_factor)
            lap_time = self.physics.calculate_lap_time(
                compound, tyre_age, fuel, 
                car_performance_factor=pace_factor,
                grid_position=grid_pos,
                lap_number=lap
            )
            
            total_time += lap_time + loss
            history.append(total_time)
            
            # Aggiornamento Variabili
            fuel -= self.physics.FUEL_BURN
            tyre_age += 1
            
        return total_time, history