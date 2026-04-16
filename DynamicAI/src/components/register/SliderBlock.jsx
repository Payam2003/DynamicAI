import { Box, Text } from "@chakra-ui/react";
import { useState } from "react";

export default function SliderBlock({ label, min_value = 0, max_value = 10, step = 1 }) {
  const [value, setValue] = useState(min_value);

  return (
    <Box>
      <Text fontWeight="medium" mb={2}>
        {label}
      </Text>

      <input
        type="range"
        min={min_value}
        max={max_value}
        step={step}
        value={value}
        onChange={(e) => setValue(Number(e.target.value))}
        style={{ width: "100%" }}
      />

      <Text mt={2} fontSize="sm" color="gray.600">
        Valore selezionato: {value}
      </Text>
    </Box>
  );
}