const { getDefaultConfig } = require("@react-native/metro-config");

/**
 * Metro configuration. The Godot game itself ships as ios/LittleGiant64.pck
 * (bundled by Xcode), so Metro only serves the React Native host.
 * @type {import('@react-native/metro-config').MetroConfig}
 */
module.exports = getDefaultConfig(__dirname);
