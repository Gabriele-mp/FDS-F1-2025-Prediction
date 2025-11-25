# src/models/gnn_mock.py

class TrafficGNN:
    """
    Simula la Graph Neural Network che calcola l'effetto del traffico.
    In futuro questa sarà una vera rete PyTorch Geometric.
    """
    def get_dirty_air_penalty(self, my_car_pace, rival_pace, gap):
        """
        Calcola quanto tempo perdo stando dietro a un'altra auto.
        Input:
            my_car_pace: Il mio passo ideale (es. 90s)
            rival_pace: Il passo di chi ho davanti (es. 91s)
            gap: Distanza in secondi (es. 0.8s)
        Output:
            Secondi persi (Penalità)
        """
        # Se sono lontano (> 2s), l'aria è pulita -> Nessuna penalità
        if gap > 2.0:
            return 0.0
        
        # Calcolo quanto sono più veloce di lui
        delta_pace = my_car_pace - rival_pace # Se negativo, sono più veloce io
        
        # CASO 1: DRS TRAIN (Sono più veloce ma bloccato vicino)
        if delta_pace < -0.5 and gap < 1.0:
            # Effetto "Aria Sporca": perdo quasi 1 secondo al giro!
            return 0.8 
            
        # CASO 2: SORPASSO FACILE (Sono MOLTO più veloce)
        elif delta_pace < -1.5:
            return 0.1 # Passo quasi subito, perdo poco tempo
            
        # CASO 3: LOTTA PARI
        else:
            return 0.4 # Perdo un po' di tempo a seguire