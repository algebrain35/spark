import { useState, useEffect } from 'react';
import { View, Text} from 'react-native';
import ProfileCard from '@/components/profile-card';
import SwipeActions from '@/components/swipe-actions';
import { scheduleOnRN, scheduleOnUI } from 'react-native-worklets';
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
    const currentProfile = profiles[currentIndex];
    const translateX = useSharedValue(0);
    const isAnimating = useSharedValue(false);
    
    function nextProfile() {
  setCurrentIndex(prev =>
    prev < profiles.length ? prev + 1 : prev
  );
}

useEffect(() => {
  isAnimating.value = false;
}, [currentIndex]);

 function handleLike() {
  console.log("Liked:", profiles[currentIndex]?.name);
  nextProfile();
}

  function handlePass() {
    console.log("Passed:", profiles[currentIndex]?.name);
    nextProfile();
 }

 const animateSwipe = (direction: 'like' | 'pass') => {
  'worklet';

  if (isAnimating.value) {
    return;
  }

  isAnimating.value = true;

  const destination = direction === 'like' ? 500 : -500;

  translateX.value = withTiming(destination, { duration: 250 }, (finished) => {
  if (finished) {
    translateX.value = 0;

    if (direction === 'like') {
      scheduleOnRN(handleLike);
    } else {
      scheduleOnRN(handlePass);
    }
  } else {
    isAnimating.value = false;
    translateX.value = 0;
  }
});
};

  

 const panGesture = usePanGesture({
  onUpdate: (event) => {
    if (isAnimating.value){
      return;
    }
    translateX.value = event.translationX;
  },
   onDeactivate: () => {
    if (isAnimating.value) {
      return;
    }
    if (translateX.value > SWIPE_THRESHOLD) {
      animateSwipe('like');
  
} else if (translateX.value < -SWIPE_THRESHOLD) {
  animateSwipe('pass');

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

    <SwipeActions onLike={() => scheduleOnUI(animateSwipe, 'like')} onPass={() => scheduleOnUI(animateSwipe, 'pass')} />
  </View>
) : (
  <Text>No more profiles available!</Text>
)
   
  )
}

 

