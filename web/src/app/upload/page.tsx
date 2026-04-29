import { Shell, PageHeader } from "@/components/Shell";
import { UploadForm } from "./UploadForm";

export default function UploadPage() {
  return (
    <Shell>
      <PageHeader
        title="Upload & Extract"
        subtitle="Drop a vendor bid PDF. The system extracts text directly when a text layer exists, or runs Tesseract OCR (English + Telugu) for scanned documents."
      />
      <UploadForm />
    </Shell>
  );
}
