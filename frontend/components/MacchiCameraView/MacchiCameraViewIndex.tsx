import React, { useRef, useState, useEffect } from "react";
import { CameraView, useCameraPermissions } from "expo-camera";
import { View, Text, StyleSheet, Image, TouchableOpacity } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { FontAwesome } from "@expo/vector-icons";
import { Audio } from 'expo-av';
import io from 'socket.io-client';
import * as FileSystem from 'expo-file-system';
import { Buffer } from 'buffer';
import CameraPermission from "./CameraPermission";
import AudioRecord from 'react-native-audio-record';

const socket = io('http://192.168.32.158:8080');

const MacchiCameraViewIndex = () => {
  const [permission, requestPermission] = useCameraPermissions();
  const [isRecording, setIsRecording] = useState(false);
  const [recordingData, setRecordingData] = useState<Audio.Recording | null>(null);
  const [jpegBase64, setJpegBase64] = useState<string | null>(null);

  const cameraRef = useRef<CameraView | null>(null);
  const cameraContainerRef = useRef(null);

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

  socket.on('connect', () => {
    console.log('🟢 接続成功');
  });

  const startRecord = async () => {
    setIsRecording(true);

    // セッションを開始
    socket.emit('start_session', {});

    // 画像を取得したらすぐ送信
    if (cameraRef.current) {
      const image = await cameraRef.current.takePictureAsync({ base64: true, imageType: 'jpg' });
      setJpegBase64(image?.base64 ?? null);
      if (image?.base64) {
        socket.emit('send_chunk', {
          mime_type: 'image/jpeg',
          data: image.base64,
        });
      }
    }

    // 録音開始 (BareならAudioRecordで)
    AudioRecord.start();
    // on('data', chunk => ... で随時チャンク送信)
    AudioRecord.on('data', data => {
      socket.emit('send_chunk', {
        mime_type: 'audio/pcm',
        data,
      });
    });
  };

  const stopRecord = async () => {
    setIsRecording(false);
    if (!recordingData) return;

    try {
      await recordingData.stopAndUnloadAsync();
      const audioData = recordingData.getURI();

      if (!audioData) return;

      const base64Data = await FileSystem.readAsStringAsync(audioData, { encoding: FileSystem.EncodingType.Base64, });
      const rawAudioData = Buffer.from(base64Data, "base64").slice(44);
      const pcmBase64 = rawAudioData.toString("base64");

      socket.emit('chat_test', { "realtime_input": [{ mime_type: 'audio/pcm', data: pcmBase64 }, { mime_type: 'image/jpeg', data: jpegBase64 }] }, (ack: any) => {
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

  socket.on('connect_error', (err) => {
    console.error('🔴 接続エラー:', err.message);
  });

  socket.on('disconnect', (reason) => {
    console.warn('⚠️ ソケットが切断されました:', reason);
  });


  if (!permission) return <Text>カメラの権限を確認中...</Text>;
  if (!permission.granted) return <CameraPermission requestPermission={requestPermission} />;

  return (
    <View style={styles.container} ref={cameraContainerRef} >
      <View style={styles.cameraContainer}>
        <CameraView style={styles.camera} ref={cameraRef} mode="picture" />
      </View>

      <TouchableOpacity
        style={styles.recordButton}
        onPress={isRecording ? stopRecord : startRecord}
      >
        <FontAwesome name="circle-thin" size={80} color={isRecording ? "red" : "white"} />
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    backgroundColor: 'black',
    alignItems: 'center',
  },
  cameraContainer: {
    width: '100%',
    aspectRatio: 1 / 1,
    position: 'absolute',
    top: 20,
  },
  camera: {
    flex: 1,
  },
  recordButton: {
    alignSelf: 'center',
    position: 'absolute',
    bottom: 40,
  },
});

export default MacchiCameraViewIndex;
