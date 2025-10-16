import React, {useState} from "react"
import { StyleSheet, SafeAreaView, Text, View, FlatList, Pressable, ScrollView} from 'react-native'
import DropDownPicker from "react-native-dropdown-picker"
import CreateRestaurantCard from '../../components/restaurant-components/RestaurantCard'

const rest_list = [
                  { id: "1",
                    name: "McDonald's",
                    terminal: 1,
                    type: "Fast food",
                    distance: 0.3,
                    imagepath: require('../../../assets/McDonalds-Logo.jpg')
                  },
                  {
                    id: "2",
                    name: "McDonald's",
                    terminal: 3,
                    type: "Fast food",
                    distance: 1.0,
                    imagepath: require('../../../assets/McDonalds-Logo.jpg')
                  }];

export default function RestaurantListScreen() {
  // Collapsible state
  const [isExpanded, setIsExpanded] = useState(false);

  // Open now toggle
  const [openNow, setOpenNow] = useState(false);

  // Applied filters state
  const [appliedFilters, setAppliedFilters] = useState({
    openNow: false,
    distance: null,
    foodReady: null,
    rating: null,
    price: null,
    priceSort: null,
    distanceSort: null,
    durationSort: null,
  });

  // Distance dropdown
  const [open1, setOpen1] = useState(false);
  const [value1, setValue1] = useState(null);
  const [items1, setItems1] = useState([
    { label: 'Any distance', value: "any" },
    { label: '1 km', value: "1" },
    { label: '2 km', value: "2" },
    { label: '3 km', value: "3" },
    { label: '3+ km', value: "3.1" },
  ]);

  // Food ready in dropdown
  const [open2, setOpen2] = useState(false);
  const [value2, setValue2] = useState(null);
  const [items2, setItems2] = useState([
    { label: 'Any time', value: "any" },
    { label: 'Within 10 minutes', value: "10" },
    { label: 'Within 15 minutes', value: "15" },
    { label: 'Within 20 minutes', value: "20" },
    { label: 'Within 30 minutes', value: "30" },
  ]);

  // Rating dropdown
  const [open3, setOpen3] = useState(false);
  const [value3, setValue3] = useState(null);
  const [items3, setItems3] = useState([
    { label: 'Any rating', value: "any" },
    { label: '4+ stars', value: "4" },
    { label: '3+ stars', value: "3" },
    { label: '2+ stars', value: "2" },
    { label: '1+ stars', value: "1" },
    { label: '0-1 stars', value: "0" },
  ]);

  // Price range dropdown
  const [open4, setOpen4] = useState(false);
  const [value4, setValue4] = useState(null);
  const [items4, setItems4] = useState([
    { label: 'Any price', value: "any" },
    { label: '$', value: "1" },
    { label: '$$', value: "2" },
    { label: '$$$', value: "3" },
    { label: '$$$$', value: "4" },
  ]);

  // Price sort dropdown
  const [open5, setOpen5] = useState(false);
  const [value5, setValue5] = useState(null);
  const [items5, setItems5] = useState([
    { label: 'low to high', value: "asc" },
    { label: 'high to low', value: "desc" },
  ]);

  // Distance sort dropdown
  const [open6, setOpen6] = useState(false);
  const [value6, setValue6] = useState(null);
  const [items6, setItems6] = useState([
    { label: 'low to high', value: "asc" },
    { label: 'high to low', value: "desc" },
  ]);

  // Duration sort dropdown
  const [open7, setOpen7] = useState(false);
  const [value7, setValue7] = useState(null);
  const [items7, setItems7] = useState([
    { label: 'low to high', value: "asc" },
    { label: 'high to low', value: "desc" },
  ]);

  const applyFilters = () => {
    setAppliedFilters({
      openNow: openNow,
      distance: value1,
      foodReady: value2,
      rating: value3,
      price: value4,
      priceSort: value5,
      distanceSort: value6,
      durationSort: value7,
    });
    setIsExpanded(false);
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
    setAppliedFilters({
      openNow: false,
      distance: null,
      foodReady: null,
      rating: null,
      price: null,
      priceSort: null,
      distanceSort: null,
      durationSort: null,
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
    
    if (appliedFilters.openNow) {
      filters.push(<View key="openNow" style={styles.filterChip}><Text style={styles.filterChipText}>Open now</Text></View>);
    }
    if (appliedFilters.distance && appliedFilters.distance !== "any") {
      filters.push(<View key="distance" style={styles.filterChip}><Text style={styles.filterChipText}>Max distance: {getFilterLabel(items1, appliedFilters.distance)}</Text></View>);
    }
    if (appliedFilters.foodReady && appliedFilters.foodReady !== "any") {
      filters.push(<View key="foodReady" style={styles.filterChip}><Text style={styles.filterChipText}>Time for food preparation: {getFilterLabel(items2, appliedFilters.foodReady)}</Text></View>);
    }
    if (appliedFilters.rating && appliedFilters.rating !== "any") {
      filters.push(<View key="rating" style={styles.filterChip}><Text style={styles.filterChipText}>Rating: {getFilterLabel(items3, appliedFilters.rating)}</Text></View>);
    }
    if (appliedFilters.price && appliedFilters.price !== "any") {
      filters.push(<View key="price" style={styles.filterChip}><Text style={styles.filterChipText}>Price: {getFilterLabel(items4, appliedFilters.price)}</Text></View>);
    }
    if (appliedFilters.priceSort) {
      filters.push(<View key="priceSort" style={styles.filterChip}><Text style={styles.filterChipText}>Sort by price: {getFilterLabel(items5, appliedFilters.priceSort)}</Text></View>);
    }
    if (appliedFilters.distanceSort) {
      filters.push(<View key="distanceSort" style={styles.filterChip}><Text style={styles.filterChipText}>Sort by distance: {getFilterLabel(items6, appliedFilters.distanceSort)}</Text></View>);
    }
    if (appliedFilters.durationSort) {
      filters.push(<View key="durationSort" style={styles.filterChip}><Text style={styles.filterChipText}>Sort by food preparation time: {getFilterLabel(items7, appliedFilters.durationSort)}</Text></View>);
    }

    return filters.length > 0 ? (
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.appliedFiltersContainer}>
        {filters}
      </ScrollView>
    ) : null;
  };

  return (
    <SafeAreaView style={styles.sav}>
      <View style={styles.top_banner}>
        <Text style={styles.airport_text}>Foods at Toronto Pearson Intl.</Text>
        <Text style={styles.terminal_text}>Your location: terminal 1, gate 3</Text>
        
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
                <Text style={styles.dropdownLabel}>Price</Text>
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
          data={rest_list}
          keyExtractor={(item) => item.id}
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.restaurantList}
          renderItem={({ item }) => (
            <CreateRestaurantCard
              name={item.name}
              type={item.type}
              terminal={item.terminal}
              distance={item.distance}
              imagepath={item.imagepath}
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
      backgroundColor: "#F36D3B",
      textAlign: "left",
      paddingVertical: 10,
      paddingHorizontal: 15,
      gap: 2,
      zIndex: 10000,
      elevation: 10,
      borderBottomWidth: 2, 
      borderBottomColor: "#000000ff"
    },
    airport_text:{
        fontSize: 18,
        fontWeight: "bold",
        color: "#fff"
    },
    terminal_text:{
      fontSize: 14,
      color: "#fff"
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
      // paddingTop: 6
    },
    sortSection: {
      flexDirection: "row",
      alignItems: "flex-end",
      gap: 12
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
    }
})