"""
District Telemedicine Operational Capacity Simulation Service
Models rural telemedicine network throughput, ophthalmologist triage workload, and queue backlogs.
"""
from ...models.schemas import DistrictSimulationInput, DistrictSimulationResult

class SimulationService:
    def run_district_simulation(self, params: DistrictSimulationInput) -> DistrictSimulationResult:
        # Working hours per day: 7.5 hours standard primary health center shift
        shift_minutes = 7.5 * 60.0
        
        # Camera screening capacity: ~12 minutes per patient capture
        minutes_per_patient_capture = 12.0
        daily_capacity_per_camera = int(shift_minutes / minutes_per_patient_capture)  # ~37 patients
        total_cameras = params.screening_centers_count * params.cameras_per_center
        total_field_daily_capacity = total_cameras * daily_capacity_per_camera
        
        # Target daily intake required to screen target population
        daily_target_need = params.annual_target_population / params.working_days_per_year
        actual_daily_screened = min(total_field_daily_capacity, int(daily_target_need * 1.15))
        annual_capacity = actual_daily_screened * params.working_days_per_year
        
        # AI Server processing capacity (assuming automated queue batch)
        # AI works in parallel/asynchronous background
        ai_seconds_needed_per_day = actual_daily_screened * params.ai_processing_time_seconds
        ai_available_seconds = 8 * 3600  # 8 hour server window
        ai_utilization = min(100.0, round((ai_seconds_needed_per_day / ai_available_seconds) * 100, 1))
        
        # Doctor Review workload: Only referable / borderline triage cases
        cases_to_review_per_day = actual_daily_screened * params.referral_triage_rate
        # Ophthalmologist review time: assume 4 hours dedicated telemedicine reading slot per day
        doc_reading_minutes_per_day = 4.0 * 60.0 * params.ophthalmologists_count
        reviews_possible_per_day = doc_reading_minutes_per_day / max(params.doctor_review_time_minutes, 0.5)
        
        doctor_utilization = round((cases_to_review_per_day / max(reviews_possible_per_day, 1)) * 100, 1)
        
        # Queue backlog and turnaround estimation
        if cases_to_review_per_day > reviews_possible_per_day:
            excess_per_day = cases_to_review_per_day - reviews_possible_per_day
            avg_queue = int(excess_per_day * 5)  # 1-week backlog
            turnaround_hours = round(24.0 + (excess_per_day / reviews_possible_per_day) * 48.0, 1)
            bottleneck = "Ophthalmologist Review"
        elif total_field_daily_capacity < daily_target_need:
            avg_queue = int(cases_to_review_per_day * 0.4)
            turnaround_hours = 4.2
            bottleneck = "Field Cameras"
        elif params.telemedicine_bandwidth_mbps < 2.0:
            avg_queue = int(cases_to_review_per_day * 0.8)
            turnaround_hours = 12.0
            bottleneck = "Bandwidth"
        else:
            avg_queue = max(2, int(cases_to_review_per_day * 0.15))
            turnaround_hours = 2.5
            bottleneck = "None"
            
        coverage = min(100.0, round((annual_capacity / max(params.annual_target_population, 1)) * 100, 1))
        
        recs = []
        if doctor_utilization > 85.0:
            recs.append(f"Ophthalmologist reading capacity is at {doctor_utilization}%. Consider adding 1 tele-retina reader or tightening AI specificity threshold.")
        if coverage < 80.0:
            recs.append(f"District population coverage is {coverage}%. Deploying {max(1, int((params.annual_target_population - annual_capacity)/(daily_capacity_per_camera*params.working_days_per_year)))} additional mobile screening cameras will achieve >90% coverage.")
        if params.telemedicine_bandwidth_mbps < 5.0:
            recs.append("Low bandwidth may delay image sync to district server. Enable local edge preprocessing and JPEG-XL progressive compression.")
        if not recs:
            recs.append("Operational balance is optimal. Network can achieve target annual diabetic population coverage without backlog.")

        return DistrictSimulationResult(
            daily_screening_capacity=actual_daily_screened,
            annual_screening_capacity=annual_capacity,
            ai_utilization_percent=ai_utilization,
            ophthalmologist_utilization_percent=doctor_utilization,
            average_review_queue_size=avg_queue,
            estimated_turnaround_hours=turnaround_hours,
            screening_coverage_percent=coverage,
            bottleneck=bottleneck,
            recommendations=recs
        )

simulation_service = SimulationService()
