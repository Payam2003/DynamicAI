import { Box, Checkbox, Text, VStack } from "@chakra-ui/react";
import { useState } from "react";

export default function ChecklistBlock({ label, options = [] }) {
  const [selected, setSelected] = useState([]);

  const toggleOption = (option) => {
    setSelected((prev) =>
      prev.includes(option)
        ? prev.filter((item) => item !== option)
        : [...prev, option]
    );
  };

  return (
    <Box>
      <Text fontWeight="medium" mb={2}>
        {label}
      </Text>

      <VStack align="stretch" gap={2}>
        {options.map((option) => (
          <Checkbox.Root
            key={option}
            checked={selected.includes(option)}
            onCheckedChange={() => toggleOption(option)}
          >
            <Checkbox.HiddenInput />
            <Checkbox.Control />
            <Checkbox.Label>{option}</Checkbox.Label>
          </Checkbox.Root>
        ))}
      </VStack>
    </Box>
  );
}