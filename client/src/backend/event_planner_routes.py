"""
Event Planner Routes
Add to your existing app.py with:
    from event_planner_routes import event_planner_bp
    app.register_blueprint(event_planner_bp)
"""

from flask import Blueprint, request, jsonify
from datetime import date, datetime, timedelta
from typing import List, Dict, Any
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from planner.core.optimized_greedy import make_day_plan, PlannerConfig
    from planner.core.models import Client, Activity, Location
    from planner.core.utils import load_events
    PLANNER_AVAILABLE = True
except ImportError as e:
    print(f"[Event Planner] Warning: Could not import planner modules: {e}")
    PLANNER_AVAILABLE = False

# Create Blueprint
event_planner_bp = Blueprint('event_planner', __name__)


def convert_preferences_to_client(preferences: Dict[str, Any]) -> Client:
    trip_start = datetime.strptime(preferences['trip_start'], '%Y-%m-%d').date()
    trip_end = datetime.strptime(preferences['trip_end'], '%Y-%m-%d').date()
    
    home_base = Location(
        lat=preferences['home_base']['lat'],
        lng=preferences['home_base']['lng'],
        city=preferences['destination_city']
    )
    
    client = Client(
        id=f"client_{preferences.get('party_type', 'user')}_{trip_start.isoformat()}",
        party_type=preferences['party_type'],
        party_members=preferences['party_members'],
        religion=preferences.get('religion'),
        ethnicity_culture=preferences.get('ethnicity_culture', []),
        vibe=preferences['vibe'],
        budget_total=float(preferences['budget_total']),
        trip_start=trip_start,
        trip_end=trip_end,
        home_base=home_base,
        avoid_long_transit=preferences['avoid_long_transit'],
        prefer_outdoor=preferences['prefer_outdoor'],
        prefer_cultural=preferences['prefer_cultural'],
        day_start_time=preferences['start_time'],
        day_end_time=preferences['end_time']
    )
    
    # Set attributes not in __init__
    client.dietary = preferences.get('dietary', {})
    client.meal_prefs = preferences.get('meal_prefs', {})
    
    return client


def format_plan_for_frontend(plan_days: List) -> List[Dict[str, Any]]:
    """Convert PlanDay objects to JSON"""
    formatted_schedule = []
    
    for plan in plan_days:
        activities = []
        
        for event in plan.events:
            activity = {
                'id': event.activity.id,
                'name': event.activity.name,
                'category': event.activity.category,
                'start_time': event.start_dt.strftime('%H:%M'),
                'end_time': event.end_dt.strftime('%H:%M'),
                'duration_min': event.activity.duration_min,
                'cost_cad': float(event.activity.cost_cad),
                'location': {
                    'lat': event.activity.location.lat,
                    'lng': event.activity.location.lng
                },
                'venue': event.activity.venue,
                'tags': event.activity.tags or [],
                'weather_note': None
            }
            activities.append(activity)
        
        day_plan = {
            'date': plan.day.isoformat(),
            'day_of_week': plan.day.strftime('%A'),
            'activities': activities,
            'total_cost': sum(a['cost_cad'] for a in activities),
            'total_duration': sum(a['duration_min'] for a in activities)
        }
        
        formatted_schedule.append(day_plan)
    
    return formatted_schedule


@event_planner_bp.route('/event_planner/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'Event Planner is available',
        'planner_loaded': PLANNER_AVAILABLE
    })


@event_planner_bp.route('/event_planner/generate', methods=['POST'])
def generate_schedule():
    """
    Generate a schedule from user preferences
    
    POST /event_planner/generate
    Body: { party_type, party_members, vibe, budget_total, trip_start, trip_end, ... }
    
    Returns: { success: true, schedule: [...], metadata: {...} }
    """
    if not PLANNER_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Planner module not available. Check imports.'
        }), 500
    
    try:
        preferences = request.get_json(force=True) or {}
        
        if not preferences:
            return jsonify({
                'success': False,
                'error': 'No preferences provided'
            }), 400
        
        print(f"[Event Planner] Generating schedule for {preferences.get('destination_city', 'Unknown')}")
        
        # Convert to Client object
        client = convert_preferences_to_client(preferences)
        
        # Load available activities
        try:
            activities = load_events()
        except Exception as e:
            print(f"[Event Planner] Error loading events: {e}")
            activities = []
        
        # Filter by city
        city = preferences['destination_city']
        city_activities = [
            a for a in activities 
            if getattr(a, 'city', '') == city
        ]
        
        print(f"[Event Planner] Found {len(city_activities)} activities in {city}")
        
        # Generate schedule
        plan_days = []
        current_day = client.trip_start
        
        config = PlannerConfig(
            use_hard_constraints=True,
            use_weather=True,
            use_budget=True,
            use_meals=True,
            use_base_plan=True,
            use_repairB=True,
            debug_print=False
        )
        
        while current_day <= client.trip_end:
            print(f"[Event Planner] Planning {current_day}")
            day_plan = make_day_plan(
                client=client,
                activities=city_activities,
                day=current_day,
                config=config
            )
            plan_days.append(day_plan)
            current_day += timedelta(days=1)
        
        formatted_schedule = format_plan_for_frontend(plan_days)
        
        total_cost = sum(day['total_cost'] for day in formatted_schedule)
        total_activities = sum(len(day['activities']) for day in formatted_schedule)
        
        print(f"[Event Planner] Generated {len(formatted_schedule)} days, {total_activities} activities, ${total_cost:.2f}")
        
        return jsonify({
            'success': True,
            'schedule': formatted_schedule,
            'metadata': {
                'total_days': len(formatted_schedule),
                'total_activities': total_activities,
                'total_cost': total_cost,
                'budget_remaining': float(preferences['budget_total']) - total_cost,
                'generated_at': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        print(f"[Event Planner] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to generate schedule'
        }), 500


@event_planner_bp.route('/event_planner/activities/<city>', methods=['GET'])
def get_activities_by_city(city: str):
    """Get available activities for a city"""
    if not PLANNER_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Planner module not available'
        }), 500
    
    try:
        activities = load_events()
        city_activities = [
            {
                'id': a.id,
                'name': a.name,
                'category': a.category,
                'tags': a.tags,
                'cost_cad': float(a.cost_cad),
                'duration_min': a.duration_min
            }
            for a in activities 
            if getattr(a, 'city', '') == city
        ]
        
        return jsonify({
            'success': True,
            'city': city,
            'count': len(city_activities),
            'activities': city_activities
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500