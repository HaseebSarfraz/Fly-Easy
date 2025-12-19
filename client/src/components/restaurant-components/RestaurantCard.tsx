import React from "react"
import { Text, View, Image, StyleSheet, Dimensions} from 'react-native'

const screen_width = Dimensions.get('screen').width

type RestaurantCard = {
    name?: string;          // NAME OF RESTAURANT
    terminal?: number;      // THE LOCATION OF RESTAURANT
    type?: string;          // TYPE OF RESTAURANT
    cuisine?: string;       // CUISINE SERVED TO
    restriction?: string;   // FOOD RESTRICTIONS RESTAURANT CATERS TO
    distance?: number;      // APPROX DISTANCE FROM THE CUSTOMER
    rating?: number;        // APPROXIMATE RATING
    price?: number;         // FOOD PRICE
    prep_time?: number;     // AVERAGE PREPARATION TIME
    open_time?: string;     // RESTAURANT'S CLOSING TIME
    close_time?: string;    // RESTAURANT'S CLOSING TIME
    open_now?: boolean;     // TO CHECK IF RESTAURANT IS OPEN NOW
    imagepath?: string;     // ENSURES ITS A PATH TO AN IMAGE AND NOT A LINK
};

const CreateRestaurantCard = ({ name, terminal, type, cuisine, restriction, distance, rating, price, prep_time, open_time, close_time, open_now, imagepath}: RestaurantCard) => {
    if (open_now){
        return(
        <View style={styles.pane}>
            <Image source={{ uri: imagepath}} style={styles.image}/>
            <View style={styles.bottom_banner}>
                <View style={styles.bottom_bannerL}>
                    <Text style={styles.name}>{name} ({rating}★)</Text>
                    <Text style={styles.type}>🍽️ {type}, 🌎 {cuisine}, <Text style={styles.restriction}>{restriction} ✓</Text></Text>
                    <Text style={styles.type}>📍 Terminal {terminal} ({distance} km)</Text>
                    <Text style={styles.open_now}>🕑 Open now, closes at {close_time}</Text>
                    <Text style={styles.type}>💲 Average price: ${price}</Text>
                    <Text style={styles.type}>⏳ Wait time: {prep_time} minutes</Text>
                </View>
            </View>
        </View>
        )
    }
    return(
        <View style={styles.pane}>
            <Image source={{ uri: imagepath}} style={styles.image}/>
            <View style={styles.bottom_banner}>
                <View style={styles.bottom_bannerL}>
                    <Text style={styles.name}>{name} ({rating}★)</Text>
                    <Text style={styles.type}>🍽️ {type}, 🌎 {cuisine}, <Text style={styles.restriction}>{restriction} ✓</Text></Text>
                    <Text style={styles.type}>📍 Terminal {terminal}, ({distance} km)</Text>
                    <Text style={styles.close_now}>🕑 Closed, opens at {open_time}</Text>
                    <Text style={styles.type}>💲 Average price: ${price}</Text>
                    <Text style={styles.type}>⏳ Wait time: {prep_time} minutes</Text>
                </View>
            </View>
        </View>
    )
}

export default CreateRestaurantCard;

const styles = StyleSheet.create({
    pane: {
        width: screen_width * 0.98,
        // maxWidth: 450,
        height: 180,
        borderRadius: 12,
        borderWidth: 1,
        borderColor: "#757573",
        overflow: "hidden",
        marginTop: 10,
        backgroundColor: "#fff",
        flexDirection: 'row',
        alignItems: 'center'
    },
    image: {
        width: 100,
        height: 100,
        resizeMode: "cover",
        borderRadius: 8,
        marginLeft: 10
    },
    name: {
        fontSize: 17,
        color: "#757573",
        textAlign: 'left',
        fontWeight: "bold"
    },
    type: {
        fontSize: 15,
        color: "#757573",
        textAlign: 'left'
    },
    restriction: {
        fontSize: 15,
        color: "#019b13ff",
        textAlign: 'left'
    },
    bottom_banner:{
        flex: 1,
        flexDirection: 'row',
        backgroundColor: "#fff",
        alignContent: "center",
        paddingHorizontal: 10
    },
    bottom_bannerL:{
        textAlign: "left",
        alignContent: "center",
        margin: 5
    },
    open_now:{
        fontSize: 15,
        color: "#019b13ff",
        fontWeight: "bold"
    },
    close_now: {
        fontSize: 15,
        color: "#b70000ff",
        fontWeight: "bold"
    }
})