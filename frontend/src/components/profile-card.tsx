
import { View, Text, StyleSheet, Image } from 'react-native';

type ProfileCardProps = {
  name: string;
  age: number;
  bio: string;
};
export default function ProfileCard(
    { name, age, bio }: ProfileCardProps
) {
   return(
    <View style={styles.card}>
      <Image
        source={require('@/assets/images/profile-placeholder.png')}
        style={styles.profileImage}
      />
      <Text style={styles.name}>{name}, {age}</Text>
      <Text style={styles.bio}>{bio}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
    card: {
        backgroundColor: '#fff',
        borderRadius: 10,
        padding: 20,
        margin: 10,
        shadowColor: '#000',
        shadowOffset: {
            width: 0,
            height: 2,
        },
        shadowOpacity: 0.25,
        shadowRadius: 3.84,
        elevation: 5,
    },
    profileImage: {
        width: 100,
        height: 100,
        borderRadius: 50,
        marginBottom: 10,
    },
    name: {
        fontSize: 24,
        fontWeight: 'bold',
        marginBottom: 5,
    },
    bio: {
        fontSize: 16,
        color: '#666',
    },
});

