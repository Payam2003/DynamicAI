import { Textarea, Text, VStack } from "@chakra-ui/react";

function TextareaBlock({ label, placeholder, sectionId, onValueChange }) {
  return (
    <VStack align="stretch" gap={2}>
      {label && (
        <Text fontSize="sm" fontWeight="medium" color="gray.700">
          {label}
        </Text>
      )}

      <Textarea
        placeholder={placeholder || "Scrivi qui..."}
        resize="vertical"
        minH="120px"
        bg="white"
        borderColor="#d8e4ff"
        _hover={{ borderColor: "#b8ccff" }}
        _focusVisible={{
          borderColor: "#3d7bfd",
          boxShadow: "0 0 0 1px #3d7bfd",
        }}
        onChange={(e) => onValueChange(sectionId, label, e.target.value)}
      />
    </VStack>
  );
}

export default TextareaBlock;