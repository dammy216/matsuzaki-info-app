import { Ionicons } from '@expo/vector-icons';
import { DarkTheme, DefaultTheme, ThemeProvider } from '@react-navigation/native';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import React from 'react';
import { View, Text, Image, TouchableOpacity, Linking, StyleSheet, Platform } from 'react-native';
import { Menu, MenuOption, MenuOptions, MenuTrigger, MenuProvider } from 'react-native-popup-menu';

export default function RootLayout() {


  return (
    <ThemeProvider value={DefaultTheme}>
      <MenuProvider>
        <Stack>
          <Stack.Screen name="(tabs)" options={{
            headerShown: true,
            headerStyle: { backgroundColor: 'white' },
            headerTitle: () => (
              <View style={headerStyle.headerTitleContainer}>
                <Text style={headerStyle.headerTitle}>松崎町観光案内アプリ</Text>
                <Image
                  source={require('../assets/images/matsu-char2.jpg')}
                  style={headerStyle.headerLeftImage}
                />
              </View>
            ),
            headerRight: () => (
              <Menu>
                <MenuTrigger customStyles={{ TriggerTouchableComponent: TouchableOpacity, triggerWrapper: headerStyle.controlButton }}>
                  <Image
                    source={require('../assets/images/Emblem_of_Matsuzaki,_Shizuoka.svg.png')}
                    style={headerStyle.headerRightImage}
                  />
                </MenuTrigger>
                <MenuOptions optionsContainerStyle={headerStyle.optionsContainer}>
                  <MenuOption onSelect={() => Linking.openURL('https://www.town.matsuzaki.shizuoka.jp/')}>
                    <Text>松崎町HP</Text>
                  </MenuOption>
                  <MenuOption onSelect={() => Linking.openURL('https://izumatsuzakinet.com/')}>
                    <Text>観光</Text>
                  </MenuOption>
                  <MenuOption onSelect={() => Linking.openURL('https://www.town.matsuzaki.shizuoka.jp/docs/2018030100018/')}>
                    <Text>まっちーについて</Text>
                  </MenuOption>
                </MenuOptions>
              </Menu>
            ),
          }} />
        </Stack>
        <StatusBar style="auto" />
      </MenuProvider>
    </ThemeProvider>
  );
}

const headerStyle = StyleSheet.create({
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
});
