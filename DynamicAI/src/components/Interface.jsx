import { useEffect, useState } from "react";
import {
  Box,
  Button,
  Card,
  Flex,
  Heading,
  Image,
  Spinner,
  Text,
  VStack,
  Alert,
  FileUpload,
} from "@chakra-ui/react";
import Workflow from "../components/Workflow.jsx";

function Interface() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [generatedUI, setGeneratedUI] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorText, setErrorText] = useState("");

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const handleAcceptedFiles = (details) => {
    const file = details.files?.[0];
    if (!file) return;

    setSelectedFile(file);
    setGeneratedUI(null);
    setErrorText("");

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }

    if (file.type.startsWith("image/")) {
      setPreviewUrl(URL.createObjectURL(file));
    } else {
      setPreviewUrl(null);
    }
  };

  const handleRejectedFiles = () => {
    setSelectedFile(null);
    setGeneratedUI(null);

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }

    setErrorText("File non valido. Carica un'immagine o un file supportato.");
  };

  const handleGenerate = async () => {
    if (!selectedFile) {
      setErrorText("Carica prima un'immagine o un file.");
      return;
    }

    setLoading(true);
    setErrorText("");
    setGeneratedUI(null);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const res = await fetch("/api/workflow-ui/generate", {
        method: "POST",
        body: formData,
      });

      let data = null;
      try {
        data = await res.json();
      } catch {
        data = null;
      }

      if (!res.ok) {
        throw new Error(
          data?.detail ||
            data?.error ||
            "Errore durante la generazione dell'interfaccia."
        );
      }

      setGeneratedUI(data);
    } catch (err) {
      console.error(err);
      setErrorText(err.message || "Qualcosa è andato storto.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box minH="100vh" bg="#eef4ff" p={6}>
      <VStack align="stretch" gap={6}>
        <Box>
          <Heading size="lg" color="#1f3b73">
            Dynamic Workflow UI Generator
          </Heading>
          <Text color="#5b6b88" mt={2}>
            Carica un'immagine e genera un'interfaccia dinamica orientata al task.
          </Text>
        </Box>

        <Flex direction={{ base: "column", xl: "row" }} gap={6} align="stretch">
          <Card.Root
            flex="1"
            borderRadius="2xl"
            bg="white"
            border="1px solid"
            borderColor="#d8e4ff"
            boxShadow="0 8px 24px rgba(31, 59, 115, 0.08)"
          >
            <Card.Body>
              <VStack align="stretch" gap={4}>
                <Heading size="md" color="#1f3b73">
                  Input
                </Heading>

                <FileUpload.Root
                  accept={{
                    "image/png": [".png"],
                    "image/jpeg": [".jpg", ".jpeg"],
                    "image/webp": [".webp"],
                    "application/pdf": [".pdf"],
                    "text/plain": [".txt"],
                  }}
                  maxFiles={1}
                  maxFileSize={10 * 1024 * 1024}
                  onFileAccept={handleAcceptedFiles}
                  onFileReject={handleRejectedFiles}
                >
                  <FileUpload.HiddenInput />

                  <FileUpload.Dropzone
                    width="100%"
                    p={8}
                    border="2px dashed"
                    borderColor="#b8ccff"
                    borderRadius="xl"
                    bg="#f7faff"
                    transition="all 0.2s ease"
                    _hover={{
                      borderColor: "#6f9cff",
                      bg: "#edf4ff",
                    }}
                  >
                    <VStack gap={2}>
                      <Text fontWeight="semibold" color="#1f3b73">
                        Trascina o clicca il file per caricarlo qui
                      </Text>
                      <Text fontSize="sm" color="#6b7a96">
                        PNG, JPG, WEBP, PDF o TXT fino a 10 MB
                      </Text>
                    </VStack>
                  </FileUpload.Dropzone>

                  <FileUpload.List />
                </FileUpload.Root>

                {selectedFile && (
                  <Text fontSize="sm" color="#4e5d78">
                    File selezionato: {selectedFile.name}
                  </Text>
                )}

                {previewUrl && (
                  <Image
                    src={previewUrl}
                    alt="Anteprima"
                    borderRadius="lg"
                    objectFit="cover"
                    maxH="360px"
                    border="1px solid"
                    borderColor="#d8e4ff"
                  />
                )}

                <Button
                  bg="#3d7bfd"
                  color="white"
                  _hover={{ bg: "#2f6ae6" }}
                  onClick={handleGenerate}
                  disabled={!selectedFile || loading}
                >
                  {loading ? "Generazione..." : "Genera interfaccia"}
                </Button>

                {errorText && (
                  <Alert.Root
                    status="error"
                    borderRadius="md"
                    bg="#fff1f1"
                    border="1px solid"
                    borderColor="#ffc9c9"
                  >
                    <Alert.Indicator />
                    <Alert.Content>
                      <Alert.Title fontSize="sm">{errorText}</Alert.Title>
                    </Alert.Content>
                  </Alert.Root>
                )}
              </VStack>
            </Card.Body>
          </Card.Root>

          <Card.Root
            flex="1.4"
            borderRadius="2xl"
            bg="white"
            border="1px solid"
            borderColor="#d8e4ff"
            boxShadow="0 8px 24px rgba(31, 59, 115, 0.08)"
          >
            <Card.Body>
              <VStack align="stretch" gap={4}>
                <Heading size="md" color="#1f3b73">
                  Generated Interface
                </Heading>

                {!generatedUI && !loading && !errorText && (
                  <Text color="#6b7a96">
                    L'interfaccia dinamica generata apparirà qui.
                  </Text>
                )}

                {loading && (
                  <Flex align="center" gap={3}>
                    <Spinner color="#3d7bfd" />
                    <Text color="#4e5d78">
                      Generazione dell'interfaccia in corso...
                    </Text>
                  </Flex>
                )}

                {generatedUI && !loading && <Workflow data={generatedUI} />}
              </VStack>
            </Card.Body>
          </Card.Root>
        </Flex>
      </VStack>
    </Box>
  );
}

export default Interface;