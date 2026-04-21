import { Box, Card, Heading, Text, VStack } from "@chakra-ui/react";
import { RegistroComponenti } from "./RegistroComponenti.js";

function Workflow({ data, feedbackState, setFeedbackState }) {
  const updateSectionFeedback = (sectionId, label, value) => {
    setFeedbackState((prev) => ({
      ...prev,
      [sectionId]: {
        completed: true,
        updated_at: new Date().toISOString(),
        values: {
          ...(prev[sectionId]?.values || {}),
          [label]: value,
        },
      },
    }));
  };

  return (
    <VStack align="stretch" gap={5}>
      <Box>
        <Heading size="md">{data.title || "Generated Workflow UI"}</Heading>
        {data.summary && (
          <Text color="gray.600" mt={1}>
            {data.summary}
          </Text>
        )}
      </Box>

      {data.sections?.map((section) => (
        <Card.Root key={section.id} borderRadius="lg" boxShadow="xs">
          <Box p={4}>
            <VStack align="stretch" gap={4}>
              <Box>
                <Heading size="sm">{section.title}</Heading>
                {section.description && (
                  <Text mt={1} fontSize="sm" color="gray.600">
                    {section.description}
                  </Text>
                )}
              </Box>

              {section.components?.map((component, index) => {
                const ComponentToRender =
                  RegistroComponenti[component.component];

                if (!ComponentToRender) {
                  return (
                    <Box
                      key={`${section.id}-${index}`}
                      p={3}
                      borderRadius="md"
                      bg="red.50"
                      border="1px solid"
                      borderColor="red.200"
                    >
                      <Text fontSize="sm" color="red.700">
                        Unsupported component: {component.component}
                      </Text>
                    </Box>
                  );
                }

                return (
                  <ComponentToRender
                    key={`${section.id}-${index}`}
                    {...component}
                    sectionId={section.id}
                    onValueChange={updateSectionFeedback}
                  />
                );
              })}
            </VStack>
          </Box>
        </Card.Root>
      ))}
    </VStack>
  );
}

export default Workflow;