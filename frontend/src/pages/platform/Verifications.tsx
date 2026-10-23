/** Coordinator and company verification requests (wireframe `PA_Verifications`, FR-ORG-03, FR-ORG-04). */
import { useTranslation } from "react-i18next";
import { PageHeader } from "../../components/ui";
import { RequestList } from "../coordinator/Students";

export default function PlatformVerifications() {
  const { t } = useTranslation();
  return (
    <>
      <PageHeader title={t("menu.verifications")} subtitle={t("requests.platform_subtitle")} />
      <RequestList />
    </>
  );
}
