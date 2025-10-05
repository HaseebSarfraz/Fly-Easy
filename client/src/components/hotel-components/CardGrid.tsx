// src/components/hotel-components/CardGrid.tsx
import React from 'react';
import { FlatList, View } from 'react-native';

type Props = {
  count?: number;        // how many boxes
  numColumns?: number;   // columns (default 2)
  gap?: number;          // spacing (default 12)
};

const CardGrid = ({ count = 8, numColumns = 2, gap = 12 }: Props) => {
  const items = Array.from({ length: count }, (_, i) => i);

  return (
    <FlatList
      data={items}
      keyExtractor={(i) => String(i)}
      numColumns={numColumns}
      showsVerticalScrollIndicator={false}
      columnWrapperStyle={{ gap }}
      contentContainerStyle={{ padding: gap }}
      renderItem={() => (
        <View style={{ flex: 1, marginBottom: gap }}>
          {/* placeholder card */}
          <View
            style={{
              height: 160,
              borderRadius: 12,
              backgroundColor: '#e5e5e5',
            }}
          />
        </View>
      )}
    />
  );
};

export default CardGrid;