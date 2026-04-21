import { Box, Text } from "@chakra-ui/react";

export default function InfoCardBlock({
  label,
  text,
  title_text,
  description_text,
}) {
  const finalLabel = label || title_text || "Informazione";
  const finalText =
    text || description_text || "Nessuna informazione aggiuntiva disponibile.";

  return (
    <Box
      p={4}
      border="1px solid"
      borderColor="gray.200"
      borderRadius="md"
      bg="gray.50"
    >
      <Text fontWeight="bold" mb={2}>
        {finalLabel}
      </Text>
      <Text>{finalText}</Text>
    </Box>
  );
}