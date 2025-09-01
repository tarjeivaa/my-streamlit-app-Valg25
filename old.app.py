import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from typing import Dict, List, Tuple

class NorwayElectionSimulator:
    """
    Simulator for Norwegian parliamentary seat allocation using the modified Sainte-Laguë method.
    The modified version uses divisors: 1.4, 3, 5, 7, 9, 11, 13, ...
    """
    
    def __init__(self):
        self.threshold = 0.04  # 4% electoral threshold in Norway
    
    def modified_sainte_lague_allocation(self, votes: Dict[str, int], total_seats: int) -> Dict[str, int]:
        """
        Allocate seats using the modified Sainte-Laguë method.
        
        Args:
            votes: Dictionary with party names as keys and vote counts as values
            total_seats: Total number of seats to allocate
            
        Returns:
            Dictionary with party names as keys and allocated seats as values
        """
        # Filter out parties below threshold
        total_valid_votes = sum(votes.values())
        qualified_parties = {
            party: vote_count 
            for party, vote_count in votes.items() 
            if vote_count / total_valid_votes >= self.threshold
        }
        
        if not qualified_parties:
            return {party: 0 for party in votes.keys()}
        
        # Initialize seat allocation
        seats = {party: 0 for party in qualified_parties.keys()}
        
        # Allocate seats one by one
        for _ in range(total_seats):
            quotients = {}
            
            for party, vote_count in qualified_parties.items():
                current_seats = seats[party]
                
                # Modified Sainte-Laguë divisors: 1.4 for first seat, then 3, 5, 7, 9, ...
                if current_seats == 0:
                    divisor = 1.4
                else:
                    divisor = 2 * current_seats + 1
                
                quotients[party] = vote_count / divisor
            
            # Award seat to party with highest quotient
            winner = max(quotients, key=quotients.get)
            seats[winner] += 1
        
        # Add zero seats for parties that didn't qualify
        all_seats = {party: 0 for party in votes.keys()}
        all_seats.update(seats)
        
        return all_seats
    
    def simulate_from_percentages(self, party_percentages: Dict[str, float], total_seats: int) -> Dict[str, int]:
        """
        Simulate seat allocation from vote percentages.
        
        Args:
            party_percentages: Dictionary with party names and their vote percentages (0-100)
            total_seats: Total seats to allocate
            
        Returns:
            Dictionary with allocated seats
        """
        # Convert percentages to vote counts (using arbitrary base of 100,000 votes)
        base_votes = 100000
        votes = {
            party: int(percentage * base_votes / 100) 
            for party, percentage in party_percentages.items()
        }
        
        return self.modified_sainte_lague_allocation(votes, total_seats)
    
    def print_results(self, party_percentages: Dict[str, float], seats: Dict[str, int], total_seats: int):
        """Display formatted results of the simulation."""
        st.subheader("Election Results")
        
        # Create DataFrame for better display
        results_data = []
        sorted_parties = sorted(seats.items(), key=lambda x: x[1], reverse=True)
        
        for party, seat_count in sorted_parties:
            vote_pct = party_percentages.get(party, 0)
            seat_pct = (seat_count / total_seats) * 100 if total_seats > 0 else 0
            
            status = "✅ Qualified" if seat_count > 0 else ("❌ Below threshold" if vote_pct > 0 else "❌ No votes")
            
            results_data.append({
                'Party': party,
                'Vote %': f"{vote_pct:.1f}%",
                'Seats': seat_count,
                'Seat %': f"{seat_pct:.1f}%",
                'Status': status
            })
        
        df = pd.DataFrame(results_data)
        st.dataframe(df, use_container_width=True)
        
        # Summary statistics
        allocated_seats = sum(seats.values())
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Seats", total_seats)
        with col2:
            st.metric("Allocated Seats", allocated_seats)
        with col3:
            st.metric("Electoral Threshold", f"{self.threshold*100}%")
        
        if allocated_seats != total_seats:
            st.error(f"⚠️ Warning: {total_seats - allocated_seats} seats unallocated!")
    
    def plot_results(self, party_percentages: Dict[str, float], seats: Dict[str, int]):
        """Create visualization of the election results."""
        # Filter out parties with no seats
        parties_with_seats = {k: v for k, v in seats.items() if v > 0}
        
        if not parties_with_seats:
            st.warning("No parties won seats - cannot create visualization")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Pie chart of seat distribution
        parties = list(parties_with_seats.keys())
        seat_counts = list(parties_with_seats.values())
        
        colors = plt.cm.Set3(range(len(parties)))
        
        ax1.pie(seat_counts, labels=parties, autopct='%1.1f%%', colors=colors)
        ax1.set_title('Seat Distribution')
        
        # Bar chart comparing vote % vs seat %
        total_seats = sum(seats.values())
        vote_pcts = [party_percentages.get(party, 0) for party in parties]
        seat_pcts = [(seats[party] / total_seats) * 100 for party in parties]
        
        x = range(len(parties))
        width = 0.35
        
        ax2.bar([i - width/2 for i in x], vote_pcts, width, label='Vote %', alpha=0.8)
        ax2.bar([i + width/2 for i in x], seat_pcts, width, label='Seat %', alpha=0.8)
        
        ax2.set_xlabel('Parties')
        ax2.set_ylabel('Percentage')
        ax2.set_title('Vote % vs Seat %')
        ax2.set_xticks(x)
        ax2.set_xticklabels(parties, rotation=45)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)  # Important: close figure to prevent memory leaks


