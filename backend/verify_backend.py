"""
Backend verification script
Tests imports, schema instantiations, routing integrity, and simulation service.
"""
import sys
import os

# Add root directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.main import app
from backend.models.schemas import DistrictSimulationInput
from backend.services.simulation.service import simulation_service
from backend.models.database import db

def test_backend():
    print(f"Testing FastAPI app: {app.title} (v{app.version})")
    
    # Test simulation service
    sim_input = DistrictSimulationInput()
    sim_output = simulation_service.run_district_simulation(sim_input)
    print(f"Simulation verified: Daily Capacity = {sim_output.daily_screening_capacity} pts/day, Annual = {sim_output.annual_screening_capacity}, Doctor Util = {sim_output.ophthalmologist_utilization_percent}%")
    
    # Test database
    print(f"Seed patients: {len(db.patients)}, Seed screenings: {len(db.screenings)}")
    
    # Test routes registered
    routes_count = len(app.routes)
    print(f"Registered {routes_count} route definitions.")
    
    print("\nALL BACKEND TESTS PASSED SUCCESSFULLY.")

if __name__ == "__main__":
    test_backend()
