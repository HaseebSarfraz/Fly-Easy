import React, {useState} from "react"
import { StyleSheet, SafeAreaView, Text, View, FlatList, Pressable} from 'react-native'
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
  // Open now toggle
  const [openNow, setOpenNow] = useState(false);

  // Distance dropdown
  const [open1, setOpen1] = useState(false);
  const [value1, setValue1] = useState(null);
  const [items1, setItems1] = useState([
    { label: 'Any distance', value: "any" },
    { label: 'Within 0.25 miles', value: "0.25" },
    { label: 'Within 0.5 miles', value: "0.5" },
    { label: 'Within 1 mile', value: "1" },
    { label: 'Within 2 miles', value: "2" },
  ]);

  // Food ready in dropdown
  const [open2, setOpen2] = useState(false);
  const [value2, setValue2] = useState(null);
  const [items2, setItems2] = useState([
    { label: 'Any time', value: "any" },
    { label: 'Within 10 min', value: "10" },
    { label: 'Within 15 min', value: "15" },
    { label: 'Within 20 min', value: "20" },
    { label: 'Within 30 min', value: "30" },
  ]);

  // Rating dropdown
  const [open3, setOpen3] = useState(false);
  const [value3, setValue3] = useState(null);
  const [items3, setItems3] = useState([
    { label: 'Any rating', value: "any" },
    { label: '4+ stars', value: "4" },
    { label: '3+ stars', value: "3" },
    { label: '2+ stars', value: "2" },
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
    { label: 'Price: Low to High', value: "asc" },
    { label: 'Price: High to Low', value: "desc" },
  ]);

  // Distance sort dropdown
  const [open6, setOpen6] = useState(false);
  const [value6, setValue6] = useState(null);
  const [items6, setItems6] = useState([
    { label: 'Distance: Nearest', value: "asc" },
    { label: 'Distance: Farthest', value: "desc" },
  ]);

  // Duration sort dropdown
  const [open7, setOpen7] = useState(false);
  const [value7, setValue7] = useState(null);
  const [items7, setItems7] = useState([
    { label: 'Duration: Fastest', value: "asc" },
    { label: 'Duration: Slowest', value: "desc" },
  ]);

  return (
    <SafeAreaView style={styles.sav}>
      <View style={styles.top_banner}>
        <Text style={styles.airport_text}>Foods at Toronto Pearson Intl.</Text>
        <Text style={styles.terminal_text}>Your location: terminal 1, gate 3</Text>
        
        <View style={[styles.filterSection, {zIndex: 5000}]}>
          <Pressable 
            style={[styles.openNowButton, openNow && styles.openNowButtonActive]} 
            onPress={() => setOpenNow(!openNow)}
          >
            <Text style={[styles.openNowText, openNow && styles.openNowTextActive]}>
              Open now
            </Text>
          </Pressable>

          <View style={styles.dropdownContainer}>
            <Text style={styles.dropdownLabel}>Distance</Text>
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

        <View style={[styles.sortSection, {zIndex: 1000}]}>
          <View style={styles.dropdownContainer}>
            <Text style={styles.dropdownLabel}>Price Sort</Text>
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
            <Text style={styles.dropdownLabel}>Distance Sort</Text>
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
            <Text style={styles.dropdownLabel}>Duration Sort</Text>
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
    filterSection: {
      flexDirection: "row",
      alignItems: "flex-end",
      gap: 12,
      paddingTop: 6,
    },
    sortSection: {
      flexDirection: "row",
      alignItems: "flex-end",
      gap: 12,
      paddingTop: 6
    },
    openNowButton: {
      height: 48,
      paddingHorizontal: 16,
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
    openNowText: {
      fontSize: 14,
      fontWeight: "500",
      color: "#333",
    },
    openNowTextActive: {
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
    }
})