import { getProfile } from "@/lib/data";
import { IdentityMenu } from "./IdentityMenu";

export async function Identity() {
  const p = await getProfile();
  return (
    <IdentityMenu
      name={p.name}
      regNo={p.reg_no}
      vid={p.vid}
      programme={p.programme}
      section={p.section}
      term={p.term}
    />
  );
}
