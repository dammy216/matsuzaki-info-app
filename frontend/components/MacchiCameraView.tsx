import React, { useRef, useState } from "react";
import { CameraView, useCameraPermissions } from "expo-camera";
import { TouchableOpacity, Text, View, StyleSheet, Button } from "react-native";
import { useFocusEffect } from "@react-navigation/native";

const ScanCameraView = () => {
  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef<CameraView | null>(null);

  useFocusEffect(
    React.useCallback(() => {
      // カメラを起動
      if (cameraRef.current) {
        cameraRef.current.resumePreview();
      }
      // カメラを停止
      return () => {
        if (cameraRef.current) {
          cameraRef.current.pausePreview();
        }
      };
    }, [])
  );

  // カメラの許可をリクエスト
  if (!permission) {
    return <Text>読み込み中...</Text>;
  }

  // カメラの権限付与をリクエスト
  if (!permission.granted) {
    return (
      <View style={{ flex: 1, justifyContent: "center" }}>
        <Button onPress={requestPermission} title="カメラを起動" />
      </View>
    );
  }

  // 編集画面を表示するか、通常のカメラ画面を表示する
  return (
    <View style={{ flex: 1 }}>
      <CameraView style={{ flex: 1 }} ref={cameraRef} mode="video">
      </CameraView>
    </View>
  );
};

export default ScanCameraView;
