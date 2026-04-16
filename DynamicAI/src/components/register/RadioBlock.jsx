import { Box, RadioGroup, Text, VStack } from "@chakra-ui/react";
import { useState } from "react";

export default function RadioBlock({ label, options = [] }) {
  const [value, setValue] = useState("");

  return (
    <Box>
      <Text fontWeight="medium" mb={2}>
        {label}
      </Text>

      <RadioGroup.Root value={value} onValueChange={(e) => setValue(e.value)}>
        <VStack align="stretch">
          {options.map((option) => (
            <RadioGroup.Item key={option} value={option}>
              <RadioGroup.ItemHiddenInput />
              <RadioGroup.ItemIndicator />
              <RadioGroup.ItemText>{option}</RadioGroup.ItemText>
            </RadioGroup.Item>
          ))}
        </VStack>
      </RadioGroup.Root>
    </Box>
  );
}