from src.models.physics_engine import TrackPhysics

class StrategyOptimizer:
    def __init__(self, track_name='AUSTIN'):
        self.physics = TrackPhysics(track_name)
        self.TOTAL_LAPS = 56 # Austin
        
    def find_optimal_strategy(self, driver_profile):
        """
        Calcola il giro di sosta IDEALE per un pilota specifico,
        basandosi sulle sue caratteristiche di consumo gomme e passo.
        """
        best_pit_lap = 0
        min_total_time = float('inf')
        
        # Parametri pilota
        compound_start = driver_profile['StartCompound']
        pace_factor = driver_profile['PaceFactor']
        
        # Provo tutte le finestre possibili (es. dal giro 10 al 45)
        # Non ha senso fermarsi al giro 1 o al 55.
        for test_pit_lap in range(12, 45):
            
            total_time = self._simulate_race_time(
                test_pit_lap, compound_start, pace_factor
            )
            
            if total_time < min_total_time:
                min_total_time = total_time
                best_pit_lap = test_pit_lap
                
        return best_pit_lap, min_total_time

    def _simulate_race_time(self, pit_lap, start_compound, pace_factor):
        """
        Simulazione veloce (senza traffico) per trovare il teorico ottimo.
        """
        time_sum = 0.0
        fuel = 100.0
        current_compound = start_compound
        tyre_age = 0 # Assumiamo gomme nuove al via per semplicità ottimizzazione
        
        for lap in range(1, self.TOTAL_LAPS + 1):
            # Pit Stop
            pit_loss = 0
            if lap == pit_lap:
                current_compound = 'HARD'
                tyre_age = 0
                pit_loss = self.physics.PIT_LOSS
            
            # Calcolo tempo (senza traffico, è l'ottimo teorico)
            lap_time = self.physics.calculate_lap_time(
                current_compound, tyre_age, fuel, pace_factor, 
                grid_position=1, lap_number=lap, traffic_gap=99.0
            )
            
            time_sum += lap_time + pit_loss
            
            # Update fisica
            fuel -= self.physics.FUEL_BURN
            tyre_age += 1
            
        return time_sum