/** The academic supervisor's students and their report counts (wireframe `AS_Dashboard` list; FR-REP-05). */
import { useTranslation } from "react-i18next";
import { PlacementTable } from "../company/Trainees";

export default function AcademicStudents() {
  const { t } = useTranslation();
  return <PlacementTable title={t("menu.my_students")} />;
}
