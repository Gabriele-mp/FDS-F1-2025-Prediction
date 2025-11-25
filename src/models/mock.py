# src/models/mock.py

class MockModel:
    """
    Simula il comportamento della vettura ad Abu Dhabi (Yas Marina).
    Implementa le 30 variabili strategiche definite nel documento.
    """
    def __init__(self):
        # --- VARIABILI SPECIFICHE ABU DHABI (Costanti) ---
        self.PIT_LOSS_BASE = 22.0      # Variabile 23: Tunnel uscita box
        self.FUEL_BURN = 1.8           # Variabile 22: Consumo kg/giro
        self.FUEL_TIME_GAIN = 0.035    # Guadagno tempo per kg perso
        self.OVERTAKE_DELTA = 1.5      # Variabile 25: Delta necessario per sorpasso
        
        # Base pace (indicativo)
        self.base_pace = 88.0 

    def predict_pace(self, compound, tyre_age, fuel_load, track_temp_drop=0):
        """
        Calcola il tempo sul giro basandosi su variabili fisiche.
        track_temp_drop: Gradi persi rispetto all'inizio (es. -5 gradi)
        """
        # 1. DEGRADO BASE (Variabili 1, 13)
        if compound == 'SOFT':
            base_deg = 0.15 
            warmup_laps = 1  # Variabile 12: Soft entra subito
        elif compound == 'MEDIUM':
            base_deg = 0.08
            warmup_laps = 2
        else: # HARD
            base_deg = 0.04
            warmup_laps = 4  # Hard ci mette tanto a scaldarsi
            
        # 2. EFFETTO TEMPERATURA (Variabile 21)
        # Se la pista si raffredda (notte), le Hard fanno più fatica (Warmup più lungo)
        # ma il degrado termico scende.
        if track_temp_drop < -5: 
            base_deg *= 0.9  # Degrado migliora col fresco
            warmup_laps += 1 # Ma warmup peggiora
            
        # Calcolo Degrado Effettivo
        current_degrade = base_deg * tyre_age
        
        # Penalità Warmup (Gomme fredde appena usciti dai box)
        warmup_penalty = 0.0
        if tyre_age < warmup_laps:
            warmup_penalty = 1.5 # Primo giro lento!
            
        # 3. EFFETTO CARBURANTE (Variabile 3)
        fuel_penalty = fuel_load * self.FUEL_TIME_GAIN
        
        return self.base_pace + current_degrade + fuel_penalty + warmup_penalty

    def get_pit_loss(self, safety_car=False):
        # Variabile 9: Track Status impact
        if safety_car:
            return 14.0 # Sosta "economica" sotto SC
        return self.PIT_LOSS_BASE