import matplotlib.pyplot as plt

def plot_strategy_comparison(laps_a, times_a, laps_b, times_b):
    """
    Genera il grafico a due pannelli: Passo Gara e Distacco.
    """
    plt.figure(figsize=(14, 6))
    
    # Pannello 1: Tempi sul giro
    plt.subplot(1, 2, 1)
    plt.plot(laps_a, times_a, label='Piano A (Pit L20)', linewidth=2)
    plt.plot(laps_b, times_b, label='Piano B (Pit L15)', linestyle='--', linewidth=2)
    plt.title('Confronto Passo Gara')
    plt.xlabel('Giro')
    plt.ylabel('Tempo (s)')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Pannello 2: Calcolo del Delta (Gap)
    cum_a = _get_cumulative(laps_a, times_a, 20) # Pit lap hardcoded per ora
    cum_b = _get_cumulative(laps_b, times_b, 15)
    delta = [a - b for a, b in zip(cum_a, cum_b)]

    plt.subplot(1, 2, 2)
    plt.plot(laps_a, delta, color='purple', linewidth=2)
    plt.axhline(0, color='black', linestyle='--')
    plt.fill_between(laps_a, delta, 0, where=[d>0 for d in delta], facecolor='orange', alpha=0.3, label='B in Vantaggio')
    plt.fill_between(laps_a, delta, 0, where=[d<0 for d in delta], facecolor='blue', alpha=0.3, label='A in Vantaggio')
    
    plt.title('Gap Strategico (Undercut)')
    plt.xlabel('Giro')
    plt.ylabel('Distacco (s)')
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()

def _get_cumulative(laps, times, pit_lap):
    # Funzione helper interna
    cumulative = []
    curr = 0
    for l, t in zip(laps, times):
        curr += t
        if l == pit_lap: curr += 22.0 # Pit Loss
        cumulative.append(curr)
    return cumulative