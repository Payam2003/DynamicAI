import { Alert } from "@chakra-ui/react";

export default function AlertBlock({
  status = "info",
  title_text,
  description_text,
  label,
  text,
}) {
  const finalTitle = title_text || label || "Avviso";
  const finalDescription = description_text || text || "";

  return (
    <Alert.Root status={status} borderRadius="md">
      <Alert.Indicator />
      <Alert.Content>
        {finalTitle && <Alert.Title>{finalTitle}</Alert.Title>}
        {finalDescription && (
          <Alert.Description>{finalDescription}</Alert.Description>
        )}
      </Alert.Content>
    </Alert.Root>
  );
}