def streamlit_app():
    """Main Streamlit application."""
    st.set_page_config(page_title="Norwegian Election Simulator", page_icon="🗳️", layout="wide")
    
    st.title("🗳️ Norwegian Parliament Seat Allocation Simulator")
    st.markdown("Using the **Modified Sainte-Laguë Method** with 4% electoral threshold")
    st.markdown("---")
    
    simulator = NorwayElectionSimulator()
    
    # Sidebar for configuration
    st.sidebar.header("Election Configuration")
    
    # Choose between preset and custom
    mode = st.sidebar.radio(
        "Choose simulation mode:",
        ["Use preset Norwegian parties", "Custom parties"]
    )
    
    total_seats = st.sidebar.slider("Total seats in district:", min_value=3, max_value=25, value=10)
    
    if mode == "Use preset Norwegian parties":
        st.sidebar.subheader("Adjust vote percentages:")
        
        # Default Norwegian parties with recent polling data
        default_parties = {
            'Arbeiderpartiet (Ap)': 26.2,
            'Høyre (H)': 20.4,
            'Senterpartiet (Sp)': 13.5,
            'Fremskrittspartiet (FrP)': 11.6,
            'Sosialistisk Venstreparti (SV)': 7.6,
            'Rødt (R)': 4.7,
            'Venstre (V)': 4.6,
            'Kristelig Folkeparti (KrF)': 3.8,
            'Miljøpartiet De Grønne (MDG)': 3.9,
        }
        
        party_percentages = {}
        for party, default_pct in default_parties.items():
            party_percentages[party] = st.sidebar.slider(
                party, 
                min_value=0.0, 
                max_value=50.0, 
                value=default_pct, 
                step=0.1,
                key=f"preset_{party}"
            )
    
    else:  # Custom parties
        st.sidebar.subheader("Add custom parties:")
        
        # Initialize session state for parties
        if 'custom_parties' not in st.session_state:
            st.session_state.custom_parties = {'Party A': 25.0, 'Party B': 20.0, 'Party C': 15.0}
        
        party_percentages = {}
        
        # Display existing parties
        parties_to_remove = []
        for i, (party, pct) in enumerate(st.session_state.custom_parties.items()):
            col1, col2, col3 = st.sidebar.columns([3, 2, 1])
            
            with col1:
                new_name = st.text_input("Party name:", value=party, key=f"name_{i}")
            with col2:
                new_pct = st.number_input("Vote %:", value=pct, min_value=0.0, max_value=100.0, step=0.1, key=f"pct_{i}")
            with col3:
                if st.button("❌", key=f"remove_{i}", help="Remove party"):
                    parties_to_remove.append(party)
            
            if new_name and new_name not in parties_to_remove:
                party_percentages[new_name] = new_pct
        
        # Remove parties marked for removal
        for party in parties_to_remove:
            del st.session_state.custom_parties[party]
        
        # Update session state
        st.session_state.custom_parties = party_percentages.copy()
        
        # Add new party button
        if st.sidebar.button("➕ Add Party"):
            party_count = len(st.session_state.custom_parties) + 1
            st.session_state.custom_parties[f"New Party {party_count}"] = 5.0
            st.experimental_rerun()
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Input Summary")
        
        # Validate percentages
        total_percentage = sum(party_percentages.values())
        
        if abs(total_percentage - 100.0) > 0.1:
            st.warning(f"⚠️ Vote percentages sum to {total_percentage:.1f}% (should be close to 100%)")
        else:
            st.success("✅ Vote percentages sum to 100%")
        
        # Show input data
        input_df = pd.DataFrame([
            {"Party": party, "Vote %": f"{pct:.1f}%"} 
            for party, pct in party_percentages.items()
        ])
        st.dataframe(input_df, use_container_width=True)
    
    with col2:
        st.subheader("Algorithm Info")
        st.info("""
        **Modified Sainte-Laguë Method:**
        - Divisors: 1.4, 3, 5, 7, 9, 11, ...
        - 4% electoral threshold
        - Used in Norwegian parliamentary elections
        - Slightly favors larger parties vs. standard Sainte-Laguë
        """)
    
    # Run simulation
    if st.button("🚀 Run Simulation", type="primary", use_container_width=True):
        if not party_percentages:
            st.error("Please add at least one party!")
        else:
            with st.spinner("Calculating seat allocation..."):
                results = simulator.simulate_from_percentages(party_percentages, total_seats)
                
                # Display results
                simulator.print_results(party_percentages, results, total_seats)
                
                # Show visualization
                st.subheader("Visualization")
                simulator.plot_results(party_percentages, results)
                
                # Show detailed allocation process
                with st.expander("🔍 Show detailed allocation process"):
                    st.markdown("**Step-by-step seat allocation:**")
                    
                    # Recreate allocation process for display
                    qualified_parties = {
                        party: party_percentages[party] 
                        for party, pct in party_percentages.items() 
                        if pct >= simulator.threshold * 100
                    }
                    
                    seats_progress = {party: 0 for party in qualified_parties.keys()}
                    allocation_steps = []
                    
                    for seat_num in range(1, total_seats + 1):
                        quotients = {}
                        for party in qualified_parties.keys():
                            current_seats = seats_progress[party]
                            if current_seats == 0:
                                divisor = 1.4
                            else:
                                divisor = 2 * current_seats + 1
                            
                            quotients[party] = qualified_parties[party] / divisor
                        
                        if quotients:
                            winner = max(quotients, key=quotients.get)
                            seats_progress[winner] += 1
                            
                            allocation_steps.append({
                                'Seat': seat_num,
                                'Winner': winner,
                                'Quotient': f"{quotients[winner]:.2f}",
                                'New Total': seats_progress[winner]
                            })
                    
                    if allocation_steps:
                        step_df = pd.DataFrame(allocation_steps)
                        st.dataframe(step_df, use_container_width=True)


# Example usage for standalone running
if __name__ == "__main__":
    # Check if running in Streamlit
    try:
        st.set_page_config(page_title="Test")
        streamlit_app()
    except:
        # Fallback to console version
        print("NORWEGIAN PARLIAMENT SEAT ALLOCATION SIMULATOR")
        print("Using the Modified Sainte-Laguë Method")
        print("="*60)
        run_simulation()
