import MacchiCameraView from '@/components/MacchiCameraView';
import { View } from 'react-native';

export default function CameraIndex() {
  return (
    <View style={{ flex: 1 }}>
      <MacchiCameraView />
    </View>
  );
}