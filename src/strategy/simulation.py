import matplotlib.pyplot as plt
from src.models.mock import MockModel

class RaceSimulation:
    def __init__(self):
        self.model = MockModel()
        self.TOTAL_LAPS = 58
        
    def run_advanced_simulation(self, my_strat, rival_strat, start_fuel=100.0):
        # Liste per i grafici
        laps = []
        my_times = []
        rival_times = []
        
        # Stato Iniziale
        my_tyre_age = 0
        my_compound = my_strat['start_tyre']
        rival_tyre_age = 0
        rival_compound = rival_strat['start_tyre']
        
        track_temp_drop = 0 
        
        print(f"🚦 START GP ABU DHABI | Fuel: {start_fuel}kg")
        
        for lap in range(1, self.TOTAL_LAPS + 1):
            # 1. Variabili Ambientali
            if lap % 10 == 0: track_temp_drop -= 1
            current_fuel = start_fuel - (lap * 1.8)
            
            # 2. Gestione Pit Stop
            # Nota: Qui calcoliamo solo il passo puro. 
            # Il tempo perso (22s) lo aggiungeremo nel grafico cumulativo.
            
            if lap == my_strat['pit_lap']:
                print(f"Lap {lap}: BOX BOX (Io) -> HARD")
                my_compound = 'HARD'
                my_tyre_age = 0
            
            if lap == rival_strat['pit_lap']:
                print(f"Lap {lap}: RIVALE BOX -> HARD")
                rival_compound = 'HARD'
                rival_tyre_age = 0
            
            # 3. Predizione
            my_time = self.model.predict_pace(my_compound, my_tyre_age, current_fuel, track_temp_drop)
            rival_time = self.model.predict_pace(rival_compound, rival_tyre_age, current_fuel, track_temp_drop)
            
            # 4. Salvataggio Dati
            laps.append(lap)
            my_times.append(my_time)
            rival_times.append(rival_time)
            
            my_tyre_age += 1
            rival_tyre_age += 1

        return laps, my_times, rival_times

    def plot_results(self, laps, my_times, rival_times, my_pit, rival_pit):
        """
        Genera il grafico del distacco cumulativo.
        """
        # Calcolo tempi cumulativi (Gara vera)
        cum_me = []
        cum_rival = []
        sum_m = 0
        sum_r = 0
        pit_loss = self.model.get_pit_loss() # 22s
        
        for lap, tm, tr in zip(laps, my_times, rival_times):
            sum_m += tm
            sum_r += tr
            # Aggiungo penalità se è il giro del pit
            if lap == my_pit: sum_m += pit_loss
            if lap == rival_pit: sum_r += pit_loss
            
            cum_me.append(sum_m)
            cum_rival.append(sum_r)
            
        # Delta: (Tempo Mio - Tempo Rivale). Se negativo, sono davanti io!
        delta = [m - r for m, r in zip(cum_me, cum_rival)]
        
        plt.figure(figsize=(10, 6))
        plt.plot(laps, delta, color='purple', linewidth=2, label='Distacco (sec)')
        plt.axhline(0, color='black', linestyle='--', label='Parità')
        
        # Coloro le aree
        plt.fill_between(laps, delta, 0, where=[d<0 for d in delta], facecolor='green', alpha=0.3, label='Io in Testa')
        plt.fill_between(laps, delta, 0, where=[d>0 for d in delta], facecolor='red', alpha=0.3, label='Rivale in Testa')
        
        plt.title(f'Simulazione Strategia: Pit L{my_pit} (Io) vs Pit L{rival_pit} (Rivale)')
        plt.xlabel('Giro')
        plt.ylabel('Distacco (< 0 = Vinco Io)')
        plt.legend()
        plt.grid(True)
        plt.show()

if __name__ == "__main__":
    sim = RaceSimulation()
    
    # Definisci le strategie
    my_pit = 18
    rival_pit = 24
    
    laps, me, rival = sim.run_advanced_simulation(
        {'start_tyre': 'MEDIUM', 'pit_lap': my_pit},
        {'start_tyre': 'MEDIUM', 'pit_lap': rival_pit}
    )
    
    # Mostra il grafico
    sim.plot_results(laps, me, rival, my_pit, rival_pit)