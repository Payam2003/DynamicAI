import { Box, Text } from "@chakra-ui/react";

export default function InfoCardBlock({ label, text }) {
  return (
    <Box p={4} border="1px solid" borderColor="gray.200" borderRadius="md" bg="gray.50">
      {label && (
        <Text fontWeight="bold" mb={2}>
          {label}
        </Text>
      )}
      <Text>{text}</Text>
    </Box>
  );
}