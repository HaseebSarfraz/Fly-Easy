import React, {useState} from "react";
import { SafeAreaView, Text, StyleSheet, View, TextInput, Button} from "react-native";
import DropDownPicker from "react-native-dropdown-picker"

const terminal = 1

export default function HotelSearchScreen() {
    // GPT-SUGGESTED CODE
    const [open1, setOpen1] = useState(false);
    const [value1, setValue1] = useState(null);
    const [items1, setItems1] = useState([
        { label: 'coffee', value: "coffee" },
        { label: 'fast-food', value: "fast-food" },
        { label: 'international cuisine', value: "international cuisine" },
    ]);

    const [open2, setOpen2] = useState(false);
    const [value2, setValue2] = useState(null);
    const [items2, setItems2] = useState([
        { label: 'vegan', value: "vegan" },
        { label: 'vegetarian', value: "vegetarian" },
        { label: 'halal', value: "halal" },
    ]);
    // END OF GPT-SUGGESTED CODE
    return (
        
        <SafeAreaView style={styles.safe}>

            <View style={styles.container}>

                <Text style={styles.header}>Find A Place To Eat</Text>

                <Text style={styles.label}>Your airport</Text>
                <TextInput style={[styles.label, styles.input]} placeholder="Airport"/>

                <Text style={styles.label}>Your terminal</Text>
                <TextInput style={[styles.label, styles.input]} placeholder="1"/>

                <View style={styles.dropdownsection}>
                <View style={styles.row}>
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
                    />
                </View>
                <View style={styles.dropdown}>
                    <Text style={styles.label}>Dietary restrictions</Text>
                        <DropDownPicker
                            open={open2}
                            value={value2}
                            items={items2}
                            setOpen={setOpen2}
                            setValue={setValue2}
                            setItems={setItems2}
                            placeholder="None"
                        />
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
    row: {
        flexDirection: 'column',
        justifyContent: 'space-between',
        gap: 10,
    },
    dropdown: {
        flex: 1,
        minWidth: 0,
    },
    dropdownsection: {
        flexDirection: "row"
    },
    button: {
    marginTop: 12,
    height: 48,
    borderRadius: 12,
    backgroundColor: "#2F6BFF",
    alignItems: "center",
    justifyContent: "center",
    },

    buttonText: {
    color: "#fff",
    fontWeight: "700",
    fontSize: 16,
    },

});