import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, FlatList, StyleSheet, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

interface Flight {
  flightNumber: string;
  airline: string;
  departure: string;
  arrival: string
  scheduledTime: string;
  actualTime: string;
  status: string;
  gate: string;
  terminal: string;
  type: string;
  aircraft: string;
}

export default function AirportTracker() {
  const [airportCode, setAirportCode] = useState('');
  const [direction, setDirection] = useState<'Departure' | 'Arrival' | 'Both'>('Both');
  const [flights, setFlights] = useState<Flight[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [airportName, setAirportName] = useState('');

  const fetchFlights = async () => {
    if (airportCode.length !== 3) {
      setError('Enter valid 3-letter airport code');
      return;
    }

    setLoading(true);
    setError('');

    try {
        // NO BACKEND. INPUT IP ADDRESS INTO THIS TO TEST. THIS IS ALL DEV. DO NOT PUSH YOUR IP ADDRESS TO GITHUB
        // GO TO TERMINAL TYPE IN IPCONFIG PASTE IPv4 ADDRESS REPLACING THE "127.0.0.1"
      const response = await fetch(
        `http://127.0.0.1:5001/airport_tracker/${airportCode.toUpperCase()}?direction=${direction}`
      );
      const data = await response.json();

      if (data.error) {
        setError(data.error);
        setFlights([]);
      } else {
        setFlights(data.flights);
        setAirportName(data.airportName);
      }
    } catch (err) {
      setError('Failed to fetch flights');
      setFlights([]);
    } finally {
      setLoading(false);
    }
  };

  const filteredFlights = flights.filter(flight => {
  const query = searchQuery.toLowerCase();
    return (
      flight.departure.toLowerCase().includes(query) ||
      flight.arrival.toLowerCase().includes(query) ||
      flight.flightNumber.toLowerCase().includes(query) ||
      flight.airline.toLowerCase().includes(query)
    );
  });

  const renderFlight = ({ item }: { item: Flight }) => (
    <View style={styles.flightCard}>
      <View style={styles.flightHeader}>
        <Text style={styles.flightNumber}>{item.flightNumber}</Text>
        <Text style={[styles.status, item.status === 'Departed' && styles.statusDeparted]}>{item.status}</Text>
      </View>
      <Text style={styles.airline}>{item.airline}</Text>
      <Text style={styles.location}>
        {item.type === 'Departure' 
          ? `To: ${item.arrival}` 
          : `From: ${item.departure}`}
      </Text>
      <View style={styles.flightDetails}>
        <Text style={styles.detailText}>🕐 {item.scheduledTime || 'N/A'}</Text>
        {item.actualTime && <Text style={styles.detailText}>✈️ {item.actualTime}</Text>}
        <Text style={styles.detailText}>🚪 Gate {item.gate} | Terminal {item.terminal}</Text>
      </View>
      <Text style={styles.aircraft}>✈️ {item.aircraft}</Text>
    </View>
  );

  return (
    <SafeAreaView style={styles.safe} edges={['bottom', 'left', 'right']}>
      <View style={styles.container}>
        <Text style={styles.title}>✈️ Airport Tracker</Text>
        <Text style={styles.subtitle}>Track flights in real-time</Text>

        <TextInput
          style={styles.input}
          placeholder="Airport Code (e.g., YYZ)"
          value={airportCode}
          onChangeText={setAirportCode}
          maxLength={3}
          autoCapitalize="characters"
          placeholderTextColor="#999"
        />

        <View style={styles.directionButtons}>
          {(['Departure', 'Arrival'] as const).map(dir => (
            <TouchableOpacity
              key={dir}
              style={[styles.directionButton, direction === dir && styles.activeButton]}
              onPress={() => setDirection(dir)}
            >
              <Text style={direction === dir ? styles.activeButtonText : styles.buttonText}>
                {dir}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <TouchableOpacity style={styles.searchButton} onPress={fetchFlights}>
          <Text style={styles.searchButtonText}>Search Flights</Text>
        </TouchableOpacity>

        {airportName && <Text style={styles.airportName}>{airportName}</Text>}

        <TextInput
          style={styles.input}
          placeholder="Search by flight, airline, or location..."
          value={searchQuery}
          onChangeText={setSearchQuery}
          placeholderTextColor="#999"
        />

        {error && <Text style={styles.error}>{error}</Text>}

        {loading ? (
          <ActivityIndicator size="large" color="#2F6BFF" style={styles.loader} />
        ) : (
          <FlatList
            data={filteredFlights}
            renderItem={renderFlight}
            keyExtractor={(item, index) => `${item.flightNumber}-${index}`}
            style={styles.flightList}
            ListEmptyComponent={
              <Text style={styles.emptyText}>
                {flights.length === 0 ? 'Search for an airport to see flights' : 'No matching flights'}
              </Text>
            }
          />
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  container: {
    flex: 1,
    padding: 24,
  },
  title: {
    fontSize: 32,
    fontWeight: '700',
    color: '#2F6BFF',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    fontWeight: '500',
    color: '#555',
    textAlign: 'center',
    marginBottom: 24,
  },
  input: {
    backgroundColor: '#f5f5f5',
    padding: 14,
    borderRadius: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    fontSize: 16,
  },
  directionButtons: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 16,
  },
  directionButton: {
    flex: 1,
    padding: 12,
    backgroundColor: 'white',
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: '#2F6BFF',
    alignItems: 'center',
  },
  activeButton: {
    backgroundColor: '#2F6BFF',
  },
  buttonText: {
    color: '#2F6BFF',
    fontWeight: '600',
    fontSize: 14,
  },
  activeButtonText: {
    color: 'white',
    fontWeight: '600',
    fontSize: 14,
  },
  searchButton: {
    backgroundColor: '#2F6BFF',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 16,
  },
  searchButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  airportName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#2F6BFF',
    marginBottom: 12,
    textAlign: 'center',
  },
  flightList: {
    flex: 1,
  },
  flightCard: {
    backgroundColor: 'white',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  flightHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  flightNumber: {
    fontSize: 18,
    fontWeight: '700',
    color: '#333',
  },
  status: {
    fontSize: 13,
    color: '#4CAF50',
    fontWeight: '600',
    paddingHorizontal: 8,
    paddingVertical: 4,
    backgroundColor: '#E8F5E9',
    borderRadius: 6,
  },
  statusDeparted: {
    color: '#2196F3',
    backgroundColor: '#E3F2FD',
  },
  airline: {
    fontSize: 15,
    color: '#666',
    marginBottom: 6,
    fontWeight: '500',
  },
  location: {
    fontSize: 16,
    color: '#333',
    marginBottom: 10,
    fontWeight: '600',
  },
  flightDetails: {
    gap: 4,
  },
  detailText: {
    fontSize: 14,
    color: '#666',
  },
  aircraft: {
    fontSize: 13,
    color: '#999',
    marginTop: 8,
    fontStyle: 'italic',
  },
  error: {
    color: '#f44336',
    textAlign: 'center',
    marginBottom: 12,
    fontSize: 14,
    fontWeight: '500',
  },
  emptyText: {
    textAlign: 'center',
    color: '#999',
    marginTop: 40,
    fontSize: 15,
  },
  loader: {
    marginTop: 40,
  },
});