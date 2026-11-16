
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import ProfileCard from '@/components/profile-card';
import { useState } from 'react';

export default function DiscoverScreen() {
  const [currentIndex, setCurrentIndex] = useState(0);

  function handleLike() {
  if (currentIndex < profiles.length) {
    setCurrentIndex(prev => prev + 1);
  }
}

  function handlePass() {
    if (currentIndex < profiles.length) {
      setCurrentIndex(prev => prev + 1);
    }
    
  }

  const profiles = [
  {
    id: 1,
    name: "John Doe",
    age: 23,
    bio: "Software Engineer | Tech Enthusiast"
  },
  {
    id: 2,
    name: "Jane Smith",
    age: 24,
    bio: "Loves hiking and traveling"
  },
  {
    id: 3,
    name: "Alex Johnson",
    age: 22,
    bio: "Photography enthusiast"
  }
];
if (currentIndex >= profiles.length) {

}
const currentProfile = profiles[currentIndex];

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Spark</Text>

        {currentProfile ? (
  <View>
    <ProfileCard
      name={currentProfile.name}
      age={currentProfile.age}
      bio={currentProfile.bio}
    />

    <Pressable onPress={handleLike}>
      <Text>Like</Text>
    </Pressable>

    <Pressable onPress={handlePass}>
      <Text>Pass</Text>
    </Pressable>
  </View>
) : (
  <Text>No more profiles available!</Text>
)}
    </View>  
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontSize: 40,
    fontWeight: 'bold',
    color: '#FF4D6D',
  },
 
});
