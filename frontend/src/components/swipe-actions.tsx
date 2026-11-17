import { View, Text, Pressable } from 'react-native';

type SwipeActionsProps = {
  onLike: () => void;
  onPass: () => void;
};

export default function SwipeActions({ onLike, onPass }: SwipeActionsProps) {
  return (
    <View style={{ flexDirection: 'row', justifyContent: 'space-around', marginTop: 20 }}>
      <Pressable onPress={onPass}>
        <Text>Pass</Text>
      </Pressable>
      <Pressable onPress={onLike}>
        <Text>Like</Text>
      </Pressable>
    </View>
  );
}