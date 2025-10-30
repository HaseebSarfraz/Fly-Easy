// restaurantsearchscreen.tsx
import React, {useState} from "react";
import { Text, StyleSheet, View, TextInput, Pressable} from "react-native"
import { SafeAreaView } from "react-native-safe-area-context"
import DropDownPicker from "react-native-dropdown-picker"
import airports from "../../backend/data/airport_codes.json";

// @ts-ignore
export default function RestaurantSearchScreen({ navigation }) {
    // To store the airport search info
    const [iata, setIATA] = useState("");
    const [terminal, setTerminal] = useState("");

    // Food Category dropdown
    const [fc_open, set_fc_open] = useState(false);
    const [fc_value, set_fc_value] = useState(null);
    const [fc_items, set_fc_items] = useState([
        { label: 'Any', value: "any" },
        { label: 'Breakfast', value: "breakfast" },
        { label: 'Lunch', value: "lunch" },
        { label: 'Dinner', value: "dinner" },
        { label: 'Fast Food', value: "fast-food" },
        { label: 'Coffee', value: "coffee" },
        { label: 'Alcoholic Beverages', value: "alcohol" }
    ]);

    // Dietary restrictions dropdown
    const [dr_open, set_dr_open] = useState(false);
    const [dr_value, set_dr_value] = useState(null);
    const [dr_items, set_dr_items] = useState([
        { label: "None", value: "none" },
        { label: 'Vegan', value: "vegan" },
        { label: 'Vegetarian', value: "vegetarian" },
        { label: 'Halal', value: "halal" },
    ]);

    // Cuisine dropdown (NEW)
    const [cs_open, set_cs_open] = useState(false);
    const [cs_value, set_cs_value] = useState(null);
    const [cs_items, set_cs_items] = useState([
        // Popular cuisines first
        { label: 'Italian', value: "italian" },
        { label: 'Chinese', value: "chinese" },
        { label: 'Japanese', value: "japanese" },
        { label: 'Mexican', value: "mexican" },
        { label: 'Indian', value: "indian" },
        { label: '---', value: "any", disabled: true },
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
                <TextInput style={[styles.label, styles.input]} value={iata} onChangeText={setIATA} placeholder="IATA code (example: 'YYZ' for Toronto Pearson Intl.)"/>

                <Text style={styles.label}>Your terminal</Text>
                <TextInput style={[styles.label, styles.input]} value={terminal} onChangeText={setTerminal} placeholder="1"/>

                <View style={styles.dropdownsection}>
                    <View style={[styles.dropdownrow, {zIndex: 3000}]}>
                        <View style={styles.dropdownblock}>
                            <Text style={styles.label}>Food Category</Text>
                            <View style={styles.dropdown}>
                                <DropDownPicker
                                open={fc_open}
                                value={fc_value}
                                items={fc_items}
                                setOpen={set_fc_open}
                                setValue={set_fc_value}
                                setItems={set_fc_items}
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
                                open={cs_open}
                                value={cs_value}
                                items={cs_items}
                                setOpen={set_cs_open}
                                setValue={set_cs_value}
                                setItems={set_cs_items}
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
                                open={dr_open}
                                value={dr_value}
                                items={dr_items}
                                setOpen={set_dr_open}
                                setValue={set_dr_value}
                                setItems={set_dr_items}
                                placeholder="None"
                                zIndex={1000}
                                zIndexInverse={3000}
                                />
                            </View>
                        </View>
                        <View style={styles.buttoncontainer}>
                            <Pressable style={styles.button} onPress={() => {
                                const airport = airports.find(a => a.iata === iata.toUpperCase());
                                navigation.navigate("RestaurantList", {iata: iata, airport: airport?.name, terminal: terminal, food_category: fc_value, cuisine: cs_value, dietary_restriction: dr_value})
                                }}>
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
