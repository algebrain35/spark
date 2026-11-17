import { useState } from 'react';
import { View, Text} from 'react-native';
import ProfileCard from '@/components/profile-card';
import SwipeActions from '@/components/swipe-actions';
import { scheduleOnRN } from 'react-native-worklets';
import {
  usePanGesture,
  GestureDetector,
} from 'react-native-gesture-handler';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming
} from 'react-native-reanimated';
const SWIPE_THRESHOLD = 100;

type Profile = {
  id: number;
  name: string;
  age: number;
  bio: string;
};

type SwipeDeckProps = {
  profiles: Profile[];
};

export default function SwipeDeck({ profiles }: SwipeDeckProps) {
    const [currentIndex, setCurrentIndex] = useState(0);
    
    function nextProfile() {
  setCurrentIndex(prev =>
    prev < profiles.length ? prev + 1 : prev
  );
}

 function handleLike() {
  console.log("Liked:", profiles[currentIndex]?.name);
  nextProfile();
}

  function handlePass() {
    console.log("Passed:", profiles[currentIndex]?.name);
    nextProfile();
 }

  const currentProfile = profiles[currentIndex];
  const translateX = useSharedValue(0);

 const panGesture = usePanGesture({
  onUpdate: (event) => {
    translateX.value = event.translationX;
  },
   onDeactivate: () => {
    if (translateX.value > SWIPE_THRESHOLD) {
  translateX.value = withTiming(500, { duration: 250 }, (finished) => {
  if (finished) {
    translateX.value = 0;
    scheduleOnRN(handleLike);
  }
});
  
} else if (translateX.value < -SWIPE_THRESHOLD) {
  translateX.value = withTiming(-500, { duration: 250 }, (finished) => {
  if (finished) {
    translateX.value = 0;
    scheduleOnRN(handlePass);
  }
});
} else {
  translateX.value = withSpring(0);
}
  },
});

const animatedStyle = useAnimatedStyle(() => {
  return {
    transform: [
      { translateX: translateX.value }
    ],
  };
});
  return (
     currentProfile ? (
  <View>
    <GestureDetector gesture={panGesture}>
        <Animated.View style={[animatedStyle]}>
      <ProfileCard
        name={currentProfile.name}
        age={currentProfile.age}
        bio={currentProfile.bio}
      />
      </Animated.View>
    </GestureDetector>

    <SwipeActions onLike={handleLike} onPass={handlePass} />
  </View>
) : (
  <Text>No more profiles available!</Text>
)
   
  )
}

 

