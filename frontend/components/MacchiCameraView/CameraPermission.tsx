import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";

type Props = {
  requestPermission: () => void;
};

const CameraPermission = (props:Props) => (
  <View style={styles.container}>
    <Text>カメラのアクセスを許可してください</Text>
    <TouchableOpacity onPress={props.requestPermission}>
      <Text style={styles.button}>カメラを許可</Text>
    </TouchableOpacity>
  </View>
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  button: {
    color: "blue",
    marginTop: 10,
  },
});

export default CameraPermission;
