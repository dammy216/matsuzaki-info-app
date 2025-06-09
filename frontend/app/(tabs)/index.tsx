import CameraViewIndex from '@/components/MacchiCameraView/CameraViewIndex';
import MacchiCameraViewIndex from '@/components/MacchiCameraView/MacchiCameraViewIndex';
import { View } from 'react-native';

export default function CameraIndex() {
  return (
    <View style={{ flex: 1 }}>
      <CameraViewIndex />
    </View>
  );
}