"""
Configurazioni circuiti F1
Parametri storici (2019-2024) per ogni tracciato
✅ DATI PRE-GARA: Da analisi stagioni precedenti
"""


class CircuitConfig:
    """
    Database parametri storici per circuito.
    Questi valori NON sono cheating - derivano da analisi storica.
    """
    
    CONFIGS = {
        'Abu Dhabi': {
            'pit_window': (23, 5),       # Giro medio pit ± std (analisi 2019-2023)
            'pit_loss_time': 22.0,       # Secondi persi in pit (tunnel lungo)
            'total_laps': 58,            # Giri totali gara
            'tyre_degradation': {        # s/giro per compound
                'SOFT': 0.12,
                'MEDIUM': 0.08,
                'HARD': 0.05
            },
            'overtake_difficulty': 0.7,  # 0=facile (Monza), 1=impossibile (Monaco)
            'drs_zones': 2,
            'safety_car_probability': 0.15,  # 15% chance SC/VSC
            'fuel_burn': 1.8,            # kg/giro
            'fuel_time_gain': 0.03       # s/giro per kg
        },
        
        'Austin': {
            'pit_window': (23, 5),
            'pit_loss_time': 21.5,
            'total_laps': 56,
            'tyre_degradation': {
                'SOFT': 0.15,
                'MEDIUM': 0.10,
                'HARD': 0.06
            },
            'overtake_difficulty': 0.5,
            'drs_zones': 2,
            'safety_car_probability': 0.20,
            'fuel_burn': 1.6,
            'fuel_time_gain': 0.035
        },
        
        'Monza': {
            'pit_window': (25, 6),
            'pit_loss_time': 18.0,       # Pit lane molto corta!
            'total_laps': 53,
            'tyre_degradation': {
                'SOFT': 0.08,
                'MEDIUM': 0.05,
                'HARD': 0.03
            },
            'overtake_difficulty': 0.2,  # Facile sorpassare
            'drs_zones': 2,
            'safety_car_probability': 0.10,
            'fuel_burn': 1.5,
            'fuel_time_gain': 0.04
        },
        
        'Monaco': {
            'pit_window': (30, 8),       # Pit molto tardivi
            'pit_loss_time': 24.0,
            'total_laps': 78,
            'tyre_degradation': {
                'SOFT': 0.06,
                'MEDIUM': 0.04,
                'HARD': 0.02
            },
            'overtake_difficulty': 0.95, # Quasi impossibile!
            'drs_zones': 1,
            'safety_car_probability': 0.50,  # 50% SC a Monaco!
            'fuel_burn': 1.3,
            'fuel_time_gain': 0.025
        },
        
        'Spa': {
            'pit_window': (20, 4),
            'pit_loss_time': 19.0,
            'total_laps': 44,
            'tyre_degradation': {
                'SOFT': 0.10,
                'MEDIUM': 0.07,
                'HARD': 0.04
            },
            'overtake_difficulty': 0.3,
            'drs_zones': 2,
            'safety_car_probability': 0.25,
            'fuel_burn': 1.7,
            'fuel_time_gain': 0.035
        },
        
        'Silverstone': {
            'pit_window': (22, 5),
            'pit_loss_time': 20.0,
            'total_laps': 52,
            'tyre_degradation': {
                'SOFT': 0.14,
                'MEDIUM': 0.09,
                'HARD': 0.05
            },
            'overtake_difficulty': 0.4,
            'drs_zones': 2,
            'safety_car_probability': 0.15,
            'fuel_burn': 1.6,
            'fuel_time_gain': 0.03
        }
    }
    
    @classmethod
    def get(cls, circuit_name):
        """
        Ritorna config per circuito.
        Se non trovato, usa default generico.
        
        Args:
            circuit_name: 'Abu Dhabi', 'Monaco', 'Austin', etc.
        """
        # Normalizza nome (case-insensitive)
        for key in cls.CONFIGS.keys():
            if key.lower() in circuit_name.lower():
                print(f"✅ Config caricata per: {key}")
                return cls.CONFIGS[key]
        
        # Fallback
        print(f"⚠️ Config per '{circuit_name}' non trovata, uso default")
        return cls.get_default()
    
    @classmethod
    def get_default(cls):
        """Config generica per circuiti sconosciuti"""
        return {
            'pit_window': (25, 5),
            'pit_loss_time': 21.0,
            'total_laps': 55,
            'tyre_degradation': {
                'SOFT': 0.10,
                'MEDIUM': 0.07,
                'HARD': 0.04
            },
            'overtake_difficulty': 0.5,
            'drs_zones': 2,
            'safety_car_probability': 0.20,
            'fuel_burn': 1.6,
            'fuel_time_gain': 0.03
        }
    
    @classmethod
    def list_available(cls):
        """Lista circuiti con config disponibile"""
        return list(cls.CONFIGS.keys())
    
    @classmethod
    def add_circuit(cls, name, config):
        """
        Aggiunge un nuovo circuito al database.
        Utile per Abu Dhabi 2025 dopo aver analizzato i dati.
        """
        cls.CONFIGS[name] = config
        print(f"✅ Circuito '{name}' aggiunto al database")