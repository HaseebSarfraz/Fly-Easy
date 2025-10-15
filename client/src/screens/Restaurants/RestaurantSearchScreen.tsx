import React, {useState} from "react";
import { SafeAreaView, Text, StyleSheet, View, TextInput, Pressable} from "react-native"
import DropDownPicker from "react-native-dropdown-picker"

const terminal = 1

// @ts-ignore
export default function HotelSearchScreen({ navigation }) {
    // Food Category dropdown
    const [open1, setOpen1] = useState(false);
    const [value1, setValue1] = useState(null);
    const [items1, setItems1] = useState([
        { label: 'Breakfast', value: "breakfast" },
        { label: 'Lunch', value: "lunch" },
        { label: 'Dinner', value: "dinner" },
        { label: 'Snacks/Fast Food', value: "snack, fast-food" },
        { label: 'Coffee &\nRefreshments', value: "coffee, refreshments" },
        { label: 'Alcoholic Beverages', value: "alcohol" }
    ]);

    // Dietary restrictions dropdown
    const [open2, setOpen2] = useState(false);
    const [value2, setValue2] = useState(null);
    const [items2, setItems2] = useState([
        { label: 'Vegan', value: "vegan" },
        { label: 'Vegetarian', value: "vegetarian" },
        { label: 'Halal', value: "halal" },
    ]);

    // Cuisine dropdown (NEW)
    const [open3, setOpen3] = useState(false);
    const [value3, setValue3] = useState(null);
    const [items3, setItems3] = useState([
        // Popular cuisines first
        { label: 'Italian', value: "italian" },
        { label: 'Chinese', value: "chinese" },
        { label: 'Japanese', value: "japanese" },
        { label: 'Mexican', value: "mexican" },
        { label: 'Indian', value: "indian" },
        { label: '---', value: "divider", disabled: true },
        // Alphabetically ordered
        { label: 'American', value: "american" },
        { label: 'French', value: "french" },
        { label: 'Greek', value: "greek" },
        { label: 'Korean', value: "korean" },
        { label: 'Mediterranean', value: "mediterranean" },
        { label: 'Middle Eastern', value: "middle-eastern" },
        { label: 'Thai', value: "thai" },
        { label: 'Vietnamese', value: "vietnamese" },
    ]);

    return (
        
        <SafeAreaView style={styles.safe}>

            <View style={styles.container}>

                <Text style={styles.header}>Find A Place To Eat</Text>
        
                <Text style={styles.label}>Your airport</Text>
                <TextInput style={[styles.label, styles.input]} placeholder="Airport"/>

                <Text style={styles.label}>Your terminal</Text>
                <TextInput style={[styles.label, styles.input]} placeholder="1"/>

                <View style={styles.dropdownsection}>
                    <View style={[styles.dropdownrow, {zIndex: 3000}]}>
                        <View style={styles.dropdownblock}>
                            <Text style={styles.label}>Food Category</Text>
                            <View style={styles.dropdown}>
                                <DropDownPicker
                                open={open1}
                                value={value1}
                                items={items1}
                                setOpen={setOpen1}
                                setValue={setValue1}
                                setItems={setItems1}
                                placeholder="Any"
                                zIndex={3000}
                                zIndexInverse={1000}
                                dropDownDirection="BOTTOM"
                            />
                            </View>
                        </View>
                        <View style={styles.dropdownblock}>
                            <Text style={styles.label}>Cuisine</Text>
                            <View style={styles.dropdown}>
                                <DropDownPicker
                                open={open3}
                                value={value3}
                                items={items3}
                                setOpen={setOpen3}
                                setValue={setValue3}
                                setItems={setItems3}
                                placeholder="Any"
                                searchable={true}
                                searchPlaceholder="Search cuisines..."
                                searchContainerStyle={{
                                    borderBottomColor: "#dfdfdf",
                                    paddingHorizontal: 10,
                                }}
                                searchTextInputStyle={{
                                    borderColor: "#dfdfdf",
                                    paddingHorizontal: 8,
                                }}
                                zIndex={2000}
                                zIndexInverse={2000}
                                dropDownDirection="BOTTOM"
                                />
                            </View>
                        </View>
                    </View>
                    <View style={[styles.dropdownrow, {zIndex: 1000}]}>
                        <View style={styles.dropdownblock}>
                            <Text style={styles.label}>Dietary restrictions</Text>
                            <View style={styles.dropdown}>
                                <DropDownPicker
                                open={open2}
                                value={value2}
                                items={items2}
                                setOpen={setOpen2}
                                setValue={setValue2}
                                setItems={setItems2}
                                placeholder="None"
                                zIndex={1000}
                                zIndexInverse={3000}
                                />
                            </View>
                        </View>
                        <View style={styles.buttoncontainer}>
                            <Pressable style={styles.button} onPress={() => navigation.navigate("RestaurantList")}>
                                <Text style={styles.buttonText}>Find Restaurants!</Text>
                            </Pressable>
                        </View>
                    </View>
                </View>
            </View>
        </SafeAreaView>
    );

}

const styles = StyleSheet.create({
    safe: {flex: 1, flexDirection: "column", backgroundColor: "#ffffffff"},
    container: {padding: 16}, 
    header: { fontSize: 28, fontWeight: "700", marginBottom: 12},
    label: {fontSize: 14, fontWeight: "600", marginBottom: 6},
    input: {
        height: 48,
        borderRadius: 12,
        borderWidth: 1,
        borderColor: "#090303ff",
        paddingHorizontal: 12,
        backgroundColor: "#fff",
        marginBottom: 14,
    },
    dropdownblock: {
        flex: 1,
        flexDirection: 'column',
        justifyContent: 'space-between'
    },
    dropdown: {
        minWidth: 120
    },
    dropdownsection: {
        flexDirection: "column",
        gap: 10,
        zIndex: 1,
    },
    dropdownrow: {
        flexDirection: "row",
        gap: 20,
    },
    button: {
        marginTop: 12,
        height: 48,
        borderRadius: 12,
        paddingHorizontal: 12, 
        paddingVertical: 10,
        backgroundColor: "#2F6BFF",
        justifyContent: "center",
        alignItems: "center"
    },
    buttonText: {
        color: "#fff",
        fontWeight: "600",
        fontSize: 16,
    },
    buttoncontainer: {
        flex: 1,
        justifyContent: 'flex-end',
    }
});