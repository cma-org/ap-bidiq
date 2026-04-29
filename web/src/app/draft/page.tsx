import { Shell, PageHeader } from "@/components/Shell";
import { DraftForm } from "./DraftForm";

export default function DraftPage() {
  return (
    <Shell>
      <PageHeader
        title="AI Drafting Assistant"
        subtitle="Generate a draft Section 1 (Instructions to Tenderers) for a new project, grounded in the AP clause library and the existing EPCC tender's structural conventions."
      />
      <DraftForm />
    </Shell>
  );
}
