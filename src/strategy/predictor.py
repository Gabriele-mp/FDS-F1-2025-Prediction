"""
STEP 3: Wrapper per usare GlobalRaceSimulator con dati reali - FIXED v2
"""
import pandas as pd
import numpy as np
from src.strategy.global_simulation import GlobalRaceSimulator
from src.data.circuit_configs import CircuitConfig

class RacePredictor:
    def __init__(self, track_name='AUSTIN'):
        self.track_name = track_name
        config = CircuitConfig.get(track_name)
        self.simulator = GlobalRaceSimulator(
            total_laps=config['total_laps'],
            pit_loss_time=config['pit_loss_time']
        )
        
    def optimize_pit_strategy(self, grid_df, use_real_pits=False, real_pit_stops=None):
        """
        Ottimizza giro pit stop per ogni driver
        
        Args:
            grid_df: DataFrame con piloti
            use_real_pits: Se True, usa pit stop reali (per validazione fisica)
            real_pit_stops: DataFrame con pit stop reali
        """
        print("🔍 Ottimizzazione strategia pit stop...")
        
        # Aggiungi colonna PitLap se non esiste
        if 'PitLap' not in grid_df.columns:
            grid_df['PitLap'] = 0
        
        if use_real_pits and real_pit_stops is not None:
            # USA PIT STOP REALI (per testare solo la fisica, non la strategia)
            print("  ⚠️  MODALITÀ VALIDAZIONE: Usando pit stop REALI")
            
            for idx, row in grid_df.iterrows():
                driver = row['Driver']
                # Cerca pit stop reale
                real_pit = real_pit_stops[real_pit_stops['Driver'] == driver]
                
                if len(real_pit) > 0:
                    # Usa il primo pit stop
                    pit_lap = int(real_pit.iloc[0]['PitLap'])
                    grid_df.at[idx, 'PitLap'] = pit_lap
                else:
                    # Default se non ha fatto pit (ritirato?)
                    grid_df.at[idx, 'PitLap'] = 25
            
            print(f"  ✅ Pit stop reali assegnati (range: {grid_df['PitLap'].min()}-{grid_df['PitLap'].max()})")
        else:
            # STRATEGIA OTTIMIZZATA (basata su pace_factor)
            print("  🧠 MODALITÀ PREDIZIONE: Ottimizzando pit stop")
            
            for idx, row in grid_df.iterrows():
                pace = row['PaceFactor']
                
                # Logica: piloti veloci anticipano, lenti ritardano
                if pace < -2.5:  # Molto veloce
                    pit_lap = 23
                elif pace < -1.0:  # Veloce
                    pit_lap = 25
                elif pace < 1.0:  # Medio
                    pit_lap = 26
                else:  # Lento
                    pit_lap = 27
                
                grid_df.at[idx, 'PitLap'] = pit_lap
            
            print(f"  ✅ Strategia ottimizzata (range: {grid_df['PitLap'].min()}-{grid_df['PitLap'].max()})")
        
        return grid_df
    
    def predict_race(self, grid_df, use_real_pits=False, real_pit_stops=None):
        """
        Esegue simulazione completa
        
        Args:
            grid_df: DataFrame con piloti e features
            use_real_pits: Se True, usa pit stop reali
            real_pit_stops: DataFrame con pit stop reali
        
        Returns:
            predictions_df: DataFrame con posizioni finali predette
        """
        print("\n" + "="*60)
        print("🏎️  AVVIO PREDIZIONE GARA")
        print("="*60 + "\n")
        
        # Ottimizza strategie
        grid_df = self.optimize_pit_strategy(grid_df, use_real_pits, real_pit_stops)
        
        # Inizializza simulatore CON IL DATAFRAME CORRETTO
        self.simulator.initialize_grid(grid_df)  # ✅ USA grid_df direttamente
        
        # RUN SIMULATION
        history_df = self.simulator.run_simulation()
        
        # Estrai risultato finale (ultimo giro)
        last_lap = history_df['Lap'].max()
        final_results = history_df[history_df['Lap'] == last_lap].copy()
        
        # Ordina per tempo totale
        final_results = final_results.sort_values('TotalTime').reset_index(drop=True)
        final_results['PredictedPosition'] = range(1, len(final_results) + 1)
        
        # Calcola gap al leader
        leader_time = final_results.iloc[0]['TotalTime']
        final_results['GapToLeader'] = final_results['TotalTime'] - leader_time
        
        print("\n" + "="*60)
        print("🏁 PREDIZIONE FINALE")
        print("="*60)
        print(final_results[['PredictedPosition', 'Driver', 'GapToLeader']].head(10).to_string(index=False))
        print()
        
        return final_results[['Driver', 'PredictedPosition', 'TotalTime', 'GapToLeader']]
    
    def compare_with_actual(self, predictions, actual_results):
        """
        Confronta predizioni con risultati reali
        
        Args:
            predictions: DataFrame da predict_race()
            actual_results: DataFrame da get_race_results()
        """
        print("\n" + "="*60)
        print("📊 VALIDAZIONE: Predetto vs Reale")
        print("="*60 + "\n")
        
        # Merge
        comparison = predictions.merge(
            actual_results[['Abbreviation', 'Position']], 
            left_on='Driver', 
            right_on='Abbreviation',
            how='inner'
        )
        comparison = comparison.rename(columns={'Position': 'ActualPosition'})
        
        # Calcola errore
        comparison['Error'] = comparison['PredictedPosition'] - comparison['ActualPosition']
        comparison['AbsError'] = comparison['Error'].abs()
        
        # Ordina per posizione reale
        comparison = comparison.sort_values('ActualPosition')
        
        print(comparison[['Driver', 'ActualPosition', 'PredictedPosition', 'Error']].head(10).to_string(index=False))
        
        # Metriche
        mae = comparison['AbsError'].mean()
        correct_top3 = (comparison[comparison['ActualPosition'] <= 3]['AbsError'] == 0).sum()
        correct_top10 = (comparison[comparison['ActualPosition'] <= 10]['AbsError'] <= 2).sum()
        
        print(f"\n📈 METRICHE:")
        print(f"  • MAE (Mean Absolute Error): {mae:.2f} posizioni")
        print(f"  • Top 3 esatti: {correct_top3}/3")
        print(f"  • Top 10 entro 2 pos: {correct_top10}/10")
        
        # Diagnosi errori grandi
        big_errors = comparison[comparison['AbsError'] > 5]
        if len(big_errors) > 0:
            print(f"\n⚠️  ERRORI GRANDI (>5 posizioni):")
            for _, row in big_errors.iterrows():
                print(f"  {row['Driver']}: Predetto {int(row['PredictedPosition'])} | Reale {int(row['ActualPosition'])} | Err {int(row['Error'])}")
        
        return comparison