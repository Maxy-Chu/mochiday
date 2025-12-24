import { JobSeniority, SelectOption } from "~/types/general"

export const SENIORITY_OPTIONS: SelectOption[] = [
    { value: "all", label: "All" },
    { value: JobSeniority.INTERN, label: "Intern" },
    { value: JobSeniority.NEWGRAD, label: "New Grad" },
    { value: JobSeniority.JUNIOR, label: "Junior" },
    { value: JobSeniority.MID, label: "Mid (3–6 YOE)" },
    { value: JobSeniority.SENIOR, label: "Senior (6+ YOE)" },
];