import pytest
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch
import pandas as pd
from .optimized_greedy import *
from .optimized_greedy import _days_in_trip
from .optimized_greedy import _soft_cap_per_day
from .optimized_greedy import _spent_today
from .optimized_greedy import _net_score_with_budget
from .optimized_greedy import _to_minutes
from .optimized_greedy import _from_minutes
from .optimized_greedy import _time_to_minutes
from .optimized_greedy import _has_fixed_times
from .optimized_greedy import _normalize_time_str
from .optimized_greedy import _parse_one_time
from .optimized_greedy import _fixed_dt_candidates
from .optimized_greedy import _dist_m
from .optimized_greedy import _travel_buffer_min
from .optimized_greedy import _window_midpoint
from .optimized_greedy import _meal_window
from .optimized_greedy import _meal_cuisines
from .optimized_greedy import _derive_diet_terms
from .optimized_greedy import _blocking_events
from .optimized_greedy import _overlap_minutes
from .optimized_greedy import _try_nudge_forward
from .optimized_greedy import _flexibility_now
from .optimized_greedy import _hard_feasible_for_anchor
from .optimized_greedy import _resolve_meal_conflict


class TestOptimizedGreedy:
    """Tests for optimized_greedy.py travel planner algorithm"""
    
    def test_days_in_trip_single_day(self):
        """Should return 1 for same-day start and end"""
        
        
        client = Mock()
        client.trip_start = date(2025, 1, 1)
        client.trip_end = date(2025, 1, 1)
        assert _days_in_trip(client) == 1
    
    def test_days_in_trip_multiple_days(self):
        """Should calculate inclusive days correctly"""
        
        
        client = Mock()
        client.trip_start = date(2025, 1, 1)
        client.trip_end = date(2025, 1, 5)
        assert _days_in_trip(client) == 5
    
    def test_soft_cap_divides_budget_by_days(self):
        """Should divide total budget evenly across trip days"""
        
        
        client = Mock()
        client.budget_total = 1000.0
        client.trip_start = date(2025, 1, 1)
        client.trip_end = date(2025, 1, 5)
        
        assert _soft_cap_per_day(client) == 200.0
    
    def test_spent_today_sums_costs(self):
        """Should sum all event costs in the plan"""
        ev1 = Mock()
        ev1.activity = Mock()
        ev1.activity.cost_cad = 25.0
        
        ev2 = Mock()
        ev2.activity = Mock()
        ev2.activity.cost_cad = 50.0
        
        plan = Mock()
        plan.events = [ev1, ev2]
        
        assert _spent_today(plan) == 75.0
    
    @patch('planner.core.optimized_greedy.base_value')
    def test_net_score_no_penalty_under_budget(self, mock_base_value):
        """Should return full base value when under budget"""
        
        
        mock_base_value.return_value = 8.0
        
        client = Mock()
        activity = Mock()
        activity.cost_cad = 25.0
        
        plan = Mock()
        plan.events = []
        
        score = _net_score_with_budget(client, activity, plan, 100.0, already_added=False)
        assert score == 8.0
    
    @patch('planner.core.optimized_greedy.base_value')
    def test_net_score_applies_penalty_over_budget(self, mock_base_value):
        """Should apply LAMBDA_BUDGET penalty when over budget"""
        mock_base_value.return_value = 5.0
        
        client = Mock()
        activity = Mock()
        activity.cost_cad = 50.0
        
        event = Mock()
        event.activity = Mock()
        event.activity.cost_cad = 75.0
        plan = Mock()
        plan.events = [event]
        
        score = _net_score_with_budget(client, activity, plan, 100.0, already_added=False)
        assert score == pytest.approx(4.25)
    
    def test_to_minutes_converts_time_string(self):
        """Should convert HH:MM to minutes from midnight"""
        assert _to_minutes("00:00") == 0
        assert _to_minutes("09:30") == 570
        assert _to_minutes("14:45") == 885
        assert _to_minutes("23:59") == 1439
    
    def test_from_minutes_creates_datetime(self):
        """Should create datetime from minutes and date"""
        
        day = date(2025, 1, 15)
        
        assert _from_minutes(day, 0) == datetime(2025, 1, 15, 0, 0)
        assert _from_minutes(day, 570) == datetime(2025, 1, 15, 9, 30)
        assert _from_minutes(day, 1439) == datetime(2025, 1, 15, 23, 59)
    
    def test_time_to_minutes_from_datetime(self):
        """Should extract minutes from datetime object"""
           
        assert _time_to_minutes(datetime(2025, 1, 1, 0, 0)) == 0
        assert _time_to_minutes(datetime(2025, 1, 1, 14, 30)) == 870
        assert _time_to_minutes(datetime(2025, 1, 1, 23, 59)) == 1439
    
    def test_overlaps_returns_false_for_adjacent_times(self):
        """Should not overlap when one ends exactly when other starts"""
        result = overlaps(
            datetime(2025, 1, 1, 10, 0),
            datetime(2025, 1, 1, 11, 0),
            datetime(2025, 1, 1, 11, 0),
            datetime(2025, 1, 1, 12, 0)
        )
        assert result is False
    
    def test_overlaps_detects_partial_overlap(self):
        """Should detect when events partially overlap"""
        result = overlaps(
            datetime(2025, 1, 1, 10, 0),
            datetime(2025, 1, 1, 11, 30),
            datetime(2025, 1, 1, 11, 0),
            datetime(2025, 1, 1, 12, 0)
        )
        assert result is True
    
    def test_overlaps_detects_containment(self):
        """Should detect when one event completely contains another"""
        result = overlaps(
            datetime(2025, 1, 1, 10, 0),
            datetime(2025, 1, 1, 14, 0),
            datetime(2025, 1, 1, 11, 0),
            datetime(2025, 1, 1, 12, 0)
        )
        assert result is True
    
    def test_fits_no_overlap_empty_schedule(self):
        """Should fit when schedule is empty"""
          
        activity = Mock()
        activity.duration_min = 60
        
        start_dt = datetime(2025, 1, 1, 10, 0)
        events = []
        
        assert fits_no_overlap(events, start_dt, activity) is True
    
    def test_fits_no_overlap_detects_conflict(self):
        """Should not fit when event would overlap existing event"""
          
        activity = Mock()
        activity.duration_min = 90
        
        event1 = Mock()
        event1.start_dt = datetime(2025, 1, 1, 10, 0)
        event1.end_dt = datetime(2025, 1, 1, 11, 30)
        
        start_dt = datetime(2025, 1, 1, 10, 30)
        
        assert fits_no_overlap([event1], start_dt, activity) is False
    
    def test_fits_in_window_within_bounds(self):
        """Should fit when event is completely within client window"""
         
        activity = Mock()
        activity.duration_min = 90
        
        client = Mock()
        client.day_start_min = 540
        client.day_end_min = 1260
        
        start_min = 600
        
        assert fits_in_window(activity, client, start_min) is True
    
    def test_fits_in_window_starts_too_early(self):
        """Should not fit when event starts before client window"""
         
        activity = Mock()
        activity.duration_min = 60
        
        client = Mock()
        client.day_start_min = 540
        client.day_end_min = 1260
        
        start_min = 480
        
        assert fits_in_window(activity, client, start_min) is False
    
    def test_fits_in_window_ends_too_late(self):
        """Should not fit when event ends after client window"""
         
        activity = Mock()
        activity.duration_min = 120
        
        client = Mock()
        client.day_start_min = 540
        client.day_end_min = 1260
        
        start_min = 1200
        
        assert fits_in_window(activity, client, start_min) is False
    
    def test_has_fixed_times_empty_list(self):
        """Should return False for empty list"""
           
        activity = Mock()
        activity.fixed_times = []
        assert _has_fixed_times(activity) is False
    
    def test_has_fixed_times_with_times(self):
        """Should return True when fixed times present"""
           
        activity = Mock()
        activity.fixed_times = ["17:00"]
        assert _has_fixed_times(activity) is True
    
    def test_normalize_time_str_unicode_dashes(self):
        """Should normalize unicode dashes to regular hyphen"""
              
        assert _normalize_time_str("09:00–11:00") == "09:00-11:00"
        assert _normalize_time_str("09:00—11:00") == "09:00-11:00"
    
    def test_normalize_time_str_whitespace(self):
        """Should strip leading and trailing whitespace"""
              
        assert _normalize_time_str("  09:00  ") == "09:00"
    
    def test_parse_one_time_24h_format(self):
        """Should parse 24-hour time format"""
          
        day = date(2025, 1, 1)
        assert _parse_one_time("14:30", day) == datetime(2025, 1, 1, 14, 30)
    
    def test_parse_one_time_12h_am(self):
        """Should parse 12-hour AM format"""
          
        day = date(2025, 1, 1)
        assert _parse_one_time("9:30 AM", day) == datetime(2025, 1, 1, 9, 30)
    
    def test_parse_one_time_12h_pm(self):
        """Should parse 12-hour PM format"""
          
        day = date(2025, 1, 1)
        assert _parse_one_time("2:30 PM", day) == datetime(2025, 1, 1, 14, 30)
    
    def test_parse_one_time_invalid(self):
        """Should return None for invalid time string"""
          
        day = date(2025, 1, 1)
        assert _parse_one_time("invalid", day) is None
    
    def test_fixed_dt_candidates_simple_string(self):
        """Should parse simple time string to datetime"""
               
        activity = Mock()
        activity.fixed_times = ["17:00"]
        day = date(2025, 8, 3)
        
        candidates = _fixed_dt_candidates(activity, day)
        
        assert len(candidates) == 1
        assert candidates[0] == datetime(2025, 8, 3, 17, 0)
    
    def test_fixed_dt_candidates_dict_format(self):
        """Should parse dict with date and start time"""
               
        activity = Mock()
        activity.fixed_times = [{"date": "2025-08-03", "start": "19:30"}]
        day = date(2025, 8, 3)
        
        candidates = _fixed_dt_candidates(activity, day)
        
        assert len(candidates) == 1
        assert candidates[0] == datetime(2025, 8, 3, 19, 30)
    
    def test_fixed_dt_candidates_wrong_date(self):
        """Should skip times for non-matching dates"""
               
        activity = Mock()
        activity.fixed_times = [{"date": "2025-08-05", "start": "19:30"}]
        day = date(2025, 8, 3)
        
        candidates = _fixed_dt_candidates(activity, day)
        
        assert len(candidates) == 0
    
    def test_dist_m_same_location(self):
        """Should return near-zero distance for same coordinates"""
        dist = _dist_m(43.653, -79.383, 43.653, -79.383)
        assert dist < 1.0
    
    def test_dist_m_different_locations(self):
        """Should calculate positive distance between different points"""
        dist = _dist_m(43.65, -79.38, 43.66, -79.39)
        assert dist > 0
    
    def test_travel_buffer_min_bounds(self):
        """Should return travel buffer between 5 and 35 minutes"""
             
        act_a = Mock()
        act_a.location = Mock()
        act_a.location.lat = 43.65
        act_a.location.lng = -79.38
        
        act_b = Mock()
        act_b.location = Mock()
        act_b.location.lat = 43.66
        act_b.location.lng = -79.39
        
        buffer = _travel_buffer_min(act_a, act_b)
        assert 5 <= buffer <= 35
    
    def test_window_midpoint_centers_meal(self):
        """Should calculate midpoint of meal window with buffers"""
           
        mid = _window_midpoint("12:00", "14:00", duration_min=60, buffer_min=10)
        assert mid == 750
    
    def test_meal_window_extraction(self):
        """Should extract meal time window from client preferences"""
        client = Mock()
        client.meal_prefs = {
            "breakfast": {"window": ["08:00", "10:00"]}
        }
        
        start, end = _meal_window(client, "breakfast")
        assert start == "08:00"
        assert end == "10:00"
    
    def test_meal_cuisines_extraction(self):
        """Should extract cuisine preferences for meal"""
         
        client = Mock()
        client.meal_prefs = {
            "dinner": {"cuisines": ["italian", "indian", "chinese"]}
        }
        
        cuisines = _meal_cuisines(client, "dinner")
        assert cuisines == ["italian", "indian", "chinese"]
    
    def test_derive_diet_terms_halal(self):
        """Should add halal to required terms when True"""
             
        diet = {
            "halal": True,
            "vegetarian": False,
            "avoid": [],
            "required_terms": []
        }
        
        required, avoid = _derive_diet_terms(diet)
        assert "halal" in required
    
    def test_derive_diet_terms_nut_allergy(self):
        """Should add nut terms to avoid list for allergy"""
             
        diet = {
            "nut_allergy": True,
            "avoid": [],
            "required_terms": []
        }
        
        required, avoid = _derive_diet_terms(diet)
        assert "peanut" in avoid
        assert any("nut" in term for term in avoid)
    
    def test_blocking_events_finds_overlaps(self):
        """Should find events that overlap proposed time slot"""
           
        ev1 = Mock()
        ev1.start_dt = datetime(2025, 1, 1, 10, 0)
        ev1.end_dt = datetime(2025, 1, 1, 11, 0)
        
        ev2 = Mock()
        ev2.start_dt = datetime(2025, 1, 1, 15, 0)
        ev2.end_dt = datetime(2025, 1, 1, 16, 0)
        
        activity = Mock()
        activity.duration_min = 120
        
        blockers = _blocking_events([ev1, ev2], datetime(2025, 1, 1, 10, 0), activity)
        
        assert len(blockers) == 1
        assert ev1 in blockers
    
    def test_overlap_minutes_calculation(self):
        """Should calculate minutes of overlap between event and slot"""
           
        start_dt = datetime(2025, 1, 1, 10, 0)
        
        activity = Mock()
        activity.duration_min = 90
        
        event = Mock()
        event.start_dt = datetime(2025, 1, 1, 11, 0)
        event.end_dt = datetime(2025, 1, 1, 12, 0)
        
        overlap = _overlap_minutes(start_dt, activity, event)
        assert overlap == 30
    
    def test_try_nudge_forward_refuses_anchors(self):
        """Should not move events with fixed times"""
             
        anchor_ev = Mock()
        anchor_ev.activity = Mock()
        anchor_ev.activity.fixed_times = ["17:00"]
        
        result = _try_nudge_forward(
            Mock(), Mock(), anchor_ev, date(2025, 1, 1), 
            Mock(), datetime.now(), max_moves=5
        )
        
        assert result is False
    
    def test_flexibility_now_anchors_zero(self):
        """Should return zero flexibility for fixed-time events"""
           
        anchor_ev = Mock()
        anchor_ev.activity = Mock()
        anchor_ev.activity.fixed_times = ["17:00"]
        
        flex = _flexibility_now(Mock(), Mock(), anchor_ev, date(2025, 1, 1))
        assert flex == 0
    
    @patch('planner.core.optimized_greedy.hc_age_ok')
    def test_hard_feasible_for_anchor_fails_age(self, mock_age_ok):
        """Should fail when party member outside age bounds"""
        
        mock_age_ok.return_value = False
        
        client = Mock()
        activity = Mock()
        activity.weather_blockers = []
        start_dt = datetime(2025, 1, 1, 10, 0)
        
        with patch('planner.core.optimized_greedy.is_weather_suitable', return_value=True):
            result = _hard_feasible_for_anchor(client, activity, start_dt)
            assert result is False
    
    def test_weather_suitable_no_blockers(self):
        """Should always be suitable when no weather blockers"""
              
        activity = Mock()
        activity.weather_blockers = []
        activity.city = "Toronto"
        activity.duration_min = 90
        
        start_dt = datetime(2025, 1, 1, 10, 0)
        
        assert is_weather_suitable(activity, start_dt) is True
    
    @patch('planner.core.optimized_greedy._fetch_hourly_once')
    @patch('planner.core.optimized_greedy._TZ_CACHE', {"Toronto": "America/Toronto"})
    def test_weather_suitable_blocks_bad_weather(self, mock_fetch):
        """Should block activity when weather matches blocker"""
              
        times = pd.to_datetime(['2025-01-01 10:00', '2025-01-01 11:00'])
        codes = [65, 65]
        mock_fetch.return_value = (times, codes)
        
        activity = Mock()
        activity.weather_blockers = ["Heavy rain"]
        activity.city = "Toronto"
        activity.duration_min = 60
        activity.location = Mock()
        activity.location.lat = 43.65
        activity.location.lng = -79.38
        
        start_dt = datetime(2025, 1, 1, 10, 0)
        
        result = is_weather_suitable(activity, start_dt)
        assert result is False
    
    @patch('planner.core.optimized_greedy._fetch_hourly_once')
    @patch('planner.core.optimized_greedy._TZ_CACHE', {"Toronto": "America/Toronto"})
    def test_weather_suitable_allows_good_weather(self, mock_fetch):
        """Should allow activity when weather is clear"""
              
        times = pd.to_datetime(['2025-01-01 10:00', '2025-01-01 11:00'])
        codes = [0, 0]
        mock_fetch.return_value = (times, codes)
        
        activity = Mock()
        activity.weather_blockers = ["Heavy rain"]
        activity.city = "Toronto"
        activity.duration_min = 60
        activity.location = Mock()
        activity.location.lat = 43.65
        activity.location.lng = -79.38
        
        start_dt = datetime(2025, 1, 1, 10, 0)
        
        result = is_weather_suitable(activity, start_dt)
        assert result is True
      
    @patch('planner.core.optimized_greedy.fits_no_overlap')
    @patch('planner.core.optimized_greedy._travel_buffer_min')
    def test_resolve_meal_conflict_after_anchor(self, mock_buffer, mock_fits):
        """Should try after anchor if before doesn't work"""
        
        
        mock_buffer.return_value = 10
        mock_fits.side_effect = [False, True]
        
        meal_ev = Mock()
        meal_ev.activity = Mock()
        meal_ev.activity.duration_min = 60
        meal_ev.activity.tags = []
        meal_ev.activity.location = Mock()
        meal_ev.start_dt = datetime(2025, 1, 1, 17, 30)
        meal_ev.end_dt = datetime(2025, 1, 1, 18, 30)
        
        anchor_ev = Mock()
        anchor_ev.activity = Mock()
        anchor_ev.activity.location = Mock()
        anchor_ev.activity.duration_min = 120
        anchor_ev.start_dt = datetime(2025, 1, 1, 18, 0)
        anchor_ev.end_dt = datetime(2025, 1, 1, 20, 0)
        
        plan = Mock()
        plan.events = []
        
        result = _resolve_meal_conflict(plan, Mock(), meal_ev, anchor_ev)
        
        assert result is True
        assert "note:eat after event" in meal_ev.activity.tags
    
    @patch('planner.core.optimized_greedy._blocking_events')
    @patch('planner.core.optimized_greedy._overlap_minutes')
    @patch('planner.core.optimized_greedy._try_nudge_forward')
    def test_repairB_tries_max_overlap_first(self, mock_nudge, mock_overlap, mock_blocking):
        """Should try nudging event with maximum overlap first"""
        ev1 = Mock()
        ev1.activity = Mock()
        ev1.activity.fixed_times = []
        
        ev2 = Mock()
        ev2.activity = Mock()
        ev2.activity.fixed_times = []
        
        mock_blocking.return_value = [ev1, ev2]
        mock_overlap.side_effect = lambda start_dt, act, ev: 60 if ev is ev1 else 30
        mock_nudge.return_value = True
        
        plan = Mock()
        plan.events = [ev1, ev2]
        plan.add = Mock()
        
        result = repairB(plan, Mock(), Mock(), date(2025, 1, 1), 
                        datetime.now(), max_moves=1, try_others=False)
        
        assert mock_nudge.call_count >= 1
        first_call_event = mock_nudge.call_args_list[0][0][2]
        assert first_call_event is ev1
    
    def test_lambda_budget_constant(self):
        """Should have correct LAMBDA_BUDGET value"""
        assert LAMBDA_BUDGET == 0.03
    
    def test_score_threshold_constant(self):
        """Should have correct SCORE_THRESHOLD value"""
        assert SCORE_THRESHOLD == 0.10
    
    def test_radius_steps_constant(self):
        """Should have correct RADIUS_STEPS"""
        assert RADIUS_STEPS == [1500, 3000, 4000]
    
    def test_weather_code_map_clear_sky(self):
        """Should map code 0 to clear sky"""
        assert WEATHER_CODE_MAP[0] == "Clear sky"
    
    def test_weather_code_map_heavy_rain(self):
        """Should map code 65 to heavy rain"""
        assert WEATHER_CODE_MAP[65] == "Heavy rain"
    
    def test_weather_code_map_thunderstorm(self):
        """Should map code 95 to thunderstorm"""
        assert WEATHER_CODE_MAP[95] == "Thunderstorm"