import { Box, NativeSelect, Text } from "@chakra-ui/react";

export default function SelectBlock({
  label,
  options = [],
  sectionId,
  onValueChange,
}) {
  return (
    <Box>
      <Text fontWeight="medium" mb={2}>
        {label}
      </Text>

      <NativeSelect.Root>
        <NativeSelect.Field
          placeholder="Seleziona un'opzione"
          onChange={(e) => {
            if (onValueChange) {
              onValueChange(sectionId, label, e.target.value);
            }
          }}
        >
          {options.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </NativeSelect.Field>
        <NativeSelect.Indicator />
      </NativeSelect.Root>
    </Box>
  );
}