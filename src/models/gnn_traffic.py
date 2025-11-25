import random

class TrafficGNN:
    """
    Gestisce traffico e SORPASSI.
    """
    def __init__(self):
        self.DIRTY_AIR_PENALTY = 0.8  
        self.OVERTAKE_THRESHOLD = 0.4 # Se sono più veloce di 0.4s, posso provare a passare
        
        # Memoria dello stato sorpassi (Chi ha passato chi)
        # Key: Driver, Value: Set di piloti superati
        self.overtakes = {} 

    def calculate_interaction(self, my_pace, rival_pace, gap_ahead, driver_name, rival_name):
        """
        Calcola penalità traffico OPPURE sorpasso.
        """
        # Se ho già superato questo rivale, lo ignoro (aria libera)
        if driver_name in self.overtakes and rival_name in self.overtakes[driver_name]:
            return 0.0

        traffic_delta = 0.0
        
        # Se sono vicino (Aria Sporca)
        if gap_ahead < 1.5:
            
            # Calcolo quanto sono più veloce di base
            pace_diff = rival_pace - my_pace # Es. 92.0 - 91.0 = +1.0s (Sono più veloce)
            
            # LOGICA SORPASSO
            # Se sono molto più veloce (e un po' di fortuna/DRS) -> SORPASSO
            if pace_diff > self.OVERTAKE_THRESHOLD:
                probability = 0.3 # 30% di chance a giro di passare
                if random.random() < probability:
                    print(f"🚀 SORPASSO! {driver_name} ha superato {rival_name}!")
                    
                    # Registro il sorpasso in memoria
                    if driver_name not in self.overtakes: self.overtakes[driver_name] = set()
                    self.overtakes[driver_name].add(rival_name)
                    
                    return -0.5 # Bonus: Aria pulita subito!
            
            # Se non passo, subisco penalità (Dirty Air)
            traffic_delta = self.DIRTY_AIR_PENALTY
            
        return traffic_delta