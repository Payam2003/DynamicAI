import { Box, Text, Textarea } from "@chakra-ui/react";

export default function TextareaBlock({ label, placeholder = "" }) {
  return (
    <Box>
      <Text fontWeight="medium" mb={2}>
        {label}
      </Text>
      <Textarea placeholder={placeholder} />
    </Box>
  );
}