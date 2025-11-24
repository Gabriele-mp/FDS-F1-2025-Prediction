# src/models/mock.py

class MockModel:
    """
    Simula il comportamento della vettura ad Abu Dhabi
    in attesa che il Membro B finisca la Rete Neurale vera (LSTM).
    """
    def __init__(self):
        # Dati estratti dai tuoi PDF "Variabili determinanti"
        self.PIT_LOSS = 22.0       # Secondi persi in pit lane (tunnel uscita)
        self.FUEL_BURN = 1.8       # Kg consumati per giro
        self.FUEL_TIME_GAIN = 0.03 # Guadagno tempo (sec) per ogni Kg in meno
        
        # Passo gara base indicativo per Abu Dhabi (1:28.0)
        self.base_pace = 88.0 

    def predict_pace(self, compound, tyre_age, fuel_load):
        """
        Restituisce il tempo previsto sul giro (in secondi).
        """
        # 1. Degrado Gomma (Semplificato per ora)
        # Soft degrada molto (0.15s/giro), Hard poco (0.04s/giro)
        if compound == 'SOFT':
            degrade = 0.15 * tyre_age  
        elif compound == 'MEDIUM':
            degrade = 0.08 * tyre_age
        else: # HARD
            degrade = 0.04 * tyre_age
            
        # 2. Effetto Carburante (Più è leggera, più va forte)
        # 100kg all'inizio -> macchina lenta. 0kg alla fine -> macchina veloce.
        fuel_penalty = fuel_load * self.FUEL_TIME_GAIN
        
        return self.base_pace + degrade + fuel_penalty

    def get_pit_loss(self):
        return self.PIT_LOSS