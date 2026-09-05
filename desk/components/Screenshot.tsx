import { screenshotUrl } from "@/lib/api";

/**
 * A PNG the agent's browser took, served by `GET /screenshots/{name}`.
 *
 * The one place the desk renders a bare `<img>`. `next/image` optimises and
 * caches remote files, and neither is wanted here: these are live artefacts of
 * the run happening on screen, served from whatever host `NEXT_PUBLIC_API_BASE`
 * points at, and a cached screenshot would be a lie.
 */
export function Screenshot({
  path,
  alt,
  className,
}: {
  path: string;
  alt: string;
  className?: string;
}) {
  return (
    // eslint-disable-next-line @next/next/no-img-element -- see above
    <img src={screenshotUrl(path)} alt={alt} className={className} />
  );
}
