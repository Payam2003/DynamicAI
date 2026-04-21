import { Box, Checkbox, Text, VStack } from "@chakra-ui/react";
import { useState } from "react";

export default function ChecklistBlock({
  label,
  options = [],
  sectionId,
  onValueChange,
}) {
  const [selected, setSelected] = useState([]);

  const toggleOption = (option) => {
    const next = selected.includes(option)
      ? selected.filter((item) => item !== option)
      : [...selected, option];

    setSelected(next);

    if (onValueChange) {
      onValueChange(sectionId, label, next);
    }
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