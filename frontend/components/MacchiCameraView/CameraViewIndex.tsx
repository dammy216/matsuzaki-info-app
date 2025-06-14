import React, { useEffect, useRef, useState } from "react";
import { View, Text, TouchableOpacity, StyleSheet, Alert } from "react-native";
import AudioRecord from "react-native-audio-record";
import { Camera, PhotoFile, useCameraDevice, useCameraPermission } from "react-native-vision-camera";
import io from "socket.io-client";
import { AudioSetting } from "./AudioSettings";
import * as FileSystem from 'expo-file-system';

const socket = io("http://192.168.32.158:8080");

const CameraViewIndex = () => {
  const { hasPermission, requestPermission } = useCameraPermission();
  const device = useCameraDevice('back');
  const cameraRef = useRef<Camera>(null);

  const [isRecording, setIsRecording] = useState(false);
  const imageIntervalRef = useRef<number | null>(null);

  // 権限チェック
  useEffect(() => {
    if (hasPermission === false) {
      requestPermission();
    }
    AudioRecord.init(AudioSetting);
  }, [hasPermission, requestPermission]);

  useEffect(() => {
    socket.on("gemini_text", (text) => {
      Alert.alert("AI応答", text);
    });
    return () => {
      socket.off("gemini_text");
    };
  }, []);

  // --- 音声＋画像ストリーミング開始 ---
  const startRecording = () => {
    setIsRecording(true);
    socket.emit("start_session", {});

    // 音声ストリーミング
    AudioRecord.start();
    AudioRecord.on("data", (data) => {
      socket.emit("send_audio_chunk", { mime_type: "audio/pcm", data, });
    });

    // 1秒ごとにカメラプレビューのJPEGフレームを送信
    imageIntervalRef.current = setInterval(() => {
      (async () => {
        try {
          const frame = (await cameraRef.current?.takePhoto({ enableShutterSound: false }));
          if (frame) {
            const base64Frame = await FileSystem.readAsStringAsync(frame.path, { encoding: FileSystem.EncodingType.Base64 });
            socket.emit("send_image_frame", { mime_type: "image/jpeg", data: base64Frame });
          }
        } catch (e) {
          console.error("画像送信エラー:", e);
        }
      })();
    }, 1000);
  };

  // --- ストリーミング停止 ---
  const stopRecording = () => {
    setIsRecording(false);
    AudioRecord.stop();
    socket.emit("end_session", {});
    if (imageIntervalRef.current) {
      clearInterval(imageIntervalRef.current);
      imageIntervalRef.current = null;
    }
  };

  if (!device || !hasPermission) {
    return <View style={styles.center}><Text>カメラ/マイク権限がありません</Text></View>;
  }

  return (
    <View style={styles.container}>
      <Camera
        ref={cameraRef}
        style={styles.camera}
        device={device}
        isActive={true}
        photo={true}
      />
      <View style={styles.buttonRow}>
        <TouchableOpacity
          style={[styles.button, { backgroundColor: isRecording ? "#f55" : "#2c2" }]}
          onPress={isRecording ? stopRecording : startRecording}
        >
          <Text style={styles.btnText}>{isRecording ? "Stop" : "Rec"}</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#111" },
  camera: { flex: 1 },
  center: { flex: 1, alignItems: "center", justifyContent: "center" },
  buttonRow: {
    flexDirection: "row",
    justifyContent: "center",
    marginBottom: 32,
    gap: 32,
  },
  button: {
    padding: 24,
    borderRadius: 100,
    backgroundColor: "#222",
    marginHorizontal: 16,
  },
  btnText: { fontSize: 24, color: "white" },
});

export default CameraViewIndex;
