// src/screens/EventPlanner/EventScheduler.tsx
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
  Platform,
} from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';

interface Activity {
  id: string;
  name: string;
  category: string;
  start_time: string;
  end_time: string;
  duration_min: number;
  cost_cad: number;
  location: {
    lat: number;
    lng: number;
  };
  venue: string;
  tags: string[];
  weather_note?: string;
}

interface DayPlan {
  date: string;
  day_of_week: string;
  activities: Activity[];
  total_cost: number;
  total_duration: number;
}

interface ScheduleResponse {
  success: boolean;
  schedule: DayPlan[];
  metadata: {
    total_days: number;
    total_activities: number;
    total_cost: number;
    budget_remaining: number;
    generated_at: string;
  };
  error?: string;
}

type Props = NativeStackScreenProps<any, 'EventScheduler'>;

// Use your computer's IP address when testing on physical device/emulator
const API_URL = Platform.select({
  ios: 'http://localhost:5001/event_planner/generate',
  android: 'http://10.0.2.2:5001/event_planner/generate', // Android emulator
  default: 'http://localhost:5001/event_planner/generate',
});

export default function EventScheduler({ route, navigation }: Props) {
  const preferences = route.params?.preferences;
  
  const [schedule, setSchedule] = useState<DayPlan[]>([]);
  const [metadata, setMetadata] = useState<any>(null);
  const [selectedDay, setSelectedDay] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    generateSchedule();
  }, []);

  const generateSchedule = async () => {
    setLoading(true);
    setError(null);

    try {
      console.log('Sending preferences to API:', preferences);

      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(preferences),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ScheduleResponse = await response.json();

      if (!data.success) {
        throw new Error(data.error || 'Failed to generate schedule');
      }

      console.log('Received schedule:', data);
      setSchedule(data.schedule);
      setMetadata(data.metadata);
    } catch (err: any) {
      console.error('Schedule generation error:', err);
      setError(err.message || 'Failed to generate schedule. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getCategoryIcon = (category: string) => {
    const icons: { [key: string]: string } = {
      food: '🍽️',
      museums: '🏛️',
      parks: '🌳',
      shopping: '🛍️',
      nightlife: '🎉',
      history: '📜',
      architecture: '🏗️',
      aquarium: '🐠',
      zoo: '🦁',
      theme_parks: '🎢',
      concerts: '🎵',
      theatre: '🎭',
      views: '🌅',
    };
    return icons[category] || '📍';
  };

  const formatTime = (time: string) => {
    const [hours, minutes] = time.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour > 12 ? hour - 12 : hour === 0 ? 12 : hour;
    return `${displayHour}:${minutes} ${ampm}`;
  };

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours === 0) return `${mins}m`;
    if (mins === 0) return `${hours}h`;
    return `${hours}h ${mins}m`;
  };

  const currentDayPlan = schedule[selectedDay];
  const totalBudget = parseFloat(preferences.budget_total) || 0;
  const totalSpent = metadata?.total_cost || schedule.reduce((sum, day) => sum + day.total_cost, 0);
  const budgetRemaining = totalBudget - totalSpent;

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#2F6BFF" />
        <Text style={styles.loadingText}>Generating your personalized itinerary...</Text>
        <Text style={styles.loadingSubtext}>This may take a moment</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorIcon}>😞</Text>
        <Text style={styles.errorText}>{error}</Text>
        <Text style={styles.errorSubtext}>
          Make sure the Flask backend is running on port 5001
        </Text>
        <View style={styles.errorButtons}>
          <TouchableOpacity onPress={generateSchedule} style={styles.retryButton}>
            <Text style={styles.retryButtonText}>Try Again</Text>
          </TouchableOpacity>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButtonError}>
            <Text style={styles.backButtonErrorText}>Back to Preferences</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerContent}>
          <View style={styles.headerLeft}>
            <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButtonHeader}>
              <Text style={styles.backButtonHeaderText}>←</Text>
            </TouchableOpacity>
            <View>
              <Text style={styles.headerTitle}>
                Your {preferences.destination_city} Itinerary
              </Text>
              <Text style={styles.headerSubtitle}>
                {new Date(preferences.trip_start).toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric',
                })} - {new Date(preferences.trip_end).toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric',
                })}
              </Text>
            </View>
          </View>

          {/* Budget Summary */}
          <View style={[
            styles.budgetBox,
            budgetRemaining >= 0 ? styles.budgetBoxGood : styles.budgetBoxBad
          ]}>
            <Text style={styles.budgetLabel}>Budget</Text>
            <Text style={[
              styles.budgetAmount,
              budgetRemaining >= 0 ? styles.budgetAmountGood : styles.budgetAmountBad
            ]}>
              ${totalSpent.toFixed(2)} / ${totalBudget.toFixed(2)}
            </Text>
          </View>
        </View>
      </View>

      {/* Day Selector */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.daySelector}
        contentContainerStyle={styles.daySelectorContent}
      >
        {schedule.map((day, index) => (
          <TouchableOpacity
            key={day.date}
            onPress={() => setSelectedDay(index)}
            style={[
              styles.dayButton,
              selectedDay === index && styles.dayButtonSelected
            ]}
          >
            <Text style={[
              styles.dayNumber,
              selectedDay === index && styles.dayNumberSelected
            ]}>
              Day {index + 1}
            </Text>
            <Text style={[
              styles.dayName,
              selectedDay === index && styles.dayNameSelected
            ]}>
              {day.day_of_week}
            </Text>
            <Text style={[
              styles.dayDate,
              selectedDay === index && styles.dayDateSelected
            ]}>
              {new Date(day.date).toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
              })}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Activities List */}
      <ScrollView style={styles.activitiesContainer}>
        {currentDayPlan && (
          <View style={styles.activitiesContent}>
            {/* Day Summary */}
            <View style={styles.daySummary}>
              <View style={styles.summaryItem}>
                <Text style={styles.summaryLabel}>📅 Date</Text>
                <Text style={styles.summaryValue}>
                  {new Date(currentDayPlan.date).toLocaleDateString('en-US', {
                    weekday: 'long',
                    month: 'long',
                    day: 'numeric',
                  })}
                </Text>
              </View>

              <View style={styles.summaryItem}>
                <Text style={styles.summaryLabel}>⏱️ Duration</Text>
                <Text style={styles.summaryValue}>
                  {formatDuration(currentDayPlan.total_duration)}
                </Text>
              </View>

              <View style={styles.summaryItem}>
                <Text style={styles.summaryLabel}>💵 Cost</Text>
                <Text style={styles.summaryValue}>
                  ${currentDayPlan.total_cost.toFixed(2)}
                </Text>
              </View>

              <View style={styles.summaryItem}>
                <Text style={styles.summaryLabel}>📍 Activities</Text>
                <Text style={styles.summaryValue}>
                  {currentDayPlan.activities.length} planned
                </Text>
              </View>
            </View>

            {/* Activity Timeline */}
            {currentDayPlan.activities.map((activity, index) => (
              <View key={activity.id} style={styles.activityCard}>
                <View style={styles.activityHeader}>
                  <View style={styles.activityIcon}>
                    <Text style={styles.activityIconText}>
                      {getCategoryIcon(activity.category)}
                    </Text>
                  </View>
                  <View style={styles.activityHeaderContent}>
                    <Text style={styles.activityTime}>
                      {formatTime(activity.start_time)}
                    </Text>
                    <Text style={styles.activityName}>{activity.name}</Text>
                  </View>
                </View>

                <View style={styles.activityDetails}>
                  <Text style={styles.activityDetail}>
                    ⏱️ {formatTime(activity.start_time)} - {formatTime(activity.end_time)}
                  </Text>
                  <Text style={styles.activityDetail}>
                    💵 ${activity.cost_cad.toFixed(2)}
                  </Text>
                  <Text style={styles.activityDetail}>
                    📍 {activity.venue}
                  </Text>
                </View>

                {/* Tags */}
                <View style={styles.tagsContainer}>
                  {activity.tags.slice(0, 5).map((tag, tagIndex) => (
                    <View key={tagIndex} style={styles.tag}>
                      <Text style={styles.tagText}>{tag}</Text>
                    </View>
                  ))}
                </View>

                {activity.weather_note && (
                  <View style={styles.weatherWarning}>
                    <Text style={styles.weatherWarningText}>
                      ⚠️ {activity.weather_note}
                    </Text>
                  </View>
                )}

                {/* Timeline connector */}
                {index < currentDayPlan.activities.length - 1 && (
                  <View style={styles.timelineConnector} />
                )}
              </View>
            ))}
          </View>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    padding: 20,
  },
  loadingText: {
    marginTop: 20,
    fontSize: 18,
    color: '#555',
    fontWeight: '600',
  },
  loadingSubtext: {
    marginTop: 8,
    fontSize: 14,
    color: '#999',
  },
  errorIcon: {
    fontSize: 64,
    marginBottom: 20,
  },
  errorText: {
    fontSize: 18,
    color: '#dc2626',
    fontWeight: '600',
    marginBottom: 8,
    textAlign: 'center',
  },
  errorSubtext: {
    fontSize: 14,
    color: '#666',
    marginBottom: 20,
    textAlign: 'center',
    maxWidth: 300,
  },
  errorButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  retryButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: '#2F6BFF',
    borderRadius: 12,
  },
  retryButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  backButtonError: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: '#ffffff',
    borderWidth: 1.5,
    borderColor: '#CFCFD6',
    borderRadius: 12,
  },
  backButtonErrorText: {
    color: '#555',
    fontSize: 16,
    fontWeight: '600',
  },
  header: {
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2,
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
  },
  backButtonHeader: {
    width: 40,
    height: 40,
    backgroundColor: '#f3f4f6',
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  backButtonHeaderText: {
    fontSize: 20,
    color: '#2F6BFF',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#2F6BFF',
  },
  headerSubtitle: {
    fontSize: 13,
    color: '#666',
    marginTop: 4,
  },
  budgetBox: {
    padding: 12,
    borderRadius: 12,
    borderWidth: 1.5,
    minWidth: 120,
  },
  budgetBoxGood: {
    backgroundColor: '#f0fdf4',
    borderColor: '#86efac',
  },
  budgetBoxBad: {
    backgroundColor: '#fef2f2',
    borderColor: '#fca5a5',
  },
  budgetLabel: {
    fontSize: 11,
    color: '#666',
    fontWeight: '500',
  },
  budgetAmount: {
    fontSize: 14,
    fontWeight: '700',
    marginTop: 4,
  },
  budgetAmountGood: {
    color: '#16a34a',
  },
  budgetAmountBad: {
    color: '#dc2626',
  },
  daySelector: {
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  daySelectorContent: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 12,
  },
  dayButton: {
    minWidth: 120,
    backgroundColor: '#ffffff',
    borderWidth: 1.5,
    borderColor: '#e5e7eb',
    borderRadius: 12,
    padding: 12,
  },
  dayButtonSelected: {
    backgroundColor: '#2F6BFF',
    borderColor: '#2F6BFF',
  },
  dayNumber: {
    fontSize: 12,
    color: '#666',
    fontWeight: '600',
    marginBottom: 4,
  },
  dayNumberSelected: {
    color: '#ffffff',
  },
  dayName: {
    fontSize: 16,
    fontWeight: '700',
    color: '#333',
    marginBottom: 4,
  },
  dayNameSelected: {
    color: '#ffffff',
  },
  dayDate: {
    fontSize: 11,
    color: '#999',
  },
  dayDateSelected: {
    color: '#ffffff',
  },
  activitiesContainer: {
    flex: 1,
  },
  activitiesContent: {
    padding: 16,
  },
  daySummary: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2,
  },
  summaryItem: {
    marginBottom: 12,
  },
  summaryLabel: {
    fontSize: 12,
    color: '#666',
    fontWeight: '600',
    marginBottom: 4,
  },
  summaryValue: {
    fontSize: 15,
    fontWeight: '700',
    color: '#333',
  },
  activityCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2,
    position: 'relative',
  },
  activityHeader: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 12,
  },
  activityIcon: {
    width: 60,
    height: 60,
    backgroundColor: '#f3f4f6',
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  activityIconText: {
    fontSize: 28,
  },
  activityHeaderContent: {
    flex: 1,
    justifyContent: 'center',
  },
  activityTime: {
    fontSize: 13,
    fontWeight: '700',
    color: '#2F6BFF',
    marginBottom: 4,
  },
  activityName: {
    fontSize: 17,
    fontWeight: '700',
    color: '#333',
  },
  activityDetails: {
    marginBottom: 12,
    gap: 6,
  },
  activityDetail: {
    fontSize: 13,
    color: '#666',
  },
  tagsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  tag: {
    backgroundColor: '#f3f4f6',
    borderRadius: 6,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  tagText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#666',
    textTransform: 'capitalize',
  },
  weatherWarning: {
    marginTop: 12,
    padding: 8,
    backgroundColor: '#fef3c7',
    borderWidth: 1,
    borderColor: '#fbbf24',
    borderRadius: 8,
  },
  weatherWarningText: {
    fontSize: 12,
    color: '#92400e',
  },
  timelineConnector: {
    position: 'absolute',
    left: 40,
    bottom: -16,
    width: 2,
    height: 16,
    backgroundColor: '#e5e7eb',
  },
});