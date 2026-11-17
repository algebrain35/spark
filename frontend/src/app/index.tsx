
import { View, Text, StyleSheet} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import SwipeDeck from '@/components/swipe-deck';

export default function DiscoverScreen() {

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


  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Spark</Text>

        <SwipeDeck profiles={profiles} />
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
