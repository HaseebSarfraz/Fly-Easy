import React from "react"
import { StyleSheet, SafeAreaView, Text, View, Dimensions, FlatList} from 'react-native'
import CreateRestaurantCard from '../components/restaurant-components/RestaurantCard'

const rest_list = [
                  { id: "1",
                    name: "McDonald's",
                    terminal: 1,
                    type: "Fast food",
                    distance: 0.3,
                    imagepath: require('../../assets/McDonalds-Logo.jpg')
                  },
                  {
                    id: "2",
                    name: "McDonald's",
                    terminal: 3,
                    type: "Fast food",
                    distance: 1.0,
                    imagepath: require('../../assets/McDonalds-Logo.jpg')
                  }];

export default function RestaurantListScreen() {
  return (
    <SafeAreaView style={styles.sav}>
      <View style={styles.top_banner}>
        <Text style={styles.airport_text}>Foods at Toronto Pearson Intl.</Text>
        <Text style={styles.terminal_text}>Your location: terminal 1, gate</Text>
      </View>
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
      paddingHorizontal: 5,
      gap: 2
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
    restaurantList: {
      gap: 10,
      alignItems: "center"
    }
})