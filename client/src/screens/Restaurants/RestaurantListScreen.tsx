import React, {useState, useEffect} from "react"
import { StyleSheet, Text, View, FlatList, Pressable, ScrollView, TextInput, ActivityIndicator} from 'react-native'
import { SafeAreaView } from "react-native-safe-area-context"

import DropDownPicker from "react-native-dropdown-picker"
import CreateRestaurantCard from '../../components/restaurant-components/RestaurantCard'

import { RootStackParamList } from "../../../App";
import { RouteProp, useRoute } from "@react-navigation/native"

type RestaurantListRouteProp = RouteProp<RootStackParamList, "RestaurantList">;

// @ts-ignore
export default function RestaurantListScreen({ navigation }) {
  const route = useRoute<RestaurantListRouteProp>();

  const {
    iata = "",
    airport = "",
    terminal = "1",
    food_category = null,
    cuisine = null,
    dietary_restriction = null,
    restaurant = "",
    max_distance = 0,
    prep_time = 0,
    min_rating = 0,
    max_price = 0,
    p_sort = 0,
    d_sort = 0,
    r_sort = 0,
    t_sort = 0,
    wants_open = false,
  } = route.params;

  // Restaurant list state
  const [restaurants, setRestaurants] = useState<any[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  // Search state
  const [searchQuery, setSearchQuery] = useState(restaurant);

  // Collapsible state
  const [isExpanded, setIsExpanded] = useState(false);

  // Open now toggle
  const [openNow, setOpenNow] = useState(wants_open);

  // Applied filters state
  const [appliedFilters, setAppliedFilters] = useState({
    openNow: wants_open,
    searchQuery: restaurant,
    distance: max_distance || null,
    foodReady: prep_time || null,
    rating: min_rating || null,
    price: max_price || null,
    priceSort: p_sort || null,
    distanceSort: d_sort || null,
    durationSort: t_sort || null,
    ratingSort: r_sort || null,
  });

  // Distance dropdown
  const [open1, setOpen1] = useState(false);
  const [value1, setValue1] = useState(max_distance || null);
  const [items1, setItems1] = useState([
    { label: 'Any', value: 0 },
    { label: '1 km', value: 1 },
    { label: '2 km', value: 2 },
    { label: '3 km', value: 3 }
  ]);

  // Food ready in dropdown
  const [open2, setOpen2] = useState(false);
  const [value2, setValue2] = useState(prep_time || null);
  const [items2, setItems2] = useState([
    { label: 'Any', value: 0 },
    { label: '10 minutes', value: 10 },
    { label: '15 minutes', value: 15 },
    { label: '20 minutes', value: 20 },
    { label: '30 minutes', value: 30 },
  ]);

  // Rating dropdown
  const [open3, setOpen3] = useState(false);
  const [value3, setValue3] = useState(min_rating || null);
  const [items3, setItems3] = useState([
    { label: 'Any', value: 0 },
    { label: '4+ stars', value: 4 },
    { label: '3+ stars', value: 3 },
    { label: '2+ stars', value: 2 },
    { label: '1+ stars', value: 1 }
  ]);

  // Price range dropdown
  const [open4, setOpen4] = useState(false);
  const [value4, setValue4] = useState(max_price || null);
  const [items4, setItems4] = useState([
    { label: 'Any', value: 0 },
    { label: '$10', value: 10 },
    { label: '$20', value: 20 },
    { label: '$30', value: 30 },
    { label: '$40', value: 40 },
  ]);

  // Price sort dropdown
  const [open5, setOpen5] = useState(false);
  const [value5, setValue5] = useState(p_sort || null);
  const [items5, setItems5] = useState([
    { label: 'No sort', value: 0 },
    { label: 'low to high', value: 1 },
    { label: 'high to low', value: -1 },
  ]);

  // Distance sort dropdown
  const [open6, setOpen6] = useState(false);
  const [value6, setValue6] = useState(d_sort || null);
  const [items6, setItems6] = useState([
    { label: 'No sort', value: 0 },
    { label: 'low to high', value: 1 },
    { label: 'high to low', value: -1 },
  ]);

  // Duration sort dropdown
  const [open7, setOpen7] = useState(false);
  const [value7, setValue7] = useState(t_sort || null);
  const [items7, setItems7] = useState([
    { label: 'No sort', value: 0 },
    { label: 'low to high', value: 1 },
    { label: 'high to low', value: -1 },
  ]);

  // Rating sort dropdown
  const [open8, setOpen8] = useState(false);
  const [value8, setValue8] = useState(r_sort || null);
  const [items8, setItems8] = useState([
    { label: 'No sort', value: 0 },
    { label: 'low to high', value: 1 },
    { label: 'high to low', value: -1 },
  ]);

  // Fetch restaurants whenever route params change
  useEffect(() => {
    (async () => {
      try {
        setErr(null);
        setRestaurants(null);
        
        const response = await fetch("http://127.0.0.1:5001/search_restaurants", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            iata,
            terminal: parseInt(terminal),
            food_category,
            cuisine,
            dietary_restriction,
            restaurant: searchQuery,
            max_distance,
            prep_time,
            min_rating,
            max_price,
            p_sort,
            d_sort,
            r_sort,
            t_sort,
            wants_open
          }),
        });
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        setRestaurants(data);
      } catch (error: any) {
        setErr(error.message);
      }
    })();
  }, [iata, terminal, food_category, cuisine, dietary_restriction, max_distance, prep_time, min_rating, max_price, p_sort, d_sort, r_sort, t_sort, wants_open]);

  const applyFilters = () => {
    const filters = {
      openNow: openNow,
      searchQuery: restaurant,
      distance: value1,
      foodReady: value2,
      rating: value3,
      price: value4,
      priceSort: value5,
      distanceSort: value6,
      durationSort: value7,
      ratingSort: value8,
    };
    
    setAppliedFilters(filters);
    setIsExpanded(false);
    
    // Navigate with new filter parameters
    navigation.push('RestaurantList', {
      iata,
      airport,
      terminal,
      food_category,
      cuisine,
      dietary_restriction,
      restaurant: searchQuery,
      max_distance: value1 ?? 0,
      prep_time: value2 ?? 0,
      min_rating: value3 ?? 0,
      max_price: value4 ?? 0,
      p_sort: value5 ?? 0,
      d_sort: value6 ?? 0,
      r_sort: value8 ?? 0,
      t_sort: value7 ?? 0,
      wants_open: openNow,
    });
  };

  const clearAllFilters = () => {
    setOpenNow(false);
    setValue1(null);
    setValue2(null);
    setValue3(null);
    setValue4(null);
    setValue5(null);
    setValue6(null);
    setValue7(null);
    setValue8(null);
    setAppliedFilters({
      openNow: false,
      searchQuery: "",
      distance: null,
      foodReady: null,
      rating: null,
      price: null,
      priceSort: null,
      distanceSort: null,
      durationSort: null,
      ratingSort: null,
    });
    
    // Navigate back with only original search params (no filters)
    navigation.push('RestaurantList', {
      iata,
      airport,
      terminal,
      food_category,
      cuisine,
      dietary_restriction,
      restaurant: "",
      max_distance: 0,
      prep_time: 0,
      min_rating: 0,
      max_price: 0,
      p_sort: 0,
      d_sort: 0,
      r_sort: 0,
      t_sort: 0,
      wants_open: false,
    });
  };

  // @ts-ignore
  const getFilterLabel = (items, value) => {
    // @ts-ignore
    const item = items.find(i => i.value === value);
    return item ? item.label : null;
  };

  const renderAppliedFilters = () => {
    const filters = [];
    if (appliedFilters.searchQuery && appliedFilters.searchQuery !== "") {
      filters.push(<View key="searchQuery" style={styles.filterChip}><Text style={styles.filterChipText}>Restaurant: {searchQuery}</Text></View>);
    }
    if (appliedFilters.openNow) {
      filters.push(<View key="openNow" style={styles.filterChip}><Text style={styles.filterChipText}>Open now</Text></View>);
    }
    if (appliedFilters.distance && appliedFilters.distance !== 0) {
      filters.push(<View key="distance" style={styles.filterChip}><Text style={styles.filterChipText}>Max distance: {getFilterLabel(items1, appliedFilters.distance)}</Text></View>);
    }
    if (appliedFilters.foodReady && appliedFilters.foodReady !== 0) {
      filters.push(<View key="foodReady" style={styles.filterChip}><Text style={styles.filterChipText}>Time for food preparation: {getFilterLabel(items2, appliedFilters.foodReady)}</Text></View>);
    }
    if (appliedFilters.rating && appliedFilters.rating !== 0) {
      filters.push(<View key="rating" style={styles.filterChip}><Text style={styles.filterChipText}>Rating: {getFilterLabel(items3, appliedFilters.rating)}</Text></View>);
    }
    if (appliedFilters.price && appliedFilters.price !== 0) {
      filters.push(<View key="price" style={styles.filterChip}><Text style={styles.filterChipText}>Price: {getFilterLabel(items4, appliedFilters.price)}</Text></View>);
    }
    if (appliedFilters.priceSort && appliedFilters.priceSort !== 0) {
      filters.push(<View key="priceSort" style={styles.filterChip}><Text style={styles.filterChipText}>Sort by price: {getFilterLabel(items5, appliedFilters.priceSort)}</Text></View>);
    }
    if (appliedFilters.distanceSort && appliedFilters.distanceSort !== 0) {
      filters.push(<View key="distanceSort" style={styles.filterChip}><Text style={styles.filterChipText}>Sort by distance: {getFilterLabel(items6, appliedFilters.distanceSort)}</Text></View>);
    }
    if (appliedFilters.durationSort && appliedFilters.durationSort !== 0) {
      filters.push(<View key="durationSort" style={styles.filterChip}><Text style={styles.filterChipText}>Sort by food preparation time: {getFilterLabel(items7, appliedFilters.durationSort)}</Text></View>);
    }
    if (appliedFilters.ratingSort && appliedFilters.ratingSort !== 0) {
      filters.push(<View key="ratingSort" style={styles.filterChip}><Text style={styles.filterChipText}>Sort by rating: {getFilterLabel(items8, appliedFilters.ratingSort)}</Text></View>);
    }
    return filters.length > 0 ? (
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.appliedFiltersContainer}>
        {filters}
      </ScrollView>
    ) : null;
  };

  // Loading state
  if (!restaurants && !err) {
    return (
      <SafeAreaView style={styles.sav}>
        <ActivityIndicator size="large" style={{ marginTop: 50 }} />
      </SafeAreaView>
    );
  }

  // Error state
  if (err) {
    return (
      <SafeAreaView style={styles.sav}>
        <Text style={{ padding: 16, color: 'red' }}>Error: {err}</Text>
      </SafeAreaView>
    );
  }

  if (restaurants?.length == 0){
    return(
      <SafeAreaView style={styles.sav}>
        <View style={styles.top_banner}>
        <Text style={styles.airport_text}>Foods at {airport}</Text>
        <Text style={styles.terminal_text}>Your location: Terminal {terminal}</Text>

        <Pressable 
          style={styles.collapsibleHeader}
          onPress={() => setIsExpanded(!isExpanded)}
        >
          <Text style={styles.collapsibleHeaderText}>Filter and Sort</Text>
          <Text style={styles.collapsibleIcon}>{isExpanded ? '▲' : '▼'}</Text>
        </Pressable>

        {!isExpanded && renderAppliedFilters()}

        {isExpanded && (
          <View style={styles.collapsibleContent}>
            <View style={styles.searchContainer}>
              <Text style={styles.searchLabel}>Search for specific restaurants</Text>
              <TextInput
                style={styles.searchInput}
                placeholder="Search..."
                placeholderTextColor="#999"
                value={searchQuery}
                onChangeText={setSearchQuery}
              />
            </View>
            <Text style={styles.sectionLabel}>Filters:</Text>
            <View style={[styles.filterSection, {zIndex: 5000}]}>
              <View style={styles.dropdownContainer}>
                <Text style={styles.dropdownLabel}>Max distance</Text>
                <DropDownPicker
                  open={open1}
                  value={value1}
                  items={items1}
                  setOpen={setOpen1}
                  setValue={setValue1}
                  setItems={setItems1}
                  placeholder="Any"
                  style={styles.dropdown}
                  zIndex={5000}
                  zIndexInverse={1000}
                  dropDownDirection="BOTTOM"
                />
              </View>

              <View style={styles.dropdownContainer}>
                <Text style={styles.dropdownLabel}>Food ready in</Text>
                <DropDownPicker
                  open={open2}
                  value={value2}
                  items={items2}
                  setOpen={setOpen2}
                  setValue={setValue2}
                  setItems={setItems2}
                  placeholder="Any"
                  style={styles.dropdown}
                  zIndex={4000}
                  zIndexInverse={2000}
                  dropDownDirection="BOTTOM"
                />
                </View>
              </View>

              <View style={[styles.filterSection, {zIndex: 3000}]}>
              <View style={styles.dropdownContainer}>
                <Text style={styles.dropdownLabel}>Rating</Text>
                <DropDownPicker
                  open={open3}
                  value={value3}
                  items={items3}
                  setOpen={setOpen3}
                  setValue={setValue3}
                  setItems={setItems3}
                  placeholder="Any"
                  style={styles.dropdown}
                  zIndex={3000}
                  zIndexInverse={3000}
                  dropDownDirection="BOTTOM"
                />
              </View>

              <View style={styles.dropdownContainer}>
                <Text style={styles.dropdownLabel}>Maximum price</Text>
                <DropDownPicker
                  open={open4}
                  value={value4}
                  items={items4}
                  setOpen={setOpen4}
                  setValue={setValue4}
                  setItems={setItems4}
                  placeholder="Any"
                  style={styles.dropdown}
                  zIndex={2000}
                  zIndexInverse={4000}
                  dropDownDirection="BOTTOM"
                />
              </View>
            </View>

            <Text style={styles.sectionLabel}>Sort by:</Text>
            <View style={[styles.sortSection, {zIndex: 1000}]}>
              <View style={styles.dropdownContainer}>
                <Text style={styles.dropdownLabel}>Price</Text>
                <DropDownPicker
                  open={open5}
                  value={value5}
                  items={items5}
                  setOpen={setOpen5}
                  setValue={setValue5}
                  setItems={setItems5}
                  placeholder="None"
                  style={styles.dropdown}
                  zIndex={1000}
                  zIndexInverse={1000}
                  dropDownDirection="BOTTOM"
                />
              </View>

              <View style={styles.dropdownContainer}>
                <Text style={styles.dropdownLabel}>Distance</Text>
                <DropDownPicker
                  open={open6}
                  value={value6}
                  items={items6}
                  setOpen={setOpen6}
                  setValue={setValue6}
                  setItems={setItems6}
                  placeholder="None"
                  style={styles.dropdown}
                  zIndex={900}
                  zIndexInverse={1100}
                  dropDownDirection="BOTTOM"
                />
              </View>
            </View>

            <View style={[styles.sortSection, {zIndex: 800}]}>
              <View style={styles.dropdownContainer}>
                <Text style={styles.dropdownLabel}>Food prep time</Text>
                <DropDownPicker
                  open={open7}
                  value={value7}
                  items={items7}
                  setOpen={setOpen7}
                  setValue={setValue7}
                  setItems={setItems7}
                  placeholder="None"
                  style={styles.dropdown}
                  zIndex={800}
                  zIndexInverse={1200}
                  dropDownDirection="BOTTOM"
                />
              </View>

              <View style={styles.dropdownContainer}>
                <Text style={styles.dropdownLabel}>Rating</Text>
                <DropDownPicker
                  open={open8}
                  value={value8}
                  items={items8}
                  setOpen={setOpen8}
                  setValue={setValue8}
                  setItems={setItems8}
                  placeholder="None"
                  style={styles.dropdown}
                  zIndex={700}
                  zIndexInverse={1300}
                  dropDownDirection="BOTTOM"
                />
              </View>
            </View>

            <View style={styles.buttonRow}>
              <Pressable 
                style={[styles.actionButton, openNow && styles.openNowButtonActive]} 
                onPress={() => setOpenNow(!openNow)}
              >
                <Text style={[styles.actionButtonText, openNow && styles.openNowTextActive]}>
                  Open now
                </Text>
              </Pressable>

              <Pressable 
                style={[styles.actionButton, styles.applyButton]} 
                onPress={applyFilters}
              >
                <Text style={[styles.actionButtonText, styles.applyButtonText]}>
                  Apply Filters
                </Text>
              </Pressable>

              <Pressable 
                style={[styles.actionButton, styles.clearButton]} 
                onPress={clearAllFilters}
              >
                <Text style={[styles.actionButtonText, styles.clearButtonText]}>
                  Clear All
                </Text>
              </Pressable>
            </View>
          </View>
        )}
      </View>
      <View style={styles.norestaurant}>
        <Text style={styles.norestaurantText}>No restaurants found. Reset the filters or, go back and search for other restaurants.</Text>
      </View>
      </SafeAreaView>
    )
  }
  return (
    <SafeAreaView style={styles.sav}>
      <View style={styles.top_banner}>
        <Text style={styles.airport_text}>Foods at {airport}</Text>
        <Text style={styles.terminal_text}>Your location: terminal {terminal}</Text>

        <Pressable 
          style={styles.collapsibleHeader}
          onPress={() => setIsExpanded(!isExpanded)}
        >
          <Text style={styles.collapsibleHeaderText}>Filter and Sort</Text>
          <Text style={styles.collapsibleIcon}>{isExpanded ? '▲' : '▼'}</Text>
        </Pressable>

        {!isExpanded && renderAppliedFilters()}

        {isExpanded && (
          <View style={styles.collapsibleContent}>
            <View style={styles.searchContainer}>
              <Text style={styles.searchLabel}>Search for specific restaurants</Text>
              <TextInput
                style={styles.searchInput}
                placeholder="search for a restaurant..."
                placeholderTextColor="#999"
                value={searchQuery}
                onChangeText={setSearchQuery}
              />
            </View>
            <Text style={styles.sectionLabel}>Filters:</Text>
            <View style={[styles.filterSection, {zIndex: 5000}]}>
              <View style={styles.dropdownContainer}>
                <Text style={styles.dropdownLabel}>Max distance</Text>
                <DropDownPicker
                  open={open1}
                  value={value1}
                  items={items1}
                  setOpen={setOpen1}
                  setValue={setValue1}
                  setItems={setItems1}
                  placeholder="Any"
                  style={styles.dropdown}
                  zIndex={5000}
                  zIndexInverse={1000}
                  dropDownDirection="BOTTOM"
                />
              </View>

              <View style={styles.dropdownContainer}>
                <Text style={styles.dropdownLabel}>Food ready in</Text>
                <DropDownPicker
                  open={open2}
                  value={value2}
                  items={items2}
                  setOpen={setOpen2}
                  setValue={setValue2}
                  setItems={setItems2}
                  placeholder="Any"
                  style={styles.dropdown}
                  zIndex={4000}
                  zIndexInverse={2000}
                  dropDownDirection="BOTTOM"
                />
                </View>
              </View>

              <View style={[styles.filterSection, {zIndex: 3000}]}>
              <View style={styles.dropdownContainer}>
                <Text style={styles.dropdownLabel}>Rating</Text>
                <DropDownPicker
                  open={open3}
                  value={value3}
                  items={items3}
                  setOpen={setOpen3}
                  setValue={setValue3}
                  setItems={setItems3}
                  placeholder="Any"
                  style={styles.dropdown}
                  zIndex={3000}
                  zIndexInverse={3000}
                  dropDownDirection="BOTTOM"
                />
              </View>

              <View style={styles.dropdownContainer}>
                <Text style={styles.dropdownLabel}>Maximum price</Text>
                <DropDownPicker
                  open={open4}
                  value={value4}
                  items={items4}
                  setOpen={setOpen4}
                  setValue={setValue4}
                  setItems={setItems4}
                  placeholder="Any"
                  style={styles.dropdown}
                  zIndex={2000}
                  zIndexInverse={4000}
                  dropDownDirection="BOTTOM"
                />
              </View>
            </View>

            <Text style={styles.sectionLabel}>Sort by:</Text>
            <View style={[styles.sortSection, {zIndex: 1000}]}>
              <View style={styles.dropdownContainer}>
                <Text style={styles.dropdownLabel}>Price</Text>
                <DropDownPicker
                  open={open5}
                  value={value5}
                  items={items5}
                  setOpen={setOpen5}
                  setValue={setValue5}
                  setItems={setItems5}
                  placeholder="None"
                  style={styles.dropdown}
                  zIndex={1000}
                  zIndexInverse={1000}
                  dropDownDirection="BOTTOM"
                />
              </View>

              <View style={styles.dropdownContainer}>
                <Text style={styles.dropdownLabel}>Distance</Text>
                <DropDownPicker
                  open={open6}
                  value={value6}
                  items={items6}
                  setOpen={setOpen6}
                  setValue={setValue6}
                  setItems={setItems6}
                  placeholder="None"
                  style={styles.dropdown}
                  zIndex={900}
                  zIndexInverse={1100}
                  dropDownDirection="BOTTOM"
                />
              </View>
            </View>

            <View style={[styles.sortSection, {zIndex: 800}]}>
              <View style={styles.dropdownContainer}>
                <Text style={styles.dropdownLabel}>Food prep time</Text>
                <DropDownPicker
                  open={open7}
                  value={value7}
                  items={items7}
                  setOpen={setOpen7}
                  setValue={setValue7}
                  setItems={setItems7}
                  placeholder="None"
                  style={styles.dropdown}
                  zIndex={800}
                  zIndexInverse={1200}
                  dropDownDirection="BOTTOM"
                />
              </View>

              <View style={styles.dropdownContainer}>
                <Text style={styles.dropdownLabel}>Rating</Text>
                <DropDownPicker
                  open={open8}
                  value={value8}
                  items={items8}
                  setOpen={setOpen8}
                  setValue={setValue8}
                  setItems={setItems8}
                  placeholder="None"
                  style={styles.dropdown}
                  zIndex={700}
                  zIndexInverse={1300}
                  dropDownDirection="BOTTOM"
                />
              </View>
            </View>

            <View style={styles.buttonRow}>
              <Pressable 
                style={[styles.actionButton, openNow && styles.openNowButtonActive]} 
                onPress={() => setOpenNow(!openNow)}
              >
                <Text style={[styles.actionButtonText, openNow && styles.openNowTextActive]}>
                  Open now
                </Text>
              </Pressable>

              <Pressable 
                style={[styles.actionButton, styles.applyButton]} 
                onPress={applyFilters}
              >
                <Text style={[styles.actionButtonText, styles.applyButtonText]}>
                  Apply Filters
                </Text>
              </Pressable>

              <Pressable 
                style={[styles.actionButton, styles.clearButton]} 
                onPress={clearAllFilters}
              >
                <Text style={[styles.actionButtonText, styles.clearButtonText]}>
                  Clear All
                </Text>
              </Pressable>
            </View>
          </View>
        )}
      </View>

      <View style={styles.listContainer}>
        <FlatList
          data={restaurants}
          keyExtractor={(item, index) => item.id || index.toString()}
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.restaurantList}
          renderItem={({ item }) => (
            <CreateRestaurantCard
              name={item.name}
              terminal={item.terminal}
              type={item.category}
              cuisine={item.cuisine}
              restriction={item.food_type}
              distance={item.distance}
              rating={item.rating}
              price={item.avg_meal_cost}
              prep_time={item.prep_time}
              open_time={item.open_time}
              close_time={item.close_time}
              open_now={item.open_now}
              imagepath={item.link}
            />
          )}
        />
      </View>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
    sav: {
      flex: 1,
      padding: 10,
      backgroundColor: "#fff"
    },
    top_banner:{
      width: "100%",
      height: "auto",
      borderRadius: 12,
      borderWidth: 1,
      backgroundColor: "#2F6BFF",
      textAlign: "left",
      paddingVertical: 10,
      paddingHorizontal: 15,
      gap: 2,
      zIndex: 10000,
      elevation: 10,
    },
    airport_text:{
        fontSize: 20,
        fontWeight: "bold",
        color: "#fff"
    },
    terminal_text:{
      fontSize: 14,
      fontWeight: "500",
      color: "#fff"
    },
    searchContainer: {
      marginTop: 8,
    },
    searchLabel: {
      fontSize: 14,
      fontWeight: "500",
      color: "#fff",
      marginBottom: 4,
    },
    searchInput: {
      backgroundColor: "#fff",
      borderRadius: 8,
      paddingHorizontal: 12,
      paddingVertical: 10,
      fontSize: 15,
      color: "#333",
    },
    collapsibleHeader: {
      flexDirection: "row",
      justifyContent: "space-between",
      alignItems: "center",
      backgroundColor: "#fff",
      paddingVertical: 12,
      paddingHorizontal: 16,
      borderRadius: 8,
      marginTop: 8,
    },
    collapsibleHeaderText: {
      fontSize: 16,
      fontWeight: "600",
      color: "#333",
    },
    collapsibleIcon: {
      fontSize: 14,
      color: "#333",
    },
    collapsibleContent: {
      marginTop: 8,
      gap: 2,
    },
    filterSection: {
      flexDirection: "row",
      alignItems: "flex-end",
      gap: 12,
    },
    sortSection: {
      flexDirection: "row",
      alignItems: "flex-end",
      gap: 12,
      marginBottom: 8,
    },
    buttonRow: {
      flexDirection: "row",
      gap: 12,
      paddingTop: 6,
    },
    actionButton: {
      flex: 1,
      height: 48,
      paddingHorizontal: 8,
      paddingVertical: 12,
      borderRadius: 8,
      borderWidth: 1,
      borderColor: "#ccc",
      backgroundColor: "#fff",
      justifyContent: "center",
      alignItems: "center",
    },
    openNowButtonActive: {
      backgroundColor: "#2F6BFF",
      borderColor: "#2F6BFF",
    },
    applyButton: {
      backgroundColor: "#28a745",
      borderColor: "#28a745",
    },
    actionButtonText: {
      fontSize: 14,
      fontWeight: "500",
      color: "#333",
    },
    openNowTextActive: {
      color: "#fff",
    },
    applyButtonText: {
      color: "#fff",
    },
    dropdownContainer: {
      flex: 1,
      minWidth: 100,
    },
    dropdownLabel: {
      fontSize: 14,
      marginLeft: 2, 
      fontWeight: "500",
      marginBottom: 4,
      color: "#fff",
    },
    dropdown: {
      minHeight: 48,
    },
    restaurantList: {
      gap: 10,
      alignItems: "center",
    },
    listContainer: {
      flex: 1,
      zIndex: 1,
    },
    appliedFiltersContainer: {
      marginTop: 8,
      flexDirection: "row",
    },
    filterChip: {
      backgroundColor: "#fff",
      paddingHorizontal: 12,
      paddingVertical: 6,
      borderRadius: 16,
      marginRight: 8,
    },
    filterChipText: {
      fontSize: 13,
      color: "#333",
      fontWeight: "500",
    },
    clearButton: {
      backgroundColor: "#dc3545",
      borderColor: "#dc3545",
    },
    clearButtonText: {
      color: "#fff",
    },
    sectionLabel: {
      fontSize: 17,
      fontWeight: "700",
      color: "#fff",
      marginBottom: 0,
      marginTop: 5
    },
    norestaurant: {
      flex: 1,
      flexDirection: "column",
      justifyContent: "center",
      alignItems: "center",
      paddingHorizontal: 20
    },
    norestaurantText: {
      fontSize: 25,
      fontWeight: "bold",
      textAlign: "center",
      color: "#bc1515ff"
    },
})