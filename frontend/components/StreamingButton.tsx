import React from "react";
import { Text, TouchableOpacity, StyleSheet } from "react-native";

interface StreamingButtonProps {
  isStreaming: boolean;
  onToggleStreaming: () => void;
}

const StreamingButton: React.FC<StreamingButtonProps> = ({ isStreaming, onToggleStreaming }) => {
  return (
    <TouchableOpacity onPress={onToggleStreaming} style={styles.button}>
      <Text style={styles.buttonText}>
        {isStreaming ? "ストリーミング停止" : "ストリーミング開始"}
      </Text>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: {
    padding: 10,
    backgroundColor: "#007bff",
    borderRadius: 5,
  },
  buttonText: {
    color: "white",
    fontSize: 16,
  },
});

export default StreamingButton;
