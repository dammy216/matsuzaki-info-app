import React, { useRef, useState, useEffect } from "react";
import { CameraView, useCameraPermissions } from "expo-camera";
import { View, Text, StyleSheet, Image, TouchableOpacity } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { FontAwesome } from "@expo/vector-icons";
import { Audio } from 'expo-av';
import io from 'socket.io-client';
import * as FileSystem from 'expo-file-system';
import { Buffer } from 'buffer';
import { recordingOptions } from "@/components/MacchiCameraView/AudioSettings";
import CameraPermission from "./CameraPermission";


const socket = io('http://192.168.32.176:8080');

const MacchiCameraViewIndex = () => {
  const [permission, requestPermission] = useCameraPermissions();
  const [isRecording, setIsRecording] = useState(false);
  const [recordingData, setRecordingData] = useState<Audio.Recording | null>(null);

  const cameraRef = useRef<CameraView | null>(null);

  useEffect(() => {
    const setAudioMode = async () => {
      try {
        await Audio.setAudioModeAsync({
          allowsRecordingIOS: true,  // 録音を許可
          playsInSilentModeIOS: true,  // マナーモードでも録音できるようにする
        });
      } catch (error) {
        console.error('Audio mode error: ', error);
      }
    };

    setAudioMode();
  }, []);

  useFocusEffect(
    React.useCallback(() => {
      if (cameraRef.current) cameraRef.current.resumePreview();
      return () => {
        if (cameraRef.current) cameraRef.current.pausePreview();
      };
    }, [])
  );

  const startRecord = async () => {
    setIsRecording(true);

    try {
      const { status } = await Audio.requestPermissionsAsync();

      if (status !== 'granted') {
        alert('マイクへのアクセスを許可してください');
        setIsRecording(false);
        return;
      }

      const newRecording = new Audio.Recording();
      await newRecording.prepareToRecordAsync(recordingOptions);
      await newRecording.startAsync();
      setRecordingData(newRecording);

    } catch (err) {
      console.error('録音開始エラー:', err);
      setIsRecording(false);
    }
  };

  const stopRecord = async () => {
    setIsRecording(false);
    if (!recordingData) return;

    try {
      await recordingData.stopAndUnloadAsync();
      const audioData = recordingData.getURI();

      if (!audioData) return;

      const base64Data = await FileSystem.readAsStringAsync(audioData, {encoding: FileSystem.EncodingType.Base64,});
      const rawAudioData = Buffer.from(base64Data, "base64").slice(44);
      const pcmBase64 = rawAudioData.toString("base64");

      socket.emit('chatTest', { "realtime_input": [{ mime_type: 'audio/pcm', data: pcmBase64 }] }, (ack: any) => {
        if (ack?.success) {
          console.log('レスポンスがありました');
        } else {
          console.error('レスポンスがありませんでした:', ack?.error);
        }
        setRecordingData(null);
      });

    } catch (err) {
      console.error('録音停止エラー:', err);
    }
  };

  if (!permission) return <Text>カメラの権限を確認中...</Text>;
  if (!permission.granted) return <CameraPermission requestPermission={requestPermission} />;

  return (
    <View style={{ flex: 1 }}>
      <CameraView style={{ flex: 1 }} ref={cameraRef} mode="picture" />
      <TouchableOpacity style={styles.recordButton} onPress={isRecording ? stopRecord : startRecord}>
        <FontAwesome name="circle-thin" size={80} color={isRecording ? "red" : "white"} />
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  recordButton: {
    flex: 0,
    alignSelf: "center",
    position: "absolute",
    bottom: 64,
  },
});

export default MacchiCameraViewIndex;
