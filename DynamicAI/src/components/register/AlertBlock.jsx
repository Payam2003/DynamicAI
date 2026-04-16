import { Alert } from "@chakra-ui/react";

export default function AlertBlock({ status = "info", title, description }) {
  return (
    <Alert.Root status={status} borderRadius="md">
      <Alert.Indicator />
      <Alert.Content>
        <Alert.Title>{title}</Alert.Title>
        {description && <Alert.Description>{description}</Alert.Description>}
      </Alert.Content>
    </Alert.Root>
  );
}