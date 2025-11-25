class TrackPhysics:
    """
    Gestisce le variabili fisiche (Variabili 1-20 del documento .tex).
    Aggiornato per gestire:
    1. Performance differenziate per auto (Pace Factor)
    2. Traffico (Dirty Air / GNN)
    """
    def __init__(self, track_name):
        if track_name == 'AUSTIN':
            self.PIT_LOSS = 20.5
            self.FUEL_BURN = 1.6
            self.FUEL_TIME_GAIN = 0.035
            self.BASE_PACE = 98.0      # Tempo medio del gruppo (1:38.0)
        else:
            # Default Abu Dhabi
            self.PIT_LOSS = 22.0
            self.FUEL_BURN = 1.8
            self.FUEL_TIME_GAIN = 0.03
            self.BASE_PACE = 88.0

    def calculate_lap_time(self, compound, tyre_age, fuel_load, 
                          car_performance_factor, grid_position, lap_number,
                          traffic_gap=99.0): # Default: Pista libera
        """
        Calcola il tempo sul giro combinando Fisica, Performance e Traffico.
        """
        
        # --- 1. CAR PERFORMANCE (Fondamentale: definire car_pace subito!) ---
        # Se factor è negativo (es. -0.5), l'auto è più veloce della media.
        car_pace = self.BASE_PACE + car_performance_factor

        # --- 2. Tyre Compound & Age ---
        if compound == 'SOFT': base_deg = 0.12 
        elif compound == 'MEDIUM': base_deg = 0.07
        else: base_deg = 0.04 # HARD
            
        tyre_deg_penalty = base_deg * tyre_age
        
        # --- 3. Fuel Load ---
        fuel_penalty = fuel_load * self.FUEL_TIME_GAIN
        
        # --- 4. GRID POSITION / START CHAOS ---
        start_penalty = 0.0
        if lap_number == 1:
            # Perdi circa 0.3s per ogni fila che hai davanti al via
            start_penalty = 2.5 + (grid_position * 0.3)
            
        # Somma parziale (Fisica pura)
        physical_time = car_pace + tyre_deg_penalty + fuel_penalty + start_penalty
        
        # --- 5. TRAFFICO (Correzione GNN) ---
        traffic_penalty = 0.0
        # Se ho qualcuno davanti a meno di 1.5s, soffro "Dirty Air"
        if traffic_gap < 1.5:
            traffic_penalty = 0.8 # Perdo tempo in curva
            # (Qui potremmo togliere qualcosa per il DRS, es -0.3, 
            # ma a Yas Marina/Austin spesso si perde comunque nel misto)
            if traffic_gap < 0.8: # DRS Zone
                traffic_penalty -= 0.3 
        
        # TEMPO FINALE
        return physical_time + traffic_penalty