import { Platform, StyleSheet } from 'react-native';

export const headerStyle = StyleSheet.create({
  headerTitleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 20,
    marginRight: 8,
  },
  headerLeftImage: {
    width: 32,
    height: 32,
  },
  headerRightImage: {
    width: 30,
    height: 30,
  },
  controlButton: {
    alignSelf: 'flex-end',
    marginRight: Platform.OS === 'web' ? 24 : 0,
  },
  optionsContainer: {
    marginTop: 40,
    borderRadius: 8,
    shadowColor: "#000",
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
    width: 136,
  },
})