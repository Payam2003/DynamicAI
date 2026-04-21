import { Box, Button, Flex, Text } from "@chakra-ui/react";
import { useState } from "react";

export default function ButtonBlock({
  label,
  options = [],
  sectionId,
  onValueChange,
}) {
  const [selected, setSelected] = useState(null);

  return (
    <Box>
      <Text fontWeight="medium" mb={2}>
        {label}
      </Text>

      <Flex gap={2} wrap="wrap">
        {options.map((option) => (
          <Button
            key={option}
            variant={selected === option ? "solid" : "outline"}
            colorScheme="blue"
            size="sm"
            onClick={() => {
              setSelected(option);
              if (onValueChange) {
                onValueChange(sectionId, label, option);
              }
            }}
          >
            {option}
          </Button>
        ))}
      </Flex>
    </Box>
  );
}