# src/strategy/simulation.py
from src.models.mock import MockModel

class RaceStrategist:
    def __init__(self, model):
        self.model = model
        self.TOTAL_LAPS = 58 # Giri totali GP Abu Dhabi

    def check_undercut_opportunity(self, current_lap, my_car, rival_car):
        """
        Valuta se conviene fermarsi ORA per superare il rivale (Undercut).
        """
        print(f"\n--- Analisi Strategica Giro {current_lap} ---")
        
        # 1. Calcolo benzina attuale
        fuel_now = 100 - (current_lap * 1.8)

        # 2. SCENARIO A: RIMANGO FUORI (Gomme vecchie)
        time_stay_out = self.model.predict_pace(
            my_car['compound'], my_car['tyre_age'], fuel_now
        )
        
        # 3. SCENARIO B: MI FERMO (Gomme nuove Hard)
        # Nota: Se mi fermo, l'età della gomma diventa 0
        time_box_now = self.model.predict_pace(
            'HARD', 0, fuel_now
        )
        
        # 4. CALCOLO DEL VANTAGGIO
        pace_advantage = time_stay_out - time_box_now
        pit_loss = self.model.get_pit_loss() # 22 secondi
        
        print(f"Passo attuale (Gomme vecchie): {time_stay_out:.3f}s")
        print(f"Passo potenziale (Gomme nuove): {time_box_now:.3f}s")
        print(f"Guadagno di passo: {pace_advantage:.3f}s al giro")
        print(f"Distacco dal rivale: {rival_car['gap_to_me']}s")
        
        # --- LOGICA DI DECISIONE ---
        # La regola d'oro: Se guadagno > 1.5s al giro E il rivale è vicino (<2s)
        # allora l'undercut è potente.
        if pace_advantage > 1.5 and rival_car['gap_to_me'] < 2.0:
            return True, "BOX BOX! Tenta l'Undercut ora!"
        else:
            return False, "STAY OUT. Non hai abbastanza vantaggio."

# --- BLOCCO DI TEST (Simulazione) ---
if __name__ == "__main__":
    # Inizializzo il modello finto
    mock_model = MockModel()
    strategist = RaceStrategist(mock_model)
    
    # Simulo una situazione di gara (es. Ferrari vs Mercedes)
    my_ferrari = {'compound': 'MEDIUM', 'tyre_age': 18} # Gomme medie usate da 18 giri
    rival_mercedes = {'gap_to_me': 1.2} # Lui è davanti di 1.2 secondi
    
    # Chiedo all'algoritmo cosa fare al giro 20
    decision, message = strategist.check_undercut_opportunity(20, my_ferrari, rival_mercedes)
    
    print(f"DECISIONE MURETTO: {message}")