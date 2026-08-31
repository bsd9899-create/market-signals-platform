import { Ionicons } from '@expo/vector-icons';
import { Tabs, useRouter } from 'expo-router';
import { Pressable, StyleSheet, View } from 'react-native';
import { colors } from '@/src/design-system';
import { spacing } from '@/src/design-system/spacing';

type IconName = keyof typeof Ionicons.glyphMap;

function TabIcon({ name, focused }: { name: IconName; focused: boolean }) {
  return <Ionicons name={name} size={24} color={focused ? colors.primary : colors.textSecondary} />;
}

/** زر "+" الأوسط — لا يفتح تبويبًا، بل يفتح شاشة الإضافة السريعة كـ Modal. */
function QuickAddButton() {
  const router = useRouter();
  return (
    <View style={styles.quickAddSlot}>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="إضافة سريعة"
        style={styles.quickAddButton}
        onPress={() => router.push('/quick-add')}
      >
        <Ionicons name="add" size={28} color={colors.onPrimary} />
      </Pressable>
    </View>
  );
}

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textSecondary,
        tabBarStyle: styles.tabBar,
        tabBarLabelStyle: styles.tabBarLabel,
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'اليوم',
          tabBarIcon: ({ focused }) => <TabIcon name={focused ? 'sunny' : 'sunny-outline'} focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="progress"
        options={{
          title: 'تقدمي',
          tabBarIcon: ({ focused }) => (
            <TabIcon name={focused ? 'trending-up' : 'trending-up-outline'} focused={focused} />
          ),
        }}
      />
      <Tabs.Screen
        name="add"
        options={{
          title: '',
          tabBarButton: () => <QuickAddButton />,
        }}
        listeners={{
          tabPress: (e) => e.preventDefault(),
        }}
      />
      <Tabs.Screen
        name="teams"
        options={{
          title: 'الفرق',
          tabBarIcon: ({ focused }) => (
            <TabIcon name={focused ? 'people' : 'people-outline'} focused={focused} />
          ),
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'حسابي',
          tabBarIcon: ({ focused }) => (
            <TabIcon name={focused ? 'person' : 'person-outline'} focused={focused} />
          ),
        }}
      />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  tabBar: {
    backgroundColor: colors.surface,
    borderTopColor: colors.divider,
    height: 64,
    paddingBottom: spacing.xs,
    paddingTop: spacing.xs,
  },
  tabBarLabel: {
    fontFamily: 'Tajawal_500Medium',
    fontSize: 11,
  },
  quickAddSlot: {
    flex: 1,
    top: -18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  quickAddButton: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: colors.primary,
    shadowOpacity: 0.3,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 4 },
    elevation: 4,
  },
});
