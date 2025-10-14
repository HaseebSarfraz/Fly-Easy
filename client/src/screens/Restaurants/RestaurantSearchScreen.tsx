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
        { label: 'coffee', value: "coffee" },
        { label: 'fast-food', value: "fast-food" },
        { label: 'international cuisine', value: "international cuisine" },
    ]);

    // Dietary restrictions dropdown
    const [open2, setOpen2] = useState(false);
    const [value2, setValue2] = useState(null);
    const [items2, setItems2] = useState([
        { label: 'vegan', value: "vegan" },
        { label: 'vegetarian', value: "vegetarian" },
        { label: 'halal', value: "halal" },
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
                            zIndex={2000}
                            zIndexInverse={2000}
                            />
                        </View>
                    </View>
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
                            <Text style={styles.buttonText}>Search</Text>
                        </Pressable>
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
        flexDirection: 'column',
        justifyContent: 'space-between'
    },
    dropdown: {
        flex: 1,
        minWidth: 120,
    },
    dropdownsection: {
        flexDirection: "row",
        gap: 20
    },
    button: {
        marginTop: 12,
        height: 48,
        borderRadius: 12,
        paddingHorizontal: 20, 
        paddingVertical: 10,
        backgroundColor: "#2F6BFF",
        justifyContent: "center",
        alignItems: "center"
    },
    buttonText: {
    color: "#fff",
    fontWeight: "700",
    fontSize: 16,
    },
    buttoncontainer: {
        flex: 1,
        marginTop: 12,
        maxWidth: 50
    }
});