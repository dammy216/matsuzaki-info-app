import React, { useRef, useState, useEffect } from "react";
import { CameraView, useCameraPermissions } from "expo-camera";
import { View, Text, StyleSheet, Image } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { useWebSocket } from "../hooks/useWebSocket";
import * as ImageManipulator from "expo-image-manipulator";
import StreamingButton from "./StreamingButton"; // 新しいコンポーネントをインポート

const ScanCameraView = () => {
  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef<CameraView | null>(null);
  const { sendMessage, messages } = useWebSocket("ws://192.168.32.176:9084"); // WebSocket接続
  const [isStreaming, setIsStreaming] = useState(false);

  useFocusEffect(
    React.useCallback(() => {
      if (cameraRef.current) cameraRef.current.resumePreview();
      return () => {
        if (cameraRef.current) cameraRef.current.pausePreview();
      };
    }, [])
  );

  useEffect(() => {
    if (!isStreaming) return;

    const interval = setInterval(() => {
      captureAndSendImage();
    }, 1000); // 1秒ごとに撮影 & 送信

    return () => clearInterval(interval);
  }, [isStreaming]);

  const captureAndSendImage = async () => {
    if (!cameraRef.current) return;

    try {
      const photo = await cameraRef.current.takePictureAsync();
      if(!photo) return;
      
      // 画像サイズを小さくして送信
      const resizedPhoto = await ImageManipulator.manipulateAsync(
        photo.uri,
        [{ resize: { width: 320, height: 240 } }], 
        { base64: true }
      );

      if (resizedPhoto.base64) {
        sendMessage({
          realtime_input: {
            media_chunks: [
              {
                mime_type: "image/jpeg",
                data: resizedPhoto.base64,
              },
            ],
          },
        });
      }
    } catch (error) {
      console.error("画像キャプチャエラー:", error);
    }
  };

  //ストリーミングオンオフ切り替え
  const toggleStreaming = () => {
    setIsStreaming(prevState => !prevState);
  };

  if (!permission) return <Text>カメラの権限を確認中...</Text>;

  if (!permission.granted) {
    return (
      <View style={styles.permissionContainer}>
        <Text>カメラのアクセスを許可してください</Text>
        <Text onPress={requestPermission} style={styles.permissionButton}>
          カメラを許可
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <CameraView style={styles.camera} ref={cameraRef} mode="picture" />
      {/* StreamingButton を使ってストリーミングの開始・停止 */}
      <StreamingButton isStreaming={isStreaming} onToggleStreaming={toggleStreaming} />
      <View style={styles.responseContainer}>
        {messages.map((msg, index) => (
          <Text key={index} style={styles.responseText}>{msg}</Text>
        ))}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: "center", justifyContent: "center" },
  camera: { width: "100%", height: "70%" },
  permissionContainer: { flex: 1, alignItems: "center", justifyContent: "center" },
  permissionButton: { color: "blue", marginTop: 10 },
  responseContainer: { marginTop: 20, padding: 10, backgroundColor: "#f1f1f1", borderRadius: 5 },
  responseText: { fontSize: 14 },
});

export default ScanCameraView;
