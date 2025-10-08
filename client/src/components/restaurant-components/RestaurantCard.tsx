import React from "react"
import { Text, View, Image, StyleSheet, Dimensions} from 'react-native'

const screen_width = Dimensions.get('screen').width

type RestaurantCard = {
    name?: string;                              // NAME OF RESTAURANT
    type?: string;                              // TYPE OF RESTAURANT
    terminal?: number;                          // THE LOCATION OF RESTAURANT
    distance?: number;                          // APPROX DISTANCE FROM THE CUSTOMER
    imagepath?: ReturnType<typeof require>;     // ENSURES ITS A PATH TO AN IMAGE AND NOT A LINK
};

const CreateRestaurantCard = ({ name, type, terminal, distance, imagepath}: RestaurantCard) => {
    return(
        <View style={styles.pane}>
            <Image source={imagepath} style={styles.image}/>
            <View style={styles.bottom_banner}>
                <View style={styles.bottom_bannerL}>
                    <Text style={styles.name}>{name}</Text>
                    <Text style={styles.type}>Category: {type}</Text>
                </View>
                <View style={styles.bottom_bannerR}>
                    <Text style={styles.name}>Terminal {terminal}, ({distance} km)</Text>
                </View>
            </View>
        </View>
    )
}

export default CreateRestaurantCard;

const styles = StyleSheet.create({
    pane: {
        width: 300,
        maxWidth: screen_width * 0.8,
        height: 300,
        maxHeight: screen_width * 0.8,
        borderRadius: 12,
        borderWidth: 1,
        borderColor: "#757573",
        overflow: "hidden",
        marginTop: 10,
        backgroundColor: "#fff"
    },
    image: {
        width: "100%",
        height: "85%",
        resizeMode: "cover",
    },
    name: {
        fontSize: 12,
        color: "#757573"
    },
    type: {
        fontSize: 10,
        color: "#757573"
    }, 
    bottom_banner:{
        flex: 1,
        flexDirection: 'row',
        height: 50,
        backgroundColor: "#fff",
        paddingVertical: 5,
        paddingHorizontal: 5,
        justifyContent: "space-between",
        alignItems: "center"
    },
    bottom_bannerL:{
        flex: 1,
        flexDirection: 'column',
        textAlign: "left",
    },
    bottom_bannerR:{
        flex: 1,
        flexDirection: 'column',
        alignItems: "flex-end",
    }
})